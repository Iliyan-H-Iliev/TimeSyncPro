import logging

from django.contrib import messages
from django.contrib.auth import views as auth_views, login, logout, authenticate, get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.views import PasswordResetConfirmView
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views import generic as views

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny

from .models import Company
from .serializers import LoginSerializer, SignupCompanySerializer

from django.contrib.auth.forms import SetPasswordForm

from TimeSyncPro.accounts.forms import SignupEmployeeForm, SignupCompanyAdministratorForm, \
    BasicEditTimeSyncProUserForm, DetailedEditTimeSyncProUserForm, CustomSetPasswordForm, EditCompanyForm
from TimeSyncPro.accounts.utils import get_user_by_slug, get_additional_form_class
from TimeSyncPro.accounts.view_mixins import CompanyContextMixin, OwnerRequiredMixin, \
    DynamicPermissionMixin, IsCompanyUserMixin, UserBySlugMixin, SuccessUrlMixin
from TimeSyncPro.core.views_mixins import AuthenticatedViewMixin, CompanyCheckMixin, \
    MultiplePermissionsRequiredMixin

# TODO Employee not see another employee profile

logger = logging.getLogger(__name__)

UserModel = get_user_model()


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


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })


class IndexView(views.TemplateView):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            # messages.info(request, "Please log in to access full features of this page.")
            return render(request, self.template_name)

        full_name = user.full_name

        return render(request, self.template_name, {
            'full_name': full_name,
        })


# class SignupCompanyView(SuccessUrlMixin, views.CreateView):
#     model = UserModel
#     template_name = "accounts/register_company.html"
#     form_class = SignupCompanyAdministratorForm
#     redirect_authenticated_user = True
#     # success_url = reverse_lazy("profile")
#
#     def dispatch(self, request, *args, **kwargs):
#         if self.request.user.is_authenticated:
#             return redirect(self.get_success_url())
#         return super().dispatch(request, *args, **kwargs)
#
#     def form_valid(self, form):
#         # Save the form and get the user
#         user = form.save()
#
#         # Authenticate and log the user in
#         authenticated_user = authenticate(
#             self.request,
#             username=form.cleaned_data['email'],
#             password=form.cleaned_data['password1']
#         )
#         if authenticated_user:
#             login(self.request, authenticated_user)
#
#         # Get the slug and company_name
#         user_slug = user.slug
#         company_name = user.company_name
#         company_slug = user.company_slug
#
#         # Check if slug and company_name are available
#         if user_slug is None or company_name is None:
#             # Handle the case where slug or company_name is not available
#             # You might want to redirect to a different page or show an error message
#             return HttpResponseRedirect(reverse('index'))
#
#         # Redirect to the profile page
#         return HttpResponseRedirect(
#             reverse('profile', kwargs={'slug': user_slug, 'company_slug': company_slug})
#         )
#
#     def form_invalid(self, form):
#         logger.warning(f"Failed login attempt: {form.cleaned_data.get('name')}")
#         logger.warning(f"Form errors: {form.errors}")
#         return super().form_invalid(form)
#
# # TODO CHECK THIS
# #     def get_success_url(self):
# #         user = self.object
# #         return reverse(
# #             'profile',
# #             kwargs={
# #                 'slug': user.slug,
# #                 "company_slug": user.company_slug
# #             }
# #         )

