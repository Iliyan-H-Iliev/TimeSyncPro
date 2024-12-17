from django.contrib import admin
from django.db.models import Prefetch

from TimeSyncPro.accounts.models import Profile
from TimeSyncPro.companies.models import Company, Department, Team


# Register your models here.


class SetCompanyAndApproverMixin:
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:

            field_querysets = {
                "company": Company.objects.filter(id=request.user.profile.company.id),
                "holiday_approver": Profile.objects.filter(
                    company=request.user.profile.company
                ),
            }

            if db_field.name in field_querysets:
                kwargs["queryset"] = field_querysets[db_field.name]

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            if "company" in fields:
                fields.remove("company")
        return fields

    def save_model(self, request, obj, form, change):
        if not change:
            obj.company = request.user.profile.company
        super().save_model(request, obj, form, change)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    readonly_fields = ("address",)

    list_display = (
        "name",
        "email",
        "holiday_approver",
        "annual_leave",
        "max_carryover_leave",
        "minimum_leave_notice",
        "maximum_leave_days_per_request",
    )

    search_fields = (
        "name",
        "email",
    )

    ordering = ("name",)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs.select_related("holiday_approver")

        if request.user.is_superuser:
            return qs

        return qs.filter(pk=request.user.profile.company.pk)


@admin.register(Department)
class DepartmentAdmin(SetCompanyAndApproverMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "holiday_approver",
        "company",
    )

    search_fields = (
        "name",
        "company__name",
    )

    ordering = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("company")

        if request.user.is_superuser:
            return qs

        return qs.filter(company=request.user.profile.company)


@admin.register(Team)
class TeamAdmin(SetCompanyAndApproverMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "holiday_approver",
        "company",
    )

    search_fields = (
        "name",
        "company__name",
    )

    ordering = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("company", "holiday_approver")

        if request.user.is_superuser:
            return qs

        return qs.filter(company=request.user.profile.company)
