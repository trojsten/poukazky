from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, FormView

from poukazky.app.forms import CouponSearchForm
from poukazky.app.models import TrojstenCoupon


class CouponSessionMixin(View):
    def dispatch(self, *args, **kwargs):
        validated_codes = self.request.session.get("codes", [])

        code = kwargs.get("code")
        if code is None or code not in validated_codes:
            return HttpResponseRedirect(reverse("coupon_form") + f"?code={code or ''}")

        return super().dispatch(*args, **kwargs)


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
        return TrojstenCoupon.objects.get(code=self.kwargs.get("code"))
