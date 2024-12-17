from django.urls import path, include

from TimeSyncPro.reports.views import BradfordFactorReport, generate_report

urlpatterns = [
    path(
        "<slug:company_slug>/reports/",
        include(
            [
                path("", generate_report, name="generate_report"),
                path(
                    "bradford-factor/",
                    BradfordFactorReport.as_view(),
                    name="bradford_factor_report",
                ),
            ]
        ),
    ),
]
