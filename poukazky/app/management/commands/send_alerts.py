from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Count, F, Q
from django.utils import timezone

from poukazky.app.models import ExternalCoupon, Provider
from poukazky.app.utils import send_mail


class Command(BaseCommand):
    help = "Send remainder emails about soon to expire external coupons and providers with low coupon count."

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

        alert_providers = Provider.objects.annotate(
            valid_coupon_cnt=Count(
                "externalcoupon",
                filter=Q(
                    externalcoupon__claimed_by=None, externalcoupon__expires_at__gte=now
                ),
            )
        ).filter(
            coupon_alert_threshold__isnull=False,
            valid_coupon_cnt__lt=F("coupon_alert_threshold"),
        )

        if alert_providers:
            send_mail(
                "Niektorí poskytovatelia majú nedostatok poukážok",
                "provider_coupon_count",
                context={"providers": alert_providers},
            )