class SignupCompanyView(SuccessUrlMixin, views.CreateView):
    model = UserModel
    template_name = "accounts/register_company.html"
    form_class = SignupCompanyAdministratorForm
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        try:
            # Save the form and get the user
            user = form.save()

            # Refresh the user object to ensure all related objects are loaded
            user.refresh_from_db()

            # Authenticate and log the user in
            authenticated_user = authenticate(
                self.request,
                username=user.email,
                password=form.cleaned_data['password1']
            )
            if authenticated_user:
                login(self.request, authenticated_user)

            # Get the slug and company_name
            user_slug = user.slug
            company_name = user.company_name
            company_slug = user.company_slug

            # Check if slug and company_name are available
            if user_slug is None or company_name is None or company_slug is None:
                # Handle the case where slug, company_name, or company_slug is not available
                return HttpResponseRedirect(reverse('index'))

            # Redirect to the profile page
            return HttpResponseRedirect(
                reverse('profile', kwargs={'slug': user_slug, 'company_slug': company_slug})
            )
        except Exception as e:
            # Log the error
            logger.error(f"Error in form_valid: {str(e)}")
            # Add form error
            form.add_error(None, f"An error occurred: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning(f"Failed signup attempt: {form.cleaned_data.get('email')}")
        logger.warning(f"Form errors: {form.errors}")
        return super().form_invalid(form)


class SignInUserView(SuccessUrlMixin, auth_views.LoginView):
    template_name = "accounts/signin_user.html"
    # TODO change to True
    redirect_authenticated_user = True
    success_url = reverse_lazy("profile")

    # def get_success_url(self):
    #     user = self.request.user
    #     kwargs = {
    #         'slug': user.slug,
    #         "company_slug": user.company_slug
    #     }
    #
    #     url_name = 'company profile' if user.is_company else 'profile'
    #     return reverse(url_name, kwargs=kwargs)

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        remember_me = form.cleaned_data.get('remember_me')
        user = authenticate(self.request, username=username, password=password)

        if user is not None:
            login(self.request, user)

            if remember_me:
                self.request.session.set_expiry(1209600)  # 2 weeks
            else:
                self.request.session.set_expiry(0)  # Browser close

            return HttpResponseRedirect(
                reverse('profile', kwargs={'slug': user.slug, "company_slug": user.company_slug}))

        return super().form_valid(form)

    def form_invalid(self, form):
        logger.warning(f"Failed login attempt: {form.cleaned_data.get('username')}")
        logger.warning(f"Form errors: {form.errors}")
        return super().form_invalid(form)


class SignupEmployeeView(MultiplePermissionsRequiredMixin, AuthenticatedViewMixin, views.CreateView):
    template_name = 'accounts/register_employee.html'
    form_class = SignupEmployeeForm
    permissions_required = [
        'accounts.add_hr',
        'accounts.add_manager',
        'accounts.add_teamleader',
        'accounts.add_staff',
    ]

    # TODO: replace 'success_url' with the actual URL name
    success_url = reverse_lazy("index")
    # allowed_groups = ['HR', 'Company']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class DetailsProfileBaseView(UserBySlugMixin, views.DetailView):
    template_name = "accounts/details_company_employee.html"
    context_object_name = 'user'
    model = UserModel

    def get_context_data(self, user, user_to_view):
        return {
            'user': user,
            'user_to_view': user_to_view,
            'company_slug': user.company_slug,
        }

    @staticmethod
    def handle_user_not_found(request):
        messages.error(request, "User not found.")
        return redirect('index')

    def get(self, request, *args, **kwargs):
        user = request.user
        user_to_view = self.get_object()

        if user_to_view is None:
            return self.handle_user_not_found(request)

        context = self.get_context_data(user, user_to_view)
        return render(request, self.template_name, context)


class DetailsOwnProfileView(OwnerRequiredMixin, DetailsProfileBaseView):
    pass


class DetailsEmployeesProfileView(
    CompanyCheckMixin,
    PermissionRequiredMixin,
    DynamicPermissionMixin,
    DetailsProfileBaseView
):
    # TODO add permission

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        user_to_view = self.get_object()
        permission = self.get_action_permission(user_to_view, "view")
        self.permission_required = permission
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, user, user_to_view):
        context = super().get_context_data(user, user_to_view)
        context['has_detailed_change_permission'] = self.has_needed_permission(user, user_to_view, "change")
        context['has_delete_permission'] = self.has_needed_permission(user, user_to_view, "delete")
        return context


#OwnerRequiredMixin, IsCompanyUserMixin,
# class DetailsCompanyProfileView(DetailsProfileBaseView):
#     model = Company
#     template_name = "accounts/company_profile.html"
#
#     def get_context_data(self, user, user_to_view):
#         context = super().get_context_data(user, user_to_view)
#         context['company'] = user.company
#         return context


