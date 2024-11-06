import logging

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models

from TimeSyncPro.history.models import History
logger = logging.getLogger(__name__)


class HistoryMixin(models.Model):
    class Meta:
        abstract = True

    tracked_fields = []

    def _get_tracked_fields(self):
        """Get list of tracked fields from Meta class"""
        if hasattr(self._meta, 'tracked_fields'):
            return self._meta.tracked_fields
        return self.tracked_fields

    def _get_state(self):
        """Get current state of tracked fields"""
        state = {}
        tracked_fields = self._get_tracked_fields()

        for field_name in tracked_fields:
            if not hasattr(self, field_name):
                continue

            try:
                field = self._meta.get_field(field_name)
                value = getattr(self, field_name)

                if isinstance(field, models.ForeignKey):
                    value = value.pk if value else None
                elif isinstance(field, models.ManyToManyField):
                    value = list(value.values_list('id', flat=True)) if value else []
                elif hasattr(value, 'code'):
                    value = value.code
                elif isinstance(value, (list, tuple)):
                    value = list(value)

                state[field_name] = value
            except Exception as e:
                logger.warning(f"Error getting state for field {field_name}: {str(e)}")
                continue

        return state

    def _get_original_state(self):
        """Get original state from database with proper field handling"""
        if not self.pk:
            return {}

        query = self.__class__.objects

        # Add select_related for ForeignKey fields
        for field_name in self._get_tracked_fields():
            try:
                field = self._meta.get_field(field_name)
                if isinstance(field, models.ForeignKey):
                    query = query.select_related(field_name)
            except Exception:
                continue

        original = query.filter(pk=self.pk).first()
        return original._get_state() if original else {}

    def _create_history(self, action, changes=None, user=None):
        """Creates history record handling errors gracefully"""
        try:
            # Determine correct user
            if isinstance(self, apps.get_model(settings.AUTH_USER_MODEL)) and action == 'register':
                history_user = self
            else:
                history_user = user

            History.objects.create(
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.pk,  # Fixed: was content_type_id
                action=action,
                changed_by=history_user,
                changes=changes or {}
            )
        except Exception as e:
            logger.error(f"Error creating history for {self.__class__.__name__}: {str(e)}")

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        is_new = not self.pk

        # Get original state before save
        original_state = {} if is_new else self._get_original_state()

        try:
            UserModel = apps.get_model(settings.AUTH_USER_MODEL)
            is_self_registration = (
                is_new and
                isinstance(self, UserModel) and
                not user
            )

            # Call parent's save
            super().save(*args, **kwargs)

            # Create history after save
            if is_self_registration:
                self._create_history('register',
                                   {'email': {'old': None, 'new': self.email}},
                                   user=self)
            elif is_new:
                current_state = self._get_state()
                changes = {
                    field: {
                        'old': None,
                        'new': str(value) if value is not None else None
                    }
                    for field, value in current_state.items()
                }
                self._create_history('create', changes, user=user)
            else:
                current_state = self._get_state()
                changes = {
                    field: {
                        'old': str(original_state.get(field)) if original_state.get(field) is not None else None,
                        'new': str(new_value) if new_value is not None else None
                    }
                    for field, new_value in current_state.items()
                    if original_state.get(field) != new_value
                }

                if changes:
                    self._create_history('update', changes, user=user)

        except Exception as e:
            logger.error(f"Error in history tracking: {str(e)}")
            super().save(*args, **kwargs)

    def delete(self, user=None, *args, **kwargs):
        """Track model deletion"""
        try:
            state = self._get_state()
            changes = {
                field: {
                    'old': str(value) if value is not None else None,
                    'new': None
                }
                for field, value in state.items()
            }

            # Create deletion history before actual deletion
            self._create_history('delete', changes=changes, user=user)

            # Perform the deletion
            return super().delete(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error tracking deletion: {str(e)}")
            return super().delete(*args, **kwargs)

