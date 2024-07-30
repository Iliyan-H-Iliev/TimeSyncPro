from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import Http404

from .forms import  BasicEditEmployeeForm, EditCompanyForm, DetailedEditEmployeesBaseForm
from .models import Company, Employee

UserModel = get_user_model()


def get_user_by_slug(slug):
    user = UserModel.objects.prefetch_related('company', 'employee').filter(
        Q(company__slug=slug) | Q(employee__slug=slug)
    ).first()

    if user is None:
        raise Http404("No user found")

    return user


def get_additional_form_class(is_company, detailed_edit=False):
    form_class = None

    if is_company:
        form_class = EditCompanyForm
    elif not is_company:
        form_class = DetailedEditEmployeesBaseForm if detailed_edit else BasicEditEmployeeForm

    return form_class


def get_obj_company(obj):

    if obj is None:
        return None

    if obj.__class__.__name__ == 'TimeSyncProUser':
        return obj.get_company
    else:
        return obj.company

