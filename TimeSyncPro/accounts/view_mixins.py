
from django.shortcuts import redirect

from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class OwnerRequiredMixin:

    def _handle_no_permission(self):
        return redirect('index')  # or wherever you want to redirect

    def dispatch(self, request, *args, **kwargs):
        # Get the user instead of the profile
        user = get_object_or_404(get_user_model(), slug=kwargs.get('slug'))

        # Check if the requesting user is the owner
        if request.user != user:
            return self._handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    # def post(self, request, *args, **kwargs):
    #     # Same check for POST requests
    #     user = get_object_or_404(UserModel, slug=kwargs.get('slug'))
    #
    #     if request.user != user:
    #         return self._handle_no_permission()
    #
    #     return super().post(request, *args, **kwargs)


class SuccessUrlMixin:
    success_url = "index"

    def get_success_url(self):
        user = self.request.user

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
        if obj.__class__.__name__ == 'TSPUser':
            if obj.profile.is_company_admin:
                return 'company_admin'

            if obj.profile.role:
                return obj.profile.role.lower().replace(' ', '_')

            if obj.is_superuser:
                return 'superuser'

            if obj.is_staff:
                return 'staff'

        return obj.__class__.__name__.lower()

    def get_action_permission_codename(self, obj, action: str):
        obj_class_name = self.get_object_class_name(obj)
        return f"{action}_{obj_class_name}"

    def get_action_permission(self, obj, action: str):
        obj_app_label = obj._meta.app_label
        permission_codename = self.get_action_permission_codename(obj, action)
        return f"{obj_app_label}.{permission_codename}"

    # @staticmethod
    # def get_all_user_permissions( user):
    #     all_permissions = user.get_all_permissions()
    #     print(all_permissions)
    #     return user.get_all_permissions()

    # def has_needed_permission(self, user, obj, action):
    #
    #     try:
    #         needed_permission_codename = self.get_action_permission_codename(obj, action)
    #     except AttributeError:
    #         return False
    #     try:
    #         user_permissions_codenames = user.user_permissions_codenames
    #     except AttributeError:
    #         return False
    #
    #     has_permission = needed_permission_codename in user_permissions_codenames
    #     return has_permission

    def has_needed_permission(self, user, obj, action):
        try:
            needed_permission_codename = self.get_action_permission_codename(obj, action)
            # Use cached permissions
            if hasattr(user, 'user_permissions_codenames'):
                return needed_permission_codename in user.user_permissions_codenames

            # Fallback if not cached
            all_permissions = user.get_all_permissions()
            user.user_permissions_codenames = {
                perm.split('.')[-1] for perm in all_permissions
            }
            return needed_permission_codename in user.user_permissions_codenames

        except AttributeError:
            return False


class CRUDUrlsMixin:
    crud_url_names = {
        'create': '',
        'detail': '',
        'update': '',
        'delete': ''
    }

    button_names = {
        'create': '',
        'detail': '',
        'update': '',
        'delete': '',
    }

    def get_crud_urls(self):
        model_name = self.model._meta.model_name
        return {
            f'{action}_url': pattern.format(model=model_name)
            for action, pattern in self.crud_url_names.items()
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_crud_urls())
        context['button_names'] = self.button_names
        return context
