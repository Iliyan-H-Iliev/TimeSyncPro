from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache


class History(models.Model):
    ACTIONS = [
        ("create", "Created"),
        ("update", "Updated"),
        ("delete", "Deleted"),
        ("register", "Registered"),
    ]

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )

    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

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
        related_name="history_changes",
    )

    changes = models.JSONField(
        null=True, help_text="{'field': {'old': old_value, 'new': new_value}}"
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),  # Combined index
            models.Index(fields=["timestamp"]),
            models.Index(fields=["action"]),
        ]
        verbose_name = "History Record"
        verbose_name_plural = "History Records"

    def __str__(self):
        model_name = self.content_type.model
        by_who = self.changed_by.email if self.changed_by else "Self Registration"
        return f"{model_name} - {self.action} by {by_who}"

    @classmethod
    def get_content_type(cls, model_class):
        """Cache ContentType lookups"""
        cache_key = f"content_type_{model_class._meta.model_name}"
        content_type = cache.get(cache_key)

        if content_type is None:
            content_type = ContentType.objects.get_for_model(model_class)
            cache.set(cache_key, content_type, 3600)  # Cache for 1 hour

        return content_type

    @property
    def change_summary(self):
        """Returns human-readable summary of changes"""
        if not self.changes:
            return "No changes recorded"

        def format_value(value, field_name):
            if value == "None" or value is None:
                return ""

            # Get the field from model
            try:
                current_filed = self.content_type.model_class()._meta.get_field(
                    field_name
                )

                # Handle foreign keys
                if isinstance(current_filed, models.ForeignKey):
                    related_model = current_filed.related_model
                    try:
                        obj = related_model.objects.get(pk=value)
                        return str(obj)
                    except:
                        return value

                # Handle boolean fields
                elif isinstance(current_filed, models.BooleanField):
                    return "Yes" if value else "No"

                # Handle choice fields
                elif hasattr(current_filed, "choices") and current_filed.choices:
                    choices_dict = dict(current_filed.choices)
                    return choices_dict.get(value, value)

            except:
                pass

            return str(value)

        summaries = []
        for field, change in self.changes.items():
            old = format_value(change.get("old"), field)
            new = format_value(change.get("new"), field)
            field = field.replace("_", " ").title()
            separator = " → "

            if not old:
                separator = ""

            summaries.append(f"{field}: {old} {separator} {new}")

        return ", ".join(summaries)

    @classmethod
    def get_for_object(cls, obj):
        """Get all history for a specific object"""
        content_type = cls.get_content_type(obj.__class__)  # Use cached content_type
        return (
            cls.objects.filter(
                content_type=content_type, object_id=obj.id  # Use cached version
            )
            .select_related("changed_by", "content_type")
            .order_by("-timestamp")
        )

    @classmethod
    def get_recent(cls, limit=10):
        """Get recent history across all models"""
        return cls.objects.select_related("content_type", "changed_by").order_by(
            "-timestamp"
        )[:limit]

    @classmethod
    def get_by_user(cls, user):
        """Get all changes made by a specific user"""
        return cls.objects.filter(changed_by=user).select_related(
            "content_type", "changed_by"
        )
