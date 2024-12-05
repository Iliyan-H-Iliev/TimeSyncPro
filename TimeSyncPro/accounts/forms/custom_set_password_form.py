from django import forms
from django.contrib.auth.forms import SetPasswordForm


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.user.is_active:
            raise forms.ValidationError("This account is already active.")
