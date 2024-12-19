from django.contrib import admin

from TimeSyncPro.common.models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "house_number_or_name",
        "line1",
        "line2",
        "street",
        "city",
        "postcode",
        "country",
        "employee",
        "company",
    )
    search_fields = (
        "house_number_or_name",
        "line1",
        "line2",
        "street",
        "city",
        "postcode",
        "country" "employee__email" "employee__profile__first_name",
        "employee__profile__last_name",
    )
    ordering = ("country", "city", "street", "house_number_or_name")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "house_number_or_name",
                    "line1",
                    "line2",
                    "street",
                    "city",
                    "postcode",
                    "country",
                )
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("employee", "company")

        if request.user.is_superuser:
            return qs

        from django.db.models import Q

        qs = qs.filter(
            Q(employee__company=request.user.profile.company)
            | Q(company=request.user.profile.company)
        )

        return qs

    def has_add_permission(self, request):
        return request.user.is_superuser
