import logging
from celery import shared_task
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

from TimeSyncPro.companies.models import Shift

logger = logging.getLogger(__name__)


@shared_task
def generate_shift_working_dates_task(shift_id, is_edit=False):
    from .models import Shift
    try:
        shift = Shift.objects.get(id=shift_id)
        shift.generate_shift_working_dates(is_edit=is_edit)
        return f"Successfully generated working dates for shift {shift_id}"
    except Exception as e:
        print(f"Error generating dates for shift {shift_id}: {str(e)}")
        raise


@shared_task(name="TimeSyncPro.companies.tasks.generate_shift_dates_for_next_year")
def generate_shift_dates_for_next_year():
    logger.info("Starting shift dates generation")
    today = timezone.now().date()
    shifts = Shift.objects.all()

    for shift in shifts:
        try:
            shift.generate_shift_working_dates()
            logger.info(f"Generated dates for shift {shift.id}")
        except Exception as e:
            logger.error(f"Error generating dates for shift {shift.id}: {str(e)}")


# @shared_task(name='TimeSyncPro.companies.tasks.print_some_text')
# def print_some_text():
#     logger.info("This is some text")
