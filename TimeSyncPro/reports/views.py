from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import render
from datetime import timedelta, datetime

from django.utils import timezone
from django.views import generic as views
from django.views.generic.edit import FormMixin

from TimeSyncPro.absences.models import Absence, Holiday
from TimeSyncPro.accounts.models import Profile
from TimeSyncPro.common.views_mixins import CompanyAccessMixin
from TimeSyncPro.companies.models import Department, Team
from TimeSyncPro.reports.forms import GenerateReportForm

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic as views
from django.db.models import Count, F, ExpressionWrapper, IntegerField, Sum, Case, When, Value, CharField, Q
from django.utils import timezone
from django.db.models.functions import Greatest, ExtractDay
from datetime import timedelta


@login_required
@permission_required('reports.generate_reports', raise_exception=True)
def generate_report(request, company_slug):
    user = request.user
    company = request.user.profile.company
    if company.slug != company_slug:
        raise PermissionDenied("You can only view your own company.")

    # Get parameters from request.GET
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    department_id = request.GET.get('department')
    team_id = request.GET.get('team')

    # Convert string dates to date objects or use defaults
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else timezone.now().date() - timezone.timedelta(days=30)
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else timezone.now().date()
    except ValueError:
        start_date = timezone.now().date() - timezone.timedelta(days=30)
        end_date = timezone.now().date()

    # Get department and team if IDs provided
    department = None
    team = None
    try:
        if department_id:
            department = Department.objects.get(id=department_id, company=company)
        if team_id:
            team = Team.objects.get(id=team_id, company=company)
    except (Department.DoesNotExist, Team.DoesNotExist):
        pass

    # Get absences
    absences_query = Absence.objects.filter(
        Q(start_date__lte=end_date) & Q(end_date__gte=start_date),
        absentee__company=company
    ).select_related(
        'absentee',
        'absentee__department',
        'absentee__team'
    )
    if user.has_perm("reports.generate_all_reports"):
        if department:
            absences_query = absences_query.filter(absentee__department=department)
        if team:
            absences_query = absences_query.filter(absentee__team=team)

    elif user.has_perm("reports.generate_department_reports") and user.profile.department:
        absences_query = absences_query.filter(absentee__department=user.profile.department)

    elif user.has_perm("reports.generate_team_reports") and user.profile.team:
        absences_query = absences_query.filter(absentee__team=user.profile.team)

    else:
        absences_query = absences_query.none()

    # Get holidays
    holidays_query = Holiday.objects.filter(
        Q(start_date__lte=end_date) & Q(end_date__gte=start_date),
        status='approved',
        requester__company=company
    ).select_related(
        'requester',
        'requester__department',
        'requester__team'
    )

    if user.has_perm("reports.generate_all_reports"):
        if department:
            holidays_query = holidays_query.filter(requester__department=department)
        if team:
            holidays_query = holidays_query.filter(requester__team=team)
    elif user.has_perm("reports.generate_department_reports") and user.profile.department:
        holidays_query = holidays_query.filter(requester__department=user.profile.department)
    elif user.has_perm("reports.generate_team_reports") and user.profile.team:
        holidays_query = holidays_query.filter(requester__team=user.profile.team)
    else:
        holidays_query = holidays_query.none()

    absence_by_type = {}
    for absence in absences_query:
        absence_type = absence.get_absence_type_display()
        if absence_type not in absence_by_type:
            absence_by_type[absence_type] = []
        absence_by_type[absence_type].append({
            'employee': absence.absentee.full_name,
            'department': absence.absentee.department.name if absence.absentee.department else 'N/A',
            'team': absence.absentee.team.name if absence.absentee.team else 'N/A',
            'start_date': absence.start_date,
            'end_date': absence.end_date,
            'days': absence.days_of_absence,
            'reason': absence.reason,
        })

    # Process holidays
    holidays_data = [
        {
            'employee': holiday.requester.full_name,
            'department': holiday.requester.department.name if holiday.requester.department else 'N/A',
            'team': holiday.requester.team.name if holiday.requester.team else 'N/A',
            'start_date': holiday.start_date,
            'end_date': holiday.end_date,
            'days': holiday.days_requested,
            'reason': holiday.reason,
        }
        for holiday in holidays_query
    ]

    if holidays_data:
        absence_by_type['Holiday'] = holidays_data

    context = {
        'departments': Department.objects.filter(company=company),
        'teams': Team.objects.filter(company=company),
        'absence_by_type': absence_by_type,
        'start_date': start_date,
        'end_date': end_date,
        'selected_department': department,
        'selected_team': team,
        'total_absences': sum(len(abs_list) for abs_list in absence_by_type.values()),
    }

    return render(request, 'reports/generate_report.html', context)


class BradfordFactorReport(CompanyAccessMixin, LoginRequiredMixin, views.ListView):
    template_name = 'reports/bradford_factor.html'

    def get_date_range(self):
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)
        return start_date, end_date

    def get_queryset(self):
        start_date, end_date = self.get_date_range()

        return Profile.objects.select_related(
            "department",
        ).prefetch_related(
            Prefetch(
                'absences',
                queryset=Absence.objects.filter(
                    start_date__range=(start_date, end_date)
                ).order_by('start_date'),
                to_attr='filtered_absences'
            )
        ).annotate(
            spells=Count(
                'absences',
                filter=Q(absences__start_date__range=(start_date, end_date))
            ),
            total_days=Sum(
                Greatest(
                    ExtractDay(
                        F('absences__end_date') - F('absences__start_date')
                    ) + 1,
                    0
                ),
                filter=Q(absences__start_date__range=(start_date, end_date))
            ),
        ).annotate(
            bradford_score=ExpressionWrapper(
                F('spells') * F('spells') * F('total_days'),
                output_field=IntegerField()
            ),
            risk_level=Case(
                When(bradford_score__gt=900, then=Value('High')),
                When(bradford_score__gt=400, then=Value('Medium')),
                default=Value('Low'),
                output_field=CharField(),
            )
        ).filter(
            company=self.request.user.profile.company
        ).order_by('bradford_score')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        bradford_data = [
            {
                'employee': employee.full_name,
                'department': employee.department,
                'spells': employee.spells,
                'total_days': employee.total_days or 0,
                'bradford_score': employee.bradford_score or 0,
                'risk_level': employee.risk_level,
                'absences': employee.filtered_absences
            }
            for employee in context['object_list']
        ]

        context['bradford_data'] = bradford_data
        return context
