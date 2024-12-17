from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse

from django.urls import NoReverseMatch
import logging

from TimeSyncPro.companies.models import Company

logger = logging.getLogger(__name__)


class CheckOwnCompanyMixin:

    def get_company(self, request):
        try:
            return Company.objects.get(slug=self.kwargs["company_slug"])
        except Company.DoesNotExist:
            raise Http404("Company does not exist.")

    def dispatch(self, request, *args, **kwargs):
        company = self.get_company(request)

        if not request.user.is_superuser:
            if company != request.user.profile.company:
                raise PermissionDenied("You can only view your own company.")
        self.company = company
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company"] = self.company
        return context


class ApiConfigMixin:
    model = None
    employee_api_url_name = None
    history_api_url_name = None
    team_api_url_name = None
    employee_history_api_url_name = None

    def get_url_patterns(self):
        """Override in child class if needed"""
        model_name = self.model._meta.model_name
        model_plural = f"{model_name}s"  # Simple pluralization

        return {
            "employees": f"/{{company_slug}}/{model_plural}/{{pk}}/employees",
            "history": f"/{{company_slug}}/{model_plural}/{{pk}}/history",
            "teams": f"/{{company_slug}}/{model_plural}/{{pk}}/teams",
            "employee_history": f"/{{company_slug}}/company-members/{{pk}}/history",
        }

    def get_api_urls(self):
        try:
            kwargs = {"pk": self.object.pk, "company_slug": self.object.company.slug}

            patterns = self.get_url_patterns()
            urls = {}
            if self.employee_api_url_name:
                urls["employees"] = patterns["employees"].format(**kwargs)
            if self.history_api_url_name:
                urls["history"] = patterns["history"].format(**kwargs)
            if self.team_api_url_name:
                urls["teams"] = patterns["teams"].format(**kwargs)
            if self.employee_history_api_url_name:
                urls["history"] = patterns["employee_history"].format(**kwargs)

            urls["updateProfile"] = reverse(
                "update_profile", kwargs={"slug": "PLACEHOLDER"}
            )
            return urls

        except Exception as e:
            logger.error(f"Error generating API URLs: {e}")
            return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            if hasattr(self, "object") and self.object:
                context["api_config"] = {
                    "urls": self.get_api_urls(),
                    "obj_id": self.object.pk,
                    "company_slug": self.object.company.slug,
                }
        except Exception as e:
            logger.error(f"Error in API config: {e}")

        return context


class AddPermissionMixin:
    add_permission = None

    def get_context_data(self, **kwargs):
        b = self.request.user.has_perm(self.add_permission)
        context = super().get_context_data(**kwargs)
        context["add_permission"] = self.request.user.has_perm(self.add_permission)
        return context


# class AddTeamPermissionMixin(AddPermissionBaseMixin):
#     add_permission = 'companies.add_team'
#
#
# class AddDepartmentPermissionMixin(AddPermissionBaseMixin):
#     add_permission = 'companies.add_department'
#
#
# class AddShiftPermissionMixin(AddPermissionBaseMixin):
#     add_permission = 'companies.add_shift'
#
#
# class AddEmployeePermissionMixin(AddPermissionBaseMixin):
#     add_permission = 'companies.add_employee'
#
