import logging
from datetime import datetime
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic as views
from TimeSyncPro.accounts.views.view_mixins import (
    DynamicPermissionMixin,
    EmployeeButtonPermissionMixin,
)
from TimeSyncPro.common.views_mixins import (
    CompanyObjectsAccessMixin,
    OwnerRequiredMixin,
    EmployeePermissionMixin,
)
from TimeSyncPro.companies.views_mixins import ApiConfigMixin


logger = logging.getLogger(__name__)

UserModel = get_user_model()


class DetailsProfileBaseView(
    ApiConfigMixin, DynamicPermissionMixin, LoginRequiredMixin, views.DetailView
):
    model = UserModel
    _cached_object = None
    template_name = "companies/employee/details_employee_profile.html"

    def get_object(self, queryset=None):
        if self._cached_object is None:
            if queryset is None:
                queryset = self.get_queryset()
            self._cached_object = super().get_object(queryset=queryset)
        return self._cached_object

    def get_queryset(self):
        return self.model.objects.select_related(
            "profile",
            "profile__company",
            "profile__company__holiday_approver",
            "profile__department",
            "profile__department__holiday_approver",
            "profile__team",
            "profile__team__holiday_approver",
            "profile__address",
            "profile__shift",
        ).filter(slug=self.kwargs.get("slug"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # all_user_permissions = set(self.request.user.get_all_permissions())
        user = self.request.user
        context.update(
            {
                "profile": self.object.profile,
                "has_detailed_change_permission": self.has_needed_permission(
                    user, self.object, "change"
                ),
                "has_delete_permission": self.has_needed_permission(
                    user, self.object, "delete"
                ),
            }
        )
        return context


class DetailsOwnProfileView(OwnerRequiredMixin, DetailsProfileBaseView):
    template_name = "accounts/details_profile.html"


class DashboardView(DetailsOwnProfileView):
    def get_template_names(self):
        return ["accounts/dashboard.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = datetime.now().date()
        profile = context["profile"]
        next_holidays = (
            profile.holidays.filter(start_date__gte=today, status="approved")
            .order_by("start_date")
            .first()
        )
        absences = profile.absences.all().count()
        context["next_holiday"] = next_holidays
        context["absences"] = absences
        return context


class DetailsEmployeesProfileView(
    CompanyObjectsAccessMixin,
    EmployeePermissionMixin,
    EmployeeButtonPermissionMixin,
    DetailsProfileBaseView,
):
    employee_history_api_url_name = "employee_history_api"
