from django.contrib import admin

from poukazky.app.models import ExternalCoupon, Provider, TrojstenCoupon

# Register your models here.


@admin.register(TrojstenCoupon)
class TrojstenCouponAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "original_amount",
        "remaining_amount",
        "created_at",
        "expires_at",
    ]


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(ExternalCoupon)
class ExternalCouponAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "amount",
        "provider__name",
        "created_at",
        "claimed_at",
        "expires_at",
    ]
