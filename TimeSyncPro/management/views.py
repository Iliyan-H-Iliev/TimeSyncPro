from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin

from .models import ShiftPattern, Team, Company
from .forms import CreateShiftPatternForm, CreateShiftBlockFormSet, CreateTeamForm, EditTeamForm, \
    UpdateShiftPatternForm, UpdateShiftBlockFormSet, EditCompanyForm, CreateCompanyForm
from django.views import generic as views

from .utils import handle_shift_pattern_post
from TimeSyncPro.common.views_mixins import NotAuthenticatedMixin, CompanyCheckMixin, MultiplePermissionsRequiredMixin, \
    CompanyContextMixin
from ..common.forms import AddressForm

UserModel = get_user_model()


class CreateCompanyView(LoginRequiredMixin, views.CreateView):
    model = Company
    template_name = "management/create_company.html"
    form_class = CreateCompanyForm
    address_form_class = AddressForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'address_form' not in context:
            context['address_form'] = self.address_form_class()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        address_form = self.address_form_class(request.POST)
        if form.is_valid() and address_form.is_valid():
            return self.form_valid(form, address_form)
        else:
            return self.form_invalid(form, address_form)

    @transaction.atomic
    def form_valid(self, form, address_form):
        try:
            self.object = form.save(commit=False)
            self.object.address = address_form.save()
            self.object.save()
            self.request.user.profile.company = self.object
            self.request.user.profile.save()
            messages.success(self.request, "Company created successfully.")
            return redirect(self.get_success_url())
        except Exception as e:
            messages.error(self.request, f"An error occurred while creating the company: {e}")
            return self.form_invalid(form, address_form)

    def form_invalid(self, form, address_form):
        return self.render_to_response(
            self.get_context_data(form=form, address_form=address_form)
        )

    def get_success_url(self):
        return reverse('company_profile', kwargs={'company_slug': self.object.slug})

    def dispatch(self, request, *args, **kwargs):
        if request.user.profile.company:
            messages.error(request, "User already belongs to a company.")
            return redirect(reverse('company_profile', kwargs={'company_slug': request.user.profile.company.slug}))
        return super().dispatch(request, *args, **kwargs)


class DetailsCompanyView(
    NotAuthenticatedMixin,
    MultiplePermissionsRequiredMixin,
    CompanyContextMixin,
    views.DetailView
):

    model = Company
    template_name = "accounts/../../templates/management/company_profile.html"
    context_object_name = 'company'
    permissions_required = [
        'management.view_company',
    ]

    def get_object(self, queryset=None):
        user = self.request.user
        company = get_object_or_404(self.model, pk=user.company.pk)
        return user.profile.company


class EditCompanyView(NotAuthenticatedMixin, views.UpdateView):
    model = Company
    template_name = 'accounts/../../templates/management/update_company.html'
    form_class = EditCompanyForm
    permissions_required = [
        'accounts.change_company',
    ]

    def get_object(self, queryset=None):
        user = self.request.user

        try:
            return self.model.objects.get(pk=user.company.pk)
        except Company.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_object()
        context['company'] = company
        return context

    def get_success_url(self):
        company = self.object
        return reverse('company profile', kwargs={'company_slug': company.slug})


class CompanyMembersView(LoginRequiredMixin, CompanyContextMixin, views.ListView):
    model = Company
    template_name = "accounts/../../templates/management/company_members.html"
    context_object_name = 'company'

    # def get_queryset(self):
    #     user = self.request.user
    #     return Company.objects.filter(id=user.profile.company.id)

    def get_object(self, queryset=None):
        user = self.request.user
        queryset = self.get_queryset()

        try:
            return queryset.get(pk=user.company.pk)
        except Company.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        company = self.get_object()

        if not company:
            messages.error(request, "User does not belong to any company.")
            return redirect('index')
        return super().get(request, *args, **kwargs)

    # # TODO check if this is the right way to fetch related models for the user profile
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_object()

        context['employees'] = Company.objects.get(pk=company.pk).employees.all()

        return context


# TODO add permision for delete
# TODO Create logic for delete company
class DeleteCompanyView(LoginRequiredMixin, CompanyCheckMixin, views.DeleteView):
    model = Company
    queryset = model.objects.all()
    template_name = 'accounts/../../templates/management/delete_company.html'
    success_url = reverse_lazy('index')

    def get(self, request, *args, **kwargs):
        user = request.user
        company = user.profile.company
        if not company:
            messages.error(request, "Company not found.")
            return redirect('index')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = request.user
        company = user.profile.company
        company.delete()
        messages.success(request, "Company deleted successfully.")
        return redirect(self.success_url)


# class ShiftPatternCreateView(LoginRequiredMixin, PermissionRequiredMixin, views.View):
#     template_name = 'create_shiftpattern_form.html'
#     form_class = CreateShiftPatternForm
#     formset_class = CreateShiftBlockFormSet
#     # permission_required = 'team_management.can_add_shift_pattern'
#     permission_required = 'management.add_shiftpattern'
#     redirect_url = 'shiftpattern list'
#
#     def get(self, request):
#         form = CreateShiftPatternForm(request=request)
#         formset = CreateShiftBlockFormSet()
#         render_parameters = [request, self.template_name, {'form': form, 'formset': formset}]
#         return render(*render_parameters)
#
#     def post(self, request):
#         form = CreateShiftPatternForm(request.POST, request=request)
#         formset = CreateShiftBlockFormSet(request.POST)
#         return handle_shift_pattern_post(request, form, formset, None, self.template_name, self.redirect_url)


