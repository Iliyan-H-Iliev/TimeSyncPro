from django.urls import path, include

from TimeSyncPro.absences.views import CreateHolidayRequestView, MyRequestsView, \
    RequestsView, HolidayRequestStatusUpdateView, ReviewHolidayView, EmployeeRequestsView
from TimeSyncPro.absences.views.absence_views import CreateAbsenceView, EmployeeAbsencesView, AbsencesView, \
    MyAbsencesView, DeleteAbsenceAPIView

urlpatterns = [
    path('api/holidays/<int:pk>/update-status/', HolidayRequestStatusUpdateView.as_view(),
         name='update_holiday_status'),
    path('api/absences/<int:pk>/delete/', DeleteAbsenceAPIView.as_view(), name='delete_absence'),
    path("users/<slug:slug>/", include([
        path("my-holidays/", MyRequestsView.as_view(), name="my_holidays"),
        path("request-holiday/", CreateHolidayRequestView.as_view(), name="request_holiday"),
        path("absences/", MyAbsencesView.as_view(), name="my_absences"),

    ])),

    path("<slug:company_slug>/", include([
        path("holiday-requests/", include([
            path("", RequestsView.as_view(), name="company_holidays"),
            path("<slug:slug>/requests/", EmployeeRequestsView.as_view(), name="employee_requests"),
            path("<int:pk>/", ReviewHolidayView.as_view(), name="review_holiday"),
        ])),
        path("absences/", include([
            path("", AbsencesView.as_view(), name="company_absences"),
            path("add-to-<slug:slug>/", CreateAbsenceView.as_view(), name="add_absence"),
            path("<slug:slug>/", EmployeeAbsencesView.as_view(), name="employee_absences"),
            path("remove/<int:pk>/", EmployeeRequestsView.as_view(), name="remove_absence"),
        ])),

    ])),
]
