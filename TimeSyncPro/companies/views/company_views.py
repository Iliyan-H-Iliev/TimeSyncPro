from django.contrib.auth import get_user_model, logout
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.db.models import Case, When, Value, IntegerField
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin

from ..models import Company
from ..forms import EditCompanyForm, CreateCompanyForm
from django.views import generic as views

from TimeSyncPro.common.views_mixins import CRUDUrlsMixin
from ..views_mixins import CheckOwnCompanyMixin, AddPermissionContextMixin
from ...absences.models import Holiday
from ...common.forms import AddressForm

UserModel = get_user_model()


class CreateCompanyView(LoginRequiredMixin, views.CreateView):
    model = Company
    template_name = "companies/company/create_company.html"
    form_class = CreateCompanyForm
    address_form_class = AddressForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "address_form" not in context:
            context["address_form"] = self.address_form_class()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
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
            messages.error(
                self.request, f"An error occurred while creating the company: {e}"
            )
            return self.form_invalid(form, address_form)

    @transaction.atomic
    def form_invalid(self, form, address_form):
        return self.render_to_response(
            self.get_context_data(form=form, address_form=address_form)
        )

    def get_success_url(self):
        return reverse("company_profile", kwargs={"company_slug": self.object.slug})

    def dispatch(self, request, *args, **kwargs):
        if request.user.profile.company:
            messages.error(request, "User already belongs to a company.")
            return redirect(
                reverse(
                    "company_profile",
                    kwargs={"company_slug": request.user.profile.company.slug},
                )
            )
        return super().dispatch(request, *args, **kwargs)


class DetailsCompanyView(
    CheckOwnCompanyMixin, LoginRequiredMixin, PermissionRequiredMixin, views.DetailView
):
    model = Company
    template_name = "companies/company/company_profile.html"
    permission_required = "companies.view_company"
    slug_url_kwarg = "company_slug"

    def get_queryset(self):
        return (
            self.model.objects.select_related(
                "address",
            )
            .prefetch_related(
                "employees",
                "departments",
                "teams",
                "shifts",
            )
            .filter(slug=self.kwargs.get("company_slug"))
        )


class EditCompanyView(
    CheckOwnCompanyMixin, LoginRequiredMixin, PermissionRequiredMixin, views.UpdateView
):
    model = Company
    template_name = "companies/company/update_company.html"
    form_class = EditCompanyForm
    address_form_class = AddressForm
    permission_required = "companies.change_company"
    slug_url_kwarg = "company_slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_object()
        context["company"] = company
        context["address_form"] = self.address_form_class(instance=company.address)
        return context

    def get_success_url(self):
        company = self.object
        return reverse("company_profile", kwargs={"company_slug": company.slug})

    @transaction.atomic
    def form_valid(self, form, address_form):
        company = form.save(commit=False)
        address = address_form.save()
        company.address = address
        company.save()
        messages.success(self.request, "Company updated successfully.")
        return HttpResponseRedirect(self.get_success_url())

    @transaction.atomic
    def form_invalid(self, form, address_form):
        return self.render_to_response(
            self.get_context_data(form=form, address_form=address_form)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        address_form = self.address_form_class(
            request.POST, instance=self.object.address
        )
        if form.is_valid() and address_form.is_valid():
            return self.form_valid(form, address_form)
        else:
            return self.form_invalid(form, address_form)


class CompanyMembersView(
    CRUDUrlsMixin,
    CheckOwnCompanyMixin,
    PermissionRequiredMixin,
    LoginRequiredMixin,
    AddPermissionContextMixin,
    views.ListView,
):
    # model = Company
    model = UserModel
    template_name = "companies/employee/employees.html"
    context_object_name = "objects"
    paginate_by = 10
    ordering = ["first_name", "last_name"]
    permission_required = "accounts.view_employee"

    add_permission = "accounts.add_employee"

    view_permission = (
        "accounts.view_hr",
        "accounts.view_manager",
        "accounts.view_team_leader",
        "accounts.view_staff",
    )

    def _get_view_permission(self):
        permissions = []
        user_permissions = self.request.user.get_all_permissions()
        for permission in self.view_permission:
            if permission in user_permissions:
                perm = permission.split(".")[1]
                perm = perm.split("_")[1:]
                permissions.append(" ".join(perm).title())
        return permissions

    crud_url_names = {
        "create": "register_employee",
        "detail": "employee_profile",
        "update": "update_employee",
        "delete": "delete_employee",
    }

    button_names = {
        "create": "Employee",
    }

    def get_queryset(self):
        query = self.request.GET.get("search", "")

        queryset = (
            self.model.objects.select_related(
                "profile",
                "profile__company",
                "profile__company__holiday_approver",
                "profile__department",
                "profile__department__holiday_approver",
                "profile__team",
                "profile__team__shift",
                "profile__team__holiday_approver",
                "profile__shift",
            )
            .filter(profile__company=self.request.user.profile.company)
            .annotate(
                sort_priority=Case(
                    When(profile__is_company_admin=True, then=Value(0)),
                    When(profile__role="HR", then=Value(1)),
                    When(profile__role="Manager", then=Value(2)),
                    When(profile__role="Team Leader", then=Value(3)),
                    When(profile__role="Staff", then=Value(4)),
                    default=Value(5),
                    output_field=IntegerField(),
                )
            )
            .order_by("sort_priority", "profile__first_name", "profile__last_name")
        )

        if query:
            queryset = queryset.filter(
                Q(profile__first_name__icontains=query)
                | Q(profile__last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(profile__role__icontains=query)
                | Q(profile__department__name__icontains=query)
                | Q(profile__team__name__icontains=query)
                | Q(profile__team__shift__name__icontains=query)
                | Q(profile__shift__name__icontains=query)
            )

        return queryset

    def get(self, request, *args, **kwargs):
        company = request.user.profile.company

        if not company:
            messages.error(request, "User does not belong to any company.")
            return redirect("index")
        return super().get(request, *args, **kwargs)

    # # TODO check if this is the right way to fetch related models for the user profile
    def get_context_data(self, **kwargs):
        holidays_requests = Holiday.objects.filter(
            Q(requester__company=self.request.user.profile.company)
            | Q(reviewer=self.request.user.profile)
        ).order_by("-start_date")

        requesters_pk = holidays_requests.values_list("requester", flat=True)

        context = super().get_context_data(**kwargs)
        context["requesters_pk"] = requesters_pk
        context["title"] = "Employees"
        context["search_value"] = self.request.GET.get("search", "")
        context["view_permissions"] = self._get_view_permission()
        context["view_requests"] = self.request.user.has_perm(
            "absences.view_all_holidays_requests"
        )
        return context


class DeleteCompanyView(
    CheckOwnCompanyMixin, LoginRequiredMixin, PermissionRequiredMixin, views.DeleteView
):
    model = Company
    template_name = "companies/company/delete_company.html"
    success_url = reverse_lazy("index")
    permission_required = "companies.delete_company"

    def get_object(self, queryset=None):
        company_slug = self.request.user.company.slug
        obj = self.model.objects.prefetch_related("employees", "employees__user").get(
            slug=company_slug
        )
        return obj

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            company = self.get_object()
            users = UserModel.objects.filter(profile__company=company)
            for user in users:
                user.groups.clear()
                user.user_permissions.clear()
                user.history_changes.clear()
            company.skip_history = True
            company.delete()
            users.delete()
        user = request.user
        logout(request)
        user.delete()

        return redirect(self.success_url)
