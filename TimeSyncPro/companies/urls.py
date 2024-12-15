from django.urls import path, include

from . import views
from ..accounts.views import SignupEmployeeView, DetailsEmployeesProfileView, DetailedEditProfileView, \
    DeleteEmployeeView, TeamEmployeesAPIView, ShiftEmployeesAPIView, DepartmentEmployeesAPIView
from ..history.views import TeamHistoryAPIView, ShiftHistoryAPIView, EmployeeHistoryAPIView, DepartmentHistoryAPIView
from .views import ShiftTeamsApiView

urlpatterns = [
    path("create-company/", views.CreateCompanyView.as_view(), name="create_company"),
    path(
        "<slug:company_slug>/", include([
            path("register-employee/", SignupEmployeeView.as_view(), name="register_employee"),
            path("company-profile/", views.DetailsCompanyView.as_view(), name="company_profile"),
            path("edit/", views.EditCompanyView.as_view(), name="update_company"),
            path("delete/", views.DeleteCompanyView.as_view(), name="delete_company"),

            path("company-members/", include([
                path("", views.CompanyMembersView.as_view(), name="company_members"),
                path("<slug:slug>/", DetailsEmployeesProfileView.as_view(), name="employee_profile"),
                path("<slug:slug>/edit/", DetailedEditProfileView.as_view(), name="update_employee"),
                path("<slug:slug>/delete/", DeleteEmployeeView.as_view(), name="delete_employee"),
                path("<int:pk>/history/", EmployeeHistoryAPIView.as_view(), name="employee_history_api"),
            ])),
            path("departments/", include([
                path("", views.DepartmentsView.as_view(), name="all_departments"),
                path("create/", views.CreateDepartmentView.as_view(), name="create_department"),
                path("<int:pk>/", views.DetailsDepartmentView.as_view(), name="details_department"),
                path("<int:pk>/edit/", views.EditDepartmentView.as_view(), name="update_department"),
                path("<int:pk>/delete/", views.DeleteDepartmentView.as_view(), name="delete_department"),
                path("<int:pk>/history/", DepartmentHistoryAPIView.as_view(), name="department_history_api"),
                path("<int:pk>/employees/", DepartmentEmployeesAPIView.as_view(), name="department_employees_api"),
            ])),
            path("shifts/", include([
                path("", views.ShiftsView.as_view(), name="all_shifts"),
                path("create/", views.CreateShiftView.as_view(), name="create_shift"),
                path("<int:pk>/", include([

                    path("", views.DetailsShiftView.as_view(), name="details_shift"),
                    path("edit/", views.EditShiftView.as_view(), name="update_shift"),
                    path("delete/", views.DeleteShiftView.as_view(), name="delete_shift"),
                    path('employees/', ShiftEmployeesAPIView.as_view(), name='shift-employees-api'),
                    path('history/', ShiftHistoryAPIView.as_view(), name='shift-history-api'),
                    path('teams/', ShiftTeamsApiView.as_view(), name='shift-teams-api'),
                ])),
            ])),
            path("teams/", include([
                path('<int:pk>/employees/', TeamEmployeesAPIView.as_view(), name='team-employees-api'),
                path('<int:pk>/history/', TeamHistoryAPIView.as_view(), name='team-history-api'),
                path("", views.TeamsView.as_view(), name="all_teams"),
                path("create/", views.CreateTeamView.as_view(), name="create_team"),
                path("<int:pk>/", views.DetailsTeamView.as_view(), name="details_team"),
                path("<int:pk>/edit/", views.EditTeamView.as_view(), name="update_team"),
                path("<int:pk>/delete/", views.DeleteTeamView.as_view(), name="delete_team"),
            ])),
        ])
    ),
]
