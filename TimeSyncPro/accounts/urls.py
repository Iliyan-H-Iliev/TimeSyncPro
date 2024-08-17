from django.urls import path, include
from django.contrib.auth import views as auth_views

from TimeSyncPro.accounts.views import (
    SignInUserView, signout_user, IndexView, about, terms_and_conditions, terms_of_use, privacy_policy,
    DetailsOwnProfileView, SignupEmployeeView, SignupCompanyView, BasicEditProfileView, CompanyMembersView,
    DetailedEditProfileView, DetailsEmployeesProfileView, DeleteEmployeeView, DeleteCompanyView,
    DetailsCompanyProfileView, EditCompanyView, PasswordResetView, PasswordChangeView, CustomPasswordResetConfirmView,
    SignUpView, LoginView, SignupAndLoginView
)

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    # path('signup-login/', SignupAndLoginView.as_view(), name='signup_login'),
    # path('api/signup/', SignUpView.as_view(), name='api_signup'),
    # path('api/login/', LoginView.as_view(), name='api_login'),
    path("about/", about, name="about"),
    path("terms-and-conditions/", terms_and_conditions, name="terms and conditions"),
    path("terms-of-use/", terms_of_use, name="terms of use"),
    path("privacy-policy/", privacy_policy, name="privacy policy"),
    path("login/", SignInUserView.as_view(), name="signin user"),
    path("logout/", signout_user, name="signout user"),
    path("register-company/", SignupCompanyView.as_view(), name="register company"),
    path('password_reset/', PasswordResetView.as_view(), name='password reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password reset done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password reset confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password reset complete'),
    path('password_change/', PasswordChangeView.as_view(), name='password change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password change done'),
    path(
        "<str:company_name>/", include([
            path("regiter-employee/", SignupEmployeeView.as_view(), name="register employee"),
            path("<slug:slug>", DetailsCompanyProfileView.as_view(), name="company profile"),
            path("<slug:slug>/edit", EditCompanyView.as_view(), name="update company profile"),
            path("<slug:slug>/delete", DeleteCompanyView.as_view(), name="delete company"),
            path("profile/<slug:slug>/", DetailsOwnProfileView.as_view(), name="profile"),
            path("profile/<slug:slug>/edit/", BasicEditProfileView.as_view(), name="edit profile"),
            path("profile/<slug:slug>/delete/", DeleteEmployeeView.as_view(), name="delete profile"),
            path("company-members/", CompanyMembersView.as_view(), name="company members"),
            path("company-members/<slug:slug>/", DetailsEmployeesProfileView.as_view(), name="company employee profile"),
            path("company-members/<slug:slug>/edit/", DetailedEditProfileView.as_view(), name="full profile update"),
        ])
    ),
]