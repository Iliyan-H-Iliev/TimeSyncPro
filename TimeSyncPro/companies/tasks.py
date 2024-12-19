import logging
from celery import shared_task
from django.db import transaction
from django.db.models import Case, When, F

from TimeSyncPro.companies.models import Company
from TimeSyncPro.shifts.models import Shift

logger = logging.getLogger(__name__)


@shared_task(name="TimeSyncPro.companies.tasks.yearly_set_next_year_leave_days")
def yearly_set_next_year_leave_days():
    logger.info("Starting Yearly Set Next Year Leave Days")

    with transaction.atomic():
        companies = Company.objects.prefetch_related("employees").all()

        for company in companies:
            try:
                employees = company.employees.all()

                employees.update(
                    remaining_leave_days=Case(
                        When(
                            remaining_leave_days__gt=company.max_carryover_leave,
                            then=company.max_carryover_leave,
                        ),
                        default=F("remaining_leave_days"),
                    )
                )

                employees.update(
                    remaining_leave_days=F("remaining_leave_days")
                    + F("next_year_leave_days"),
                    next_year_leave_days=company.annual_leave,
                )

                logger.info(
                    f"Successfully updated leave days for company {company.name} - {len(employees)} employees"
                )

            except Exception as e:
                logger.error(f"Error processing company {company.name}: {str(e)}")
                continue

    logger.info("Completed Yearly Set Next Year Leave Days")


# @shared_task(name='TimeSyncPro.companies.tasks.print_some_text')
# def print_text():
#     logger.info("Text")
