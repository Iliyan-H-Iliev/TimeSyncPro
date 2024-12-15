from django import template
from django.forms.fields import Field
from django.template.defaultfilters import title
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def placeholder(field, token):
    try:
        if isinstance(field.field, Field):
            field.field.widget.attrs['placeholder'] = str(token)
        return field
    except (AttributeError, TypeError):
        return field


@register.filter
def add_class(field, class_name):

    try:
        if isinstance(field.field, Field):
            existing_classes = field.field.widget.attrs.get('class', '')
            if existing_classes:
                class_name = f"{existing_classes} {class_name}"
            field.field.widget.attrs['class'] = class_name
        return field
    except (AttributeError, TypeError):
        return field


@register.simple_tag
def render_field(field, **kwargs):
    try:

        if isinstance(field.field, Field):
            wrapper_class = kwargs.pop('wrapper_class', '')
            label_class = kwargs.pop('label_class', '')
            is_readonly = (
                    field.name in getattr(field.form, 'readonly_fields', []) or
                    getattr(field.field.widget, 'readonly', False) or
                    field.field.widget.attrs.get('readonly') or
                    field.field.widget.attrs.get('disabled')
            )

            # Add required class to label if field is required
            if field.field.required and not is_readonly:
                label_class += ' required-label'

            if is_readonly:
                kwargs["class"] = kwargs.get("class", "") + " read-only"

            field.field.widget.attrs.update(kwargs)

            html = f'<div class="{wrapper_class}">'
            html += f'<div class="wrap-label-field">'
            if field.label:
                html += f'<label class="{label_class}">{field.label}</label>'
            html += str(field)
            html += '</div>'
            if field.errors:
                html += f'<div class="field-errors">{" ".join(field.errors)}</div>'
            if field.help_text:
                html += f'<small class="form-text text-muted">{field.help_text}</small>'
            html += '</div>'
            return mark_safe(html)
        return field
    except (AttributeError, TypeError):
        return field
