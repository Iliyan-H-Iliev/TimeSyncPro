from django.urls import path, include
from django.contrib.auth import views as auth_views

from TimeSyncPro.accounts.views import (
    SignInUserView, signout_user, IndexUser, about, terms_and_conditions, terms_of_use, privacy_policy,
    DetailsOwnProfileView, SignupEmployeeView, SignupCompanyAdministratorUser, BasicEditProfileView,
    DetailedEditProfileView, DetailsEmployeesProfileView, DeleteEmployeeView,
    PasswordResetView, PasswordChangeView, CustomPasswordResetConfirmView,
    ActivateAndSetPasswordView, contact, features, DetailedOwnEditProfileView,
)
from TimeSyncPro.management.views import CompanyMembersView, DetailsCompanyProfileView, EditCompanyView, \
    DeleteCompanyView

urlpatterns = [
    path("", IndexUser.as_view(), name="index"),
    # path('signup-login/', SignupAndLoginView.as_view(), name='signup_login'),
    # path('api/signup/', SignUpView.as_view(), name='api_signup'),
    # path('api/login/', LoginView.as_view(), name='api_login'),
    path("features/", features, name="features"),
    path("about/", about, name="about"),
    path("terms-and-conditions/", terms_and_conditions, name="terms and conditions"),
    path("terms-of-use/", terms_of_use, name="terms of use"),
    path("privacy-policy/", privacy_policy, name="privacy policy"),
    path("contact/", contact, name="contact"),
    path("login/", SignInUserView.as_view(), name="signin user"),
    path("logout/", signout_user, name="signout user"),
    path("register-company/", SignupCompanyAdministratorUser.as_view(), name="signup administrator"),
    path('password_reset/', PasswordResetView.as_view(), name='password reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password reset done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password reset confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password reset complete'),
    path('password_change/', PasswordChangeView.as_view(), name='password change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password change done'),
    path('activate-set-password/<str:token>/', ActivateAndSetPasswordView.as_view(), name='activate and set password'),

    path("users/profile/<slug:slug>/", include([
        path("", DetailsOwnProfileView.as_view(), name="profile"),
        path("edit/", BasicEditProfileView.as_view(), name="edit profile"),
        path("detailed-edit/", DetailedOwnEditProfileView.as_view(), name="full edit profile"),
    ])),



]
