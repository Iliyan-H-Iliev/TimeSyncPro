# from celery import shared_task
# from django.core.mail import send_mail
#
#
# @shared_task
# def send_holiday_status_email(start_date, end_date, status, review_reason, recipient_email):
#     action = status.lower()
#     subject = f"Your holiday request has been {action}"
#     message = f"Your holiday request from {start_date} to {end_date} has been {action}."
#
#     if review_reason:
#         message += f"\n\nReason: {review_reason}"
#
#     return send_mail(
#         subject,
#         message,
#         'from@abv.com',  # TODO - Update this email address
#         [recipient_email],
#         fail_silently=False,
#     )


import logging
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 5},
    queue='emails'
)
def send_holiday_status_email(
        self,
        start_date,
        end_date,
        status,
        review_reason,
        recipient_email,
        requester_name,
        reviewer_name,
        days_requested
):
    """
    Send holiday status update email with HTML template and error handling.

    Args:
        start_date (str): Holiday start date
        end_date (str): Holiday end date
        status (str): Holiday status (approved/denied)
        review_reason (str): Reason for approval/denial
        recipient_email (str): Email address of recipient
        requester_name (str): Name of person requesting holiday
        reviewer_name (str): Name of person reviewing request
        days_requested (int): Number of days requested
    """
    try:
        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Prepare context for email template
        context = {
            'requester_name': requester_name,
            'reviewer_name': reviewer_name,
            'start_date': start_date.strftime('%B %d, %Y'),
            'end_date': end_date.strftime('%B %d, %Y'),
            'days_requested': days_requested,
            'status': status.title(),
            'review_reason': review_reason,
            'is_approved': status == 'approved'
        }

        # Render email templates
        html_content = render_to_string('email_templates/holiday_status_update.html', context)
        text_content = strip_tags(html_content)

        # Create email subject
        subject = f"Holiday Request {status.title()} - {start_date.strftime('%B %d')} to {end_date.strftime('%B %d')}"

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email='your-company@example.com',
            to=[recipient_email],
            reply_to=['hr@your-company.com']
        )

        # Attach HTML content
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send()

        logger.info(f"Holiday status email sent successfully to {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send holiday status email: {str(e)}")
        raise self.retry(exc=e)