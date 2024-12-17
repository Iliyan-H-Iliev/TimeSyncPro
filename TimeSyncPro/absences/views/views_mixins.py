from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from TimeSyncPro.common.views_mixins import BasePermissionMixin

UserModel = get_user_model()


class HolidayReviewAccessMixin(UserPassesTestMixin):
    def test_func(self):
        self.object = self.get_object()

        current_employee_holiday_approver = self.object.requester.get_holiday_approver()

        return (
            self.object.reviewer == self.request.user.profile
            or current_employee_holiday_approver == self.request.user.profile
            or self.request.user.has_perm("absences.can_update_holiday_requests_status")
        )

    def handle_no_permission(self):
        raise PermissionDenied(
            "You do not have permission to review this holiday request."
        )


#
# class EmployeeHolidayRequestsAccessMixin(UserPassesTestMixin):
#
#     def test_func(self):
#
#         employee = self.get_object()
#
#         employee_leave_approver = employee.profile.get_holiday_approver()
#
#         if employee.profile.department:
#             if self.request.user.has_perm('absences.view_department_holidays_requests'):
#                 return employee.profile.department == self.request.user.profile.department
#
#         if employee.profile.team:
#             if self.request.user.has_perm('absences.view_team_holidays_requests'):
#                 return employee.profile.team == self.request.user.profile.team
#
#         return (employee_leave_approver == self.request.user.profile or
#                 self.request.user.has_perm('absences.view_all_holidays_requests'))
#
#     def handle_no_permission(self):
#         raise PermissionDenied('You do not have permission to view this employee\'s holiday requests.')


class HolidayPermissionMixin(BasePermissionMixin):

    permission_required = {
        "all": "absences.view_all_holidays",
        "department": "absences.view_department_holidays",
        "team": "absences.view_team_holidays",
    }

    def get_target_profile(self):
        return self.get_object().profile

    def is_approver(self, target_profile):
        return self.request.user.profile == target_profile.get_holiday_approver()

    def test_func(self):
        if super().test_func():
            return True

        target_profile = self.get_target_profile()
        return self.is_approver(target_profile)


class AbsencePermissionMixin(BasePermissionMixin):

    permission_required = {
        "all": "absences.view_all_absences",
        "department": "absences.view_department_absences",
        "team": "absences.view_team_absences",
    }

    def get_target_profile(self):
        return self.get_object().profile


class HasAnyOfPermissionMixin(UserPassesTestMixin):
    required_permissions = []

    def test_func(self):
        return any(
            self.request.user.has_perm(perm) for perm in self.required_permissions
        )

    def handle_no_permission(self):
        raise PermissionDenied("You do not have permission to view this page.")


class GetEmployeeMixin:

    def get_object(self):
        obj = UserModel.objects.select_related(
            "profile", "profile__department", "profile__team"
        ).get(slug=self.kwargs.get("slug"))

        if not obj:
            raise Http404("Employee not found")

        return obj
