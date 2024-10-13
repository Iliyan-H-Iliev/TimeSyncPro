import random
from django import template
from django.utils.lorem_ipsum import paragraphs
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def random_lorem_paragraphs():

    paragraph_count = random.randint(2, 5)

    lorem_paragraphs = paragraphs(paragraph_count)

    return mark_safe(''.join([f'<p>{para}</p>' for para in lorem_paragraphs]))
