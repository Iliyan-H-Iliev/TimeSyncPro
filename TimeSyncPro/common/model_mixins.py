from django.db import models

from TimeSyncPro.common.utils import format_email


class CreatedModifiedMixin(models.Model):

    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class EmailFormatingMixin:

    @staticmethod
    def format_email(email):
        return format_email(email)
