from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import AccessMixin

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.http import url_has_allowed_host_and_scheme

from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from TimeSyncPro.companies.models import Company

UserModel = get_user_model()


# from TimeSyncPro.accounts.utils import get_obj_company, get_user_by_slug
# TODO move to accounts


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


class CompanyAccessMixin:
    def dispatch(self, request, *args, **kwargs):

        user_company = request.user.company

        if not user_company:
            raise PermissionDenied("You must be associated with a company")

        target_company = get_object_or_404(Company, slug=kwargs.get('company_slug'))

        if user_company != target_company:
            raise PermissionDenied("You can only access your own company's data")

        return super().dispatch(request, *args, **kwargs)


class CompanyObjectsAccessMixin:

    def get_company_filed(self):

        company_field = None

        if hasattr(self.model, 'profile'):
            company_field = 'profile__company'
        elif hasattr(self.model, 'company'):
            company_field = 'company'

        return company_field

    def get_queryset(self):
        base_queryset = super().get_queryset() if hasattr(super(), 'get_queryset') else self.model.objects.all()

        if self.request.user.is_superuser:
            return base_queryset

        company_slug = self.kwargs.get('company_slug')

        if not company_slug:
            return base_queryset.none()

        company_field = self.get_company_filed()
        if not company_field:
            return base_queryset.none()

        filters = {f"{company_field}__slug": company_slug}

        return base_queryset.filter(**filters)

    def get_company_permission(self, obj):
        user_company = self.request.user.profile.company

        if not user_company:
            return False

        if hasattr(obj, 'company'):
            obj_company = obj.company
        elif hasattr(obj, 'profile'):
            obj_company = getattr(obj.profile, 'company', None)
        else:
            return False

        return user_company == obj_company

    def dispatch(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()

            if not self.get_company_permission(self.object):
                raise PermissionDenied(
                    f"You can only view {self.model._meta.verbose_name} within your own company."
                )

            return super().dispatch(request, *args, **kwargs)

        except Http404:
            raise PermissionDenied(
                f"You can only view {self.model._meta.verbose_name} within your own company."
            )
        except Exception as e:
            raise PermissionDenied(
                f"An error occurred while checking permissions: {str(e)}"
            )


# class CompanyCheckMixin:
#
#     def get_queryset(self):
#         base_queryset = super().get_queryset() if hasattr(super(), 'get_queryset') else self.model.objects.all()
#         base_queryset = base_queryset.select_related('company')
#         return base_queryset.filter(company=self.request.user.profile.company)
#
#     def dispatch(self, request, *args, **kwargs):
#         try:
#             # Uses Query 1 result
#             self.object = self.get_object()
#             return super().dispatch(request, *args, **kwargs)
#         except Http404:
#             raise PermissionDenied(f"You can only view {self.model.__name__.lower()} within your own company.")


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
class UserDataMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_data'] = {
            'profile': self.request.user.profile,
            'company': self.request.user.profile.company,
            'department': self.request.user.profile.department,
            'team': self.request.user.profile.team,
            'shift': self.request.user.profile.shift,
            'address': self.request.user.profile.address,
            'holiday_approver': self.request.user.profile.get_holiday_approver,
        }
        return context


class AuthenticatedUserMixin(UserPassesTestMixin):

    success_url_name = "profile"

    def test_func(self):
        user = self.request.user
        return not user.is_authenticated

    def get_success_url(self):
        user = self.request.user

        if not hasattr(user, 'profile'):
            return reverse("create_profile_company", kwargs={'slug': user.slug})

        if hasattr(user, 'profile') and hasattr(user, 'slug'):
            return reverse(self.success_url_name, kwargs={'slug': user.slug})

        if hasattr(user, 'profile') and hasattr(user, 'slug') and hasattr(user.profile, 'company'):
            if user.profile is not None and user.profile.company is not None:
                return reverse("dashboard", kwargs={'slug': user.slug})

        return reverse('index')

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(self.get_success_url())
        return redirect(reverse("terms_and_conditions"))

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class BasePermissionMixin(UserPassesTestMixin):

    permission_required = {
        "all": None,
        "department": None,
        "team": None,
    }

    def get_target_profile(self):
        raise NotImplementedError("Subclass must implement get_target_profile()")

    def is_same_department(self, target_profile):
        if target_profile.department and self.request.user.profile.department:
            return target_profile.department == self.request.user.profile.department
        return False

    def is_same_team(self, target_profile):
        if target_profile.team and self.request.user.profile.team:
            return target_profile.team == self.request.user.profile.team
        return False

    def test_func(self):
        target_profile = self.get_target_profile()

        if self.request.user.has_perm(self.permission_required['all']):
            return True

        if self.request.user.has_perm(self.permission_required['department']):
            if self.is_same_department(target_profile):
                return True

        if self.request.user.has_perm(self.permission_required['team']):
            if self.is_same_team(target_profile):
                return True

        return False

    def handle_no_permission(self):
        raise PermissionDenied('You do not have permission to access this resource.')


class EmployeePermissionMixin(BasePermissionMixin):

    permission_required = {
        "all": "accounts.view_all_employees",
        "department": "accounts.view_department_employees",
        "team": "accounts.view_team_employees",
    }

    def get_target_profile(self):
        return self.get_object().profile


class SmallPagination(PageNumberPagination):
    page_size = 4
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,  # Total number of items
            'page_size': self.page_size,  # Items per page
            'current_page': self.page.number,  # Current page number
            'total_pages': self.page.paginator.num_pages,  # Total number of pages
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class ReturnToPageMixin:
    default_return_url = None
    fallback_url = 'dashboard'

    def get_success_url(self):
        return (
                self._get_next_url() or
                self._get_session_url() or
                self._get_referer_url() or
                self._get_default_url() or
                self._get_fallback_url()
        )

    def _is_safe_url(self, url):
        return url and url_has_allowed_host_and_scheme(
            url=url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure()
        )

    def _get_next_url(self):
        next_url = self.request.GET.get('next')
        return next_url if self._is_safe_url(next_url) else None

    def _get_session_url(self):
        session_url = self.request.session.get('previous_page')
        return session_url if self._is_safe_url(session_url) else None

    def _get_referer_url(self):
        referer = self.request.META.get('HTTP_REFERER')
        return referer if self._is_safe_url(referer) else None

    def _get_default_url(self):
        if self.default_return_url:
            try:
                return reverse(self.default_return_url, kwargs={
                    'company_slug': self.request.user.profile.company.slug
                })
            except:
                return None
        return None

    def _get_fallback_url(self):
        try:
            return super().get_success_url()
        except:
            try:
                return reverse(self.fallback_url, kwargs={
                    'slug': self.request.user.slug
                })
            except:
                return reverse('index')

    def get(self, request, *args, **kwargs):
        request.session['previous_page'] = request.META.get('HTTP_REFERER')
        return super().get(request, *args, **kwargs)


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
