import logging
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.db import transaction, IntegrityError
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic as views
from TimeSyncPro.accounts import forms
from TimeSyncPro.common.models import Address
import TimeSyncPro.common.forms as common_forms

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class SignupEmployeeView(PermissionRequiredMixin, LoginRequiredMixin, views.CreateView):
    template_name = "accounts/register_employee.html"
    form_class = forms.SignupEmployeeForm
    object = None

    permissions_required = [
        "accounts.add_company_admin",
        "accounts.add_hr",
        "accounts.add_manager",
        "accounts.add_team_leader",
        "accounts.add_staff",
    ]

    def has_permission(self):
        return any(
            self.request.user.has_perm(perm) for perm in self.permissions_required
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "form" not in kwargs:
            kwargs["form"] = self.get_form()
        if "address_form" not in kwargs:
            kwargs["address_form"] = common_forms.AddressForm()
        company = self.request.user.company
        context["company_slug"] = company.slug if company else None
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        address_form = common_forms.AddressForm(request.POST)

        if all(f.is_valid() for f in [form, address_form]):
            return self.form_valid(form, address_form)
        else:
            return self.form_invalid(form, address_form)

    @transaction.atomic
    def form_valid(self, form, address_form):
        try:
            self.object = form.save()

            if address_form.has_data():
                address = address_form.save()
            else:
                address = Address.objects.create()

            self.object.profile.address = address
            self.object.profile.save()

            messages.success(self.request, f"Employee successfully registered.")
            return redirect(self.get_success_url())

        except IntegrityError as e:
            messages.error(
                self.request, "An error occurred while registering the employee."
            )
            return self.form_invalid(form, address_form)
        except Exception as e:
            messages.error(
                self.request,
                f"An error occurred while registering the employee: {str(e)}",
            )
            return self.form_invalid(form, address_form)

    def get_success_url(self):
        return reverse(
            "company_members", kwargs={"company_slug": self.request.user.company.slug}
        )

    @transaction.atomic
    def form_invalid(self, form, address_form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")

        messages.error(
            self.request, "An error occurred while registering the employee."
        )
        return self.render_to_response(
            self.get_context_data(form=form, address_form=address_form)
        )
