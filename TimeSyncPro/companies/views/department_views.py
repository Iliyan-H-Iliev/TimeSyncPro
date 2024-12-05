from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.db.models import Prefetch
from django.urls import reverse

from ..models import Department, Shift
from ..forms import CreateDepartmentForm
from django.views import generic as views

from TimeSyncPro.common.views_mixins import CompanyObjectsAccessMixin, MultiplePermissionsRequiredMixin, ReturnToPageMixin
from ...accounts.models import Profile


class CreateDepartmentView(LoginRequiredMixin, PermissionRequiredMixin, views.CreateView):
    model = Department
    form_class = CreateDepartmentForm
    template_name = 'companies/department/create_department.html'
    permission_required = 'companies.add_department'

    class Meta:
        fields = ['name', 'description', 'company']


class DepartmentsView(LoginRequiredMixin, PermissionRequiredMixin, views.ListView):
    model = Department
    template_name = 'companies/department/all_departments.html'
    permission_required = 'companies.view_department'
    context_object_name = 'departments'

    def get_queryset(self):
        return Department.objects.filter(company=self.request.user.company)

    def get_object(self, queryset=None):
        return self.get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class EditDepartmentView(ReturnToPageMixin, CompanyObjectsAccessMixin, LoginRequiredMixin, PermissionRequiredMixin, views.UpdateView):
    model = Department
    form_class = CreateDepartmentForm
    template_name = 'companies/department/update_department.html'
    permission_required = 'companies.change_department'

    def get_queryset(self):
        queryset = super().get_queryset()

        if not hasattr(self.request.user, 'profile'):
            return queryset.none()

        queryset = (queryset.select_related('company').prefetch_related(
            Prefetch('company__employees', queryset=Profile.objects.select_related('user', 'department')),
            Prefetch('company__shifts', queryset=Shift.objects.select_related('company')),
        ).filter(company=self.request.user.profile.company))

        return queryset


class DetailDepartmentView(CompanyObjectsAccessMixin, LoginRequiredMixin, PermissionRequiredMixin, views.DetailView):
    model = Department
    template_name = 'companies/department/department_detail.html'
    permission_required = 'companies.view_department'

    def get_queryset(self):
        queryset = super().get_queryset()

        user = self.request.user

        if not hasattr(user, 'profile'):
            return queryset.none()

        return queryset.filter(user.profile.company)


class DeleteDepartmentView(CompanyObjectsAccessMixin, LoginRequiredMixin, PermissionRequiredMixin, views.DeleteView):
    model = Department
    template_name = 'companies/department/delete_department.html'
    permission_required = 'companies.delete_department'

    def get_queryset(self):
        queryset = super().get_queryset()

        user = self.request.user

        if not hasattr(user, 'profile'):
            return queryset.none()

        return queryset.filter(user.profile.company)

    def get_success_url(self):
        return reverse('all_departments' , kwargs={'company_slug': self.request.user.profile.company.slug})