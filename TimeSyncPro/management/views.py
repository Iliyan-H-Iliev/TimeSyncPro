from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin

from .models import ShiftPattern, Team
from .forms import CreateShiftPatternForm, CreateShiftBlockFormSet, CreateTeamForm, EditTeamForm, \
    UpdateShiftPatternForm, UpdateShiftBlockForm, UpdateShiftBlockFormSet
from django.views import generic as views

from .utils import handle_shift_pattern_post
from ..core.views_mixins import AuthenticatedViewMixin, CompanyCheckMixin

UserModel = get_user_model()


class ShiftPatternCreateView(AuthenticatedViewMixin, PermissionRequiredMixin, views.View):
    template_name = 'create_shiftpattern_form.html'
    form_class = CreateShiftPatternForm
    formset_class = CreateShiftBlockFormSet
    permission_required = 'team_management.can_add_shift_pattern'
    redirect_url = 'shiftpattern list'

    def get(self, request):
        form = CreateShiftPatternForm(request=request)
        formset = CreateShiftBlockFormSet()
        render_parameters = [request, self.template_name, {'form': form, 'formset': formset}]
        return render(*render_parameters)

    def post(self, request):
        form = CreateShiftPatternForm(request.POST, request=request)
        formset = CreateShiftBlockFormSet(request.POST)
        return handle_shift_pattern_post(request, form, formset, None, self.template_name, self.redirect_url)


class ShiftPatternEditView(CompanyCheckMixin, PermissionRequiredMixin,AuthenticatedViewMixin, views.View):
    template_name = 'edit_shiftpattern_form.html'
    form_class = UpdateShiftPatternForm
    formset_class = UpdateShiftBlockFormSet
    permission_required = "team_management.can_change_shift_pattern"
    redirect_url = 'shiftpattern list'

    def get_object(self):
        return get_object_or_404(ShiftPattern, pk=self.kwargs.get('pk'))

    def get(self, request, pk):
        shift_pattern = self.get_object()
        form = UpdateShiftPatternForm(instance=shift_pattern, request=request)
        formset = UpdateShiftBlockFormSet(instance=shift_pattern)

        render_parameters = [request, self.template_name, {'form': form, 'formset': formset}]
        return render(*render_parameters)

    def post(self, request, pk):
        shift_pattern = self.get_object()
        form = UpdateShiftPatternForm(request.POST, instance=shift_pattern, request=request)
        formset = UpdateShiftBlockFormSet(request.POST, instance=shift_pattern)
        return handle_shift_pattern_post(request, form, formset, pk, self.template_name, self.redirect_url)


class ShiftPatternListView(AuthenticatedViewMixin, PermissionRequiredMixin, views.ListView):
    model = ShiftPattern
    template_name = 'shiftpattern_list.html'
    context_object_name = 'shift_patterns'
    permission_required = 'team_management.can_view_shift_pattern'

    def get_queryset(self):
        return ShiftPattern.objects.filter(company=self.request.user.get_company)

    def get_object(self, queryset=None):
        return self.get_queryset()


class ShiftPatternDetailView(AuthenticatedViewMixin, PermissionRequiredMixin, views.DetailView):
    model = ShiftPattern
    template_name = 'shiftpattern_detail.html'
    context_object_name = 'shift_pattern'
    permission_required = 'team_management.can_view_shift_pattern'

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            "blocks",
            "teams",
        ).filter(company=self.request.user.get_company)

    def get_object(self, queryset=None):
        return self.get_queryset().get(pk=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift_pattern = self.object
        context["shift_pattern_blocks"] = shift_pattern.blocks.all()
        context["shift_pattern_teams"] = shift_pattern.teams.all()
        return context


class ShiftPatternDeleteView(CompanyCheckMixin, AuthenticatedViewMixin, PermissionRequiredMixin, views.DeleteView):
    model = ShiftPattern
    template_name = 'delete_shiftpattern.html'
    permission_required = 'team_management.can_delete_shift_pattern'
    success_url = reverse_lazy('shiftpattern list')

    def get_object(self, queryset=None):
        return self.get_queryset().get(pk=self.kwargs.get('pk'))

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        shift_pattern = self.get_object()
        shift_pattern_blocks = shift_pattern.blocks.all()
        for block in shift_pattern_blocks:
            block.working_dates.clear()
            block.delete()
        return super().post(request, *args, **kwargs)


class TeamListView(AuthenticatedViewMixin, PermissionRequiredMixin, views.ListView):
    model = Team
    template_name = 'team_list.html'
    permission_required = 'team_management.can_view_team'
    context_object_name = 'teams'

    def get_queryset(self):
        return Team.objects.filter(company=self.request.user.get_company)

    def get_object(self, queryset=None):
        return self.get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class TeamCreateView(AuthenticatedViewMixin, PermissionRequiredMixin, views.CreateView):
    model = Team
    form_class = CreateTeamForm
    template_name = 'create_team_form.html'
    permission_required = 'team_management.can_add_team'
    success_url = reverse_lazy('team list')

    def form_valid(self, form):
        form.instance.company = self.request.user.get_company
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['company'] = self.request.user.get_company
        return kwargs


class TeamEditView(CompanyCheckMixin, AuthenticatedViewMixin, PermissionRequiredMixin, views.UpdateView):
    model = Team
    form_class = EditTeamForm
    template_name = 'edti_team.html'
    permission_required = 'team_management.can_change_team'
    success_url = reverse_lazy('team list')

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().company != self.request.user.get_company:
            return redirect('team list')

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['company'] = self.request.user.get_company
        kwargs['team'] = self.object
        return kwargs

    def get_object(self, queryset=None):
        return self.get_queryset().get(pk=self.kwargs.get('pk'))


class TeamDeleteView(CompanyCheckMixin, AuthenticatedViewMixin, PermissionRequiredMixin, views.DeleteView):
    model = Team
    template_name = 'delete_team.html'
    permission_required = 'team_management.can_delete_team'
    success_url = reverse_lazy('team list')

    def get_object(self, queryset=None):
        return self.get_queryset().get(pk=self.kwargs.get('pk'))

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        team = self.get_object()
        team.employees.update(team=None)
        return super().post(request, *args, **kwargs)