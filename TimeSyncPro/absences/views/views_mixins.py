from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from TimeSyncPro.accounts.models import Profile


class HolidayReviewAccessMixin(UserPassesTestMixin):
    def test_func(self):
        self.object = self.get_object()

        current_employee_holiday_approver = self.object.requester.get_holiday_approver()

        return (self.object.reviewer == self.request.user.profile or
                current_employee_holiday_approver == self.request.user.profile or
                self.request.user.has_perm('absences.can_update_holiday_requests_status'))

    def handle_no_permission(self):
        raise PermissionDenied('You do not have permission to review this holiday request.')


class EmployeeHolidayRequestsAccessMixin(UserPassesTestMixin):

    def test_func(self):

        employee = self.get_object()

        employee_leave_approver = employee.profile.get_holiday_approver()

        return (employee_leave_approver == self.request.user.profile or
                self.request.user.has_perm('absences.can_view_all_holidays_requests'))

    def handle_no_permission(self):
        raise PermissionDenied('You do not have permission to view this employee\'s holiday requests.')


class AllHolidayRequestsAccessMixin(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.has_perm('absences.can_view_all_holidays_requests')

    def handle_no_permission(self):
        raise PermissionDenied('You do not have permission to view all holiday requests.')
