from django.urls import path
from django.views.generic import TemplateView

from TimeSyncPro.common.views import IndexView, features, about, terms_and_conditions, terms_of_use, privacy_policy, contact

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("features/", features, name="features"),
    path("about/", about, name="about"),
    path("terms-and-conditions/", terms_and_conditions, name="terms_and_conditions"),
    path("terms-of-use/", terms_of_use, name="terms_of_use"),
    path("privacy-policy/", privacy_policy, name="privacy_policy"),
    path("contact/", contact, name="contact"),
    path('403/', TemplateView.as_view(template_name='403.html')),
    path('404/', TemplateView.as_view(template_name='404.html')),
]
