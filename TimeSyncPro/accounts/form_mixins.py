from django.core.exceptions import ValidationError, ImproperlyConfigured

from TimeSyncPro.accounts.utils import format_email



class ReadonlyFieldsFormMixin:
    readonly_fields = ()

    def _apply_readonly_on_fields(self):
        for field_name in self.readonly_field_names:
            self.fields[field_name].widget.attrs["readonly"] = "readonly"
            self.fields[field_name].widget.attrs["disabled"] = "disabled"

    @property
    def readonly_field_names(self):
        if self.readonly_fields == "__all__":
            return self.fields.keys()

        return self.readonly_fields


class CleanEmailMixin:
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = format_email(email)

            # Ensure Meta and model are properly defined
            if not hasattr(self, 'Meta') or not hasattr(self.Meta, 'model'):
                raise ImproperlyConfigured(
                    "The 'Meta' class or 'model' attribute is missing in the form."
                )

            model = self.Meta.model

            if model.objects.filter(email=email).exists():
                raise ValidationError("A user with this email already exists.")
        return email
