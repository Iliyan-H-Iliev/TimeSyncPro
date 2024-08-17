from django.contrib.auth.mixins import UserPassesTestMixin, AccessMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

from TimeSyncPro.accounts.models import Employee
from TimeSyncPro.accounts.utils import get_obj_company, get_user_by_slug


class OwnerRequiredMixin(AccessMixin):
    def _handle_no_permission(self):
        obj = self.get_object()

        if not self.request.user.is_authenticated or obj != self.request.user:
            return self.handle_no_permission()
        return None

    def get(self, *args, **kwargs):
        response = self._handle_no_permission()
        if response:
            return response
        return super().get(*args, **kwargs)


class CompanyContextMixin():
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.get_company

        context['company'] = company if company else None
        context['company_name'] = company.company_name if company else None
        context['employees'] = Employee.objects.filter(company=company) if company else None

        return context


class UserBySlugMixin:
    def get_object(self):
        user_slug = self.kwargs['slug']
        user_to_edit = get_user_by_slug(user_slug)
        return user_to_edit


class SuccessUrlMixin:
    success_url = "index"

    def get_success_url(self):
        user = self.request.user
        return reverse(
            'profile',
            kwargs={
                'slug': user.slug,
                "company_name": user.get_company_name
            }
        )



# class UserGroupRequiredMixin(UserPassesTestMixin):
#     allowed_groups = []
#
#     def test_func(self):
#         return (
#                 self.request.user.is_authenticated and
#                 self.request.user.groups.filter(name__in=self.allowed_groups).exists()
#         )
#
#     def handle_no_permission(self):
#         if not self.request.user.is_authenticated:
#             messages.info(self.request, "You are not authorized to access this page.")
#             return redirect('signin user')
#         else:
#             messages.error(self.request, "Only HR and Company users can register employees.")
#             return redirect('index')


class DynamicPermissionMixin:

    @staticmethod
    def get_object_class_name(obj):

        if obj.__class__.__name__ == 'TimeSyncProUser':

            if obj.is_company:
                return obj.related_instance.__class__.__name__.lower()

            return obj.related_instance.role.lower().replace(' ', '_')

        return obj.__class__.__name__.lower()

    def get_action_permission_codename(self, obj, action: str):
        obj_class_name = self.get_object_class_name(obj)
        return f"{action}_{obj_class_name}"

    def get_action_permission(self, obj, action: str):

        obj_app_label = obj._meta.app_label
        permission_codename = self.get_action_permission_codename(obj, action)

        return f"{obj_app_label}.{permission_codename}"

    # def get_action_permission_codename(self, obj, action: str):
    #     permission = self.get_action_permission(obj, action)
    #     print(permission)
    #     return permission.split('.')[-1]

    def has_needed_permission(self, user, obj, action):

        try:
            needed_permission_codename = self.get_action_permission_codename(obj, action)
        except AttributeError:
            return False

        try:
            user_permissions_codenames = user.user_permissions_codenames
            print(user_permissions_codenames)
        except AttributeError:
            return False

        has_permission = needed_permission_codename in user_permissions_codenames
        return has_permission


class IsAuthorizedUserMixin(UserPassesTestMixin):
    def test_func(self, *args, **kwargs):
        user = self.request.user
        obj_to_edit = self.get_object()

        return (
                user.get_company == get_obj_company(obj_to_edit)
        )

    def handle_no_permission(self):
        messages.error(self.request, "You are not authorized to access this page.")
        return redirect('index')


class IsCompanyUserMixin(UserPassesTestMixin):
    def test_func(self, *args, **kwargs):
        user = self.request.user
        return user.is_company

    def handle_no_permission(self):
        messages.error(self.request, "You are not authorized to access this page.")
        return redirect('index')


