from typing import Iterable

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from poukazky.app.models import TrojstenCoupon
from poukazky.app.render_typst import render_typst


def generate_coupons(coupons: Iterable[TrojstenCoupon]) -> bytes:
    ctx = {}

    ctx["coupons"] = [
        {
            "code": c.code,
            "amount": c.original_amount,
        }
        for c in coupons
    ]

    return render_typst("coupon_trojsten.typ", ctx)


def send_mail(
    subject: str,
    template_name: str,
    emails: list[str] = settings.COUPON_ADMINS,
    context: dict = {},
    reply_to: list[str] = ["roots@trojsten.sk"],
):
    text_content = render_to_string(f"emails/{template_name}.txt", context)
    html_content = render_to_string(f"emails/{template_name}.html", context)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        "Trojsten poukážky <noreply@trojsten.sk>",
        emails,
        reply_to=reply_to,
    )

    email.attach_alternative(html_content, "text/html")

    email.send()
