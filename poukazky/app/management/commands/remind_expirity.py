from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from poukazky.app.models import ExternalCoupon
from poukazky.app.utils import send_mail


class Command(BaseCommand):
    help = "Send remainder emails about soon to expire external coupons"

    def execute(self, *args, **options):
        now = timezone.now()
        soon_to_expire = ExternalCoupon.objects.filter(
            claimed_by=None,
            expires_at__lte=now + timedelta(days=30),
            expires_at__gte=now,
        )

        if soon_to_expire:
            send_mail(
                "Niektoré poukážky expirujú čoskoro",
                "coupon_expire",
                context={"coupons": soon_to_expire},
            )
