import logging
from datetime import datetime

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib import messages
from django.contrib.auth import views as auth_views, login, logout, authenticate, get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.forms import SetPasswordForm
from django.core.cache import cache
from django.db import transaction, IntegrityError
from django.db.models import Prefetch
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import generic as views
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from TimeSyncPro.accounts import forms

from TimeSyncPro.accounts.forms import SignupEmployeeForm, SignupCompanyAdministratorForm, \
    BasicEditTSPUserForm, DetailedEditTSPUserForm, CustomSetPasswordForm, \
    DetailedEditProfileForm, BasicEditProfileForm
from TimeSyncPro.accounts.forms.edit_profile_form import AdminEditProfileForm, DetailedEditOwnProfileForm
from TimeSyncPro.accounts.models import Profile
from TimeSyncPro.accounts.serializers import EmployeeSerializer
from TimeSyncPro.accounts.view_mixins import OwnerRequiredMixin, \
    DynamicPermissionMixin, SuccessUrlMixin
from TimeSyncPro.common.models import Address
# from TimeSyncPro.core.utils import format_email
from TimeSyncPro.common.views_mixins import CompanyObjectsAccessMixin, \
    MultiplePermissionsRequiredMixin, AuthenticatedUserMixin, UserDataMixin, SmallPagination, ReturnToPageMixin
import TimeSyncPro.companies.forms as company_forms
import TimeSyncPro.common.forms as common_forms
from TimeSyncPro.companies.models import Team
from TimeSyncPro.companies.views_mixins import ApiConfigMixin

