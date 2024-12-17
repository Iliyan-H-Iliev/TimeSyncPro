import logging
from django.contrib.auth import views as auth_views, login, authenticate, get_user_model
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.urls import reverse
from TimeSyncPro.accounts import forms

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class SignInUserView(auth_views.LoginView):
    template_name = "accounts/signin_user.html"
    redirect_authenticated_user = True
    form_class = forms.SignInUserForm
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 300
    REMEMBER_ME_DURATION = 1209600

    def get_success_url(self):
        user = self.request.user
        profile = getattr(user, "profile", None)
        company = getattr(profile, "company", None)
        is_super = user.is_superuser
        is_sta = user.is_staff

        if (
            (user.is_superuser or user.is_staff) and company is None
        ) or company is None:
            return reverse("profile", kwargs={"slug": user.slug})

        if profile is None:
            return reverse("create_profile_company", kwargs={"slug": user.slug})

        return reverse("dashboard", kwargs={"slug": user.slug})

    def form_valid(self, form):
        username = form.cleaned_data.get("username", "").strip()
        cache_key = f"login_attempts_{username.lower()}"
        attempts = cache.get(cache_key, 0)

        if attempts >= self.MAX_LOGIN_ATTEMPTS:
            form.add_error(
                None,
                "Too many login attempts. Please try again later.",
            )
            logger.warning(
                f"Login blocked due to too many attempts for user: {username}"
            )
            return self.form_invalid(form)

        password = form.cleaned_data.get("password")
        remember_me = form.cleaned_data.get("remember_me")
        expiry_time = self.REMEMBER_ME_DURATION if remember_me else 0

        user = authenticate(
            self.request,
            username=username,
            password=password,
        )

        if user is None:
            cache.set(cache_key, attempts + 1, self.LOCKOUT_DURATION)
            form.add_error(None, "Invalid email or password")
            return self.form_invalid(form)

        cache.delete(cache_key)
        login(self.request, user)
        self.request.session.set_expiry(expiry_time)

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        logger.warning(f"Failed login attempt: {form.cleaned_data.get('username')}")
        logger.warning(f"Form errors: {form.errors}")
        return super().form_invalid(form)
