from django.contrib.auth import get_user_model
from django.db.models import Q, F
from django.views import generic as views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .views_mixins import HolidayReviewAccessMixin, HolidayPermissionMixin, HasAnyOfPermissionMixin, GetEmployeeMixin
from ..forms import RequestHolidayForm, ReviewHolidayForm
from ..models import Holiday
from ..serializers import HolidayStatusUpdateSerializer
from ...common.views_mixins import CompanyAccessMixin, OwnerRequiredMixin

UserModel = get_user_model()


class HolidaysBaseView(LoginRequiredMixin, views.ListView):
    model = Holiday
    template_name = "absences/holiday/holiday_requests.html"
    paginate_by = 10
    context_object_name = "objects"
    ordering = ["-start_date"]

    def get_queryset(self):
        query = self.request.GET.get("search", "")
        status_filter = self.request.GET.get("status", None)

        queryset = (Holiday.objects.select_related(
            "requester",
            "reviewer",
            "reviewed_by",
            "requester__team",
        ).filter(requester__company=self.request.user.profile.company)).order_by("start_date")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if query:
            queryset = queryset.filter(
                Q(requester__first_name__icontains=query) |
                Q(requester__last_name__icontains=query) |
                Q(requester__user__email__icontains=query) |
                Q(reviewer__first_name__icontains=query) |
                Q(reviewer__last_name__icontains=query) |
                Q(reviewer__user__email__icontains=query) |
                Q(start_date__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Holiday Requests"
        context["search_value"] = self.request.GET.get("search", "")
        context["status_filter"] = self.request.GET.get("status", "")
        return context


class RequestsView(HasAnyOfPermissionMixin, CompanyAccessMixin, HolidaysBaseView):

    required_permissions = [
        "absences.view_all_holidays_requests",
        "absences.view_department_holidays_requests",
        "absences.view_team_holidays_requests",
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user.has_perm("absences.view_all_holidays_requests"):
            if user.has_perm("absences.view_department_holidays_requests") and user.profile.department:
                queryset = queryset.filter(
                    requester__team__department=user.profile.department
                )
            elif user.has_perm("absences.view_team_holidays_requests") and user.profile.team:
                queryset = queryset.filter(
                    requester__team=user.profile.team
                )
            else:
                queryset = queryset.none()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_name"] = True
        return context


class EmployeeRequestsView(GetEmployeeMixin, HolidayPermissionMixin, HolidaysBaseView):
    template_name = "absences/holiday/employee_requests.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        employee = self.get_object()
        queryset = super().get_queryset()
        return queryset.filter(requester=employee.profile)

    def get_context_data(self, **kwargs):
        employee = self.object
        context = super().get_context_data(**kwargs)
        context["title"] = f"{employee.profile.full_name} Requests"
        context["not_found"] = f"{employee.profile.full_name} has no requests"
        context["employee"] = employee
        return context


class MyRequestsView(OwnerRequiredMixin, HolidaysBaseView):
    template_name = "absences/holiday/my_requests.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(requester=self.request.user.profile)


class CreateHolidayRequestView(LoginRequiredMixin, views.CreateView):
    model = Holiday
    form_class = RequestHolidayForm
    template_name = "absences/holiday/request_holiday.html"

    def get_success_url(self):
        return reverse("my_holidays", kwargs={"slug": self.request.user.slug})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.requester = self.request.user.profile
        messages.success(self.request, "Holiday request submitted.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request,
                       "There was an error with your holiday request. Please review the form and try again.")
        return super().form_invalid(form)


class ReviewHolidayView(HolidayReviewAccessMixin, LoginRequiredMixin, views.DetailView):
    model = Holiday
    form_class = ReviewHolidayForm
    template_name = "absences/holiday/review_holiday.html"

    def get_queryset(self):
        return Holiday.objects.select_related(
            "requester",
            "requester__team",
            "reviewer"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        holiday = self.object
        requester_team = holiday.requester.get_team()
        if requester_team:
            team_members_in_holiday = (
                requester_team.get_team_members_at_holiday(
                    holiday.start_date,
                    holiday.end_date
                ))

            context.update({
                "requester_team": requester_team,
                "team_members_in_holiday": team_members_in_holiday,
                "team_members_in_holiday_count": requester_team.get_numbers_of_team_members_holiday_days_by_queryset(
                    team_members_in_holiday
                )
            })

        context["form"] = self.form_class()
        return context


class HolidayRequestStatusUpdateView(UpdateAPIView):
    queryset = Holiday.objects.all()
    serializer_class = HolidayStatusUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        holiday = super().get_object()

        if self.request.user.profile != holiday.requester:
            if self.request.data.get("status") == holiday.StatusChoices.CANCELLED:
                raise PermissionDenied("You can only cancel your own holiday requests.")
        elif (self.request.user.profile == holiday.reviewer or
                self.request.user.profile == holiday.requester.get_holiday_approver() or
              self.request.user.has_perm("absences.can_update_holiday_requests_status")):
            pass
        else:
            raise PermissionDenied("You do not have permission to update this holiday request.")

        return holiday

    def partial_update(self, request, *args, **kwargs):
        try:
            holiday = self.get_object()
            serializer = self.get_serializer(holiday, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            new_status = serializer.validated_data["status"]
            if new_status in [Holiday.StatusChoices.CANCELLED, Holiday.StatusChoices.DENIED]:
                holiday.requester.remaining_leave_days = F("remaining_leave_days") + holiday.days_requested
                holiday.requester.save(update_fields=["remaining_leave_days"])
            serializer.save()
            return Response({"message": f"Holiday request {new_status} successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
