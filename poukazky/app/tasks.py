import secrets
from datetime import timedelta
from io import BytesIO

from django.core.files.storage import default_storage
from django.utils import timezone
from django_rq import job

from poukazky.app.models import ExternalCoupon, TrojstenCoupon
from poukazky.app.utils import generate_coupons, send_mail


@job
def coupon_exchanged(coupon_id: int):
    coupon = ExternalCoupon.objects.get(id=coupon_id)

    send_mail(
        "Trojsten poukážka bola práve vymenená",
        "coupon_exchanged",
        context={"coupon": coupon},
    )


@job
def generate_coupons_pdf(coupon_ids: list[int]) -> str:
    coupons = TrojstenCoupon.objects.filter(id__in=coupon_ids)
    pdf_bytes = generate_coupons(coupons)

    filename = f"tmp_coupons/{secrets.token_hex(32)}.pdf"
    default_storage.save(filename, BytesIO(pdf_bytes))
    cleanup_coupon_pdfs.delay()
    return filename


@job
def cleanup_coupon_pdfs():
    cutoff = timezone.now() - timedelta(minutes=30)
    _, filenames = default_storage.listdir("tmp_coupons")

    for filename in filenames:
        path = f"tmp_coupons/{filename}"
        if default_storage.get_modified_time(path) < cutoff:
            default_storage.delete(path)
