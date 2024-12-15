from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Prefetch, Max
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin

from ..models import Shift, Company, Department, Team, ShiftBlock
from ..forms import CreateShiftForm, CreateShiftBlockFormSet, UpdateShiftForm, UpdateShiftBlockFormSet
from django.views import generic as views

from ..utils import handle_shift_post
from TimeSyncPro.common.views_mixins import CompanyObjectsAccessMixin, MultiplePermissionsRequiredMixin, \
    CompanyAccessMixin, CRUDUrlsMixin
from ..views_mixins import ApiConfigMixin
from ...accounts.models import Profile


class ShiftsView(CompanyAccessMixin, CRUDUrlsMixin, LoginRequiredMixin, PermissionRequiredMixin, views.ListView):
    model = Shift
    template_name = 'companies/shift/all_shifts.html'
    context_object_name = 'objects'
    permission_required = 'companies.view_shift'
    paginate_by = 4

    crud_url_names = {
        'create': 'create_shift',
        'update': 'update_shift',
        'delete': 'delete_shift',
        'detail': 'details_shift',
    }

    button_names = {
        'create': 'Shift',
    }

    def get_queryset(self):
        query = self.request.GET.get('search', '')
        queryset = self.model.objects.all().filter(company=self.request.user.company).order_by('name').prefetch_related(
            "blocks",
            "teams",
        )

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )
        return queryset

    # def get_object(self, queryset=None):
    #     if not queryset:
    #         queryset = self.get_queryset()
    #     return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Shifts"
        context['search_value'] = self.request.GET.get('search', '')
        return context


class DetailsShiftView(ApiConfigMixin, LoginRequiredMixin, PermissionRequiredMixin, views.DetailView):
    model = Shift
    template_name = 'companies/shift/details_shift.html'
    context_object_name = 'shift'
    permission_required = 'companies.view_shift'
    employee_api_url_name = 'shift-employees-api'
    history_api_url_name = 'shift-history-api'
    team_api_url_name = 'shift-teams-api'

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            "blocks",
            "teams",
        ).filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift = self.object
        context["shift_blocks"] = shift.blocks.all()
        context["shift_teams"] = shift.teams.all()
        return context

class CreateShiftView(LoginRequiredMixin, PermissionRequiredMixin, views.CreateView):
    model = Shift
    template_name = 'companies/shift/create_shift.html'
    form_class = CreateShiftForm
    formset_class = CreateShiftBlockFormSet
    permission_required = 'companies.add_shift'
    redirect_url = 'all_shifts'

    def setup(self, request, *args, **kwargs):
        """Initialize company at the start"""
        super().setup(request, *args, **kwargs)
        self.company = get_object_or_404(Company, slug=kwargs.get('company_slug'))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['company'] = self.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'formset' not in context:
            context['formset'] = self.formset_class(
                initial=[{}]
            )
        context['company'] = self.company
        return context

    def post(self, *args, **kwargs):
        request = self.request
        company = self.company
        form = self.form_class(request.POST, request=request, company=company)
        formset = self.formset_class(request.POST)
        if form.is_valid() and formset.is_valid():
            return self.form_valid(request, form, formset, company=company)
        return self.form_invalid(form, formset, company=company)

    @transaction.atomic
    def form_valid(self, request, form, formset, pk=None, company=None, obj=None):
        return handle_shift_post(
            request=request,
            form=form,
            formset=formset,
            pk=None,
            company=company,
            template_name=self.template_name,
            redirect_url=self.redirect_url,
        )

    @transaction.atomic
    def form_invalid(self, form, formset, company=None):
        """Handle form or formset errors by re-rendering the page."""
        return render(self.request, self.template_name, {
            'form': form,
            'formset': formset,
            'company': company,
        })


class EditShiftView(CompanyObjectsAccessMixin, PermissionRequiredMixin, LoginRequiredMixin, views.UpdateView):
    model = Shift
    template_name = "companies/shift/update_shift.html"
    form_class = UpdateShiftForm
    formset_class = UpdateShiftBlockFormSet
    permission_required = "companies.change_shift"
    redirect_url = 'all_shifts'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['shift'] = self.object
        kwargs['company'] = self.request.user.company
        return kwargs

    def get_queryset(self):
        queryset = super().get_queryset()

        if not hasattr(self.request.user, 'profile'):
            return queryset.none()

        queryset = (queryset.select_related('company').prefetch_related(
            Prefetch('company__employees', queryset=Profile.objects.select_related('user', 'department')),
            Prefetch('company__departments', queryset=Department.objects.select_related('company')),
            Prefetch('company__teams', queryset=Team.objects.select_related('company')),
        ).filter(company=self.request.user.profile.company))

        return queryset

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(instance=self.object, request=request)
        formset = self.formset_class(instance=self.object)

        return render(request, self.template_name, {
            'form': form,
            'formset': formset,
            'object': self.object,
        })

    def post(self, *args, **kwargs):
        request = self.request
        self.object = self.get_object()
        pk = self.object.pk or None
        company = request.user.company
        form = self.form_class(request.POST, instance=self.object, request=request)
        formset = self.formset_class(request.POST, instance=self.object)
        if form.is_valid() and formset.is_valid():
            return self.form_valid(request, form, formset, pk, company, obj=self.object)
        return self.form_invalid(form, formset)

    @transaction.atomic
    def form_valid(self, request, form, formset, pk, company, obj=None):
        return handle_shift_post(
            request=request,
            form=form,
            formset=formset,
            pk=pk,
            company=company,
            template_name=self.template_name,
            redirect_url=self.redirect_url,
            obj=obj
        )

    @transaction.atomic
    def form_invalid(self, form, formset):
        """Handle form or formset errors by re-rendering the page."""
        return render(self.request, self.template_name, {
            'form': form,
            'formset': formset,
            'object': self.object,
        })


class DeleteShiftView(CompanyObjectsAccessMixin, LoginRequiredMixin, PermissionRequiredMixin, views.DeleteView):
    model = Shift
    template_name = 'companies/shift/delete_shift.html'
    permission_required = 'companies.delete_shift'

    def get_success_url(self):
        return reverse('all_shifts', kwargs={'company_slug': self.object.company.slug})

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        """Override delete to handle related objects in bulk"""
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Bulk delete related objects
        blocks = self.object.blocks.all()
        blocks.delete()
        self.object.delete()

        messages.success(request, f"Shift and all related data were successfully deleted.")
        return HttpResponseRedirect(success_url)
