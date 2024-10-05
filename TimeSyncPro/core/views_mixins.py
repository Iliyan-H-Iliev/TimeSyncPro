from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect, get_object_or_404


# from TimeSyncPro.accounts.utils import get_obj_company, get_user_by_slug
# TODO move to accounts

class NotAuthenticatedMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('signin user')

        return super().dispatch(request, *args, **kwargs)


class CompanyCheckMixin:
    redirect_url = 'index'  # Default redirect URL

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        user_slug = self.kwargs['slug']

        # Fetch the user with related Employee and Company in a single query
        user_to_check = get_object_or_404(self.queryset, slug=user_slug)

        # Compare the user's company with the fetched object's company
        if user.profile.company.id != user_to_check.profile.company.id:
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
