from django.urls import path, include
from .views import CreateShiftPatternView, ShiftPatternsView, CreateTeamView, TeamsView, \
    DetailsShiftPatternView, \
    EditTeamView, EditShiftPatternView, DeleteShiftPatternView, DeleteTeamView, CompanyMembersView, \
    DetailsCompanyView, EditCompanyView, DeleteCompanyView, CreateCompanyView
from ..accounts.views import SignupEmployeeView, DetailsEmployeesProfileView, DetailedEditProfileView, \
    DeleteEmployeeView

urlpatterns = [
    path("create-company/", CreateCompanyView.as_view(), name="create_company"),
    path(
        "<slug:company_slug>/", include([
            path("register-employee/", SignupEmployeeView.as_view(), name="register_employee"),
            path("company-profile/", DetailsCompanyView.as_view(), name="company_profile"),
            path("edit/", EditCompanyView.as_view(), name="update_company"),
            path("delete/", DeleteCompanyView.as_view(), name="delete_company"),

            path("company-members/", include([
                path("", CompanyMembersView.as_view(), name="company_members"),
                path("<slug:slug>/", DetailsEmployeesProfileView.as_view(), name="employee_profile"),
                path("<slug:slug>/edit/", DetailedEditProfileView.as_view(), name="update_employee"),
                path("<slug:slug>/delete/", DeleteEmployeeView.as_view(), name="delete_employee"),
            ])),
            #TODO: Optimize path
            path("shiftpatterns/", include([
                path("", ShiftPatternsView.as_view(), name="all_shift_patterns"),
                path("create/", CreateShiftPatternView.as_view(), name="create_shift_pattern"),
                path("<int:pk>/", DetailsShiftPatternView.as_view(), name="shift_pattern"),
                path("<int:pk>/edit/", EditShiftPatternView.as_view(), name="update_shift_pattern"),
                path("<int:pk>/delete/", DeleteShiftPatternView.as_view(), name="delete_shift_pattern"),
            ])),
            path("teams/", include([
                path("", TeamsView.as_view(), name="all_teams"),
                path("create/", CreateTeamView.as_view(), name="create_team"),
                # path("<int:pk>/", TeamDetailView.as_view(), name="team detail"),
                path("<int:pk>/edit/", EditTeamView.as_view(), name="update_team"),
                path("<int:pk>/delete/", DeleteTeamView.as_view(), name="delete_team"),
            ])),
        ])
    ),
]
