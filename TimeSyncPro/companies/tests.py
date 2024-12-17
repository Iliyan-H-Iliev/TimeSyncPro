from django.test import TestCase

#
# # Create your tests here.
# import smtplib
#
# # Test SMTP connection directly
# server = smtplib.SMTP('127.0.0.1', 1025)
# try:
#     server.sendmail(
#         'from@example.com',
#         ['to@example.com'],
#         'Subject: test\n\nThis is a test email'
#     )
#     print("Email sent successfully")
# except Exception as e:
#     print(f"Error: {e}")
# finally:
#     server.quit()


from django.test import TestCase
from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend


class EmailTests(TestCase):
    def test_email_sending(self):
        connection = EmailBackend(
            host="127.0.0.1",
            port=1025,
            username=None,
            password=None,
            use_tls=False,
            use_ssl=False,
            fail_silently=False,
        )

        email = EmailMessage(
            subject="Test Subject",
            body="Test Message",
            from_email="from@example.com",
            to=["to@example.com"],
            connection=connection,
        )

        email.send()
