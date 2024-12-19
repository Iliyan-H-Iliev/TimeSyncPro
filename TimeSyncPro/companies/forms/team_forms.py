from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from .mixins import Select2SlideCheckboxWidget
from ..models import Team
from TimeSyncPro.common.form_mixins import CheckExistingNamePerCompanyMixin
from ...accounts.models import Profile
from ...shifts.models import Shift

UserModel = get_user_model()


class TeamBaseForm(CheckExistingNamePerCompanyMixin, forms.ModelForm):

    team_members = forms.ModelMultipleChoiceField(
        queryset=UserModel.objects.none(),
        required=False,
        widget=Select2SlideCheckboxWidget(
            attrs={"class": "select2-checkbox", "data-placeholder": "Select members..."}
        ),
    )

    class Meta:
        model = Team
        fields = [
            "name",
            "shift",
            "holiday_approver",
            "employees_holidays_at_a_time",
            "team_members",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)
        self.user = user
        self.company = company

        if self.company:
            self.fields["team_members"].queryset = self.company.employees.filter(
                team=None
            )
            self.fields["holiday_approver"].queryset = (
                self.company.get_company_holiday_approvers()
            )
            self.fields["shift"].queryset = self.company.shifts.all()
        else:
            self.fields["team_members"].queryset = UserModel.objects.none()
            self.fields["holiday_approver"].queryset = UserModel.objects.none()
            self.fields["shift"].queryset = Shift.objects.none()

        self.fields["team_members"].label = "Team Members"

    def save(self, commit=True):
        team = super().save(commit=False)
        team.company = self.company

        if commit:
            team.save()
            if "team_members" in self.cleaned_data:
                Profile.objects.filter(
                    id__in=[m.id for m in self.cleaned_data["team_members"]]
                ).update(team=team)

        return team


class CreateTeamForm(TeamBaseForm):
    pass


class EditTeamForm(TeamBaseForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        company = kwargs.pop("company", None)
        team = kwargs.pop("team", None)
        super().__init__(*args, **kwargs)
        self.user = user
        self.company = company
        self.team = team
        self.initial_team_members = set(self.team.employees.all() if self.team else [])

        if self.company:
            sorted_team_members = self.team.employees.all().order_by(
                "first_name", "last_name"
            )
            sorted_non_team_members = self.team.company.employees.filter(
                team=None
            ).order_by("first_name", "last_name")
            combined_queryset = sorted_team_members | sorted_non_team_members

            self.fields["team_members"].queryset = combined_queryset
            self.fields["team_members"].initial = self.initial_team_members
            self.fields["holiday_approver"].queryset = (
                self.team.company.employees.filter(role__in=["HR", "MANAGER"])
            )
            self.fields["shift"].queryset = self.team.company.shifts.all()

            self.fields["team_members"].label = "Team Members"
            # self.fields['team_members'].help_text = "Select team members from the list"

    @transaction.atomic
    def save(self, commit=True):
        team = super().save(commit=False)
        if commit:
            team.save()

            final_team_members = set(self.cleaned_data.get("team_members", []))

            members_to_remove = self.initial_team_members - final_team_members
            Profile.objects.filter(id__in=[m.id for m in members_to_remove]).update(
                team=None
            )

            members_to_add = final_team_members - self.initial_team_members
            Profile.objects.filter(id__in=[m.id for m in members_to_add]).update(
                team=team
            )

        return team


# TODO TeamListView


class DeleteTeamForm(forms.Form):
    pass
