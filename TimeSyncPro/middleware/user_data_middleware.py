from django.contrib.auth import get_user_model


class UserDataMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user = (
                get_user_model().objects
                .select_related(
                    'profile',
                    'profile__company'
                )
                .get(id=request.user.id)
            )

        response = self.get_response(request)
        return response
