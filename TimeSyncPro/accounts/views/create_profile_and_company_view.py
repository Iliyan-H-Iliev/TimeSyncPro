import logging
from TimeSyncPro.accounts.models import Profile
from TimeSyncPro.common.models import Address
from TimeSyncPro.common.views_mixins import OwnerRequiredMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.views import generic as views
from TimeSyncPro.accounts import forms
import TimeSyncPro.companies.forms as company_forms
import TimeSyncPro.common.forms as common_forms

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class CreateProfileAndCompanyView(
    OwnerRequiredMixin, LoginRequiredMixin, views.CreateView
):
    model = Profile
    template_name = "accounts/create_profile_and_company.html"
    form_class = forms.CreateCompanyAdministratorProfileForm
    company_form_class = company_forms.CreateCompanyForm
    profile_address_form_class = common_forms.AddressForm
    company_address_form_class = common_forms.AddressForm

    def dispatch(self, request, *args, **kwargs):
        if (hasattr(request.user, "profile") and request.user.profile is not None) and (
            hasattr(request.user.profile, "company")
            and request.user.profile.company is not None
        ):
            return redirect("dashboard", slug=request.user.slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "company_form" not in kwargs:
            context["company_form"] = self.company_form_class()
        if "company_address_form" not in kwargs:
            context["company_address_form"] = self.company_address_form_class()
        if "profile_form" not in kwargs:
            context["profile_form"] = self.form_class()
        if "profile_address_form" not in kwargs:
            context["profile_address_form"] = self.profile_address_form_class()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        company_form = self.company_form_class(request.POST)
        company_address_form = self.company_address_form_class(
            request.POST, prefix="company"
        )
        profile_address_form = self.profile_address_form_class(
            request.POST, prefix="profile"
        )

        if all(
            [
                form.is_valid(),
                company_form.is_valid(),
                company_address_form.is_valid(),
                profile_address_form.is_valid(),
            ]
        ):
            return self.form_valid(
                form, company_form, company_address_form, profile_address_form
            )
        else:
            return self.form_invalid(
                form, company_form, company_address_form, profile_address_form
            )

    @transaction.atomic
    def form_valid(
        self, form, company_form, company_address_form, profile_address_form
    ):
        try:

            if company_address_form.has_data():
                company_address = company_address_form.save()
            else:
                company_address = Address.objects.create()

            if profile_address_form.has_data():
                profile_address = profile_address_form.save()
            else:
                profile_address = Address.objects.create()

            company = company_form.save(commit=False)
            company.address = company_address
            company.save()

            user = self.request.user

            profile = form.save(commit=False)
            profile.user = user
            profile.address = profile_address
            profile.company = company
            profile.is_company_admin = True

            profile.save()

            company.holiday_approver = profile
            company.save()

            first_name = form.cleaned_data.get("first_name")
            last_name = form.cleaned_data.get("last_name")
            employee_id = form.cleaned_data.get("employee_id")

            user.save(
                first_name=first_name, last_name=last_name, employee_id=employee_id
            )

            messages.success(self.request, "Company and profile created successfully.")
            return redirect("profile", slug=self.request.user.slug)

        except Exception as e:
            transaction.set_rollback(True)
            messages.error(self.request, f"An error occurred: {str(e)}")
            return self.form_invalid(
                form, company_form, company_address_form, profile_address_form
            )

    @transaction.atomic
    def form_invalid(
        self, form, company_form, company_address_form, profile_address_form
    ):
        messages.error(self.request, "Please correct the errors below.")
        return self.render_to_response(
            self.get_context_data(
                form=form,
                company_form=company_form,
                company_address_form=company_address_form,
                profile_address_form=profile_address_form,
            )
        )
