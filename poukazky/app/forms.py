from datetime import timedelta

from coupon_codes import cc_validate
from django import forms
from django.conf import settings
from django.forms import ValidationError
from django.utils import timezone

from poukazky.app.models import ExternalCoupon, Provider, TrojstenCoupon


class CouponSearchForm(forms.Form):
    code = forms.CharField(
        label="Kód poukážky",
        widget=forms.TextInput(
            attrs={
                "placeholder": "-".join(
                    "X" * settings.COUPON_PART_LEN for _ in range(settings.COUPON_PARTS)
                )
            }
        ),
    )

    def clean_code(self) -> str:
        value = self.cleaned_data.get("code")

        if value is None:
            raise ValidationError("Zadaj kód!")

        parsed = cc_validate(
            value, n_parts=settings.COUPON_PARTS, part_len=settings.COUPON_PART_LEN
        )

        if parsed == "":
            raise ValidationError("Zadaj platný kód")

        coupon = TrojstenCoupon.objects.filter(code=parsed)

        if not coupon.exists():
            raise ValidationError("Zadaj platný kód")

        return parsed


class CouponExchangeForm(forms.Form):
    amount = forms.ChoiceField(label="Hodnota")

    def __init__(self, provider: Provider, max_amount: int, **kwargs):
        super().__init__(**kwargs)
        expiration = timezone.now().date() + timedelta(
            days=settings.MIN_EXPIRATION_DAYS
        )

        self.fields["amount"].choices = [
            (c["amount"], f"{c['amount']} €")
            for c in ExternalCoupon.objects.filter(
                provider=provider,
                claimed_by=None,
                amount__lte=max_amount,
                expires_at__gte=expiration,
            )
            .order_by("amount")
            .values("amount")
            .distinct()
        ]
