
from datetime import datetime, timedelta

from django import forms
from django.db import transaction

from .models import Shift, ShiftBlock, Team, Company, Department
from django.forms.models import inlineformset_factory

from ..accounts.form_mixins import RequiredFieldsFormMixin
from TimeSyncPro.common.form_mixins import CheckCompanyExistingSlugMixin, CheckExistingNamePerCompanyMixin
from ..accounts.models import Profile






