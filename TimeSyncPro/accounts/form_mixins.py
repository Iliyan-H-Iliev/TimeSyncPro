from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django import forms
from django.db.models import Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from TimeSyncPro.accounts.models import Profile

UserModel = get_user_model()


class ReadonlyFieldsFormMixin(forms.ModelForm):
    readonly_fields = ()

    def _apply_readonly_on_fields(self):
        for field_name in self.readonly_field_names:
            self.fields[field_name].widget.attrs["readonly"] = "readonly"
            self.fields[field_name].widget.attrs["disabled"] = "disabled"

    @property
    def readonly_field_names(self):
        if self.readonly_fields[0] == "__all__":
            return self.fields.keys()

        return self.readonly_fields


class RequiredFieldsFormMixin(forms.ModelForm):
    required_fields = ()
    not_required_fields = ()

    def _apply_required_on_fields(self):
        for field_name in self.required_field_names:
            self.fields[field_name].required = True

    def _apply_not_required_on_fields(self):
        a = self.not_required_field_names
        print(a)
        for field_name in self.not_required_field_names:
            self.fields[field_name].required = False

    @property
    def required_field_names(self):
        if self.required_fields[0] == "__all__":
            return self.fields.keys()

        return self.required_fields

    @property
    def not_required_field_names(self):
        if self.not_required_fields[0] == "__all__":
            return self.fields.keys()

        return list(self.not_required_fields) if isinstance(self.not_required_fields, (list, tuple)) else [self.not_required_fields]


class CleanEmailMixin(forms.ModelForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email

        email = UserModel.formated_email(email)

        if not hasattr(self, 'Meta') or not hasattr(self.Meta, 'model'):
            raise ImproperlyConfigured(
                _("The 'Meta' class or 'model' attribute is missing in the form.")
            )

        model = self.Meta.model

        # Check if this is an update for an existing instance
        exclude_id = self.instance.id if self.instance and self.instance.pk else None

        if model.objects.filter(Q(email=email) & ~Q(id=exclude_id)).exists():
            raise ValidationError(_("A user with this email already exists."))

        return email


class ProfileFieldsMixin(forms.ModelForm):
    profile_fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        profile_fields = forms.models.fields_for_model(
            Profile,
            fields=self.profile_fields
        )
        self.fields.update(profile_fields)



