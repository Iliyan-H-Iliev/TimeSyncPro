from django.utils.text import slugify


def format_email(email):
    if email is None:
        return None
    return email.lower()
