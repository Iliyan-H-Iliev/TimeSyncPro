from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views import generic as views
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from TimeSyncPro.absences.forms import CreateAbsenceForm
from TimeSyncPro.absences.models import Absence
from .views_mixins import AbsencePermissionMixin, HasAnyOfPermissionMixin, GetEmployeeMixin
from TimeSyncPro.common.views_mixins import ReturnToPageMixin, OwnerRequiredMixin, CRUDUrlsMixin

UserModel = get_user_model()


class CreateAbsenceView(ReturnToPageMixin, PermissionRequiredMixin, LoginRequiredMixin, views.CreateView):
    model = Absence
    template_name = "absences/absence/create_absence.html"
    form_class = CreateAbsenceForm
    permission_required = "absences.add_absence"

    def get_absentee(self, queryset=None):
        queryset = UserModel.objects.select_related("profile")
        obj = get_object_or_404(queryset, slug=self.kwargs.get("slug"))
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        kwargs["absentee"] = self.get_absentee()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["absentee"] = self.get_absentee()
        context["form"] = self.get_form()
        return context


class AbsencesBaseView(LoginRequiredMixin, views.ListView):
    model = Absence
    template_name = "absences/absence/absences.html"
    context_object_name = "objects"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("search", "")
        type_filter = self.request.GET.get("type", None)

        queryset = (Absence.objects.select_related(
            "absentee",
            "absentee__user",
            "added_by",
            "added_by__user",
        ).filter(added_by__company=self.request.user.profile.company)).order_by("-start_date")

        if type_filter:
            queryset = queryset.filter(absence_type=type_filter)

        if query:
            queryset = queryset.filter(
                Q(absentee__first_name__icontains=query) |
                Q(absentee__last_name__icontains=query) |
                Q(absentee__user__email__icontains=query) |
                Q(added_by__first_name__icontains=query) |
                Q(added_by__last_name__icontains=query) |
                Q(added_by__user__email__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Absences"
        context["search_value"] = self.request.GET.get("search", "")
        context["type_filter"] = self.request.GET.get("type", "")
        return context


class AbsencesView(HasAnyOfPermissionMixin, AbsencesBaseView):

    required_permissions = [
        "absences.view_all_absences",
        "absences.view_department_absences",
        "absences.view_team_absences",
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.has_perm("absences.view_all_absences"):
            if user.has_perm("view_department_absences"):
                queryset = queryset.filter(absentee__department=user.profile.department)
            elif user.has_perm("view_team_absences"):
                queryset = queryset.filter(absentee__team=user.profile.team)
            else:
                queryset = queryset.none()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_name"] = True
        return context


class MyAbsencesView(OwnerRequiredMixin, AbsencesBaseView):

    template_name = "absences/absence/my_absences.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(absentee=self.request.user.profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "My Absences"
        context["not_found"] = "You have no absences"
        return context


class EmployeeAbsencesView(GetEmployeeMixin, AbsencePermissionMixin, AbsencesBaseView):
    template_name = "absences/absence/employee_absences.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)


    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(absentee=self.object.profile).order_by("start_date")

    def get_context_data(self, **kwargs):
        employee = self.object
        context = super().get_context_data(**kwargs)
        context["title"] = f"{employee.profile.full_name} Absences"
        context["not_found"] = f"{employee.profile.full_name} has no absences"
        context["employee"] = employee
        return context


class DeleteAbsenceAPIView(DestroyAPIView):
    permission_required = [IsAuthenticated]

    def get_queryset(self):
        return Absence.objects.filter(added_by__company=self.request.user.profile.company)

    def get_object(self):
        obj = super().get_object()
        if obj.absentee == self.request.user.profile:
            raise PermissionDenied("You do not have permission to delete this absence.")
        if not self.request.user.has_perm("absences.delete_absence"):
            raise PermissionDenied("You do not have permission to delete absences.")
        return obj

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except Exception as e:
            raise ValidationError(f"You cannot delete this absence: {e}")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Absence deleted successfully"}, status=status.HTTP_200_OK)





