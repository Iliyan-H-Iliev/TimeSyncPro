from django.urls import path, include

from TimeSyncPro.absences.views import RequestHolidayView, MyHolidaysView, \
    AllHolidaysView, HolidayRequestStatusUpdateView, ReviewHolidayView

urlpatterns = [
    path('api/holidays/<int:pk>/update-status/', HolidayRequestStatusUpdateView.as_view(), name='update_holiday_status'),
    path("users/<slug:slug>/", include([
        path("my-holidays/", MyHolidaysView.as_view(), name="my_holidays"),
        path("holiday-request/", RequestHolidayView.as_view(), name="request_holiday"),
    ])),

    path("<slug:company_slug>/holiday-requests/", include([
        path("", AllHolidaysView.as_view(), name="company_holidays"),
        path("<int:pk>/", ReviewHolidayView.as_view(), name="review_holiday"),
    ])),
]