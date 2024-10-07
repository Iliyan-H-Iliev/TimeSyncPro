import uuid

from django.utils.text import slugify




def capitalize_words(string):
    return " ".join([word.capitalize() for word in string.split()])
