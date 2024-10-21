from django.urls import path, include
from django.contrib.auth import views as auth_views

from TimeSyncPro.accounts.views import (
    SignInUserView, signout_user, DetailsOwnProfileView, SignupCompanyAdministratorUser,
    BasicEditProfileView, PasswordResetView, PasswordChangeView, CustomPasswordResetConfirmView,
    ActivateAndSetPasswordView, DetailedOwnEditProfileView,
)

urlpatterns = [
    # path('signup-login/', SignupAndLoginView.as_view(), name='signup_login'),
    # path('api/signup/', SignUpView.as_view(), name='api_signup'),
    # path('api/login/', LoginView.as_view(), name='api_login'),
    path("login/", SignInUserView.as_view(), name="sign_in"),
    path("logout/", signout_user, name="sign_out"),
    path("register/", SignupCompanyAdministratorUser.as_view(), name="sign_up_administrator"),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password_change/', PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('activate-set-password/<str:token>/', ActivateAndSetPasswordView.as_view(), name='activate_and_set_password'),

    path("users/<slug:slug>/profile/", include([
        path("", DetailsOwnProfileView.as_view(), name="profile"),
        path("edit/", BasicEditProfileView.as_view(), name="update_profile"),
        path("detailed-edit/", DetailedOwnEditProfileView.as_view(), name="detailed_update_own_profile"),
    ])),

]