class DetailsCompanyProfileView(CompanyContextMixin, views.DetailView):
    model = Company
    template_name = "accounts/company_profile.html"
    context_object_name = 'company'

    def get_object(self, queryset=None):
        user = self.request.user
        company = user.company
        return company



class EditProfileBaseView(AuthenticatedViewMixin, views.View):
    success_url = 'index'
    detailed_edit = False

    @staticmethod
    def get_user_to_edit(slug):
        return get_user_by_slug(slug)

    def get_success_url(self, slug, company_slug):
        return reverse(self.success_url, kwargs={'slug': slug, 'company_slug': company_slug})

    def get_additional_form_class(self, detailed_edit):
        try:
            return get_additional_form_class(detailed_edit=detailed_edit)
        except ValueError as e:
            messages.error(self.request, str(e))
            return None

    def get_additional_form(self, user, request=None):
        additional_form_class = self.get_additional_form_class( detailed_edit=self.detailed_edit)
        if not additional_form_class:
            return None

        related_instance = user.related_instance

        if request:
            return additional_form_class(request.POST, instance=related_instance)
        return additional_form_class(instance=related_instance)

    def get_context_data(self, user_form, additional_form, user, user_to_edit=None, company_slug=None):
        return {
            'user_form': user_form,
            'additional_form': additional_form,
            'user': user,
            'user_to_edit': user_to_edit,
            'company_slug': company_slug,
        }

    def form_valid(self, user_form, additional_form, user, user_to_edit=None):
        user_form.save()
        if additional_form:
            additional_form.save()
        messages.success(self.request, 'Profile updated successfully.')
        return redirect(self.get_success_url(user.slug, user.company_slug))

    def form_invalid(self, user_form, additional_form, context):
        messages.error(self.request, 'Please correct the error below.')
        return render(self.request, self.template_name, context)


class BasicEditProfileView(OwnerRequiredMixin, EditProfileBaseView):
    template_name = 'accounts/edit_profile.html'
    form_class = BasicEditTimeSyncProUserForm
    success_url = 'profile'
    detailed_edit = False

    def get(self, request, *args, **kwargs):
        user = request.user
        user_form = self.form_class(instance=user)
        additional_form = self.get_additional_form(user)
        if additional_form is None:
            return redirect('index')
        context = self.get_context_data(user_form, additional_form, user)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = request.user
        user_form = self.form_class(request.POST, instance=user)
        additional_form = self.get_additional_form(user, request)
        if additional_form is None:
            return redirect('index')

        if user_form.is_valid() and (additional_form is None or additional_form.is_valid()):
            return self.form_valid(user_form, additional_form, user, user)

        context = self.get_context_data(user_form, additional_form, user)
        return self.form_invalid(user_form, additional_form, context)


class DetailedEditProfileView(UserBySlugMixin, PermissionRequiredMixin, DynamicPermissionMixin, EditProfileBaseView):
    template_name = 'accounts/full_profile_edit.html'
    form_class = DetailedEditTimeSyncProUserForm
    success_url = 'company employee profile'
    detailed_edit = True

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        user_to_edit = self.get_object()
        permission = self.get_action_permission(user_to_edit, "change")
        self.permission_required = permission
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        user = request.user
        user_to_edit = self.get_object()
        company_slug = user.company_slug

        user_form = self.form_class(instance=user_to_edit)
        additional_form = self.get_additional_form(user_to_edit)
        if additional_form is None:
            return redirect('index')
        context = self.get_context_data(user_form, additional_form, user, user_to_edit, company_slug)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        slug = self.kwargs['slug']
        user = request.user
        user_to_edit = self.get_user_to_edit(slug)
        company_slug = user.company_slug

        if user_to_edit is None:
            messages.error(request, "User not found.")
            return redirect('index')

        user_form = self.form_class(request.POST or None, instance=user_to_edit)
        additional_form = self.get_additional_form(user_to_edit, request)
        if additional_form is None:
            return redirect('index')

        if user_form.is_valid() and (additional_form is None or additional_form.is_valid()):
            return self.form_valid(user_form, additional_form, user, user_to_edit)

        context = self.get_context_data(user_form, additional_form, user, user_to_edit, company_slug)
        return self.form_invalid(user_form, additional_form, context)


