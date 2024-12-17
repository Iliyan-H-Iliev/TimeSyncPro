from threading import local

from django.utils.deprecation import MiddlewareMixin

_user = local()


class HistoryUserMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)

    def process_request(self, request):
        """Set current user and cache permissions"""
        if request.user.is_authenticated:
            if not hasattr(request.user, "_cached_permissions"):
                # Cache all permissions
                all_permissions = request.user.get_all_permissions()
                request.user._cached_permissions = all_permissions
                # Cache permission codenames
                request.user.user_permissions_codenames = {
                    perm.split(".")[-1] for perm in all_permissions
                }

            set_current_user(request.user)
        else:
            set_current_user(None)
        return None

    def process_response(self, request, response):
        """Clear user at the end of request"""
        clear_current_user()
        return response

    def process_exception(self, request, exception):
        """Clear user in case of exception"""
        clear_current_user()
        return None


def get_current_user():
    return getattr(_user, "value", None)


def set_current_user(user):
    _user.value = user


def clear_current_user():
    _user.value = None
