from django.urls import path, include
from django.contrib.auth import views as auth_views

from TimeSyncPro.accounts import views
from TimeSyncPro.accounts.views import get_working_days

urlpatterns = [
    path("api/get-working-days/", get_working_days, name="get_working_days"),
    # path('signup-login/', SignupAndLoginView.as_view(), name='signup_login'),
    # path('api/signup/', SignUpView.as_view(), name='api_signup'),
    # path('api/login/', LoginView.as_view(), name='api_login'),
    path("sign-in/", views.SignInUserView.as_view(), name="sign_in"),
    path("sign-out/", views.LogoutAPIView.as_view(), name="sign_out"),
    path("register/", views.SignupCompanyAdministratorUser.as_view(), name="sign_up_administrator"),
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password-change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('activate-set-password/<str:token>/', views.ActivateAndSetPasswordView.as_view(),
         name='activate_and_set_password'),
    path('users/<slug:slug>/', include([
        path("create-profile-company/", views.CreateProfileAndCompanyView.as_view(), name="create_profile_company"),
        path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
        path("profile/", include([
            path("", views.DetailsOwnProfileView.as_view(), name="profile"),
            path("edit/", views.EditProfileDispatcherView.as_view(), name="update_profile"),
        ])),
    ])),
]
