import logging

from django.contrib import messages
from django.contrib.auth import views as auth_views, login, logout, authenticate, get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.forms import SetPasswordForm
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import generic as views

from TimeSyncPro.accounts import forms

# from rest_framework import generics, status
# from rest_framework.response import Response
# from rest_framework.authtoken.models import Token
# from rest_framework.permissions import AllowAny

# from .serializers import LoginSerializer, SignupCompanySerializer

from TimeSyncPro.accounts.forms import SignupEmployeeForm, SignupCompanyAdministratorForm, \
    BasicEditTSPUserForm, DetailedEditTSPUserForm, CustomSetPasswordForm, \
    DetailedEditProfileForm, BasicEditProfileForm
from TimeSyncPro.accounts.view_mixins import OwnerRequiredMixin, \
    DynamicPermissionMixin, SuccessUrlMixin
# from TimeSyncPro.core.utils import format_email
from TimeSyncPro.common.views_mixins import NotAuthenticatedMixin, CompanyCheckMixin, \
    MultiplePermissionsRequiredMixin, AuthenticatedUserMixin

# TODO Employee not see another employee profile

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class SignupCompanyAdministratorUser(AuthenticatedUserMixin, views.CreateView):
    template_name = "accounts/signup_company_administrator.html"
    form_class = SignupCompanyAdministratorForm

    @transaction.atomic
    def form_valid(self, form):
        logger.debug("Entering form_valid method")
        try:

            user = form.save()

            authenticated_user = authenticate(
                self.request,
                username=user.email,
                password=form.cleaned_data['password1']
            )

            if authenticated_user:
                login(self.request, authenticated_user)

            if user.slug is None:
                return HttpResponseRedirect(reverse('index'))

            return redirect("create_company")

        except Exception as e:
            logger.error(f"Error in form_valid: {str(e)}")
            form.add_error(None, f"An error occurred: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning(f"Failed signup attempt: {form.cleaned_data.get('email')}")
        logger.warning(f"Form errors: {form.errors}")
        return super().form_invalid(form)


class SignInUserView(auth_views.LoginView):
    template_name = "accounts/signin_user.html"
    redirect_authenticated_user = True
    success_url = "profile"

    def get_redirect_url(self):
        if self.request.user.is_authenticated:
            user = self.request.user
            return reverse(
                self.success_url,
                kwargs={
                    'slug': user.slug,
                    # 'company_slug': user.company.slug,
                })
        return super().get_redirect_url()

    def form_valid(self, form):
        username = UserModel.formated_email(form.cleaned_data.get('username'))
        password = form.cleaned_data.get('password')
        remember_me = form.cleaned_data.get('remember_me')
        user = authenticate(
            self.request,
            username=username,
            password=password,
        )

        if user is not None:
            login(self.request, user)

            if remember_me:
                self.request.session.set_expiry(1209600)  # 2 weeks
            else:
                self.request.session.set_expiry(0)  # Browser close

            return HttpResponseRedirect(
                reverse('profile', kwargs={'slug': user.slug})
            )
        else:
            form.add_error(None, "Invalid username or password")
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning(f"Failed login attempt: {form.cleaned_data.get('username')}")
        logger.warning(f"Form errors: {form.errors}")
        return super().form_invalid(form)


class SignupEmployeeView(MultiplePermissionsRequiredMixin, NotAuthenticatedMixin, views.CreateView):
    template_name = 'accounts/register_employee.html'
    form_class = forms.SignupEmployeeForm

    permissions_required = [
        'accounts.add_administrator',
        'accounts.add_hr',
        'accounts.add_manager',
        'accounts.add_teamleader',
        'accounts.add_staff',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        context['company_slug'] = company.slug if company else None
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        employee = form.save(commit=False)

        user = self.request.user
        company = user.company

        if not company or not company.slug:
            messages.warning(self.request, "Company not found. Redirecting to home page.")
            return redirect('index')

        employee.save()

        messages.success(self.request, f"Employee successfully registered.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('company members', kwargs={'company_slug': self.request.user.company.slug})

    def form_invalid(self, form):
        messages.error(self.request, "An error occurred while registering the employee.")
        return super().form_invalid(form)


class DetailsProfileBaseView(LoginRequiredMixin, DynamicPermissionMixin, views.DetailView):
    model = UserModel
    context_object_name = "user_to_view"

    def get_queryset(self):
        return self.model.objects.select_related('profile__company').prefetch_related(
            Prefetch('groups', queryset=Group.objects.prefetch_related('permissions')),
            'user_permissions'
        )

    def get_template_names(self):
        if self.request.user == self.get_object():
            return ["accounts/details_profile.html"]
        return ["management/details_employee_profile.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        user_to_view = self.object

        all_permissions = set(user.get_all_permissions())

        company_slug = user.company.slug

        context.update({
            # 'user_to_view': user_to_view,
            'company_slug': company_slug if company_slug else None,
            'has_detailed_change_permission': self.get_action_permission(user_to_view, "change") in all_permissions,
            'has_delete_permission': self.get_action_permission(user_to_view, "delete") in all_permissions,
        })
        return context

    # @staticmethod
    # def handle_user_not_found(request):
    #     messages.error(request, "User not found.")
    #     return redirect('index')

    # def get(self, request, *args, **kwargs):
    #     context = self.get_context_data()
    #     return render(request, self.template_name, context)


class DetailsOwnProfileView(OwnerRequiredMixin, DetailsProfileBaseView):
    # template_name = "accounts/details_profile.html"

    # TODO check get_object
    def get_object(self, queryset=None):
        # self.object = self.request.user
        # return self.object
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context["permissions"] = self.request.user.get_all_permissions()
        return context


class DetailsEmployeesProfileView(
    NotAuthenticatedMixin,
    CompanyCheckMixin,
    PermissionRequiredMixin,
    DetailsProfileBaseView
):

    def get_permission_required(self):
        user_to_view = self.get_object()
        return [self.get_action_permission(user_to_view, "view")]

    def get_object(self, queryset=None):
        queryset = self.get_queryset() if queryset is None else queryset
        return get_object_or_404(queryset, slug=self.kwargs.get('slug'))


class EditProfileBaseView(NotAuthenticatedMixin, views.UpdateView):
    model = UserModel
    template_name = 'accounts/update_profile.html'
    form_class = BasicEditTSPUserForm
    success_url = 'profile'
    detailed_edit = False

    def get_queryset(self):
        return self.model.objects.select_related(
            'profile__company'
        ).prefetch_related(
            Prefetch(
                'groups',
                queryset=Group.objects.prefetch_related('permissions')
            ),
            'user_permissions'
        )

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return get_object_or_404(queryset, slug=self.kwargs.get('slug'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_form'] = self.get_form()
        context['additional_form'] = self.get_additional_form()
        context['user'] = self.request.user
        context['user_to_edit'] = self.object
        context['company_slug'] = self.object.profile.company.slug if self.object.profile.company else None
        return context

    def get_additional_form(self):
        additional_form_class = self._get_additional_form_class()
        if not additional_form_class:
            return None

        if self.request.method == 'POST':
            return additional_form_class(self.request.POST, instance=self.object.profile)
        return additional_form_class(instance=self.object.profile)

    def _get_additional_form_class(self):
        try:
            return DetailedEditProfileForm if self.detailed_edit else BasicEditProfileForm
        except ValueError as e:
            messages.error(self.request, str(e))
            return None

    def form_valid(self, form):
        additional_form = self.get_additional_form()
        context = self.get_context_data()
        if additional_form and not additional_form.is_valid():
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                self.object = form.save()
                if additional_form:
                    additional_form.save()
                messages.success(self.request, 'Profile updated successfully.')
                return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, "An unexpected error occurred while saving the profile.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse("profile", kwargs={'slug': self.object.slug})


class BasicEditProfileView(OwnerRequiredMixin, EditProfileBaseView):
    def get_object(self, queryset=None):
        return self.request.user


class DetailedEditProfileView(PermissionRequiredMixin, DynamicPermissionMixin, EditProfileBaseView):
    template_name = 'accounts/update_employee_profile.html'
    form_class = DetailedEditTSPUserForm

    detailed_edit = True

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        permission = self.get_action_permission(self.object, "change")
        self.permission_required = permission
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("company_members", kwargs={"company_slug": self.object.profile.company.slug})


class DetailedOwnEditProfileView(OwnerRequiredMixin, DetailedEditProfileView):
    template_name = 'accounts/full_update_own_profile.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("profile", kwargs={'slug': self.object.slug})



class DeleteEmployeeView(
    SuccessUrlMixin,
    NotAuthenticatedMixin,
    PermissionRequiredMixin,
    CompanyCheckMixin,
    DynamicPermissionMixin,
    views.DeleteView
):
    model = UserModel
    queryset = model.objects.select_related(
        'profile__company'  # Fetch employee and company in one query
    ).prefetch_related(
        Prefetch(
            'groups',
            queryset=Group.objects.prefetch_related('permissions')),  # Prefetch permissions through groups
        'user_permissions'  # Prefetch individual user permissions
    )
    template_name = 'accounts/delete_user.html'
    success_url = reverse_lazy('company members')

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        user_slug = self.kwargs['slug']
        user_to_delete = get_object_or_404(self.queryset, slug=user_slug)
        permission = self.get_action_permission(user_to_delete, "delete")
        self.permission_required = permission
        return super().dispatch(request, *args, **kwargs)

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     user = self.request.user
    #     user_to_delete = get_object_or_404(self.queryset, slug=self.kwargs['slug'])
    #     all_permissions = list(user.get_all_permissions())
    #
    #     context['has_delete_employee_permission'] = self.get_action_permission(user_to_delete, "delete") in all_permissions,
    #     return context

    # def get_success_url(self):
    #     user = self.request.user
    #     company_slug = user.profile.company.slug
    #     return reverse('company members', kwargs={"company_slug": company_slug})

    def post(self, request, *args, **kwargs):
        user_to_delete = get_object_or_404(self.queryset, slug=self.kwargs['slug'])
        related_instance = user_to_delete.employee

        if related_instance.role == 'Manager':
            manager_teams = related_instance.teams.all()
            for team in manager_teams:
                team.manager = None
                team.save()

        related_instance.delete()
        user_to_delete.delete()
        messages.success(request, "User deleted successfully.")
        return redirect(self.get_success_url())


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("password reset done")


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    success_url = reverse_lazy('password_reset_complete')
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


def signout_user(request):
    logout(request)
    return redirect('index')




class ActivateAndSetPasswordView(views.View):
    template_name = 'accounts/activate_and_set_password.html'

    def get(self, request, token):
        try:
            user = UserModel.objects.get(activation_token=token, is_active=False)
            form = SetPasswordForm(user)
            return render(request, self.template_name, {'form': form})
        except UserModel.DoesNotExist:
            messages.error(request, "Invalid or expired activation link.")
            return redirect('home')

    def post(self, request, token):
        try:
            user = UserModel.objects.get(activation_token=token, is_active=False)
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                user.is_active = True
                user.activation_token = ''
                user.save()
                login(request, user)
                messages.success(request, "Your account has been activated and password set successfully.")
                return redirect('profile')  # Redirect to the employee's profile page
            return render(request, self.template_name, {'form': form})
        except UserModel.DoesNotExist:
            messages.error(request, "Invalid or expired activation link.")
            return redirect('home')

# class SignupAndLoginView(views.TemplateView):
#     template_name = 'accounts/signup_login.html'
#
#
# class SignUpView(generics.CreateAPIView):
#     queryset = UserModel.objects.all()
#     serializer_class = SignupCompanySerializer
#     permission_classes = [AllowAny]
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()
#         token, created = Token.objects.get_or_create(user=user)
#         return Response({
#             'user': SignupCompanySerializer(user).data,
#             'token': token.key
#         })


# class LoginView(generics.GenericAPIView):
#     serializer_class = LoginSerializer
#     permission_classes = [AllowAny]
#
#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data
#         token, created = Token.objects.get_or_create(user=user)
#         return Response({
#             'token': token.key,
#             'user_id': user.pk,
#             'email': user.email
#         })
#
