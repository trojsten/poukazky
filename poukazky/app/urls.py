from django.urls import path

from poukazky.app.views import (
    CouponDetailView,
    CouponExchangeView,
    CouponFormView,
    CouponPDFView,
)

urlpatterns = [
    path("", CouponFormView.as_view(), name="coupon_form"),
    path("<code:code>/", CouponDetailView.as_view(), name="coupon_detail"),
    path(
        "<code:code>/exchange/<int:provider>/",
        CouponExchangeView.as_view(),
        name="coupon_exchange",
    ),
    path(
        "download_pdf/<job_id>/",
        CouponPDFView.as_view(),
        name="coupon_pdf_download",
    ),
]
