import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from typing import Dict, Any, List, Optional

from TimeSyncPro.history.models import History
from TimeSyncPro.middleware.history_user_middleware import get_current_user

logger = logging.getLogger(__name__)


class HistoryMixin(models.Model):
    class Meta:
        abstract = True

    tracked_fields: List[str] = []

    def _get_tracked_fields(self) -> List[str]:
        """Get list of tracked fields from Meta class or instance"""
        if hasattr(self._meta, 'tracked_fields'):
            return self._meta.tracked_fields
        return self.tracked_fields

    def _format_field_value(self, field: models.Field, value: Any) -> Optional[Any]:
        """Format field value for storage based on field type"""
        try:
            if value is None:
                return None

            if isinstance(field, models.ForeignKey):
                return value.pk if value else None

            elif isinstance(field, models.ManyToManyField):
                return sorted(list(value.values_list('id', flat=True))) if value else []

            elif isinstance(field, (models.DateTimeField, models.DateField)):
                return value.isoformat() if value else None

            elif isinstance(field, models.JSONField):
                return value

            elif hasattr(value, 'code'):
                return value.code

            elif isinstance(value, (list, tuple)):
                return sorted(list(value))

            return str(value)

        except Exception as e:
            logger.warning(f"Error formatting value for field {field.name}: {str(e)}")
            return str(value) if value is not None else None

    def _get_state(self) -> Dict[str, Any]:
        state = {}
        tracked_fields = self._get_tracked_fields()

        for field_name in tracked_fields:
            try:
                if not hasattr(self, field_name):
                    continue

                field = self._meta.get_field(field_name)
                value = getattr(self, field_name)
                state[field_name] = self._format_field_value(field, value)

            except Exception as e:
                logger.warning(
                    f"Error getting state for field {field_name} in {self.__class__.__name__}: {str(e)}"
                )
                continue

        return state

    def _get_original_state(self) -> Dict[str, Any]:
        """Get original state from database with optimized querying"""
        if not self.pk:
            return {}

        try:
            # Build optimized query
            query = self.__class__.objects
            select_related_fields = []
            prefetch_related_fields = []

            for field_name in self._get_tracked_fields():
                try:
                    field = self._meta.get_field(field_name)
                    if isinstance(field, models.ForeignKey):
                        select_related_fields.append(field_name)
                    elif isinstance(field, models.ManyToManyField):
                        prefetch_related_fields.append(field_name)
                except Exception:
                    continue

            if select_related_fields:
                query = query.select_related(*select_related_fields)
            if prefetch_related_fields:
                query = query.prefetch_related(*prefetch_related_fields)

            original = query.filter(pk=self.pk).first()
            return original._get_state() if original else {}

        except Exception as e:
            logger.error(f"Error getting original state: {str(e)}")
            return {}

    def _create_history(self, action: str, changes: Dict[str, Any]) -> None:
        """Creates history record with error handling and validation"""
        try:
            if not changes:  # Skip if no changes
                return

            history_user = get_current_user()
            if not history_user and action == 'register':
                history_user = self if isinstance(self, settings.AUTH_USER_MODEL) else None

            if not self.pk:
                logger.warning("Cannot create history for unsaved instance")
                return

            History.objects.create(
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.pk,
                action=action,
                changed_by=history_user,
                changes=changes
            )

        except Exception as e:
            logger.error(
                f"Error creating history for {self.__class__.__name__} {action}: {str(e)}"
            )

    def save(self, *args, **kwargs) -> None:
        """Save instance with better history tracking control"""
        is_new = not self.pk
        skip_history = kwargs.pop('skip_history', False)
        original_state = {} if is_new else self._get_original_state()

        try:
            # First save the instance
            super().save(*args, **kwargs)

            # Skip history if requested or during certain operations
            if skip_history:
                return

            current_state = self._get_state()

            if is_new:
                changes = {
                    field: {
                        'old': None,
                        'new': value
                    }
                    for field, value in current_state.items()
                }
                self._create_history('create', changes)
            else:
                changes = {
                    field: {
                        'old': original_state.get(field),
                        'new': new_value
                    }
                    for field, new_value in current_state.items()
                    if original_state.get(field) != new_value
                }
                if changes:
                    self._create_history('update', changes)

        except Exception as e:
            logger.error(f"Error in save history tracking: {str(e)}", exc_info=True)
            if not is_new:  # Only retry save if it's an update
                super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> tuple:
        """Delete instance and track deletion"""
        try:
            state = self._get_state()
            changes = {
                field: {
                    'old': value,
                    'new': None
                }
                for field, value in state.items()
            }
            self._create_history('delete', changes=changes)

        except Exception as e:
            logger.error(f"Error in delete history tracking: {str(e)}")

        finally:
            return super().delete(*args, **kwargs)

