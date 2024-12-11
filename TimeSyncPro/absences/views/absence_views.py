from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views import generic as views

from TimeSyncPro.absences.forms.absence_forms import CreateAbsenceForm
from TimeSyncPro.absences.models import Absence
from TimeSyncPro.common.views_mixins import ReturnToPageMixin


UserModel = get_user_model()


class CreateAbsenceView(ReturnToPageMixin, PermissionRequiredMixin, LoginRequiredMixin, views.CreateView):
    model = Absence
    template_name = "absences/create_absence.html"
    form_class = CreateAbsenceForm
    permission_required = 'absences.add_absence'

    def get_absentee(self, queryset=None):
        queryset = UserModel.objects.select_related('profile')
        obj = get_object_or_404(queryset, slug=self.kwargs.get('slug'))
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['absentee'] = self.get_absentee()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['absentee'] = self.get_absentee()
        context['form'] = self.get_form()
        return context


class AbsencesBaseView(LoginRequiredMixin, views.ListView):
    model = Absence
    template_name = "absences/absences_base.html"
    context_object_name = "objects"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('search', '')
        type_filter = self.request.GET.get('type', None)
        user = self.request.user

        queryset = (Absence.objects.select_related(
            "absentee",
            "absentee__user",
            "added_by",
            "added_by__user",
        ).filter(added_by__company=self.request.user.profile.company)).order_by('start_date')

        if not user.has_perm('absences.view_all_absences'):
            if user.has_perm('view_department_absences'):
                queryset = queryset.filter(absentee__department=user.profile.department)
            elif user.has_perm('view_team_absences'):
                queryset = queryset.filter(absentee__team=user.profile.team)
            else:
                queryset = queryset.none()

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
        context['title'] = 'Absences'
        context['search_value'] = self.request.GET.get('search', '')
        context['type_filter'] = self.request.GET.get('type', '')
        return context


class AbsencesView(PermissionRequiredMixin, AbsencesBaseView):
    permission_required = any([
        'absences.view_all_absences',
        'absences.view_department_absences',
        'absences.view_team_absences',
    ])


class MyAbsencesView(AbsencesBaseView):
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(absentee=self.request.user.profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Absences'
        return context


class EmployeeAbsencesView(PermissionRequiredMixin, AbsencesBaseView):
    permission_required = any([
        'absences.view_all_absences',
        'absences.view_department_absences',
        'absences.view_team_absences',
    ])
    template_name = "absences/employee_absences.html"

    def get_object(self):
        return get_object_or_404(UserModel, slug=self.kwargs['slug'])

    def get_queryset(self):
        employee = self.get_object()
        queryset = super().get_queryset()
        return queryset.filter(absentee=employee.profile)

    def get_context_data(self, **kwargs):
        employee = self.get_object()
        context = super().get_context_data(**kwargs)
        context['title'] = f'{employee.profile.full_name} Absences'
        context['employee'] = self.get_object()
        return context


class AbsenceDetailView(PermissionRequiredMixin, LoginRequiredMixin, views.DetailView):
    model = Absence
    template_name = "absences/absence_detail.html"
    permission_required = 'absences.view_absence'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related(
            "absentee",
            "absentee__user",
            "added_by",
            "added_by__user",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Absence Detail'
        return context


