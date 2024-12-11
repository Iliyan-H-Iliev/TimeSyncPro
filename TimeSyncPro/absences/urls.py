from django.urls import path, include

from TimeSyncPro.absences.views import RequestHolidayView, MyHolidaysView, \
    AllHolidaysView, HolidayRequestStatusUpdateView, ReviewHolidayView, EmployeeHolidaysView
from TimeSyncPro.absences.views.absence_views import CreateAbsenceView

urlpatterns = [
    path('api/holidays/<int:pk>/update-status/', HolidayRequestStatusUpdateView.as_view(),
         name='update_holiday_status'),
    path("users/<slug:slug>/", include([
        path("my-holidays/", MyHolidaysView.as_view(), name="my_holidays"),
        path("holiday-request/", RequestHolidayView.as_view(), name="request_holiday"),
    ])),

    path("<slug:company_slug>/", include([
        path("holiday-requests/", include([
            path("", AllHolidaysView.as_view(), name="company_holidays"),
            path("<slug:slug>/requests/", EmployeeHolidaysView.as_view(), name="employee_requests"),
            path("<int:pk>/", ReviewHolidayView.as_view(), name="review_holiday"),
        ])),
        path("absences/", include([
            path("", AllHolidaysView.as_view(), name="company_absences"),
            path("add-to-<slug:slug>/", CreateAbsenceView.as_view(), name="add_absence"),
            path("<slug:slug>/absences/", EmployeeHolidaysView.as_view(), name="employee_absences"),
            path("remove/<int:pk>/", EmployeeHolidaysView.as_view(), name="remove_absence"),
        ])),
    ])),
]
