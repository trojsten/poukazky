from typing import Any

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.views import View
from django.views.generic import DetailView, FormView

from poukazky.app.forms import CouponExchangeForm, CouponSearchForm
from poukazky.app.models import Provider, TrojstenCoupon


class CouponSessionMixin(View):
    def dispatch(self, *args, **kwargs):
        validated_codes = self.request.session.get("codes", [])

        code = kwargs.get("code")
        if code is None or code not in validated_codes:
            return HttpResponseRedirect(reverse("coupon_form") + f"?code={code or ''}")

        return super().dispatch(*args, **kwargs)

    @cached_property
    def coupon(self):
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

    def get_object(self, *args, **kwargs):
        return self.coupon

    def get_available_providers(self):
        return Provider.objects.all()

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
        return ctx

    def get_form_kwargs(self) -> dict[str, Any]:
        kw = super().get_form_kwargs()
        kw["provider"] = self.provider
        kw["max_amount"] = self.coupon.remaining_amount
        return kw
