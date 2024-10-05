from datetime import timedelta

from django import forms
from .models import ShiftPattern, ShiftBlock, Team, Company
from django.forms.models import inlineformset_factory



# TODO only Administrator can edit company
class EditCompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "name",
            "leave_days_per_year",
            "transferable_leave_days",
            "location",
            "leave_approver",
            "transferable_leave_days",
            "minimum_leave_notice",
            "maximum_leave_days_per_request",
            "working_on_local_holidays",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['leave_approver'].queryset = Profile.objects.filter(company=self.instance)
        self.fields['leave_approver'].queryset = Company.objects.get(pk=self.instance.pk).employees.all()

    # def clean(self):
    #     cleaned_data = super().clean()
    #     if 'location' in cleaned_data and not cleaned_data.get('time_zone'):
    #         # If a location is set but no time zone, suggest one
    #         cleaned_data['time_zone'] = self.instance.suggest_time_zone()
    #     return cleaned_data



class ShiftPatternBaseForm(forms.ModelForm):
    # TODO is start_date is on week pattern should start from Monday!!!
    class Meta:
        model = ShiftPattern
        fields = ['name', 'description', 'rotation_weeks', 'start_date',]

    def clean(self):
        cleaned_data = super().clean()
        rotation_weeks = cleaned_data.get('rotation_weeks')
        name = cleaned_data.get('name')
        company = self.request.user.company

        if ShiftPattern.objects.filter(company=company, name=name).exclude(pk=self.instance.pk).exists():
            self.add_error('name', 'Shift pattern with this name already exists for your company.')

        if rotation_weeks < 1:
            self.add_error("rotation_weeks","Rotation weeks must be at least 1.")

        return cleaned_data


class ShiftBlockBaseForm(forms.ModelForm):
    MIN_DAYS_ON = 0
    MAX_DAYS_ON = 7
    MIN_DAYS_OFF = 0
    MAX_DAYS_OFF = 7
    MIN_DURATION_HOURS = 0
    MAX_DURATION_HOURS = 23
    MIN_DURATION_MINUTES = 0
    MAX_DURATION_MINUTES = 59

    CHOICES = [
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
        (7, 'Sunday'),
    ]

    week_days = forms.MultipleChoiceField(
        choices=CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    duration_hours = forms.IntegerField(
        required=False,
        label="Duration (hours)",
        min_value=MIN_DURATION_HOURS,
        max_value=MAX_DURATION_HOURS,
    )

    duration_minutes = forms.IntegerField(
        required=False,
        label="Duration (minutes)",
        min_value=MIN_DURATION_MINUTES,
        max_value=MAX_DURATION_MINUTES,
    )

    class Meta:
        model = ShiftBlock
        fields = [
            "week_days",
            'days_on', 'days_off',
            'start_time', 'end_time',
            "duration_hours",
            "duration_minutes",
        ]

    def clean_duration(self):
        hours = self.cleaned_data.get("duration_hours") or 0
        minutes = self.cleaned_data.get("duration_minutes") or 0
        if hours or minutes:
            return timedelta(hours=hours, minutes=minutes)
        return None

    def clean(self):
        # TODO debug this
        cleaned_data = super().clean()
        week_days = cleaned_data.get("week_days")
        days_on = cleaned_data.get("days_on")
        days_off = cleaned_data.get("days_off")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        self.instance.duration = self.clean_duration()

        if not week_days and (days_on is None and days_off is None):
            self.add_error(
                "week_days",
                "You must specify either working days or a pattern (days on and days off)."
            )

        if week_days:
            if days_on is not None or days_off is not None:
                self.add_error(
                    "week_days",
                    "You must specify either working days or a pattern (days on and days off), not both."
                )

        if week_days:
            week_days_int = [int(day) for day in week_days]
            self.instance.selected_days = week_days_int
            on_off_days = [1 if i in week_days_int else 0 for i in range(1, 8)]
            self.instance.on_off_days = on_off_days

        else:
            on_off_days = []

            if days_on is not None:
                on_off_days.extend([1] * days_on)

            if days_off is not None:
                on_off_days.extend([0] * days_off)

            self.instance.on_off_days = on_off_days

        return cleaned_data


class CreateShiftPatternForm(ShiftPatternBaseForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CreateShiftPatternForm, self).__init__(*args, **kwargs)


class CreateShiftBlockForm(ShiftBlockBaseForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CreateShiftBlockForm, self).__init__(*args, **kwargs)


CreateShiftBlockFormSet = forms.inlineformset_factory(
    ShiftPattern, ShiftBlock,
    form=CreateShiftBlockForm,
    extra=2,
    can_delete=True
)


class UpdateShiftPatternForm(ShiftPatternBaseForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(UpdateShiftPatternForm, self).__init__(*args, **kwargs)


class UpdateShiftBlockForm(ShiftBlockBaseForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(UpdateShiftBlockForm, self).__init__(*args, **kwargs)
        if self.instance.selected_days:
            self.fields['week_days'].initial = self.instance.selected_days

        if self.instance.duration:
            total_seconds = self.instance.duration.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            self.fields['duration_hours'].initial = hours
            self.fields['duration_minutes'].initial = minutes


UpdateShiftBlockFormSet = inlineformset_factory(
    ShiftPattern, ShiftBlock,
    form=UpdateShiftBlockForm,
    extra=1,
    can_delete=True
)


class DeleteShiftPatternForm(forms.Form):
    pass


class CreateTeamForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        company = kwargs.pop('company', None)
        super(CreateTeamForm, self).__init__(*args, **kwargs)
        self.fields['team_members'].queryset = company.employees.filter(team=None)

    team_members = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        # TODO add company field
        model = Team
        fields = ['name', 'shift_pattern', 'team_members']

    def save(self, commit=True):
        team = super(CreateTeamForm, self).save(commit=False)
        team.save()
        for employee in self.cleaned_data['team_members']:
            employee.team = team
            employee.save()
        return team


class EditTeamForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        company = kwargs.pop('company', None)
        team = kwargs.pop('team', None)
        super(EditTeamForm, self).__init__(*args, **kwargs)
        self.team = team
        self.initial_team_members = set(team.employees.all())

        sorted_team_members = team.employees.all().order_by('first_name', 'last_name')

        sorted_non_team_members = company.employees.filter(team=None).order_by('first_name', 'last_name')

        combined_queryset = sorted_team_members | sorted_non_team_members

        # Set the queryset for team_members to the combined sorted querysets
        self.fields['team_members'].queryset = combined_queryset

        # Set the initial value to the current team members
        self.fields['team_members'].initial = self.initial_team_members

    team_members = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    def save(self, commit=True):
        team = super(EditTeamForm, self).save(commit=False)
        if commit:
            team.save()

        final_team_members = set(self.cleaned_data['team_members'])

        members_to_remove = self.initial_team_members - final_team_members
        for employee in members_to_remove:
            employee.team = None
            employee.save()

        members_to_add = final_team_members - self.initial_team_members
        for employee in members_to_add:
            employee.team = team
            employee.save()

        return team

    class Meta:
        model = Team
        fields = ['name', 'shift_pattern', 'team_members']

#TODO TeamListView


class DeleteTeamForm(forms.Form):
    pass
