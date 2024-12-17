from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

UserModel = get_user_model()


class SignInUserForm(AuthenticationForm):

    error_messages = {
        "invalid_login": "Invalid email or password.",
        "inactive": "This account is inactive.",
    }

    def clean_username(self):
        email = self.cleaned_data.get("username")
        if email:
            email = UserModel.objects.normalize_email(email)
        return email

    class Meta:
        model = UserModel
        fields = ["username", "password"]
