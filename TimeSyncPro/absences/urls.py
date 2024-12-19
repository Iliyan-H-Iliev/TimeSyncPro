from django.urls import path, include

from TimeSyncPro.absences import views

urlpatterns = [
    path(
        "api/holidays/<int:pk>/update-status/",
        views.HolidayRequestStatusUpdateView.as_view(),
        name="update_holiday_status",
    ),
    path(
        "api/absences/<int:pk>/delete/",
        views.DeleteAbsenceAPIView.as_view(),
        name="delete_absence",
    ),
    path(
        "users/<slug:slug>/",
        include(
            [
                path("my-holidays/", views.MyRequestsView.as_view(), name="my_holidays"),
                path(
                    "request-holiday/",
                    views.CreateHolidayRequestView.as_view(),
                    name="request_holiday",
                ),
                path("absences/", views.MyAbsencesView.as_view(), name="my_absences"),
            ]
        ),
    ),
    path(
        "<slug:company_slug>/",
        include(
            [
                path(
                    "holiday-requests/",
                    include(
                        [
                            path("", views.RequestsView.as_view(), name="company_holidays"),
                            path(
                                "<slug:slug>/requests/",
                                views.EmployeeRequestsView.as_view(),
                                name="employee_requests",
                            ),
                            path(
                                "<int:pk>/",
                                views.ReviewHolidayView.as_view(),
                                name="review_holiday",
                            ),
                        ]
                    ),
                ),
                path(
                    "absences/",
                    include(
                        [
                            path("", views.AbsencesView.as_view(), name="company_absences"),
                            path(
                                "add-to-<slug:slug>/",
                                views.CreateAbsenceView.as_view(),
                                name="add_absence",
                            ),
                            path(
                                "<slug:slug>/",
                                views.EmployeeAbsencesView.as_view(),
                                name="employee_absences",
                            ),
                            path(
                                "remove/<int:pk>/",
                                views.EmployeeRequestsView.as_view(),
                                name="remove_absence",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
