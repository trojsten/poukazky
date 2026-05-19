from django.db import models
from django.utils import timezone


class TrojstenCoupon(models.Model):
    id: int

    code = models.CharField(max_length=32, unique=True)

    original_amount = models.PositiveIntegerField()
    remaining_amount = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateField()

    note = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code

    @property
    def has_expired(self):
        return timezone.now().date() > self.expires_at


class Provider(models.Model):
    id: int

    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)

    logo = models.ImageField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ExternalCoupon(models.Model):
    id: int

    code = models.CharField(max_length=64)
    amount = models.PositiveIntegerField()
    provider = models.ForeignKey(Provider, on_delete=models.RESTRICT)
    provider_id: int

    claimed_by = models.ForeignKey(
        TrojstenCoupon, on_delete=models.RESTRICT, blank=True, null=True
    )
    claimed_by_id: int | None
    claimed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "code", "provider", name="externalcoupon__code__provider__unique"
            )
        ]
        ordering = ["-claimed_by", "-expires_at", "code"]

    def __str__(self) -> str:
        return f"{self.provider.name} / {self.code}"
