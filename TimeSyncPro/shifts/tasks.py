import logging
from celery import shared_task

from .models import Shift

logger = logging.getLogger(__name__)


@shared_task()
def generate_shift_working_dates_task(shift_id, is_edit=False):
    logger.info("Starting shift working dates generation")
    try:
        shift = Shift.objects.get(id=shift_id)
        shift.generate_shift_working_dates(is_edit=is_edit)
        return f"Successfully generated working dates for shift {shift_id}"

    except Exception as e:
        logger.error(f"Error generating dates for shift {shift_id}: {str(e)}")
        raise


@shared_task(name="TimeSyncPro.shift.tasks.generate_shift_dates_for_next_year")
def generate_shift_dates_for_next_year():
    logger.info("Starting shift working dates generation for next year")

    shifts = Shift.objects.all()

    for shift in shifts:
        try:
            shift.generate_shift_working_dates()
            logger.info(f"Generated dates for shift {shift.id}")
        except Exception as e:
            logger.error(f"Error generating dates for shift {shift.id}: {str(e)}")

