from django.urls import path, include

from TimeSyncPro.absences.views import RequestHolidayView, MyHolidaysView, DetailsHolidayView, CancelHolidayView, \
    AllHolidaysView

urlpatterns = [
    path("users/<slug:slug>/my-holidays/", include([
        path("", MyHolidaysView.as_view(), name="my_holidays"),
        path("request/", RequestHolidayView.as_view(), name="request_holiday"),
        path("<int:pk>/", DetailsHolidayView.as_view(), name="details_holiday"),
        path("<int:pk>/cancel", CancelHolidayView.as_view(), name="cancel_holiday"),
    ])),

    path("<slug:company_slug>/holidays/", include([
        path("", AllHolidaysView.as_view(), name="company_holidays"),
        path("<int:pk>/", DetailsHolidayView.as_view(), name="company_details_holiday"),
    ])),
]