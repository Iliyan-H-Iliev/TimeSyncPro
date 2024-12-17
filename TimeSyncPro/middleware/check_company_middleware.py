from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from TimeSyncPro.middleware.utils import get_current_user, set_current_user


class CompanyCheckMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.base_allowed_urls = [
            reverse("sign_out"),
            reverse("index"),
            reverse("about"),
            reverse("contact"),
            reverse("features"),
            reverse("privacy_policy"),
            reverse("terms_and_conditions"),
            reverse("terms_of_use"),
            reverse("password_change"),
            reverse("password_change_done"),
        ]

    def get_allowed_urls(self, user_slug: str):
        return self.base_allowed_urls + [
            reverse("create_profile_company", kwargs={"slug": user_slug}),
            reverse("profile", kwargs={"slug": user_slug}),
            reverse("update_profile", kwargs={"slug": user_slug}),
        ]

    def get_user(self, request):
        return get_current_user() or request.user

    def cache_user(self, request) -> None:
        if not hasattr(request, "_cached_user"):
            try:
                cached_user = (
                    get_user_model()
                    .objects.select_related(
                        "profile",
                        "profile__company",
                        "profile__address",
                        "profile__company__address",
                    )
                    .prefetch_related("user_permissions", "groups__permissions")
                    .get(id=request.user.id)
                )

                if not hasattr(cached_user, "_cached_permissions"):
                    all_permissions = cached_user.get_all_permissions()
                    cached_user._cached_permissions = all_permissions
                    cached_user.user_permissions_codenames = {
                        perm.split(".")[-1] for perm in all_permissions
                    }

                request._cached_user = cached_user
                request.user = cached_user
                set_current_user(cached_user)
            except get_user_model().DoesNotExist:
                pass

    def should_bypass_check(self, request) -> bool:
        current_user = self.get_user(request)

        if current_user.is_authenticated:
            allowed_urls = self.get_allowed_urls(current_user.slug)
        else:
            allowed_urls = self.base_allowed_urls

        return (
            not current_user
            or not current_user.is_authenticated
            or request.path in allowed_urls
            or request.path.startswith("/admin")
            or request.path.startswith("/static/")
            or request.path.startswith("/media/")
        )

    def process_request(self, request):
        if self.should_bypass_check(request):
            return None

        self.cache_user(request)
        current_user = self.get_user(request)

        if not self.has_registered_company(current_user):
            return self.handle_no_company(request)

        return None

    def handle_no_company(self, request) -> redirect:
        current_user = self.get_user(request)
        target_url = reverse(
            "create_profile_company", kwargs={"slug": current_user.slug}
        )
        if request.path == target_url:
            return None

        if current_user.is_superuser or current_user.is_staff:
            return redirect("profile", slug=current_user.slug)

        return redirect("create_profile_company", slug=current_user.slug)

    @staticmethod
    def has_registered_company(user) -> bool:
        try:
            return bool(user.profile and user.profile.company)
        except (AttributeError, get_user_model().profile.RelatedObjectDoesNotExist):
            return False
