from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Permission, Group
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Prefetch

from TimeSyncPro.accounts.models import Profile
from TimeSyncPro.common.models import Address
from TimeSyncPro.companies.models import Company, Department, Team, Shift

UserModel = get_user_model()

admin.site.unregister(Group)


@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser


class GetQuerySetMixin:
    filter = None

    def get_queryset(self, request):
        # Check filter attribute when method is called, not at class definition
        if not self.filter:
            raise ImproperlyConfigured("filter attribute must be set")

        qs = super().get_queryset(request)

        # Check for superuser or staff without company first
        if request.user.is_superuser or (
            request.user.is_staff and
            not hasattr(request.user.profile, 'company')
        ):
            return qs

        # Check for users with company
        if hasattr(request.user.profile, 'company'):
            filter_kwargs = {self.filter: request.user.profile.company}
            return qs.filter(**filter_kwargs)

        # Return empty queryset for other cases
        return qs.none()


@admin.register(UserModel)
class TSPUserAdmin(GetQuerySetMixin, UserAdmin):
    filter = 'profile__company'

    list_display = ('email', 'is_active', 'is_staff', 'company_name', 'role', 'is_company_admin')
    list_filter = ('is_active', 'is_staff', 'profile__role', 'profile__is_company_admin')
    search_fields = ('email', 'profile__first_name', 'profile__last_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Status', {'fields': ('is_active', 'is_staff')}),
        ('Groups and Permissions', {
            'fields': ('groups', 'user_permissions'),
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    def has_add_permission(self, request):
        # Allow only superusers or users with specific permission
        return request.user.is_superuser or request.user.has_perm('auth.add_user')

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets

        # Custom fieldsets based on user role
        if request.user.is_superuser:
            return (
                (None, {'fields': ('email', 'password')}),
                ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
            )
        elif hasattr(request.user.profile, 'company') and request.user.profile.is_company_admin:
            return (
                (None, {'fields': ('email', 'password')}),
                ('Permissions', {'fields': ('is_active', 'groups')}),
            )
        else:
            return (
                (None, {'fields': ('email',)}),
                ('Permissions', {'fields': ('is_active',)}),
            )

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []

        readonly_fields = ['email', "password1", "password2"]
        if not (hasattr(request.user, 'profile') and request.user.profile.is_company_admin):
            readonly_fields.extend(['is_staff', 'groups'])
        return readonly_fields

    def company_name(self, obj):
        return obj.company.name if obj.company else '-'

    company_name.short_description = 'Company'

    def role(self, obj):
        return obj.profile.role if hasattr(obj, 'profile') else '-'

    role.short_description = 'Role'

    def is_company_admin(self, obj):
        return obj.profile.is_company_admin if hasattr(obj, 'profile') else False

    is_company_admin.boolean = True
    is_company_admin.short_description = 'Company Admin'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "groups":
                kwargs["queryset"] = Group.objects.filter(
                    user__profile__company=request.user.company
                ).distinct()
            elif db_field.name == "user_permissions":
                if request.user.profile.is_company_admin:
                    kwargs["queryset"] = Permission.objects.all()
                else:
                    kwargs["queryset"] = Permission.objects.none()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "company":
                kwargs["queryset"] = request.user.profile.company
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CompanyFilteredAdmin(admin.ModelAdmin):
    readonly_fields = ("address",)

    @staticmethod
    def get_company_filtered_queryset(queryset, request):
        if not request.user.is_superuser:
            return queryset.filter(company=request.user.profile.company)
        return queryset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:

            company_with_related_data = Company.objects.prefetch_related(
                Prefetch('teams', queryset=Team.objects.all()),
                Prefetch('shifts', queryset=Shift.objects.all()),
                Prefetch('departments', queryset=Department.objects.all()),
                Prefetch('employees', queryset=Profile.objects.all()),
            ).get(id=request.user.profile.company.id)

            field_querysets = {
                "user": UserModel.objects.filter(profile__company=request.user.profile.company),
                "company": Company.objects.filter(id=request.user.profile.company.id),
                "department": company_with_related_data.departments.filter(company=request.user.profile.company),
                "team": company_with_related_data.teams.filter(company=request.user.profile.company),
                "shift": company_with_related_data.shifts.filter(company=request.user.profile.company),
                "employee": company_with_related_data.employees.filter(company=request.user.profile.company),
            }

            if db_field.name in field_querysets:
                kwargs["queryset"] = field_querysets[db_field.name]

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Profile)
class ProfileAdmin(GetQuerySetMixin, CompanyFilteredAdmin):
    filter = 'company'

    list_display = ('user', 'company', 'role', 'department', 'team')
    list_filter = ('role', 'department', 'team')
    search_fields = ('user__email', 'first_name', 'last_name')

    def has_add_permission(self, request):
        # Allow only superusers or users with specific permission
        return request.user.is_superuser or request.user.has_perm('auth.add_user')

