from datetime import date, timedelta

from coupon_codes.coupon_codes import cc_generate
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.utils import timezone


class TrojstenCoupon(models.Model):
    id: int

    code = models.CharField(
        max_length=32, unique=True, editable=False, verbose_name="kód"
    )

    original_amount = models.PositiveIntegerField(
        editable=False, verbose_name="pôvodná hodnota"
    )
    remaining_amount = models.PositiveIntegerField(verbose_name="zostávajúca hodnota")

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="dátum vytvorenia"
    )
    expires_at = models.DateField(verbose_name="dátum expirácie")

    note = models.TextField(blank=True, verbose_name="poznámka")

    class Meta:
        verbose_name = "Trojsten poukážka"
        verbose_name_plural = "Trojsten poukážky"

        ordering = ["code"]

    def __str__(self) -> str:
        return self.code

    @property
    @admin.display(description="Expirovala", boolean=True, ordering="expires_at")
    def has_expired(self):
        return timezone.now().date() > self.expires_at

    @classmethod
    def generate(cls, amount: int, expires_at: date):
        while True:
            code = cc_generate(
                n_parts=settings.COUPON_PARTS, part_len=settings.COUPON_PART_LEN
            )

            if not TrojstenCoupon.objects.filter(code=code).exists():
                break

        return TrojstenCoupon.objects.create(
            code=code,
            original_amount=amount,
            remaining_amount=amount,
            expires_at=expires_at,
        )


class Provider(models.Model):
    id: int

    name = models.CharField(max_length=64, unique=True, verbose_name="názov")
    description = models.TextField(blank=True, verbose_name="ďalšie informácie")

    logo = models.ImageField(blank=True, verbose_name="logo")

    class Meta:
        verbose_name = "poskytovateľ"
        verbose_name_plural = "poskytovatelia"

        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ExternalCoupon(models.Model):
    id: int

    code = models.CharField(max_length=64, verbose_name="kód")
    amount = models.PositiveIntegerField(verbose_name="hodnota")
    provider = models.ForeignKey(
        Provider, on_delete=models.RESTRICT, verbose_name="poskytovateľ"
    )
    provider_id: int

    claimed_by = models.ForeignKey(
        TrojstenCoupon,
        on_delete=models.RESTRICT,
        blank=True,
        null=True,
        verbose_name="vymenené",
    )
    claimed_by_id: int | None
    claimed_at = models.DateTimeField(
        blank=True, null=True, verbose_name="dátum vymenenia"
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="dátum vytvorenia"
    )
    expires_at = models.DateField(verbose_name="dátum expirácie")

    class Meta:
        verbose_name = "poukážka od poskytovateľa"
        verbose_name_plural = "poukážky od poskytovateľa"

        constraints = [
            models.UniqueConstraint(
                "code", "provider", name="externalcoupon__code__provider__unique"
            )
        ]
        ordering = ["-claimed_by", "-expires_at", "code"]

    def __str__(self) -> str:
        return f"{self.provider.name} / {self.code}"

    @property
    def user_expiration(self):
        if not self.claimed_at:
            return None
        return (self.claimed_at + timedelta(days=settings.MIN_EXPIRATION_DAYS)).date()
