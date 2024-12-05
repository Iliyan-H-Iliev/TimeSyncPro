from django.db.models import Prefetch, Q
from django.urls import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin

from ..models import Shift, Team, Department
from ..forms import CreateTeamForm, EditTeamForm
from django.views import generic as views

from TimeSyncPro.common.views_mixins import CompanyObjectsAccessMixin, CompanyAccessMixin
from ..views_mixins import ApiConfigMixin
from ...accounts.models import Profile
from ...accounts.view_mixins import CRUDUrlsMixin


class TeamsView(CompanyAccessMixin, CRUDUrlsMixin, LoginRequiredMixin, PermissionRequiredMixin, views.ListView):
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
        ).filter(company=self.request.user.company))

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
        return kwargs


class DeleteTeamView(CompanyObjectsAccessMixin, LoginRequiredMixin, PermissionRequiredMixin, views.DeleteView):
    model = Team
    template_name = 'companies/team/delete_team.html'
    permission_required = 'companies.delete_team'

    def get_success_url(self):
        company_slug = self.request.user.company.slug
        return reverse('all_teams', kwargs={'company_slug': company_slug})


class DetailsTeamView(ApiConfigMixin, CompanyObjectsAccessMixin, LoginRequiredMixin, PermissionRequiredMixin, views.DetailView):
    model = Team
    template_name = 'companies/team/details_team.html'
    permission_required = 'companies.view_team'

    employee_api_url_name = 'team-employees-api'
    history_api_url_name = 'team-history-api'

    def get_queryset(self):
        queryset = super().get_queryset()

        queryset = (queryset.select_related(
            'company',
            'shift',
            'holiday_approver',
            'department',
        ).prefetch_related(
            "employees",
        ).filter(company=self.request.user.profile.company))

        return queryset