# TODO Employee not see another employee profile

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class SignupCompanyAdministratorUser(AuthenticatedUserMixin, views.CreateView):
    template_name = "accounts/signup_company_administrator.html"
    form_class = SignupCompanyAdministratorForm
    success_url_name = "profile"

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

            return redirect("create_profile_company", slug=user.slug)

        except Exception as e:
            logger.error(f"Error in form_valid: {str(e)}")
            form.add_error(None, f"An error occurred: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning(f"Failed signup attempt: {form.cleaned_data.get('email')}")
        logger.warning(f"Form errors: {form.errors}")
        return super().form_invalid(form)


class CreateProfileAndCompanyView(OwnerRequiredMixin, views.CreateView):
    model = Profile
    template_name = "accounts/create_profile_and_company.html"
    form_class = forms.CreateCompanyAdministratorProfileForm
    company_form_class = company_forms.CreateCompanyForm
    profile_address_form_class = common_forms.AddressForm
    company_address_form_class = common_forms.AddressForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'company_form' not in kwargs:
            context['company_form'] = self.company_form_class()
        if 'company_address_form' not in kwargs:
            context['company_address_form'] = self.company_address_form_class()
        if "profile_form" not in kwargs:
            context['profile_form'] = self.form_class()
        if 'profile_address_form' not in kwargs:
            context['profile_address_form'] = self.profile_address_form_class()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        company_form = self.company_form_class(request.POST)
        company_address_form = self.company_address_form_class(request.POST, prefix='company')
        profile_address_form = self.profile_address_form_class(request.POST, prefix='profile')

        if all([
            form.is_valid(),
            company_form.is_valid(),
            company_address_form.is_valid(),
            profile_address_form.is_valid()
        ]):
            return self.form_valid(form, company_form, company_address_form, profile_address_form)
        else:
            return self.form_invalid(form, company_form, company_address_form, profile_address_form)

    @transaction.atomic
    def form_valid(self, form, company_form, company_address_form, profile_address_form):
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

            profile = form.save(commit=False)
            profile.user = self.request.user
            profile.address = profile_address
            profile.company = company
            profile.is_company_admin = True
            user = self.request.user

            profile.save()

            company.holiday_approver = profile
            company.save()

            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            employee_id = form.cleaned_data.get('employee_id')

            user.save(first_name=first_name, last_name=last_name, employee_id=employee_id)

            messages.success(self.request, "Company and profile created successfully.")
            return redirect("profile", slug=self.request.user.slug)

        except Exception as e:
            transaction.set_rollback(True)
            messages.error(self.request, f"An error occurred: {str(e)}")
            return self.form_invalid(form, company_form, company_address_form, profile_address_form)

    @transaction.atomic
    def form_invalid(self, form, company_form, company_address_form, profile_address_form):
        messages.error(self.request, "Please correct the errors below.")
        return self.render_to_response(
            self.get_context_data(
                form=form,
                company_form=company_form,
                company_address_form=company_address_form,
                profile_address_form=profile_address_form
            )
        )


class SignInUserView(auth_views.LoginView):
    template_name = "accounts/signin_user.html"
    redirect_authenticated_user = True
    form_class = forms.SignInUserForm
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 300  # 5 minutes
    REMEMBER_ME_DURATION = 1209600  # 2 weeks

    def get_success_url(self):
        user = self.request.user

        if not hasattr(user.profile, 'company'):
            return reverse("profile", kwargs={'slug': user.slug})

        return reverse("dashboard", kwargs={'slug': user.slug})

    def form_valid(self, form):
        username = form.cleaned_data.get('username', "").strip()
        cache_key = f'login_attempts_{username.lower()}'
        attempts = cache.get(cache_key, 0)

        if attempts >= self.MAX_LOGIN_ATTEMPTS:
            form.add_error(
                None,
                "Too many login attempts. Please try again later.",
            )
            logger.warning(f"Login blocked due to too many attempts for user: {username}")
            return self.form_invalid(form)

        password = form.cleaned_data.get('password')
        remember_me = form.cleaned_data.get('remember_me')
        expiry_time = (self.REMEMBER_ME_DURATION if remember_me else 0)

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


class SignupEmployeeView(MultiplePermissionsRequiredMixin, LoginRequiredMixin, views.CreateView):
    template_name = 'accounts/register_employee.html'
    form_class = forms.SignupEmployeeForm
    object = None

    permissions_required = [
        'accounts.add_company_admin',
        'accounts.add_hr',
        'accounts.add_manager',
        'accounts.add_team_leader',
        'accounts.add_staff',
    ]

    def get_context_data(self, **kwargs):
        if 'address_form' not in kwargs:
            kwargs['address_form'] = common_forms.AddressForm()
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        context['company_slug'] = company.slug if company else None
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
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
            messages.error(self.request, "An error occurred while registering the employee.")
            return self.form_invalid(form, address_form)
        except Exception as e:
            messages.error(self.request, f"An error occurred while registering the employee: {str(e)}")
            return self.form_invalid(form, address_form)

    def get_success_url(self):
        return reverse('company_members', kwargs={'company_slug': self.request.user.company.slug})

    @transaction.atomic
    def form_invalid(self, form, address_form):
        messages.error(self.request, "An error occurred while registering the employee.")
        return self.render_to_response(self.get_context_data(form=form, address_form=address_form))


class DetailsProfileBaseView(ApiConfigMixin, DynamicPermissionMixin, LoginRequiredMixin, views.DetailView):
    model = UserModel
    _cached_object = None
    template_name = "companies/employee/details_employee_profile.html"

    def get_object(self, queryset=None):
        if self._cached_object is None:
            if queryset is None:
                queryset = self.get_queryset()
            self._cached_object = super().get_object(queryset=queryset)
        return self._cached_object

    # def get_template_names(self):
    #     if self.request.user == self.get_object():
    #         return ["accounts/details_profile.html"]
    #     return ["companies/employee/details_employee_profile.html"]

    def get_queryset(self):
        return self.model.objects.select_related(
            'profile',
            'profile__company',
            'profile__department',
            'profile__team',
            'profile__address',
            'profile__shift',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # all_user_permissions = set(self.request.user.get_all_permissions())
        user = self.request.user

        context.update({
            'profile': self.object.profile,
            'has_detailed_change_permission': self.has_needed_permission(user, self.object, "change"),
            'has_delete_permission': self.has_needed_permission(user, self.object, "delete"),
        })
        return context


class DetailsOwnProfileView(OwnerRequiredMixin, DetailsProfileBaseView):
    template_name = "accounts/details_profile.html"


class DashboardView(DetailsOwnProfileView):
    def get_template_names(self):
        return ["accounts/dashboard.html"]


class DetailsEmployeesProfileView(
    CompanyObjectsAccessMixin,
    PermissionRequiredMixin,
    DetailsProfileBaseView,
):
    employee_history_api_url_name = 'employee_history_api'

    def get_permission_required(self):
        user_to_view = self.get_object()
        return [self.get_action_permission(user_to_view, "view")]


class EditProfileDispatcherView(OwnerRequiredMixin, DynamicPermissionMixin, views.View):

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        permission = self.get_action_permission(user, "change")

        if user.has_perm(permission) or user.is_superuser:
            view = DetailedEditOwnProfileView.as_view()
        else:
            view = BasicEditOwnProfileView.as_view()

        return view(request, *args, **kwargs)


class EditProfileBaseView(ReturnToPageMixin, LoginRequiredMixin, views.UpdateView):
    model = UserModel
    template_name = 'accounts/update_profile.html'
    form_class = BasicEditTSPUserForm
    detailed_edit = False
    address_form = common_forms.AddressForm

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.select_related(
            'profile__company',
            'profile__department',
            'profile__team',
            'profile__address',
            'profile__shift'
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
        context['profile_form'] = self.get_additional_form()
        context['address_form'] = self.address_form(instance=self.object.profile.address)
        return context

    def get_additional_form(self):
        additional_form_class = self._get_additional_form_class()
        if not additional_form_class:
            return None

        kwargs = {
            'instance': self.object.profile,
            'request': self.request,
        }

        if self.request.method == 'POST':
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
                address_form = self.address_form(request.POST, instance=self.object.profile.address)

                if all(f.is_valid() for f in [form, additional_form, address_form] if f):
                    return self.form_valid(form, additional_form, address_form)
                return self.form_invalid(form, additional_form, address_form)
        except Exception as e:
            messages.error(request, "An error occurred. Please try again.")
            return self.render_to_response(self.get_context_data(
                form=form,
                additional_form=additional_form,
                address_form=address_form
            ))

    @transaction.atomic
    def form_valid(self, form, additional_form, address_form):
        try:
            address = None
            first_name = additional_form.cleaned_data.get('first_name')
            last_name = additional_form.cleaned_data.get('last_name')
            employee_id = additional_form.cleaned_data.get('employee_id')

            obj = form.save(commit=False)
            obj.save(first_name=first_name, last_name=last_name, employee_id=employee_id)

            if additional_form:
                profile = additional_form.save()

            if address_form:
                address = address_form.save()

            if address and obj.profile.address == None:
                obj.profile.address = address
                obj.profile.save()

            messages.success(self.request, 'Profile updated successfully.')

            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, "An unexpected error occurred while saving the profile.")
            logger.error(f"Error updating profile for user {self.object.id}: {str(e)}")
            return self.form_invalid(form, additional_form, address_form)

    @transaction.atomic
    def form_invalid(self, form, additional_form, address_form):
        messages.error(self.request, 'Please correct the errors below.')

        return self.render_to_response(self.get_context_data(
            form=form,
            additional_form=additional_form,
            address_form=self.address_form(instance=self.object.profile.address)
        ))

    def get_success_url(self):
        return reverse("profile", kwargs={'slug': self.object.slug})


class BasicEditOwnProfileView(OwnerRequiredMixin, EditProfileBaseView):
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
        return reverse(
            "company_members",
            kwargs={"company_slug": self.object.profile.company.slug})


class DetailedEditOwnProfileView(OwnerRequiredMixin, DetailedEditProfileView):
    form_class = DetailedEditTSPUserForm
    template_name = 'accounts/update_profile.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("profile", kwargs={'slug': self.object.slug})


class DeleteEmployeeView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CompanyObjectsAccessMixin,
    DynamicPermissionMixin,
    views.DeleteView
):
    model = UserModel
    template_name = 'accounts/delete_user.html'

    # queryset = model.objects.select_related(
    #     'profile__company'  # Fetch employee and company in one query
    # ).prefetch_related(
    #     Prefetch(
    #         'groups',
    #         queryset=Group.objects.prefetch_related('permissions')),  # Prefetch permissions through groups
    #     'user_permissions'  # Prefetch individual user permissions
    # )

    def get_queryset(self):
        queryset = self.model.objects.select_related(
            'profile__company'  # Fetch employee and company in one query
        ).prefetch_related(
            Prefetch(
                'groups',
                queryset=Group.objects.prefetch_related('permissions')),  # Prefetch permissions through groups
            'user_permissions'  # Prefetch individual user permissions
        )
        return queryset

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

    def get_success_url(self):
        user = self.request.user
        company_slug = user.profile.company.slug
        return reverse('company members', kwargs={"company_slug": company_slug})

    def post(self, request, *args, **kwargs):
        user_to_delete = get_object_or_404(self.queryset, slug=self.kwargs['slug'])
        related_instance = user_to_delete.profile

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


class ActivateAndSetPasswordView(views.View):
    template_name = 'accounts/activate_and_set_password.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('profile', slug=request.user.slug)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, token):
        try:
            user = UserModel.objects.get(activation_token=token, is_active=False)
            form = SetPasswordForm(user)
            return render(request, self.template_name, {'form': form})
        except UserModel.DoesNotExist:
            messages.error(request, "Invalid or expired activation link.")
            return redirect('index')

    def post(self, request, token):
        try:
            user = UserModel.objects.get(activation_token=token, is_active=False)
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                user.is_active = True
                user.activation_token = ''
                user.save()

                # Authenticate user before login
                authenticated_user = authenticate(
                    request,
                    username=user.email,  # Assuming email is used for authentication
                    password=form.cleaned_data['new_password1']  # SetPasswordForm uses new_password1
                )

                if authenticated_user:
                    login(request, authenticated_user)
                    messages.success(request, "Your account has been activated and password set successfully.")
                    return redirect('profile', slug=authenticated_user.slug)
                else:
                    messages.error(request, "Error logging in after activation.")
                    return redirect('login')

            return render(request, self.template_name, {'form': form})
        except UserModel.DoesNotExist:
            messages.error(request, "Invalid or expired activation link.")
            return redirect('index')


class TeamEmployeesAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = EmployeeSerializer
    pagination_class = SmallPagination

    def get_queryset(self):
        return Profile.objects.filter(
            team_id=self.kwargs['pk'],
            team__company__slug=self.kwargs['company_slug']
        ).select_related('user').order_by('first_name')


class ShiftEmployeesAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = EmployeeSerializer
    pagination_class = SmallPagination

    def get_queryset(self):
        return Profile.objects.filter(
            shift_id=self.kwargs['pk'],
            shift__company__slug=self.kwargs['company_slug']
        ).select_related('user').order_by("first_name")


class DepartmentEmployeesAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = EmployeeSerializer
    pagination_class = SmallPagination

    def get_queryset(self):
        return Profile.objects.filter(
            department_id=self.kwargs['pk'],
            department__company__slug=self.kwargs['company_slug']
        ).select_related('user').order_by('first_name')


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


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            logout(request)

            return Response(
                {"message": "Successfully logged out."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Failed to logout. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def get_working_days(request):
    """API to calculate working days based on start_date and end_date."""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    profile_id = request.GET.get('profile_id')  # Optional if needed to calculate shift-specific days

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        profile = get_object_or_404(Profile, id=profile_id)
        working_days = profile.get_working_days_by_period(start_date, end_date)
        remaining_days = profile.remaining_leave_days

        return JsonResponse({'working_days': working_days, 'remaining_days': remaining_days})

    return JsonResponse({'error': 'Invalid input'}, status=HTTP_400_BAD_REQUEST)