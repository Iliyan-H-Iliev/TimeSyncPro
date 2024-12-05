import random
from django import template
from django.utils.lorem_ipsum import paragraphs
from django.utils.safestring import mark_safe
import json

register = template.Library()


@register.simple_tag
def random_lorem_paragraphs():

    paragraph_count = random.randint(2, 5)

    lorem_paragraphs = paragraphs(paragraph_count)

    return mark_safe(''.join([f'<p>{para}</p>' for para in lorem_paragraphs]))


@register.simple_tag
def url_query_append_tag(request, field, value):
    # field = 'page'; value = 2
    dict_ = request.GET.copy()  # request.GET -> {'pet_name': 'george'} -> ?pet_name=george
    dict_[field] = value  #  {'pet_name': 'george', 'page': 2}
    return dict_.urlencode()  # {'pet_name': 'george', 'page': 2} -> pet_name=george&page=2


@register.filter(is_safe=True)
def to_json(value):
    return json.dumps(value)
