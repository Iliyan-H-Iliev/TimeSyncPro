import logging
from django.contrib import messages
from django.contrib.auth import views as auth_views, login, authenticate, get_user_model
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.forms import SetPasswordForm
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic as views
from TimeSyncPro.accounts.forms import CustomSetPasswordForm

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("password reset done")


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    success_url = reverse_lazy("password_reset_complete")
    form_class = CustomSetPasswordForm

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.user
        if not user.is_active:
            user.is_active = True
            user.save()
        return response


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("password change done")


class ActivateAndSetPasswordView(views.View):
    template_name = "accounts/activate_and_set_password.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("profile", slug=request.user.slug)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, token):
        try:
            user = UserModel.objects.get(activation_token=token, is_active=False)
            form = SetPasswordForm(user)
            return render(request, self.template_name, {"form": form})
        except UserModel.DoesNotExist:
            messages.error(request, "Invalid or expired activation link.")
            return redirect("index")

    def post(self, request, token):
        try:
            user = UserModel.objects.get(activation_token=token, is_active=False)
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                user.is_active = True
                user.activation_token = ""
                user.save()

                authenticated_user = authenticate(
                    request,
                    username=user.email,
                    password=form.cleaned_data["new_password1"],
                )

                if authenticated_user:
                    login(request, authenticated_user)
                    messages.success(
                        request,
                        "Your account has been activated and password set successfully.",
                    )
                    return redirect("profile", slug=authenticated_user.slug)
                else:
                    messages.error(request, "Error logging in after activation.")
                    return redirect("login")

            return render(request, self.template_name, {"form": form})
        except UserModel.DoesNotExist:
            messages.error(request, "Invalid or expired activation link.")
            return redirect("index")
