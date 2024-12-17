from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.db.models import Prefetch
from django.urls import reverse

from ..models import Department, Shift, Team
from ..forms import CreateDepartmentForm, EditDepartmentForm
from django.views import generic as views

from TimeSyncPro.common.views_mixins import CompanyObjectsAccessMixin, \
    ReturnToPageMixin, CompanyAccessMixin, CRUDUrlsMixin
from ..views_mixins import ApiConfigMixin, AddPermissionMixin
from ...accounts.models import Profile


class CreateDepartmentView(LoginRequiredMixin, PermissionRequiredMixin, views.CreateView):
    model = Department
    form_class = CreateDepartmentForm
    template_name = 'companies/department/create_department.html'
    permission_required = 'companies.add_department'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse(
            'all_departments',
            kwargs={'company_slug': self.request.user.company.slug}
        )

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        return super().form_valid(form)


class DepartmentsView(
    AddPermissionMixin,
    CompanyAccessMixin,
    CRUDUrlsMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    views.ListView
):
    model = Department
    template_name = 'companies/department/all_departments.html'
    permission_required = 'companies.view_department'
    context_object_name = 'objects'
    paginate_by = 4
    ordering = 'name'

    add_permission = 'companies.add_department'

    crud_url_names = {
        "create": "create_department",
        "detail": "details_department",
        "update": "update_department",
        "delete": "delete_department",
    }

    button_names = {
        'create': 'Department',
    }

    def get_queryset(self):
        query = self.request.GET.get('search', '')
        queryset = (Department.objects.select_related("holiday_approver").prefetch_related(
            Prefetch(
                'employees',
                queryset=Profile.objects.select_related('user', 'team', 'shift')),
        ).filter(company=self.request.user.profile.company)).order_by('name')

        if query:
            queryset = queryset.filter(name__icontains=query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Departments'
        context['search_value'] = self.request.GET.get('search', '')
        return context


class EditDepartmentView(
    ReturnToPageMixin,
    CompanyObjectsAccessMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    views.UpdateView
):
    model = Department
    form_class = EditDepartmentForm
    template_name = 'companies/department/update_department.html'
    permission_required = 'companies.change_department'

    def get_queryset(self):
        queryset = super().get_queryset()

        if not hasattr(self.request.user, 'profile'):
            return queryset.none()

        queryset = (queryset.select_related(
            'company',
            'holiday_approver',
            'holiday_approver__user'
        ).prefetch_related(
            Prefetch(
                'company__employees',
                queryset=Profile.objects.select_related(
                    'user',
                    'team',
                    'shift'
                )
            ),
            Prefetch(
                'company__shifts',
                queryset=Shift.objects.select_related('company')
            ),
            Prefetch(
                'company__teams',
                queryset=Team.objects.select_related('company')
            ),
        ).filter(company=self.request.user.company))

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'company': self.request.user.company,
            'user': self.request.user,
            'department': self.object
        })

        return kwargs

    def get_success_url(self):
        return reverse(
            'all_departments',
            kwargs={'company_slug': self.request.user.company.slug}
        )


class DetailsDepartmentView(
    ApiConfigMixin,
    CompanyObjectsAccessMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    views.DetailView
):
    model = Department
    template_name = 'companies/department/details_department.html'
    permission_required = 'companies.view_department'
    employee_api_url_name = 'department-employees-api'
    history_api_url_name = 'department-history-api'

    def get_queryset(self):
        queryset = super().get_queryset()

        queryset = (queryset.select_related(
            "holiday_approver",
        ).prefetch_related(
            "employees"
        ).filter(company=self.request.user.company))

        return queryset


# TODO - Add DeleteDepartmentView
class DeleteDepartmentView(
    CompanyObjectsAccessMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    views.DeleteView
):
    model = Department
    template_name = 'companies/department/delete_department.html'
    permission_required = 'companies.delete_department'

    def get_success_url(self):
        return reverse('all_departments', kwargs={'company_slug': self.request.user.profile.company.slug})
