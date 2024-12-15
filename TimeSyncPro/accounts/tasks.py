import logging

from celery import shared_task
from django.core.mail import send_mail, EmailMessage
from django.core.mail.backends.console import EmailBackend
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse


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
#
#
# @shared_task
# def send_activation_email(email, domain, protocol, relative_url):
#     try:
#         activation_url = f'{protocol}://{domain}{relative_url}'
#
#         print(f"Sending email to: {email}")  # Debug print
#         print(f"Activation URL: {activation_url}")  # Debug print
#
#         send_mail(
#             'Activate your account',
#             f'Click here to activate your account: {activation_url}',
#             'noreply@example.com',
#             [email],
#             fail_silently=False,
#         )
#
#         print("Email sent successfully")
#
#         logger.info(f"Activation email sent to {email}.")
#     except Exception as e:
#         logger.error(f"Failed to send activation email to {email}: {str(e)}")
#

# @shared_task
# def send_activation_email(email, domain, protocol, relative_url):
#     logger.info("Starting email task")
#     activation_url = f'{protocol}://{domain}{relative_url}'
#
#     connection = EmailBackend(
#         host='mailhog',  # Use container name
#         port=1025,
#         username=None,
#         password=None,
#         use_tls=False,
#         use_ssl=False
#     )
#
#     email_message = EmailMessage(
#         subject='Activate your account',
#         body=f'Click here to activate: {activation_url}',
#         from_email='from@example.com',
#         to=[email],
#         connection=connection
#     )
#
#     try:
#         email_message.send()
#         logger.info(f"Email sent to {email}")
#         return f"Email sent successfully to {email}"
#     except Exception as e:
#         logger.error(f"Error sending email: {str(e)}")
#         raise  # Raise the exception to see the actual error

# @shared_task
# def send_activation_email(email, domain, protocol, relative_url):
#     import smtplib
#     logger.info("Testing SMTP connection directly")
#
#     try:
#         # Try direct SMTP connection
#         server = smtplib.SMTP('mailhog', 1025)  # or whatever host you're using
#         server.sendmail(
#             'from@example.com',
#             [email],
#             'Test message from Celery'
#         )
#         server.quit()
#         logger.info("Direct SMTP test successful")
#     except Exception as e:
#         logger.error(f"Direct SMTP test failed: {str(e)}")
#         raise

# @shared_task
# def send_activation_email(email, domain, protocol, relative_url):
#     import smtplib
#     logger.info("Testing SMTP connection directly")
#
#     try:
#         # Use localhost since Celery is running on host machine
#         server = smtplib.SMTP('localhost', 1025)  # or '127.0.0.1'
#         server.sendmail(
#             'from@example.com',
#             [email],
#             'Test message from Celery'
#         )
#         server.quit()
#         logger.info("Direct SMTP test successful")
#     except Exception as e:
#         logger.error(f"Direct SMTP test failed: {str(e)}")
#         raise
#
#     # Rest of your email code
#     activation_url = f'{protocol}://{domain}{relative_url}'
#
#     connection = EmailBackend(
#         host='localhost',  # Use localhost here too
#         port=1025,
#         username=None,
#         password=None,
#         use_tls=False,
#         use_ssl=False
#     )
#
#     email_message = EmailMessage(
#         subject='Activate your account',
#         body=f'Click here to activate: {activation_url}',
#         from_email='from@example.com',
#         to=[email],
#         connection=connection
#     )
#
#     try:
#         email_message.send()
#         logger.info(f"Email sent to {email}")
#         return f"Email sent successfully to {email}"
#     except Exception as e:
#         logger.error(f"Error sending email: {str(e)}")
#         raise


# @shared_task
# def send_activation_email(email, domain, protocol, relative_url):
#     logger.info("Starting email task")
#     activation_url = f'{protocol}://{domain}{relative_url}'
#
#     connection = EmailBackend(
#         host='mailhog',
#         port=1025,
#         username=None,
#         password=None,
#         use_tls=False,
#         use_ssl=False
#     )
#
#     email_message = EmailMessage(
#         subject='Activate your account',
#         body=f'Click here to activate: {activation_url}',
#         from_email='from@example.com',
#         to=[email],
#         connection=connection
#     )
#
#     try:
#         email_message.send()
#         logger.info(f"Email sent to {email}")
#         return f"Email sent successfully to {email}"
#     except Exception as e:
#         logger.error(f"Error sending email: {str(e)}")
#         raise


@shared_task
def send_activation_email(email, domain, protocol, relative_url):
    try:
        activation_url = f"{protocol}://{domain}{relative_url}"
        subject = 'Activate your account'
        message = f'Please click the following link to activate your account: {activation_url}'

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER or 'noreply@example.com',
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False
