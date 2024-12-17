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
    retry_kwargs={"max_retries": 5},
    queue="emails",
)
def send_email_to_reviewer(
    self,
    start_date,
    end_date,
    requester_name,
    reviewer_email,
    reviewer_name,
    days_requested,
):
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        context = {
            "requester_name": requester_name,
            "reviewer_name": reviewer_name,
            "start_date": start_date.strftime("%B %d, %Y"),
            "end_date": end_date.strftime("%B %d, %Y"),
            "days_requested": days_requested,
        }

        html_content = render_to_string(
            "email_templates/new_request_for_review.html", context
        )
        text_content = strip_tags(html_content)

        subject = f"New Holiday Request for Review - {start_date.strftime('%B %d')} to {end_date.strftime('%B %d')}"

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email="timesyncpro@donotreply.com",
            to=[reviewer_email],
        )

        email.attach_alternative(html_content, "text/html")

        email.send()

        logger.info(f"New holiday request email sent successfully to {reviewer_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send new holiday request email: {str(e)}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
    queue="emails",
)
def send_new_holiday_request_email(
    self, start_date, end_date, requester_email, requester_name, days_requested
):
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        context = {
            "requester_name": requester_name,
            "start_date": start_date.strftime("%B %d, %Y"),
            "end_date": end_date.strftime("%B %d, %Y"),
            "days_requested": days_requested,
        }

        html_content = render_to_string(
            "email_templates/new_holiday_request.html", context
        )
        text_content = strip_tags(html_content)

        subject = f"New Holiday Request - {start_date.strftime('%B %d')} to {end_date.strftime('%B %d')}"

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email="timesyncpro@donotreply.com",
            to=[requester_email],
        )

        email.attach_alternative(html_content, "text/html")

        email.send()

        logger.info(f"New holiday request email sent successfully to {requester_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send new holiday request email: {str(e)}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
    queue="emails",
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
    days_requested,
):
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        context = {
            "requester_name": requester_name,
            "reviewer_name": reviewer_name,
            "start_date": start_date.strftime("%B %d, %Y"),
            "end_date": end_date.strftime("%B %d, %Y"),
            "days_requested": days_requested,
            "status": status.title(),
            "review_reason": review_reason,
            "is_approved": status == "approved",
        }

        html_content = render_to_string(
            "email_templates/holiday_status_update.html", context
        )
        text_content = strip_tags(html_content)

        subject = f"Holiday Request {status.title()} - {start_date.strftime('%B %d')} to {end_date.strftime('%B %d')}"

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email="timesyncpro@donotreply.com",
            to=[recipient_email],
        )

        email.attach_alternative(html_content, "text/html")

        email.send()

        logger.info(f"Holiday status email sent successfully to {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send holiday status email: {str(e)}")
        raise self.retry(exc=e)
