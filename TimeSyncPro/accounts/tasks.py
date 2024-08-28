# from celery import shared_task
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.conf import settings
# from django.urls import reverse
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
# def send_activation_email(user_email, activation_url):
#     subject = "Activate Your Account and Set Password"
#     message = f"Please click the following link to activate your account and set your password: {activation_url}"
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])
#

