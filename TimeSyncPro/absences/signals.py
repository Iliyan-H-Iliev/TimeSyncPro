from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Holiday

import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Holiday)
def notify_new_holiday_request(sender, instance, created, **kwargs):
    if created:
        try:
            from .tasks import send_new_holiday_request_email, send_email_to_reviewer

            send_new_holiday_request_email.delay(
                str(instance.start_date),
                str(instance.end_date),
                instance.requester.user.email,
                instance.requester.full_name,
                instance.days_requested,
            )

            send_email_to_reviewer.delay(
                str(instance.start_date),
                str(instance.end_date),
                instance.requester.full_name,
                instance.reviewer.user.email,
                instance.reviewer.full_name,
                instance.days_requested,
            )

        except Exception as e:
            logger.error(f"Failed to queue new holiday request email: {str(e)}")


@receiver(post_save, sender=Holiday)
def notify_holiday_status_change(sender, instance, created, **kwargs):
    if not created and instance.status != Holiday.StatusChoices.PENDING:
        try:
            from .tasks import send_holiday_status_email

            reviewer_name = instance.reviewed_by.full_name if instance.status != Holiday.StatusChoices.CANCELLED else instance.requester.full_name

            send_holiday_status_email.delay(
                str(instance.start_date),
                str(instance.end_date),
                instance.status,
                instance.review_reason,
                instance.requester.user.email,
                instance.requester.full_name,
                reviewer_name,
                instance.days_requested,
            )
        except Exception as e:
            logger.error(f"Failed to queue holiday status email: {str(e)}")
