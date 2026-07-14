import csv

from django import forms
from django.contrib import admin, messages
from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django_admin_action_forms.admin import AdminActionFormsMixin
from django_admin_action_forms.decorators import action_with_form
from django_admin_action_forms.forms import AdminActionForm
from django_no_queryset_admin_actions.admin import NoQuerySetAdminActionsMixin
from django_no_queryset_admin_actions.decorators import no_queryset_action
from rq.job import Job

from poukazky.app.models import ExternalCoupon, Provider, TrojstenCoupon
from poukazky.app.tasks import generate_coupons_pdf


class GenerateCouponForm(AdminActionForm):
    amount = forms.IntegerField(label="Suma")
    count = forms.IntegerField(
        label="Počet poukážok", help_text="Tlačia sa 3 poukážky na stranu"
    )
    expires_at = forms.DateField(label="Expirácia poukážok")


class BulkUpdateCouponForm(AdminActionForm):
    expires_at = forms.DateField(label="Expirácia poukážok")
    note = forms.CharField(label="Poznámka", widget=forms.Textarea(), required=False)


@admin.register(TrojstenCoupon)
class TrojstenCouponAdmin(
    NoQuerySetAdminActionsMixin, AdminActionFormsMixin, admin.ModelAdmin
):
    list_display = [
        "code",
        "is_used",
        "has_expired",
        "original_amount",
        "remaining_amount",
        "created_at",
        "expires_at",
    ]
    search_fields = ["code", "note"]
    readonly_fields = [
        "code",
        "original_amount",
        "created_at",
    ]

    @admin.display(description="minutá", boolean=True, ordering="remaining_amount")
    def is_used(self, value):
        return value.remaining_amount == 0

    @no_queryset_action(description="Vytvoriť nové poukážky")
    @action_with_form(
        GenerateCouponForm,
    )
    def generate_coupon(self, request, data):
        with transaction.atomic():
            coupons = [
                TrojstenCoupon.generate(data["amount"], data["expires_at"]).id
                for _ in range(data["count"])
            ]

        job: Job = generate_coupons_pdf.delay(coupons)  # type:ignore
        return HttpResponseRedirect(
            reverse("coupon_pdf_download", kwargs={"job_id": job.id})
        )

    @admin.display(description="Vygenerovať PDF označených poukážok")
    def regenerate_coupons(self, request, queryset: QuerySet[TrojstenCoupon]):
        job: Job = generate_coupons_pdf.delay(
            list(queryset.values_list("id", flat=True))
        )  # type:ignore
        return HttpResponseRedirect(
            reverse("coupon_pdf_download", kwargs={"job_id": job.id})
        )

    @action_with_form(
        BulkUpdateCouponForm,
        description="Upraviť vybrané poukážky",
    )
    def bulk_update(self, request, queryset, data):
        queryset.update(expires_at=data["expires_at"], note=data["note"])

    actions = [generate_coupon, regenerate_coupons, bulk_update]


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ["name"]


class ImportCSVForm(AdminActionForm):
    csv = forms.FileField(
        label="CSV", help_text="Stĺpce: provider, code, amount, expires_at"
    )

    def clean_csv(self):
        try:
            r = csv.DictReader(
                self.cleaned_data["csv"].read().decode("utf-8").splitlines()
            )

            if not r.fieldnames:
                raise ValidationError("Chýba header")

            if not {"provider", "code", "amount", "expires_at"}.issubset(r.fieldnames):
                raise ValidationError("Nesprávne stĺpce")

        except (csv.Error, ValueError) as e:
            raise ValidationError("Neplatné csv: " + str(e))

        return r


@admin.register(ExternalCoupon)
class ExternalCouponAdmin(
    NoQuerySetAdminActionsMixin, AdminActionFormsMixin, admin.ModelAdmin
):
    list_display = [
        "code",
        "amount",
        "provider__name",
        "created_at",
        "claimed_at",
        "expires_at",
    ]

    @no_queryset_action(description="Importovať poukážky")
    @action_with_form(
        ImportCSVForm,
    )
    def import_coupons(self, request, data):
        providers = {}

        todo = []
        for r in data["csv"]:
            if r["provider"] not in providers:
                try:
                    providers[r["provider"]] = Provider.objects.get(
                        name__iexact=r["provider"]
                    )
                except Provider.DoesNotExist:
                    self.message_user(
                        request,
                        f"Poskytovateľ {r['provider']} sa nenašiel!",
                        level=messages.ERROR,
                    )
                    return

            todo.append(
                ExternalCoupon(
                    code=r["code"],
                    amount=r["amount"],
                    expires_at=r["expires_at"],
                    provider=providers[r["provider"]],
                )
            )

        try:
            ExternalCoupon.objects.bulk_create(todo)
        except IntegrityError:
            self.message_user(
                request,
                "Nejaký kód už existuje!",
                level=messages.ERROR,
            )
            return

        self.message_user(
            request,
            "Úspešne naimportované!",
            level=messages.SUCCESS,
        )

    actions = [import_coupons]
