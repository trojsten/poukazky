from datetime import timedelta

from coupon_codes import cc_validate
from django import forms
from django.conf import settings
from django.forms import ValidationError
from django.utils import timezone
from turnstile.fields import TurnstileField

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
    turnstile = TurnstileField(theme="light")

    # we use clean instead of clean_code, so that turnstile validation runs
    # first and we only validate code if turnstile validation passed
    def clean(self):
        cleaned_data = super().clean()

        value = cleaned_data["code"]
        del cleaned_data["code"]

        if "turnstile" not in cleaned_data or self.errors:
            return cleaned_data

        if value is None:
            self.add_error("code", ValidationError("Zadaj kód!"))
            return cleaned_data

        if value in {
            "XXXX-XXXX-XXXX-XXXX",
            "TROJ-STEN-TECH-TEAM",
            "TROJ-STEN-POUK-AZKA",
            "TROJ-STEN-POUK-AZKY",
        }:
            self.add_error(
                "code", ValidationError("Dobrý pokus, ale zadaj prosím platný kód")
            )
            return cleaned_data

        value = [
            c for c in value if c.lower() in "1234567890qwertyuiopasdfghjklzxcvbnm"
        ]
        value = "-".join("".join(value[i : i + 4]) for i in range(0, len(value), 4))

        parsed = cc_validate(
            value, n_parts=settings.COUPON_PARTS, part_len=settings.COUPON_PART_LEN
        )

        if parsed == "":
            self.add_error("code", ValidationError("Zadaj platný kód"))
            return cleaned_data

        coupon = TrojstenCoupon.objects.filter(code=parsed)

        if not coupon.exists():
            self.add_error("code", ValidationError("Zadaj platný kód"))
            return cleaned_data

        cleaned_data["code"] = parsed

        return cleaned_data


class CouponExchangeForm(forms.Form):
    amount = forms.ChoiceField(label="Dostupné hodnoty")

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
