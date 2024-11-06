from django.shortcuts import redirect
from django.urls import reverse
# from django.contrib.admin.views.decorators import staff_member_required


class CompanyCheckMiddleware:
    """
    Middleware to restrict access to all pages except 'create_profile_company'
    until the user has set up their company and profile.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not (request.user.is_staff or request.user.is_superuser):
            profile = self.has_registered_company(request.user)
            company = self.has_profile(request.user)

            if not self.has_registered_company(request.user) and not self.has_profile(request.user):
                allowed_urls = [
                    reverse("sign_out"),
                ]
                create_profile_url = reverse("create_profile_company", kwargs={'slug': request.user.slug})
                allowed_urls.append(create_profile_url)
                if not request.path.startswith('/admin/') and request.path not in allowed_urls:
                    return redirect("create_profile_company", slug=request.user.slug)

        response = self.get_response(request)
        return response

    @staticmethod
    def has_registered_company(user):
        return hasattr(user, 'company') and user.company is not None

    @staticmethod
    def has_profile(user):
        return hasattr(user, 'profile') and user.profile is not None
