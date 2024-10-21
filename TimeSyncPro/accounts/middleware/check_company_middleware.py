from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required


class CompanyCheckMiddleware:
    """
    Middleware to restrict access to all pages except 'setup_company'
    until the user has set up their company.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_staff:
            if not self.has_registered_company(request.user):
                allowed_urls = [reverse('profile'), reverse('create_company')]
                if not request.path.startswith('/admin/') and request.path not in allowed_urls:
                    return redirect('create_company')

        response = self.get_response(request)
        return response

    @staticmethod
    def has_registered_company(user):
        return hasattr(user, 'company') and user.company is not None
