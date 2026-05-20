from poukazky.app.models import TrojstenCoupon
from poukazky.app.render_typst import render_typst


def generate_coupons(coupons: list[TrojstenCoupon]) -> bytes:
    ctx = {}

    ctx["coupons"] = [
        {
            "code": c.code,
            "amount": c.original_amount,
        }
        for c in coupons
    ]

    return render_typst("coupon_trojsten.typ", ctx)
