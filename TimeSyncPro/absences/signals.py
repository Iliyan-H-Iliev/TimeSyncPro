from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Holiday


# @receiver(post_save, sender=Holiday)
# def notify_holiday_status_change(sender, instance, created, **kwargs):
#     if not created and instance.reviewed_by:
#         action = 'approved' if instance.status == Holiday.StatusChoices.APPROVED else 'denied'
#         subject = f"Your holiday request has been {action}"
#         message = f"Your holiday request from {instance.start_date} to {instance.end_date} has been {action}."
#         if instance.review_reason:
#             message += f"\n\nReason: {instance.review_reason}"
#
#         send_mail(
#             subject,
#             message,
#             'from@abv.com',  # TODO - Update this email address
#             [instance.requester.user.email],
#             fail_silently=False,
#         )

#
# @receiver(post_save, sender=Holiday)
# def notify_holiday_status_change(sender, instance, created, **kwargs):
#     if not created and instance.reviewed_by:
#         try:
#             from .tasks import send_holiday_status_email
#
#             send_holiday_status_email.delay(
#                 str(instance.start_date),
#                 str(instance.end_date),
#                 instance.status,
#                 instance.review_reason,
#                 instance.requester.user.email
#             )
#         except Exception as e:
#             print(f"Failed to queue email notification: {str(e)}")

import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Holiday)
def notify_holiday_status_change(sender, instance, created, **kwargs):
    if not created and instance.reviewed_by:
        try:
            from .tasks import send_holiday_status_email

            task = send_holiday_status_email.delay(
                str(instance.start_date),
                str(instance.end_date),
                instance.status,
                instance.review_reason,
                instance.requester.user.email,
                instance.requester.full_name,
                instance.reviewed_by.full_name,
                instance.days_requested
            )
            print(f"Queued holiday status email with task ID: {task.id}")
        except Exception as e:
            logger.error(f"Failed to queue holiday status email: {str(e)}")
