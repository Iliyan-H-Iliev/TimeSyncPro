import logging

from django.contrib import messages
from django.contrib.auth import views as auth_views, login, logout, authenticate, get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import PasswordResetConfirmView
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import generic as views

# from rest_framework import generics, status
# from rest_framework.response import Response
# from rest_framework.authtoken.models import Token
# from rest_framework.permissions import AllowAny

from .models import Company
# from .serializers import LoginSerializer, SignupCompanySerializer

from django.contrib.auth.forms import SetPasswordForm

from TimeSyncPro.accounts.forms import SignupEmployeeForm, SignupCompanyAdministratorForm, \
    BasicEditTimeSyncProUserForm, DetailedEditTimeSyncProUserForm, CustomSetPasswordForm, EditCompanyForm, \
    DetailedEditEmployeesBaseForm, BasicEditEmployeeForm
from TimeSyncPro.accounts.view_mixins import CompanyContextMixin, OwnerRequiredMixin, \
    DynamicPermissionMixin, UserBySlugMixin, SuccessUrlMixin
from TimeSyncPro.core.views_mixins import AuthenticatedViewMixin, CompanyCheckMixin, \
    MultiplePermissionsRequiredMixin

# TODO Employee not see another employee profile

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class IndexView(views.TemplateView):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            # messages.info(request, "Please log in to access full features of this page.")
            return render(request, self.template_name)

        full_name = user.employee.full_name

        return render(request, self.template_name, {
            'full_name': full_name,
        })


class SignupCompanyAdministratorView(views.CreateView):
    model = UserModel
    template_name = "accounts/signup_company_administrator.html"
    form_class = SignupCompanyAdministratorForm
    redirect_authenticated_user = True
    success_url = "profile"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(
                reverse(self.success_url, kwargs={
                    'slug': self.request.user.slug,
                    'company_slug': self.request.user.employee.company.slug
                })
            )
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        logger.debug("Entering form_valid method")
        try:

            user = form.save()

            # # Refresh the user object to ensure all related objects are loaded
            # user.refresh_from_db()

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
            company_slug = user.employee.company.slug

            # Check if slug and company_name are available
            if user_slug is None or company_slug is None:
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


class SignInUserView(auth_views.LoginView):
    template_name = "accounts/signin_user.html"
    redirect_authenticated_user = True
    success_url = reverse_lazy("profile")

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(
                reverse(
                    self.success_url,
                    kwargs={
                        'slug': self.request.user.slug,
                        'company_slug': self.request.user.employee.company.slug
                    }
                )
            )
        return super().dispatch(request, *args, **kwargs)

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
                reverse('profile', kwargs={'slug': user.slug, "company_slug": user.employee.company.slug})
            )
        else:
            form.add_error(None, "Invalid username or password")
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning(f"Failed login attempt: {form.cleaned_data.get('username')}")
        logger.warning(f"Form errors: {form.errors}")
        return super().form_invalid(form)


class SignupEmployeeView(MultiplePermissionsRequiredMixin, AuthenticatedViewMixin, views.CreateView):
    template_name = 'accounts/register_employee.html'
    form_class = SignupEmployeeForm

    # TODO check for queryset
    permissions_required = [
        'accounts.add_administrator',
        'accounts.add_hr',
        'accounts.add_manager',
        'accounts.add_teamleader',
        'accounts.add_staff',
    ]

    # TODO: replace 'success_url' with the actual URL name
    success_url = reverse_lazy("index")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        # Redirect to the employee's profile or another page
        employee = form.instance
        user = self.request.user
        self.success_url = reverse_lazy('company members', kwargs={
            'company_slug': user.employee.company.slug
        })
        return response

    def get_success_url(self):
        # Return the dynamically set success URL
        return self.success_url


