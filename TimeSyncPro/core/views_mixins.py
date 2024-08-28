from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import  redirect

from TimeSyncPro.accounts.utils import get_obj_company, get_user_by_slug


class AuthenticatedViewMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('signin user')

        return super(AuthenticatedViewMixin, self).dispatch(request, *args, **kwargs)


class CompanyCheckMixin:
    redirect_url = 'index'  # Default redirect URL

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        user_slug = self.kwargs['slug']
        obj_to_check = get_user_by_slug(user_slug)

        if user.company != get_obj_company(obj_to_check):
            return redirect(self.get_redirect_url())
        return super().dispatch(request, *args, **kwargs)

    def get_redirect_url(self):
        return self.redirect_url


class MultiplePermissionsRequiredMixin(AccessMixin):
    permissions_required = []

    def has_permissions(self):
        user = self.request.user
        perm = self.permissions_required
        user_permissions = user.get_all_permissions()
        return any(perm in user_permissions for perm in self.permissions_required)

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permissions():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

