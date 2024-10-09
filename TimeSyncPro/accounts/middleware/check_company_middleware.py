from django.shortcuts import redirect
from django.urls import reverse


class CheckCompanyCreateMiddleware:
    """
    Middleware to restrict access to all pages except 'setup_company'
    until the user has set up their company.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Assuming 'company' is a related field or a property of the user model
            if not hasattr(request.user, 'company') or not request.user.company:
                # Get the URL for the 'setup_company' page
                create_company_url = reverse('create company')

                # Allow access only to the 'setup_company' page
                if request.path != create_company_url:
                    return redirect('create company')

        # Proceed with the response if the user is not authenticated or has a company
        response = self.get_response(request)
        return response
