from coupon_codes import cc_validate
from django import forms
from django.conf import settings
from django.forms import ValidationError

from poukazky.app.models import TrojstenCoupon


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
