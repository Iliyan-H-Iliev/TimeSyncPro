import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from TimeSyncPro.accounts.models import Profile
from TimeSyncPro.common.models import Address

logger = logging.getLogger(__name__)

UserModel = get_user_model()


# TODO use this signal to assign user to group
@receiver(post_save, sender=Profile)
def assign_user_to_group(sender, instance, created, **kwargs):
    def assign_group():
        try:
            if instance.group_name:
                group, _ = Group.objects.get_or_create(name=instance.group_name)
                user = instance.user

                user.groups.clear()
                user.groups.add(group)

                # user.is_staff = instance.is_company_admin
                user.save()

        except Exception as e:
            logger.error(f"Failed to assign group to user {instance.user.id}: {str(e)}")

    transaction.on_commit(assign_group)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance: UserModel, created: bool, **kwargs):

    if not created:
        return

    if hasattr(instance, "skip_profile_creation") and instance.skip_profile_creation:
        return

    try:
        Profile.objects.get(user=instance)
    except Profile.DoesNotExist:
        with transaction.atomic():
            address = Address.objects.create()
            Profile.objects.create(
                user=instance,
                address=address,
            )
