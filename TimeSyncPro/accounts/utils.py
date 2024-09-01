import uuid

from django.utils.text import slugify


def generate_unique_slug(instance, field, max_length):
    base_slug = slugify(getattr(instance, field).split("@")[0])[:max_length - 8]
    unique_slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"  # Append first 8 characters of a UUID

    # Ensure the slug fits within the max_length
    return unique_slug[:max_length]


def format_company_name(company_name):
    return company_name.lower().replace(" ", "")


def format_email(email):
    return email.lower()


def capitalize_words(string):
    return " ".join([word.capitalize() for word in string.split()])
