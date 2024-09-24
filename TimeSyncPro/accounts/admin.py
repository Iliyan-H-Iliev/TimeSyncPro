from django.contrib import admin
from django.contrib.auth import get_user_model

from TimeSyncPro.accounts.models import Company, Profile

UserModel = get_user_model()


# Register your models here.
@admin.register(UserModel)
class UserModelAdmin(admin.ModelAdmin):

    list_display = [
        'email',
        'date_joined',
        'is_staff',
        'is_active',
    ]

    search_fields = [
        'email',
        'date_joined',
    ]

    list_filter = [
        'is_staff',
        'is_active',
    ]


# @admin.register(Company)
# class CompanyAdmin(admin.ModelAdmin):
#
#     list_display = [
#         'company_name',
#         'user',
#     ]
#
#     search_fields = [
#         'company_name',
#         'user',
#     ]
#
#     list_filter = [
#         'company_name',
#         'user',
#     ]


@admin.register(Profile)
class EmployeeAdmin(admin.ModelAdmin):

    list_display = [
        'first_name',
        'last_name',
        'employee_id',
        'date_of_hire',
        'days_off_left',
        'phone_number',
        'address',
        'date_of_birth',
        'profile_picture',
        'company',
    ]

    search_fields = [
        'first_name',
        'last_name',
        'employee_id',
        'date_of_hire',
        'days_off_left',
        'phone_number',
        'address',
        'date_of_birth',
        'profile_picture',
        'company',
    ]

    list_filter = [
        'first_name',
        'last_name',
        'employee_id',
        'date_of_hire',
        'days_off_left',
        'phone_number',
        'address',
        'date_of_birth',
        'profile_picture',
        'company',
    ]