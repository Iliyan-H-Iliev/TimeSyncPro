from django.urls import path
from django.views.generic import TemplateView
import TimeSyncPro.common.views as views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("features/", views.features, name="features"),
    path("about/", views.about, name="about"),
    path(
        "terms-and-conditions/", views.terms_and_conditions, name="terms_and_conditions"
    ),
    path("terms-of-use/", views.terms_of_use, name="terms_of_use"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("contact/", views.contact, name="contact"),
    path("403/", TemplateView.as_view(template_name="403.html")),
    path("404/", TemplateView.as_view(template_name="404.html")),
]
