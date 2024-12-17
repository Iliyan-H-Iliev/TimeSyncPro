import logging
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views import generic as views
from TimeSyncPro.accounts.forms import (
    BasicEditTSPUserForm,
    DetailedEditTSPUserForm,
    DetailedEditProfileForm,
    BasicEditProfileForm,
)
from TimeSyncPro.accounts.forms.edit_profile_forms import (
    AdminEditProfileForm,
    DetailedEditOwnProfileForm,
)
from TimeSyncPro.accounts.views.view_mixins import DynamicPermissionMixin
from TimeSyncPro.common.views_mixins import ReturnToPageMixin, OwnerRequiredMixin
import TimeSyncPro.common.forms as common_forms

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class EditProfileDispatcherView(OwnerRequiredMixin, DynamicPermissionMixin, views.View):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("sign_in")

        user = request.user
        permission = self.get_action_permission(user, "change")

        if user.has_perm(permission) or user.is_superuser:
            view = DetailedEditOwnProfileView.as_view()
        else:
            view = BasicEditOwnProfileView.as_view()

        return view(request, *args, **kwargs)


class EditProfileBaseView(ReturnToPageMixin, LoginRequiredMixin, views.UpdateView):
    model = UserModel
    template_name = "accounts/update_profile.html"
    form_class = BasicEditTSPUserForm
    detailed_edit = False
    address_form = common_forms.AddressForm

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.select_related(
            "profile__company",
            "profile__department",
            "profile__team",
            "profile__address",
            "profile__shift",
        ).prefetch_related(
            Prefetch("groups", queryset=Group.objects.prefetch_related("permissions")),
            "user_permissions",
        )

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return get_object_or_404(queryset, slug=self.kwargs.get("slug"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_form"] = self.get_form()
        context["profile_form"] = self.get_additional_form()
        context["address_form"] = self.address_form(
            instance=self.object.profile.address
        )
        return context

    def get_additional_form(self):
        additional_form_class = self._get_additional_form_class()
        if not additional_form_class:
            return None

        kwargs = {
            "instance": self.object.profile,
            "request": self.request,
        }

        if self.request.method == "POST":
            return additional_form_class(self.request.POST, **kwargs)
        return additional_form_class(**kwargs)

    def _get_additional_form_class(self):
        try:
            if not self.request.user.profile.company:
                if self.request.user.is_superuser or self.request.user.is_staff:
                    return AdminEditProfileForm

            if self.request.user == self.object and self.detailed_edit:
                return DetailedEditOwnProfileForm
            elif self.request.user != self.object and self.detailed_edit:
                return DetailedEditProfileForm
            else:
                return BasicEditProfileForm
        #
        except ValueError as e:
            messages.error(self.request, str(e))
            return None

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                form = self.get_form()
                additional_form = self.get_additional_form()
                address_form = self.address_form(
                    request.POST, instance=self.object.profile.address
                )

                if all(
                    f.is_valid() for f in [form, additional_form, address_form] if f
                ):
                    return self.form_valid(form, additional_form, address_form)
                return self.form_invalid(form, additional_form, address_form)
        except Exception as e:
            messages.error(request, "An error occurred. Please try again.")
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    additional_form=additional_form,
                    address_form=address_form,
                )
            )

    @transaction.atomic
    def form_valid(self, form, additional_form, address_form):
        try:
            address = None
            first_name = additional_form.cleaned_data.get("first_name")
            last_name = additional_form.cleaned_data.get("last_name")
            employee_id = additional_form.cleaned_data.get("employee_id")

            obj = form.save(commit=False)
            obj.save(
                first_name=first_name, last_name=last_name, employee_id=employee_id
            )

            if additional_form:
                profile = additional_form.save()

            if address_form:
                address = address_form.save()

            if address and obj.profile.address is None:
                obj.profile.address = address
                obj.profile.save()

            messages.success(self.request, "Profile updated successfully.")

            return super().form_valid(form)
        except Exception as e:
            messages.error(
                self.request, "An unexpected error occurred while saving the profile."
            )
            logger.error(f"Error updating profile for user {self.object.id}: {str(e)}")
            return self.form_invalid(form, additional_form, address_form)

    @transaction.atomic
    def form_invalid(self, form, additional_form, address_form):
        messages.error(self.request, "Please correct the errors below.")

        return self.render_to_response(
            self.get_context_data(
                form=form,
                additional_form=additional_form,
                address_form=self.address_form(instance=self.object.profile.address),
            )
        )

    def get_success_url(self):
        return reverse("profile", kwargs={"slug": self.object.slug})


class BasicEditOwnProfileView(OwnerRequiredMixin, EditProfileBaseView):
    def get_object(self, queryset=None):
        return self.request.user


class DetailedEditProfileView(
    PermissionRequiredMixin, DynamicPermissionMixin, EditProfileBaseView
):
    template_name = "accounts/update_employee_profile.html"
    form_class = DetailedEditTSPUserForm
    detailed_edit = True

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        permission = self.get_action_permission(self.object, "change")
        self.permission_required = permission
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "company_members", kwargs={"company_slug": self.object.profile.company.slug}
        )


class DetailedEditOwnProfileView(OwnerRequiredMixin, DetailedEditProfileView):
    form_class = DetailedEditTSPUserForm
    template_name = "accounts/update_profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("profile", kwargs={"slug": self.object.slug})
