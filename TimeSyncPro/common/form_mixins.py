from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.core.exceptions import ValidationError
from django import forms
from django.utils.translation import gettext_lazy as _
from TimeSyncPro.companies.models import Company

UserModel = get_user_model()


class ReadonlyFieldsFormMixin(forms.ModelForm):
    readonly_fields = ()

    def _apply_readonly_on_fields(self):
        for field_name in self.readonly_field_names:
            if field_name not in self.fields:
                continue

            field = self.fields[field_name]

            if isinstance(field, forms.Field):
                if isinstance(field, forms.DateField):
                    field.widget = forms.DateInput()
                elif isinstance(field, forms.EmailField):
                    field.widget = forms.EmailInput()
                elif isinstance(field, forms.BooleanField):
                    field.widget = forms.CheckboxInput()
                else:
                    field.widget = forms.TextInput()

            if not hasattr(field.widget, "attrs"):
                field.widget.attrs = {}

            css_classes = field.widget.attrs.get("class", "").split()
            css_classes.extend(["read-only"])

            field.widget.attrs.update(
                {
                    "readonly": "readonly",
                    "aria-readonly": "true",
                    "class": " ".join(filter(None, css_classes)),
                    "tabindex": "-1",
                }
            )

    @property
    def readonly_field_names(self):
        if self.readonly_fields[0] == "__all__":
            return self.fields.keys()

        return self.readonly_fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_readonly_on_fields()


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

        return (
            list(self.not_required_fields)
            if isinstance(self.not_required_fields, (list, tuple))
            else [self.not_required_fields]
        )


class CleanEmailMixin(forms.ModelForm):
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            return email

        email = UserModel.objects.normalize_email(email)

        if not hasattr(self, "Meta") or not hasattr(self.Meta, "model"):
            raise ImproperlyConfigured(
                _("The 'Meta' class or 'model' attribute is missing in the form.")
            )

        model = self.Meta.model

        exclude_id = self.instance.id if self.instance and self.instance.pk else None

        if model.objects.filter(Q(email=email) & ~Q(id=exclude_id)).exists():
            raise ValidationError(_("A user with this email already exists."))

        return email


class CheckExistingNameBaseMixin(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.company = None

        if kwargs.get("instance"):
            if isinstance(kwargs.get("instance"), Company):
                self.company = kwargs.get("instance")

            elif hasattr(kwargs.get("instance"), "company"):
                self.company = kwargs.get("instance").company

            if self.company:
                if kwargs.get("company"):
                    kwargs.pop("company")

        elif kwargs.get("company"):
            self.company = kwargs.pop("company")

        self.user = kwargs.get("user")
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if not name:
            return name

        self._validate_form_structure()
        self.check_name_uniqueness(name)

        return name

    def _validate_form_structure(self):
        if not hasattr(self, "Meta") or not hasattr(self.Meta, "model"):
            raise ValidationError(
                _("The 'Meta' class or 'model' attribute is missing in the form.")
            )

    def check_name_uniqueness(self, name):
        model = self.Meta.model
        exclude_id = self.instance.pk if self.instance else None

        if model.objects.filter(name__iexact=name).exclude(pk=exclude_id).exists():
            raise ValidationError(_("A record with this name already exists."))


class CheckCompanyExistingSlugMixin(CheckExistingNameBaseMixin):

    def check_name_uniqueness(self, name):
        exclude_id = self.instance.pk if self.instance else None

        slug = Company.slug_generator(name, Company.MAX_SLUG_LENGTH)

        if Company.objects.filter(slug=slug).exclude(pk=exclude_id).exists():
            raise ValidationError(_("Company with this name already exists."))


class CheckExistingNamePerCompanyMixin(CheckExistingNameBaseMixin):

    def check_name_uniqueness(self, name):
        obj = self.instance if self.instance else None
        company = self.company
        exclude_id = obj.pk if obj else None
        model = self.Meta.model

        if exclude_id:
            if (
                model.objects.filter(name__iexact=name, company=company)
                .exclude(pk=exclude_id)
                .exists()
            ):
                raise ValidationError(
                    _("A record with this name already exists for this company.")
                )

        else:
            if model.objects.filter(name__iexact=name, company=company).exists():
                raise ValidationError(
                    _("A record with this name already exists for your company.")
                )


class LabelMixin:
    def add_labels(self):
        for field_name, field in self.fields.items():
            label = field_name.replace("_", " ").title()
            field.label = label

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_labels()


class CleanFormMixin:

    def clean(self):
        cleaned_data = super().clean()

        form_fields = set(self.fields.keys())

        for field in self.instance._meta.fields:

            if field.name not in form_fields:
                continue

            value = cleaned_data.get(field.name)
            if value is not None:
                try:
                    for validator in field.validators:
                        validator(value)
                except ValidationError as e:
                    self.add_error(field.name, e)

        return cleaned_data
