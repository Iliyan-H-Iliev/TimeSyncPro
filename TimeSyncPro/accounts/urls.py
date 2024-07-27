from django.urls import path, include
from django.contrib.auth import views as auth_views

from TimeSyncPro.accounts.views import (
    SignInUserView, signout_user, IndexView,
    DetailsOwnProfileView, SignupEmployeeView, SignupCompanyView, BasicEditProfileView, CompanyMembersView,
    DetailedEditProfileView, DetailsEmployeesProfileView
)

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", SignInUserView.as_view(), name="signin user"),
    path("logout/", signout_user, name="signout user"),
    path("register-company/", SignupCompanyView.as_view(), name="register company"),



    path(
        "<str:company_name>/", include([
            path("regiter-employee/", SignupEmployeeView.as_view(), name="register employee"),
            # path("<slug:slug>", CompanyProfileDetailsView.as_view(), name="company profile"),
            path("profile/<slug:slug>/", DetailsOwnProfileView.as_view(), name="profile"),
            path("profile/<slug:slug>/edit/", BasicEditProfileView.as_view(), name="edit profile"),
            # path("profile/<slug:slug>/delete/", ProfileDeleteView.as_view(), name="delete profile"),
            path("company-members/", CompanyMembersView.as_view(), name="company members"),
            path("company-members/<slug:slug>/", DetailsEmployeesProfileView.as_view(), name="company employee profile"),
            path("company-members/<slug:slug>/edit/", DetailedEditProfileView.as_view(), name="full profile update"),
        ])
    ),
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password reset done"),
    # path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password reset confirm"),
]