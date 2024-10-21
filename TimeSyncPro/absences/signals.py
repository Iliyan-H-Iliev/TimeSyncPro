from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Holiday


@receiver(post_save, sender=Holiday)
def notify_holiday_status_change(sender, instance, created, **kwargs):
    if not created and instance.reviewed_by:
        action = 'approved' if instance.status == Holiday.StatusChoices.APPROVED else 'denied'
        subject = f"Your holiday request has been {action}"
        message = f"Your holiday request from {instance.start_date} to {instance.end_date} has been {action}."
        if instance.review_reason:
            message += f"\n\nReason: {instance.review_reason}"

        send_mail(
            subject,
            message,
            'from@abv.com',  # TODO - Update this email address
            [instance.user.email],
            fail_silently=False,
        )