class CreateShiftPatternView(LoginRequiredMixin, PermissionRequiredMixin, CompanyContextMixin, views.View):
    template_name = 'management/create_shiftpattern_form.html'
    form_class = CreateShiftPatternForm
    formset_class = CreateShiftBlockFormSet
    permission_required = 'management.add_shiftpattern'
    redirect_url = 'all_shift_patterns'

    def dispatch(self, request, *args, **kwargs):
        self.company = self.get_company()
        return super().dispatch(request, *args, **kwargs)

    def get_company(self):
        company_slug = self.kwargs.get('company_slug')
        return get_object_or_404(Company, slug=company_slug)

    def get(self, request, company_slug, *args, **kwargs):
        form = self.form_class(request=request, company=self.company)
        formset = self.formset_class()
        context = {'form': form, 'formset': formset, 'company': self.company}
        return render(request, self.template_name, context)

    def post(self, request, company_slug, *args, **kwargs):
        form = self.form_class(request.POST, request=request, company=self.company)
        formset = self.formset_class(request.POST)
        if form.is_valid() and formset.is_valid():
            shift_pattern = form.save(commit=False)
            shift_pattern.company = self.company
            shift_pattern.save()
            formset.instance = shift_pattern
            formset.save()
            return redirect(self.get_success_url())
        context = {'form': form, 'formset': formset, 'company': self.company}
        return render(request, self.template_name, context)

    def get_success_url(self):
        return reverse(self.redirect_url, kwargs={'company_slug': self.company.slug})


class EditShiftPatternView(CompanyCheckMixin, PermissionRequiredMixin, LoginRequiredMixin, views.View):
    template_name = 'update_shift_pattern.html'
    form_class = UpdateShiftPatternForm
    formset_class = UpdateShiftBlockFormSet
    permission_required = "management.change_shiftpattern"
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


class ShiftPatternsView(NotAuthenticatedMixin, PermissionRequiredMixin, views.ListView):
    model = ShiftPattern
    template_name = 'management/all_shift_patterns.html'
    context_object_name = 'shift_patterns'
    permission_required = 'management.view_shiftpattern'

    def get_queryset(self):
        return ShiftPattern.objects.filter(company=self.request.user.company)

    def get_object(self, queryset=None):
        return self.get_queryset()


class DetailsShiftPatternView(NotAuthenticatedMixin, PermissionRequiredMixin, views.DetailView):
    model = ShiftPattern
    template_name = 'management/details_shift_pattern.html'
    context_object_name = 'shift_pattern'
    permission_required = 'management.view_shiftpattern'

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


class DeleteShiftPatternView(CompanyCheckMixin, NotAuthenticatedMixin, PermissionRequiredMixin, views.DeleteView):
    model = ShiftPattern
    template_name = 'management/delete_shiftpattern.html'
    permission_required = 'management.delete_shiftpattern'
    success_url = reverse_lazy("all_shift_patterns")

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


class TeamsView(NotAuthenticatedMixin, PermissionRequiredMixin, views.ListView):
    model = Team
    template_name = 'management/all_teams.html'
    permission_required = 'management.view_team'
    context_object_name = 'teams'

    def get_queryset(self):
        return Team.objects.filter(company=self.request.user.company)

    def get_object(self, queryset=None):
        return self.get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class CreateTeamView(NotAuthenticatedMixin, PermissionRequiredMixin, views.CreateView):
    model = Team
    form_class = CreateTeamForm
    template_name = 'management/create_team.html'
    permission_required = 'management.add_team'
    success_url = reverse_lazy('team list')

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['company'] = self.request.user.company
        return kwargs


class EditTeamView(CompanyCheckMixin, NotAuthenticatedMixin, PermissionRequiredMixin, views.UpdateView):
    model = Team
    form_class = EditTeamForm
    template_name = 'management/update_team.html'
    permission_required = 'management.change_team'
    success_url = reverse_lazy('team list')

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().company != self.request.user.company:
            return redirect('team list')

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['company'] = self.request.user.company
        kwargs['team'] = self.object
        return kwargs

    def get_object(self, queryset=None):
        return self.get_queryset().get(pk=self.kwargs.get('pk'))


class DeleteTeamView(CompanyCheckMixin, NotAuthenticatedMixin, PermissionRequiredMixin, views.DeleteView):
    model = Team
    template_name = 'management/delete_team.html'
    permission_required = 'management.delete_team'
    success_url = reverse_lazy('team list')

    def get_object(self, queryset=None):
        return self.get_queryset().get(pk=self.kwargs.get('pk'))

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        team = self.get_object()
        team.employees.update(team=None)
        return super().post(request, *args, **kwargs)