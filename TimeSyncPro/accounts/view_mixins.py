from django.contrib.auth.mixins import UserPassesTestMixin, AccessMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

from TimeSyncPro.accounts.models import Profile


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


class UserBySlugMixin:
    def get_object(self):
        queryset = self.queryset
        user_slug = self.kwargs['slug']
        user_to_edit = queryset.get(user_slug=user_slug)
        return user_to_edit


class SuccessUrlMixin:
    success_url = "index"

    def get_success_url(self):
        user = self.request.user
        # Ensure the user is authenticated before accessing attributes
        if user.is_authenticated:
            return reverse(
                self.success_url,
                kwargs={
                    'slug': user.slug,
                    "company_slug": user.profile.company.slug
                }
            )
        return reverse(self.success_url)


class DynamicPermissionMixin:

    @staticmethod
    def get_object_class_name(obj):
        if obj.__class__.__name__ == 'TimeSyncProUser':
            return obj.profile.role.lower().replace(' ', '_')
        return obj.__class__.__name__.lower()

    def get_action_permission_codename(self, obj, action: str):
        obj_class_name = self.get_object_class_name(obj)
        return f"{action}_{obj_class_name}"

    def get_action_permission(self, obj, action: str):
        obj_app_label = obj._meta.app_label
        permission_codename = self.get_action_permission_codename(obj, action)
        return f"{obj_app_label}.{permission_codename}"

    @staticmethod
    def get_all_user_permissions( user):
        all_permissions = user.get_all_permissions()
        print(all_permissions)
        return user.get_all_permissions()

    def has_needed_permission(self, user, obj, action):
        try:
            needed_permission_codename = self.get_action_permission_codename(obj, action)
        except AttributeError:
            return False
        try:
            user_permissions_codenames = user.user_permissions_codenames
        except AttributeError:
            return False

        has_permission = needed_permission_codename in user_permissions_codenames
        return has_permission


# TODO Fix this
class IsAuthorizedUserMixin(UserPassesTestMixin):

    @staticmethod
    def _get_obj_company(obj_to_edit):
        try:
            return obj_to_edit.company
        except AttributeError as e:
            return obj_to_edit

    def test_func(self, *args, **kwargs):
        user = self.request.user
        obj_to_edit = self.get_object()

        return (
                user.company == self._get_obj_company(obj_to_edit)
        )

    def handle_no_permission(self):
        messages.error(self.request, "You are not authorized to access this page.")
        return redirect('index')


