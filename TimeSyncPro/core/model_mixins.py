from django.db import models


class CreatedModifiedMixin(models.Model):

    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class EmailFormatingMixin:

    @staticmethod
    def formated_email(email):
        if email is None:
            return None
        return email.lower()