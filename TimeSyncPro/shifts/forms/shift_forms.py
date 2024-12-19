from django import forms

from TimeSyncPro.companies.forms.mixins import Select2SlideCheckboxWidget
from TimeSyncPro.common.form_mixins import CheckExistingNamePerCompanyMixin, LabelMixin
from TimeSyncPro.common.form_mixins import ReadonlyFieldsFormMixin
from TimeSyncPro.shifts.models import Shift


class ShiftBaseForm(
    CheckExistingNamePerCompanyMixin,
    ReadonlyFieldsFormMixin,
    LabelMixin,
    forms.ModelForm,
):
    readonly_fields = [
        "rotation_weeks",
    ]

    shift_members = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=Select2SlideCheckboxWidget(
            attrs={"class": "select2-checkbox", "data-placeholder": "Select members..."}
        ),
    )

    shift_teams = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=Select2SlideCheckboxWidget(
            attrs={"class": "select2-checkbox", "data-placeholder": "Select teams..."}
        ),
    )

    class Meta:
        model = Shift
        fields = [
            "name",
            "start_date",
            "description",
            "shift_members",
            "shift_teams",
            "rotation_weeks",
        ]

        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    # def clean(self):
    #     cleaned_data = super().clean()
    #     rotation_weeks = cleaned_data.get('rotation_weeks')
    #     name = cleaned_data.get('name')
    #     company = self.request.user.company
    #
    #     if rotation_weeks < 1:
    #         self.add_error("rotation_weeks", "Rotation weeks must be at least 1.")
    #
    #     return cleaned_data

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self.company = None

        if kwargs.get("instance"):
            self.company = kwargs.get("instance").company

        if kwargs.get("company"):
            self.company = kwargs.get("company")

        self.fields["shift_members"].queryset = self.company.employees.filter(
            shift=None
        )
        self.fields["shift_teams"].queryset = self.company.teams.filter(shift=None)

        self.fields["rotation_weeks"].widget.attrs["id"] = "rotation-weeks"


class CreateShiftForm(ShiftBaseForm):
    pass


class UpdateShiftForm(ShiftBaseForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.shift = kwargs.get("instance", None)
        super().__init__(*args, **kwargs)
        self.company = self.shift.company
        self.initial_shift_members = set(
            self.shift.employees.all() if self.shift else []
        )
        self.initial_shift_teams = set(self.shift.teams.all() if self.shift else [])

        if self.company:
            sorted_shift_members = self.shift.employees.all().order_by(
                "first_name", "last_name"
            )
            sorted_non_shift_members = self.company.employees.filter(
                shift=None
            ).order_by("first_name", "last_name")
            combined_queryset = sorted_shift_members | sorted_non_shift_members

            sorted_shift_teams = self.shift.teams.all().order_by("name")
            sorted_non_shift_teams = self.company.teams.filter(shift=None).order_by(
                "name"
            )
            combined_teams_queryset = sorted_shift_teams | sorted_non_shift_teams

        self.fields["shift_members"].queryset = combined_queryset
        self.fields["shift_members"].initial = self.initial_shift_members

        self.fields["shift_teams"].queryset = combined_teams_queryset
        self.fields["shift_teams"].initial = self.initial_shift_teams

    # def __init__(self, *args, **kwargs):
    #     self.request = kwargs.pop('request', None)
    #     self.company = kwargs.get('instance').company
    #     super().__init__(*args, **kwargs)


class DeleteShiftForm(forms.Form):
    pass
