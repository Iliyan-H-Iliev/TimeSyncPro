from django.core.exceptions import ValidationError
from django import forms
from django.db.models import Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from TimeSyncPro.companies.models import Company


class CheckExistingNameBaseMixin(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.company = None

        if kwargs.get('instance'):
            if isinstance(kwargs.get('instance'), Company):
                self.company = kwargs.get('instance')

            elif hasattr(kwargs.get('instance'), 'company'):
                self.company = kwargs.get('instance').company

            if self.company:
                if kwargs.get('company'):
                    kwargs.pop('company')

        elif kwargs.get('company'):
            self.company = kwargs.pop('company')

        self.user = kwargs.get('user')
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            return name

        self._validate_form_structure()
        self.check_name_uniqueness(name)

        return name

    def _validate_form_structure(self):
        if not hasattr(self, 'Meta') or not hasattr(self.Meta, 'model'):
            raise ValidationError(
                _("The 'Meta' class or 'model' attribute is missing in the form.")
            )

    def check_name_uniqueness(self, name):
        model = self.Meta.model
        exclude_id = self.instance.pk if self.instance else None

        if model.objects.filter(name__iexact=name).exclude(pk=exclude_id).exists():
            raise ValidationError(_("A record with this name already exists."))


class CheckCompanyExistingSlugMixin(CheckExistingNameBaseMixin):
    # def __init__(self, *args, **kwargs):
    #     self.company = kwargs.get('company')
    #     self.user = kwargs.get('user')
    #     super().__init__(*args, **kwargs)

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
            if model.objects.filter(name__iexact=name, company=company).exclude(pk=exclude_id).exists():
                raise ValidationError(_("A record with this name already exists for this company."))

        else:
            if model.objects.filter(name__iexact=name, company=company).exists():
                raise ValidationError(_("A record with this name already exists for your company."))


class LabelMixin:
    def add_labels(self):
        for field_name, field in self.fields.items():
            label = field_name.replace('_', ' ').title()
            field.label = label

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_labels()
