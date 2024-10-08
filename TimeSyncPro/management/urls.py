from django.urls import path, include
from .views import ShiftPatternCreateView, ShiftPatternListViewNot, TeamCreateViewNot, TeamListViewNot, \
    ShiftPatternDetailViewNot, \
    TeamEditViewNot, ShiftPatternEditViewNot, ShiftPatternDeleteViewNot, TeamDeleteViewNot, CompanyMembersView, \
    DetailsCompanyProfileView, EditCompanyView, DeleteCompanyView
from ..accounts.views import SignupEmployeeView, DetailsEmployeesProfileView, DetailedEditProfileView, \
    DeleteEmployeeView

urlpatterns = [
    path(
        "<slug:company_slug>/", include([
            path("register-employee/", SignupEmployeeView.as_view(), name="register employee"),
            path("company-profile/", DetailsCompanyProfileView.as_view(), name="company profile"),
            path("edit/", EditCompanyView.as_view(), name="update company profile"),
            path("<slug:slug>/delete/", DeleteCompanyView.as_view(), name="delete company"),

            path("company-members/", include([
                path("", CompanyMembersView.as_view(), name="company members"),
                path("<slug:slug>/", DetailsEmployeesProfileView.as_view(), name="employee profile"),
                path("<slug:slug>/edit/", DetailedEditProfileView.as_view(), name="full profile update"),
                path("<slug:slug>/delete/", DeleteEmployeeView.as_view(), name="delete profile"),
            ])),
            #TODO: Optimize path
            path("shiftpatterns/", include([
                path("", ShiftPatternListViewNot.as_view(), name="shift pattern list"),
                path("create/", ShiftPatternCreateView.as_view(), name="shift pattern create"),
                path("<int:pk>/", ShiftPatternDetailViewNot.as_view(), name="shift pattern detail"),
                path("<int:pk>/edit/", ShiftPatternEditViewNot.as_view(), name="shift pattern edit"),
                path("<int:pk>/delete/", ShiftPatternDeleteViewNot.as_view(), name="shift pattern delete"),
            ])),
            path("teams/", include([
                path("", TeamListViewNot.as_view(), name="team list"),
                path("create/", TeamCreateViewNot.as_view(), name="team create"),
                # path("<int:pk>/", TeamDetailView.as_view(), name="team detail"),
                path("<int:pk>/edit/", TeamEditViewNot.as_view(), name="team edit"),
                path("<int:pk>/delete/", TeamDeleteViewNot.as_view(), name="team delete"),
            ])),
        ])
    ),
]