from coupon_codes.coupon_codes import cc_validate
from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, register_converter


class CouponCodeConverter:
    regex = f"([a-z0-9A-Z]{{{settings.COUPON_PART_LEN}}}-){{{settings.COUPON_PARTS - 1}}}[a-z0-9A-Z]{{{settings.COUPON_PART_LEN}}}"

    def to_python(self, value):
        return cc_validate(
            value, n_parts=settings.COUPON_PARTS, part_len=settings.COUPON_PART_LEN
        )

    def to_url(self, value):
        return cc_validate(
            value, n_parts=settings.COUPON_PARTS, part_len=settings.COUPON_PART_LEN
        )


register_converter(CouponCodeConverter, "code")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("poukazky.users.urls")),
    path("", include("poukazky.app.urls")),
] + debug_toolbar_urls()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