# class EditCompanyView(BasicEditProfileView):
#     template_name = 'accounts/edit_company.html'
#     success_url = 'company profile'
#     detailed_edit = True


class EditCompanyView(AuthenticatedViewMixin, views.UpdateView):
    model = Company
    template_name = 'accounts/edit_company.html'
    form_class = EditCompanyForm
    permissions_required = [
        'accounts.change_company',
    ]

    def get_object(self, queryset=None):
        user = self.request.user
        company = user.company
        return company

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.object
        context['company'] = company
        return context

    def get_success_url(self):
        company = self.object
        return reverse('company profile', kwargs={'company_slug': company.slug})

class DeleteEmployeeView(SuccessUrlMixin, UserBySlugMixin, AuthenticatedViewMixin, PermissionRequiredMixin, CompanyCheckMixin, DynamicPermissionMixin, views.DeleteView):
    model = UserModel
    template_name = 'accounts/delete_user.html'
    success_url = reverse_lazy('company members')

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        user_slug = self.kwargs['slug']
        user_to_delete = get_user_by_slug(user_slug)
        permission = self.get_action_permission(user_to_delete, "delete")
        self.permission_required = permission
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_to_delete = self.get_object()
        context['has_delete_employee_permission'] = self.has_needed_permission(user, user_to_delete, "delete")
        return context

    # def get_success_url(self):
    #     user = self.request.user
    #     company_slug = user.company_slug
    #     return reverse('company members', kwargs={"company_slug": company_slug})

    def post(self, request, *args, **kwargs):
        user_to_delete = self.get_object()
        related_instance = user_to_delete.related_instance

        if related_instance.role == 'Manager':
            manager_teams = related_instance.teams.all()
            for team in manager_teams:
                team.manager = None
                team.save()

        related_instance.delete()
        user_to_delete.delete()
        messages.success(request, "User deleted successfully.")
        return redirect(self.get_success_url())


class CompanyMembersView(AuthenticatedViewMixin, CompanyContextMixin, views.ListView):
    model = UserModel
    template_name = "accounts/company_members.html"
    context_object_name = 'company'

    def get_object(self, queryset=None):
        user = self.request.user
        company = user.company
        return company

    # # TODO: CHECK IF THIS IS THE RIGHT WAY TO FETCH RELATED MODELS FOR THE USER PROFILE
    def get_queryset(self):
        user_company = self.request.user.company
        if not user_company:
            return UserModel.objects.none()  # Return an empty queryset if no company
        return UserModel.objects.prefetch_related('employee').filter(employee__company=user_company)

    def get(self, request, *args, **kwargs):
        company = self.get_object()

        if not company:
            messages.error(request, "User does not belong to any company.")
            return redirect('index')
        return super().get(request, *args, **kwargs)

    # # TODO check if this is the right way to fetch related models for the user profile
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     company = self.object
    #
    #     context['company'] = company if company else None
    #     context['employees'] = Employee.objects.filter(company=company) if company else None
    #
    #     return context


class DeleteCompanyView(OwnerRequiredMixin, CompanyCheckMixin, views.DeleteView):
    model = UserModel
    template_name = 'accounts/delete_company.html'
    success_url = reverse_lazy('index')

    def get(self, request, *args, **kwargs):
        user = request.user
        company = user.company
        if not company:
            messages.error(request, "Company not found.")
            return redirect('index')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = request.user
        user.delete()
        messages.success(request, "Company deleted successfully.")
        return redirect(self.success_url)


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


def about(request):
    return render(request, 'static_html/about.html')


def terms_and_conditions(request):
    return render(request, 'static_html/terms_and_conditions.html')


def terms_of_use(request):
    return render(request, 'static_html/terms_of_use.html')


def privacy_policy(request):
    return render(request, 'static_html/privacy_policy.html')


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