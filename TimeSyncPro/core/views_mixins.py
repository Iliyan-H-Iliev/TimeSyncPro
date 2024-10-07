from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, get_object_or_404

UserModel = get_user_model()


# from TimeSyncPro.accounts.utils import get_obj_company, get_user_by_slug
# TODO move to accounts

class NotAuthenticatedMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('signin user')

        return super().dispatch(request, *args, **kwargs)


class CompanyCheckMixin:

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        user_slug = self.kwargs['slug']

        if hasattr(self, 'get_queryset'):
            queryset = self.get_queryset()
        else:
            queryset = UserModel.objects.all()

        user_to_check = get_object_or_404(queryset, slug=user_slug)

        if user_to_check.company != request.user.company:
            raise PermissionDenied("You can only view profiles within your own company.")

        return super().dispatch(request, *args, **kwargs)



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


# TODO remove company_name and company_slug
class CompanyContextMixin():
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company

        if company:
            context['company'] = company
            context['company_name'] = company.name
            context['company_slug'] = company.slug
        else:
            context['company'] = None
            context['company_name'] = None
            context['company_slug'] = None

        return context
