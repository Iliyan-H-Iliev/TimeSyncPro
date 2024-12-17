import logging
from celery import shared_task
from django.core.mail import send_mail, EmailMessage
from django.core.mail.backends.console import EmailBackend
from django.template.loader import render_to_string
from django.conf import settings

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
def send_activation_email(email, domain, protocol, relative_url):
    try:
        activation_url = f"{protocol}://{domain}{relative_url}"
        subject = "Activate your account"
        message = f"Please click the following link to activate your account: {activation_url}"

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER or "noreply@example.com",
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False
