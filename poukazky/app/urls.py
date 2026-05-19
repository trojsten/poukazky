from django.urls import path

from poukazky.app.views import CouponDetailView, CouponFormView

urlpatterns = [
    path("", CouponFormView.as_view(), name="coupon_form"),
    path("<code:code>/", CouponDetailView.as_view(), name="coupon_detail"),
]
