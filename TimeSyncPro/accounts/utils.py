import uuid

from django.utils.text import slugify


def generate_unique_slug(full_name, max_length):
    base_slug = slugify(full_name)[:max_length - 9]
    unique_slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"

    return unique_slug[:max_length]





def capitalize_words(string):
    return " ".join([word.capitalize() for word in string.split()])
