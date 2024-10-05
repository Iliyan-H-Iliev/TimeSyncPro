from django.core.exceptions import ValidationError
from django import forms
from django.db.models import Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from TimeSyncPro.management.models import Company


class CleanCompanyNameMixin(forms.ModelForm):
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            return name

        name = self.format_name(name)

        if not hasattr(self, 'Meta') or not hasattr(self.Meta, 'model'):
            raise ValidationError(
                _("The 'Meta' class or 'model' attribute is missing in the form.")
            )

        # model = self.Meta.model

        exclude_id = self.instance.id if self.instance and self.instance.pk else None

        if Company.objects.filter(Q(slug=name) & ~Q(id=exclude_id)).exists():
            raise ValidationError(_("A company with this name already exists."))

        return name

    @staticmethod
    def format_name(name):
        if name is None:
            return None
        return slugify(name)
