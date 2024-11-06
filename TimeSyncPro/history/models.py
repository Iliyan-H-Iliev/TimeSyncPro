from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.contrib.contenttypes.models import ContentType


class History(models.Model):
    ACTIONS = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('register', 'Registered')
    ]

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )

    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    timestamp = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    action = models.CharField(
        max_length=20,
        choices=ACTIONS,
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='history_changes'
    )

    changes = models.JSONField(
        null=True,
        help_text="{'field': {'old': old_value, 'new': new_value}}"
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),  # Combined index
            models.Index(fields=['timestamp']),
            models.Index(fields=['action']),
        ]
        verbose_name = 'History Record'
        verbose_name_plural = 'History Records'

    def __str__(self):
        model_name = self.content_type.model
        by_who = self.changed_by.email if self.changed_by else 'Self Registration'
        return f"{model_name} - {self.action} by {by_who}"

    @property
    def change_summary(self):
        """Returns human-readable summary of changes"""
        if not self.changes:
            return "No changes recorded"

        summaries = []
        for field, change in self.changes.items():
            old = change.get('old', 'None')
            new = change.get('new', 'None')
            summaries.append(f"{field}: {old} → {new}")

        return ", ".join(summaries)

    @classmethod
    def get_for_object(cls, obj):
        """Get all history for a specific object"""
        return cls.objects.filter(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id
        ).select_related('changed_by')

    @classmethod
    def get_recent(cls, limit=10):
        """Get recent history across all models"""
        return cls.objects.select_related(
            'content_type', 'changed_by'
        ).order_by('-timestamp')[:limit]

    @classmethod
    def get_by_user(cls, user):
        """Get all changes made by a specific user"""
        return cls.objects.filter(
            changed_by=user
        ).select_related('content_type', 'changed_by')
