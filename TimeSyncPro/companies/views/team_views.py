from django.core.paginator import Paginator
from django.db.models import Prefetch, Q, OuterRef
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin

from ..models import Shift, Team, Department
from ..forms import CreateTeamForm, EditTeamForm
from django.views import generic as views

from TimeSyncPro.common.views_mixins import NotAuthenticatedMixin, CompanyObjectsAccessMixin, MultiplePermissionsRequiredMixin
from ..views_mixins import ApiConfigMixin
from ...accounts.models import Profile
from ...accounts.view_mixins import CRUDUrlsMixin
from ...history.models import History
from ...history.views_mixins import HistoryViewMixin


class TeamsView(CRUDUrlsMixin, LoginRequiredMixin, PermissionRequiredMixin, views.ListView):
    model = Team
    template_name = 'companies/team/all_teams.html'
    permission_required = 'companies.view_team'
    context_object_name = 'objects'
    paginate_by = 4
    ordering = 'name'

    crud_url_names = {
        "create": "create_team",
        "detail": "details_team",
        "update": "update_team",
        "delete": "delete_team",
    }

    button_names = {
        'create': 'Team',
    }

    def get_queryset(self):
        query = self.request.GET.get('search', '')
        queryset = (Team.objects.select_related(
            'shift',
            'holiday_approver',
            'department',
        ).prefetch_related(
            Prefetch('employees', queryset=Profile.objects.select_related('user', 'department')),
        ).filter(company=self.request.user.profile.company)).order_by('name')

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(department__name__icontains=query) |
                Q(shift__name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Teams'
        context['search_value'] = self.request.GET.get('search', '')
        return context


class CreateTeamView(LoginRequiredMixin, PermissionRequiredMixin, views.CreateView):
    model = Team
    form_class = CreateTeamForm
    template_name = 'companies/team/create_team.html'
    permission_required = 'companies.add_team'

    def get_success_url(self):
        company_slug = self.kwargs.get('company_slug')
        return reverse('all_teams', kwargs={'company_slug': company_slug})

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['company'] = self.request.user.company
        return kwargs


class EditTeamView(CompanyObjectsAccessMixin, LoginRequiredMixin, PermissionRequiredMixin, views.UpdateView):
    model = Team
    form_class = EditTeamForm
    template_name = 'companies/team/update_team.html'
    permission_required = 'companies.change_team'

    def get_queryset(self):
        queryset = super().get_queryset()

        queryset = (queryset.select_related(
               'company',
               'department',
               'holiday_approver',
               'holiday_approver__user'
           ).prefetch_related(
               Prefetch(
                   'company__employees',
                   queryset=Profile.objects.select_related(
                       'user',
                       'department'
                   )
               ),
               Prefetch(
                   'company__departments',
                   queryset=Department.objects.select_related('company')
               ),
               Prefetch(
                   'company__shifts',
                   queryset=Shift.objects.select_related('company')
               ),
        ).filter(company=self.request.user.profile.company))

        return queryset

    def get_success_url(self):
        company_slug = self.request.user.company.slug
        return reverse('all_teams', kwargs={'company_slug': company_slug})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'user': self.request.user,
            'company': self.request.user.profile.company,
            'team': self.object,
        })
        # kwargs['user'] = self.request.user
        # kwargs['company'] = self.request.user.company
        # kwargs['team'] = self.object
        return kwargs

    # def get_object(self, queryset=None):
    #     if not queryset:
    #         queryset = self.get_queryset()
    #     return queryset.get(pk=self.kwargs.get('pk'))


class DeleteTeamView(CompanyObjectsAccessMixin, LoginRequiredMixin, PermissionRequiredMixin, views.DeleteView):
    model = Team
    template_name = 'companies/team/delete_team.html'
    permission_required = 'companies.delete_team'


    def get_success_url(self):
        company_slug = self.request.user.company.slug
        return reverse('all_teams', kwargs={'company_slug': company_slug})

    def get_object(self, queryset=None):
        return self.get_queryset().get(pk=self.kwargs.get('pk'))

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        team = self.get_object()
        team.employees.update(team=None)
        return super().post(request, *args, **kwargs)


class DetailsTeamView(ApiConfigMixin, CompanyObjectsAccessMixin, LoginRequiredMixin, PermissionRequiredMixin, views.DetailView):
    model = Team
    template_name = 'companies/team/details_team.html'
    permission_required = 'companies.view_team'
    # history_paginate_by = 1
    # employees_paginate_by = 10
    employee_api_url_name = 'team-employees-api'
    history_api_url_name = 'team-history-api'

    def get_queryset(self):
        queryset = super().get_queryset()

        if not hasattr(self.request.user, 'profile'):
            return queryset.none()

        queryset = (queryset.select_related(
            'company',
            'shift',
            'holiday_approver',
            'department',
        ).prefetch_related(
            "employees",
        ).filter(company=self.request.user.profile.company))

        return queryset

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #
    #     employees = self.object.employees.select_related(
    #         'user',
    #         'department',
    #     ).order_by('first_name')
    #     employees_page = self.request.GET.get('employees_page', 1)
    #     employees_paginator = Paginator(employees, self.employees_paginate_by)
    #     context['employees'] = employees_paginator.get_page(employees_page)
    #     context['team_id'] = self.object.id
    #     context['company_slug'] = self.object.company.slug
    #     return context

    def get_object(self, queryset=None):
        return self.get_queryset().get(pk=self.kwargs.get('pk'))
