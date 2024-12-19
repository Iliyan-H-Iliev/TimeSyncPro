from django.urls import path, include
from . import views
from ..accounts.views import ShiftEmployeesAPIView
from ..companies.views import ShiftTeamsApiView
from ..history.views import ShiftHistoryAPIView

urlpatterns = [
    path(
        "<slug:company_slug>/",
        include(
            [
                path(
                    "shifts/",
                    include(
                        [
                            path("", views.ShiftsView.as_view(), name="all_shifts"),
                            path(
                                "create/",
                                views.CreateShiftView.as_view(),
                                name="create_shift",
                            ),
                            path(
                                "<int:pk>/",
                                include(
                                    [
                                        path(
                                            "",
                                            views.DetailsShiftView.as_view(),
                                            name="details_shift",
                                        ),
                                        path(
                                            "edit/",
                                            views.EditShiftView.as_view(),
                                            name="update_shift",
                                        ),
                                        path(
                                            "delete/",
                                            views.DeleteShiftView.as_view(),
                                            name="delete_shift",
                                        ),
                                        path(
                                            "employees/",
                                            ShiftEmployeesAPIView.as_view(),
                                            name="shift-employees-api",
                                        ),
                                        path(
                                            "history/",
                                            ShiftHistoryAPIView.as_view(),
                                            name="shift-history-api",
                                        ),
                                        path(
                                            "teams/",
                                            ShiftTeamsApiView.as_view(),
                                            name="shift-teams-api",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