class DetailsProfileBaseView(DynamicPermissionMixin, views.DetailView):
    template_name = "accounts/details_company_employee.html"
    context_object_name = 'user'
    model = UserModel
    queryset = model.objects.select_related(
        'employee__company'  # Fetch employee and company in one query
    ).prefetch_related(
        Prefetch(
            'groups',
            queryset=Group.objects.prefetch_related('permissions')),  # Prefetch permissions through groups
        'user_permissions'  # Prefetch individual user permissions
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_to_view = self.get_object()
        company_slug = user.employee.company.slug

        # Get all permissions at once
        all_permissions = list(user.get_all_permissions())

        context.update({
            'user_to_view': user_to_view,
            'company_slug': company_slug,
            'has_detailed_change_permission': self.get_action_permission(user_to_view, "change") in all_permissions,
            'has_delete_permission': self.get_action_permission(user_to_view, "delete") in all_permissions,
        })
        return context

    @staticmethod
    def handle_user_not_found(request):
        messages.error(request, "User not found.")
        return redirect('index')

    def get(self, request, *args, **kwargs):
        user_to_view = self.get_object()

        if not user_to_view:
            return self.handle_user_not_found(request)

        context = self.get_context_data()
        return render(request, self.template_name, context)


class DetailsOwnProfileView(OwnerRequiredMixin, DetailsProfileBaseView):
    # TODO check get_object
    def get_object(self, queryset=None):
        self.object = self.request.user
        return self.object


class DetailsEmployeesProfileView(
    AuthenticatedViewMixin,
    CompanyCheckMixin,
    PermissionRequiredMixin,
    DetailsProfileBaseView
):
    def get_object(self, queryset=None):
        user_slug = self.kwargs.get('slug')
        # Fetch the object based on slug or raise a 404 if not found
        self.object = get_object_or_404(self.queryset, slug=user_slug)
        return self.object

    def dispatch(self, request, *args, **kwargs):
        user_to_view = self.get_object()
        permission = self.get_action_permission(user_to_view, "view")
        self.permission_required = permission
        return super().dispatch(request, *args, **kwargs)


class DetailsCompanyProfileView(
    AuthenticatedViewMixin,
    MultiplePermissionsRequiredMixin,
    CompanyContextMixin,
    views.DetailView
):

    model = Company
    template_name = "accounts/company_profile.html"
    context_object_name = 'company'
    permissions_required = [
        'accounts.view_company',
    ]

    def get_object(self, queryset=None):
        user = self.request.user
        company = get_object_or_404(self.model, company_id=user.employee.company_id)
        return user.employee.company


class EditProfileBaseView(AuthenticatedViewMixin, views.View):
    success_url = 'index'
    detailed_edit = False
    model = UserModel

    queryset = model.objects.select_related(
        'employee__company'  # Fetch employee and company in one query
    ).prefetch_related(
        Prefetch(
            'groups',
            queryset=Group.objects.prefetch_related('permissions')),  # Prefetch permissions through groups
        'user_permissions'  # Prefetch individual user permissions
    )

    def get_user_to_edit(self, slug):
        user_to_edit = self.queryset.filter(slug=slug).first()
        if not user_to_edit:
            raise Http404("User not found")
        return user_to_edit

    @staticmethod
    def _get_additional_form_class(detailed_edit=False):
        form_class = DetailedEditEmployeesBaseForm if detailed_edit else BasicEditEmployeeForm
        return form_class

    def get_success_url(self, slug, company_slug):
        return reverse(self.success_url, kwargs={'slug': slug, 'company_slug': company_slug})

    def get_additional_form_class(self, detailed_edit):
        try:
            return self._get_additional_form_class(detailed_edit=detailed_edit)
        except ValueError as e:
            messages.error(self.request, str(e))
            return None

    def get_additional_form(self, user, request=None):
        additional_form_class = self.get_additional_form_class(detailed_edit=self.detailed_edit)
        if not additional_form_class:
            return None

        related_instance = user.employee

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
        try:
            with transaction.atomic():
                user_form.save()
                if additional_form:
                    additional_form.save()
                messages.success(self.request, 'Profile updated successfully.')
                return redirect(self.get_success_url(user.slug, user.company_slug))
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            messages.error(self.request, "An unexpected error occurred while saving the profile.")
            return self.form_invalid(user_form, additional_form, {})

    def form_invalid(self, user_form, additional_form, context):
        messages.error(self.request, 'Please correct the error below.')
        return render(self.request, self.template_name, context)

    def handle_form_loading_failure(self, user, user_to_edit=None):
        logger.error(f"Failed to load forms for user {user_to_edit.email if user_to_edit else user.email}")
        messages.error(self.request, "An unexpected error occurred. Please try again.")
        return redirect(
            self.get_success_url(slug=user.slug, company_slug=user.employee.company.slug))


class BasicEditProfileView(OwnerRequiredMixin, EditProfileBaseView):
    template_name = 'accounts/edit_profile.html'
    form_class = BasicEditTimeSyncProUserForm
    success_url = 'profile'
    detailed_edit = False

    def get(self, request, *args, **kwargs):
        user = request.user
        user_form = self.form_class(instance=user)
        additional_form = self.get_additional_form(user)
        if additional_form is None or user_form is None:
            return self.handle_form_loading_failure(user)

        context = self.get_context_data(user_form, additional_form, user)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = request.user
        user_form = self.form_class(request.POST, instance=user)
        additional_form = self.get_additional_form(user, request)
        if additional_form is None or user_form is None:
            return self.handle_form_loading_failure(user)

        if user_form.is_valid() and (additional_form is None or additional_form.is_valid()):
            return self.form_valid(user_form, additional_form, user, user)

        context = self.get_context_data(user_form, additional_form, user)
        return self.form_invalid(user_form, additional_form, context)


class DetailedEditProfileView(PermissionRequiredMixin, DynamicPermissionMixin, EditProfileBaseView):
    template_name = 'accounts/full_profile_edit.html'
    form_class = DetailedEditTimeSyncProUserForm
    success_url = 'company employee profile'
    detailed_edit = True

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        user_to_edit = self.get_user_to_edit(slug=self.kwargs['slug'])
        permission = self.get_action_permission(user_to_edit, "change")
        self.permission_required = permission
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        user = request.user
        user_to_edit = self.get_user_to_edit(slug=self.kwargs['slug'])
        company_slug = user.employee.company.slug

        user_form = self.form_class(instance=user_to_edit)
        additional_form = self.get_additional_form(user_to_edit)

        if additional_form is None or user_form is None:
            return self.handle_form_loading_failure(user, user_to_edit)
        context = self.get_context_data(user_form, additional_form, user, user_to_edit, company_slug)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = request.user
        user_to_edit = self.get_user_to_edit(slug=self.kwargs['slug'])
        company_slug = user.employee.company.slug

        user_form = self.form_class(request.POST or None, instance=user_to_edit)
        additional_form = self.get_additional_form(user_to_edit, request)

        if additional_form is None or user_form is None:
            return self.handle_form_loading_failure(user, user_to_edit)

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
        return user.employee.company

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_object()
        context['company'] = company
        return context

    def get_success_url(self):
        company = self.object
        return reverse('company profile', kwargs={'company_slug': company.slug})


class DeleteEmployeeView(SuccessUrlMixin, AuthenticatedViewMixin, PermissionRequiredMixin,
                         CompanyCheckMixin, DynamicPermissionMixin, views.DeleteView):

    model = UserModel
    queryset = model.objects.select_related(
        'employee__company'  # Fetch employee and company in one query
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
    #     company_slug = user.employee.company.slug
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


class CompanyMembersView(AuthenticatedViewMixin, CompanyContextMixin, views.ListView):
    model = UserModel
    queryset = model.objects.select_related(
        'employee__company'  # Fetch employee and company in one query
    ).prefetch_related(
        Prefetch(
            'groups',
            queryset=Group.objects.prefetch_related('permissions')),  # Prefetch permissions through groups
        'user_permissions'  # Prefetch individual user permissions
    )
    template_name = "accounts/company_members.html"
    context_object_name = 'company'

    def get_object(self, queryset=None):
        user = self.request.user
        company = get_object_or_404(self.queryset, employee__company_id=user.employee.company_id)
        return company

    # # TODO: CHECK IF THIS IS THE RIGHT WAY TO FETCH RELATED MODELS FOR THE USER PROFILE
    # def get_queryset(self):
    #     user_company = self.request.user.employee.company
    #     if not user_company:
    #         return UserModel.objects.none()  # Return an empty queryset if no company
    #     return UserModel.objects.prefetch_related('employee').filter(employee__company=user_company)

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


# TODO add permision for delete
# TODO Create logic for delete company
class DeleteCompanyView(OwnerRequiredMixin, CompanyCheckMixin, views.DeleteView):
    model = Company
    queryset = model.objects.all()
    template_name = 'accounts/delete_company.html'
    success_url = reverse_lazy('index')

    def get(self, request, *args, **kwargs):
        user = request.user
        company = user.employee.company
        if not company:
            messages.error(request, "Company not found.")
            return redirect('index')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = request.user
        company = user.employee.company
        company.delete()
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


# class SignupCompanyView(SuccessUrlMixin, views.CreateView):
#     model = UserModel
#     template_name = "accounts/signup_company_administrator.html"
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


# class DetailsProfileBaseView(UserBySlugMixin, DynamicPermissionMixin, views.DetailView):
#     template_name = "accounts/details_company_employee.html"
#     context_object_name = 'user'
#     # model = UserModel
#     queryset = UserModel.objects.select_related('employee__company').prefetch_related(
#         'employee',  # Assuming UserModel has a related Employee
#         'employee__company',  # Assuming Employee has a related Company
#         'groups__permissions',  # Prefetching related permissions through groups
#         'user_permissions'  # Prefetching individual user permissions
#     )
#
#     slug_url_kwarg = 'employee_slug'
#
#     # def get_queryset(self, *args, **kwargs):
#     #     user = self.request.user
#     #     user_to_view = self.get_object()
#     #     return UserModel.objects.prefetch_related('employee').all()
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user
#         user_to_view = self.queryset.filter(employee__slug=self.kwargs.get('slug')).first()
#         company_slug = self.queryset.filter(user=user).first().company_slug
#         all_permissions = self.queryset.filter(user=user).first().permissions.all()
#         context['user_to_view'] = user_to_view
#         context['company_slug'] = company_slug
#         context['has_detailed_change_permission'] = self.get_action_permission(user_to_view, "change") in all_permissions
#         context['has_delete_permission'] = self.get_action_permission(user_to_view, "delete") in all_permissions
#         return context
#
#
#     # def get_context_data(self, user, user_to_view):
#     #     user_permissions = user.get_all_permissions()
#     #     return {
#     #         'user': user,
#     #         'user_to_view': user_to_view,
#     #         'company_slug': user.company_slug,
#     #         'has_detailed_change_permission': self.get_action_permission(user_to_view, "change") in user_permissions,
#     #         'has_delete_permission': self.get_action_permission(user_to_view, "delete") in user_permissions,
#     #     }
#
#     @staticmethod
#     def handle_user_not_found(request):
#         messages.error(request, "User not found.")
#         return redirect('index')
#
#     def get(self, request, *args, **kwargs):
#         user = request.user
#         user_to_view = self.get_object()
#
#         if user_to_view is None:
#             return self.handle_user_not_found(request)
#
#         context = self.get_context_data()
#         return render(request, self.template_name, context)


# class DetailsProfileBaseView(UserBySlugMixin, DynamicPermissionMixin, views.DetailView):
#     template_name = "accounts/details_company_employee.html"
#     context_object_name = 'user'
#
#     # Optimize the queryset with select_related and prefetch_related
#     queryset = UserModel.objects.select_related('employee__company').prefetch_related(
#         'employee',  # Assuming UserModel has a related Employee
#         'employee__company',  # Assuming Employee has a related Company
#         'groups__permissions',  # Prefetching related permissions through groups
#         'user_permissions'  # Prefetching individual user permissions
#     )
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user
#         user_to_view = get_object_or_404(self.get_queryset(), employee__slug=kwargs.get('slug'))
#
#
#         # Get all permissions only once
#         user_permissions = user.get_all_permissions()
#
#         # Adding to the context dictionary
#         context.update({
#             'user_to_view': user_to_view,
#             'company_slug': user_to_view.employee.company.slug if hasattr(user_to_view.employee, 'company') else None,
#             'has_detailed_change_permission': self.get_action_permission(user_to_view, "change") in user_permissions,
#             'has_delete_permission': self.get_action_permission(user_to_view, "delete") in user_permissions,
#         })
#         return context
#
#     def get_object(self):
#         # This method ensures self.object is set
#         return get_object_or_404(self.queryset,  employee__slug=self.kwargs.get('slug'))
#
#     @staticmethod
#     def handle_user_not_found(request):
#         messages.error(request, "User not found.")
#         return redirect('index')
#
#     def get(self, request, *args, **kwargs):
#         user = request.user
#         # Using get_object_or_404 to simplify the object retrieval process
#         user_to_view = get_object_or_404(self.get_queryset(), employee__slug=kwargs.get('slug'))
#
#         context = self.get_context_data(user=user, user_to_view=user_to_view)
#         return render(request, self.template_name, context)


# class DetailsProfileBaseView(DynamicPermissionMixin, views.DetailView):
#     template_name = "accounts/details_company_employee.html"
#     context_object_name = 'user'
#
#     queryset = UserModel.objects.select_related('employee__company').prefetch_related(
#         Prefetch('groups', queryset=Group.objects.prefetch_related('permissions')),
#         # Prefetch related permissions through groups
#         Prefetch('user_permissions')  # Prefetch individual user permissions
#     )
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user
#         user_to_view = self.get_object()
#         company_slug = self.queryset.filter(email=user.email).first().employee.company.slug
#         all_permissions = list(user.get_all_permissions())
#         context['user_to_view'] = user_to_view
#         context['company_slug'] = company_slug
#         context['has_detailed_change_permission'] = self.get_action_permission(user_to_view, "change") in all_permissions
#         context['has_delete_permission'] = self.get_action_permission(user_to_view, "delete") in all_permissions
#         return context
#
#     @staticmethod
#     def handle_user_not_found(request):
#         messages.error(request, "User not found.")
#         return redirect('index')
#
#     def get(self, request, *args, **kwargs):
#         user_to_view = self.get_object()
#
#         if user_to_view is None:
#             return self.handle_user_not_found(request)
#
#         context = self.get_context_data()
#         return render(request, self.template_name, context)
#
#
# class DetailsOwnProfileView(OwnerRequiredMixin, DetailsProfileBaseView):
#     def get_object(self, queryset=None):
#         self.object = self.request.user
#         return self.object
#
#
# class DetailsEmployeesProfileView(
#     CompanyCheckMixin,
#     PermissionRequiredMixin,
#     DetailsProfileBaseView
# ):
#     # TODO add permission
#
#     def get_object(self, queryset=None):
#         user_slug = self.kwargs['slug']
#         self.object = self.queryset.filter(employee__slug=user_slug).first()
#         return self.object
#
#     def dispatch(self, request, *args, **kwargs):
#         user_to_view = self.get_object()
#         permission = self.get_action_permission(user_to_view, "view")
#         self.permission_required = permission
#         return super().dispatch(request, *args, **kwargs)

# def get_context_data(self, user, user_to_view):
#     context = super().get_context_data(user, user_to_view)
#     needed_permission = self.get_all_needed_permission(user_to_view)
#     # context['has_detailed_change_permission'] = self.has_needed_permission(user, user_to_view, "change")
#     context['has_delete_permission'] = self.has_needed_permission(user, user_to_view, "delete")
#     return context


# OwnerRequiredMixin, IsCompanyUserMixin,
# class DetailsCompanyProfileView(DetailsProfileBaseView):
#     model = Company
#     template_name = "accounts/company_profile.html"
#
#     def get_context_data(self, user, user_to_view):
#         context = super().get_context_data(user, user_to_view)
#         context['company'] = user.company
#         return context
