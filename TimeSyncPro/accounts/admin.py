from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission, Group
from django.db.models import Prefetch

from TimeSyncPro.accounts.models import Profile
from TimeSyncPro.companies.models import Company, Department, Team, Shift

UserModel = get_user_model()


@admin.register(UserModel)
class TSPUserAdmin(UserAdmin):
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile'):
            return qs.filter(profile__company=request.user.profile.company)
        return qs.none()

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets

        # Custom fieldsets based on user role
        if request.user.is_superuser:
            return (
                (None, {'fields': ('email', 'password')}),
                ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
            )
        elif hasattr(request.user, 'profile') and request.user.profile.is_company_admin:
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

        readonly_fields = ['email']
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
                    users__profile__company=request.user.company
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

            # field_querysets = {
            #     "company": Company.objects.filter(id=request.user.profile.company.id),
            #     "department": Department.objects.filter(company=request.user.profile.company),
            #     "team": Team.objects.filter(department__company=request.user.profile.company),
            #     "shift_pattern": ShiftPattern.objects.filter(company=request.user.profile.company),
            #     "manager": Profile.objects.filter(
            #         company=request.user.profile.company,
            #         role='Manager'
            #     ),
            # }
            field_querysets = {
                "company": company_with_related_data.company,
                "department": company_with_related_data.departments.all(),
                "team": company_with_related_data.teams.all(),
                "shift": company_with_related_data.shifts.all(),
                "employee": company_with_related_data.employees.all(),
            }

            if db_field.name in field_querysets:
                kwargs["queryset"] = field_querysets[db_field.name]

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Profile)
class ProfileAdmin(CompanyFilteredAdmin):
    list_display = ('user', 'company', 'role', 'department', 'team')
    list_filter = ('role', 'department', 'team')
    search_fields = ('user__email', 'first_name', 'last_name')