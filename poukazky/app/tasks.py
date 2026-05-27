from django_rq import job

from poukazky.app.models import ExternalCoupon
from poukazky.app.utils import send_mail


@job
def coupon_exchanged(coupon_id: int):
    coupon = ExternalCoupon.objects.get(id=coupon_id)

    send_mail(
        "Trojsten poukážka bola práve vymenená",
        "coupon_exchanged",
        context={"coupon": coupon},
    )
