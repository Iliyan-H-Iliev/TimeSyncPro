from django.shortcuts import render
from django.views import generic as views

from TimeSyncPro.common.views_mixins import AuthenticatedUserMixin


class Index(AuthenticatedUserMixin, views.TemplateView):
    template_name = "common/index.html"
    success_url_name = "profile"


def about(request):
    return render(request, 'common/about.html')


def terms_and_conditions(request):
    return render(request, 'common/terms_and_conditions.html')


def terms_of_use(request):
    return render(request, 'common/terms_of_use.html')


def privacy_policy(request):
    return render(request, 'common/privacy_policy.html')


def contact(request):
    return render(request, 'common/contact.html')


def features(request):
    return render(request, 'common/features.html')
