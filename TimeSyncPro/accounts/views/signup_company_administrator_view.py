import logging
from django.contrib.auth import login, authenticate, get_user_model
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic as views
from TimeSyncPro.accounts.forms import SignupCompanyAdministratorForm
from TimeSyncPro.common.views_mixins import AuthenticatedUserMixin


logger = logging.getLogger(__name__)

UserModel = get_user_model()


class SignupCompanyAdministratorView(AuthenticatedUserMixin, views.CreateView):
    template_name = "accounts/signup_company_administrator.html"
    form_class = SignupCompanyAdministratorForm

    def get_success_url(self):
        return reverse("create_profile_company", kwargs={"slug": self.object.slug})

    def form_valid(self, form):
        try:
            user = form.save()

            authenticated_user = authenticate(
                self.request,
                username=user.email,
                password=form.cleaned_data["password1"],
            )

            if authenticated_user:
                login(self.request, authenticated_user)

            if user.slug is None:
                return HttpResponseRedirect(reverse("index"))

            self.object = user

            return self.get_success_url()

        except Exception as e:
            logger.error(f"Error in form_valid: {str(e)}")
            form.add_error(None, f"An error occurred: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning(f"Form errors: {form.errors}")
        return super().form_invalid(form)
