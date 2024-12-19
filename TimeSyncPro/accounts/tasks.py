import logging
from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives

from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


#
#
# @shared_task
# def send_welcome_email(user_email):
#     subject = 'Welcome to the Company'
#     message = render_to_string('email_templates/welcome_email.html')
#
#     send_mail(
#         subject,
#         message,
#         'from@example.com',
#         [user_email],
#         fail_silently=False,
#         html_message=message
#     )
#
#
# @shared_task
# def send_password_reset_email(user_email, activation_url):
#     subject = 'Reset Your Password'
#     message = render_to_string('email_templates/password_reset_email.html', {
#         'activation_url': activation_url,
#     })
#
#     send_mail(
#         subject,
#         message,
#         'from@example.com',
#         [user_email],
#         fail_silently=False,
#         html_message=message
#     )


@shared_task
def send_activation_email(email, domain, protocol, relative_url, full_name):
    try:
        template_name = "email_templates/activation_email.html"
        activation_url = f"{protocol}://{domain}{relative_url}"
        subject = "Activate your account"

        context = {
            "full_name": full_name,
            "activation_url": activation_url,
        }

        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.EMAIL_HOST_USER or "noreply@timesyncpro.com",
            recipient_list=[email],
            fail_silently=False,
            html_message=html_content,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


@shared_task
def send_welcome_email(recipient_email, user_full_name):
    try:
        template_name = "email_templates/welcome_email.html"
        context = {
            "full_name": user_full_name,
        }

        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)

        subject = "Welcome to TimeSyncPro"

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.EMAIL_HOST_USER or "noreply@timesyncpro.com",
            recipient_list=[recipient_email],
            fail_silently=False,
            html_message=html_content,
        )
        logger.info(f"Welcome email sent successfully to {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return False


# @shared_task(
#     bind=True,
#     autoretry_for=(Exception,),
#     retry_backoff=True,
#     retry_kwargs={"max_retries": 5},
#     queue="emails",
# )
# def send_welcome_email(self, recipient_email, user_full_name):
#     logger.info(f"Starting welcome email task - recipient: {recipient_email}")
#
#     try:
#
#         template_name = "email_templates/welcome_email.html"
#         logger.info(f"Looking for template: {template_name}")
#
#         context = {
#             "full_name": user_full_name,
#         }
#
#         try:
#             html_content = render_to_string(template_name, context)
#             logger.info("Template rendered successfully")
#         except TemplateDoesNotExist:
#             logger.error(f"Template not found: {template_name}")
#             raise
#
#         text_content = strip_tags(html_content)
#
#         # Log email settings
#         logger.info(f"Email settings check - "
#                     f"EMAIL_HOST: {settings.EMAIL_HOST}, "
#                     f"EMAIL_PORT: {settings.EMAIL_PORT}")
#
#         msg = EmailMultiAlternatives(
#             subject="Welcome to TimeSyncPro",
#             body=text_content,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[recipient_email],
#         )
#
#         msg.attach_alternative(html_content, "text/html")
#
#         logger.info("Attempting to send email...")
#         msg.send()
#         logger.info(f"Welcome email successfully sent to {recipient_email}")
#
#         return True
#
#     except Exception as e:
#         logger.error(f"Failed to send welcome email: {str(e)}", exc_info=True)
#         # Log the full traceback
#         import traceback
#         logger.error(f"Traceback: {traceback.format_exc()}")
#         raise self.retry(exc=e)

# @shared_task(
#     bind=True,
#     autoretry_for=(Exception,),
#     retry_backoff=True,
#     retry_kwargs={"max_retries": 5},
#     queue="emails",
# )
# def send_welcome_email(
#     self,
#     recipient_email,
#     user_full_name,
# ):
#     try:
#         print("Sending welcome email")
#         context = {
#             "full_name": user_full_name,
#         }
#
#         html_content = render_to_string(
#             "email_templates/welcome_email.html", context
#         )
#
#         text_content = strip_tags(html_content)
#
#         subject = "Welcome to TimeSyncPro"
#
#         msg = EmailMultiAlternatives(
#             subject=subject,
#             body=text_content,
#             from_email="timesyncpro@donotreply.com",
#             to=[recipient_email],
#         )
#
#         print(f"Preparing to send email to: {recipient_email}")
#
#         msg.attach_alternative(html_content, "text/html")
#
#         msg.send()
#
#         logger.info(f"Welcome email sent successfully to {recipient_email}")
#         return True
#
#     except Exception as e:
#         logger.error(f"Failed to send welcome email: {str(e)}")
#         raise self.retry(exc=e)
