from typing import Any

import django_rq
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.timezone import timedelta
from django.views import View
from django.views.generic import DetailView, FormView
from rq.exceptions import NoSuchJobError
from rq.job import Job, JobStatus

from poukazky.app.forms import CouponExchangeForm, CouponSearchForm
from poukazky.app.models import ExternalCoupon, Provider, TrojstenCoupon
from poukazky.app.tasks import coupon_exchanged


class CouponSessionMixin(View):
    check_expiration: bool = True

    def dispatch(self, *args, **kwargs):
        validated_codes = self.request.session.get("codes", [])

        code = kwargs.get("code")
        if code is None or code not in validated_codes:
            return HttpResponseRedirect(reverse("coupon_form") + f"?code={code or ''}")

        if self.check_expiration and self.coupon.has_expired:
            return redirect("coupon_detail", code=code)

        return super().dispatch(*args, **kwargs)

    @cached_property
    def coupon(self) -> TrojstenCoupon:
        return get_object_or_404(TrojstenCoupon, code=self.kwargs["code"])


class CouponFormView(FormView):
    template_name = "app/search.html"
    form_class = CouponSearchForm

    def get_initial(self):
        if code := self.request.GET.get("code"):
            return {"code": code}

        return {}

    def form_valid(self, form):
        self.request.session["codes"] = self.request.session.get("codes", []) + [
            form.cleaned_data["code"]
        ]

        return redirect("coupon_detail", code=form.cleaned_data["code"])


class CouponDetailView(CouponSessionMixin, DetailView):
    template_name = "app/detail.html"
    model = TrojstenCoupon

    check_expiration = False

    def get_object(self, *args, **kwargs):
        return self.coupon

    def get_available_providers(self):
        expiration = timezone.now().date() + timedelta(
            days=settings.MIN_EXPIRATION_DAYS
        )

        return Provider.objects.annotate(
            available=Exists(
                ExternalCoupon.objects.filter(
                    provider_id=OuterRef("pk"),
                    claimed_by=None,
                    amount__lte=self.coupon.remaining_amount,
                    expires_at__gte=expiration,
                )
            )
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["providers"] = self.get_available_providers()
        return ctx


class CouponExchangeView(CouponSessionMixin, FormView):
    template_name = "app/exchange.html"
    form_class = CouponExchangeForm

    @cached_property
    def provider(self):
        return get_object_or_404(Provider, id=self.kwargs["provider"])

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["coupon"] = self.coupon
        ctx["provider"] = self.provider
        ctx["expiration_days"] = settings.MIN_EXPIRATION_DAYS
        return ctx

    def get_form_kwargs(self) -> dict[str, Any]:
        kw = super().get_form_kwargs()
        kw["provider"] = self.provider
        kw["max_amount"] = self.coupon.remaining_amount
        return kw

    def form_valid(self, form):
        expiration = timezone.now().date() + timedelta(
            days=settings.MIN_EXPIRATION_DAYS
        )

        with transaction.atomic():
            external_coupon: ExternalCoupon = (
                ExternalCoupon.objects.filter(
                    provider=self.provider,
                    claimed_by=None,
                    amount=form.cleaned_data["amount"],
                    expires_at__gte=expiration,
                )
                .order_by("expires_at")
                .select_for_update()
                .first()
            )

            external_coupon.claimed_by = self.coupon
            external_coupon.claimed_at = timezone.now()

            self.coupon.remaining_amount -= external_coupon.amount

            external_coupon.save()
            self.coupon.save()

            coupon_exchanged.delay(external_coupon.id)

        return redirect("coupon_detail", code=self.coupon.code)


class CouponPDFView(PermissionRequiredMixin, View):
    permission_required = "app.create_trojstencoupon"

    def get(self, request, *args, **kwargs):
        conn = django_rq.get_connection()
        try:
            job = Job.fetch(kwargs["job_id"], conn)
            if job.func_name != "poukazky.app.tasks.generate_coupons_pdf":
                raise Http404()
        except NoSuchJobError:
            raise Http404()

        if job.get_status() != JobStatus.FINISHED:
            resp = HttpResponse("Rendering...")
            resp.headers["Refresh"] = 5
            return resp

        return HttpResponseRedirect(default_storage.url(job.result))
