import logging
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.contrib.auth.models import Group
from django.db.models import Prefetch
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views import generic as views
from TimeSyncPro.accounts.views.view_mixins import DynamicPermissionMixin
from TimeSyncPro.common.views_mixins import CompanyObjectsAccessMixin

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class DeleteEmployeeView(
    CompanyObjectsAccessMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DynamicPermissionMixin,
    views.DeleteView,
):
    model = UserModel
    template_name = "accounts/delete_employee.html"
    context_object_name = "object"

    def get_queryset(self):
        queryset = self.model.objects.select_related(
            "profile__company"
        ).prefetch_related(
            Prefetch("groups", queryset=Group.objects.prefetch_related("permissions")),
            "user_permissions",
        )
        return queryset

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_queryset(), slug=self.kwargs["slug"])

    def get_permission_required(self):
        user_to_delete = self.get_object()
        return [self.get_action_permission(user_to_delete, "delete")]

    def get_success_url(self):
        user = self.request.user
        company_slug = user.profile.company.slug
        return reverse("company_members", kwargs={"company_slug": company_slug})

    def post(self, request, *args, **kwargs):
        # Changed from self.queryset to self.get_queryset()
        user_to_delete = get_object_or_404(
            self.get_queryset(), slug=self.kwargs["slug"]
        )
        related_instance = user_to_delete.profile

        try:
            # Delete in try-except block for better error handling
            related_instance.delete()
            user_to_delete.delete()
            messages.success(request, "User deleted successfully.")
        except Exception as e:
            messages.error(request, f"Error deleting user: {str(e)}")
            logger.error(f"Error deleting user: {str(e)}")

        return redirect(self.get_success_url())
