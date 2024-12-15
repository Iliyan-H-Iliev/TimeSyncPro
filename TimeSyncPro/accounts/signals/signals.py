import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from TimeSyncPro.accounts.models import Profile
from TimeSyncPro.common.models import Address

logger = logging.getLogger(__name__)

# from .models import Employee
# from .tasks import send_welcome_email, send_password_reset_email, send_activation_email
#
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
#
#
# @receiver(post_save, sender=UserModel)
# def send_welcome_email_after_activation(sender, instance, **kwargs):
#     if instance.is_active and kwargs.get('created', False) is False:
#
#         send_welcome_email.delay(instance.email)
#
#
# @receiver(post_save, sender=UserModel)
# def send_activation_email_after_signup(sender, instance, **kwargs):
#     if not instance.is_active and kwargs.get('created', False) is False:
#
#         send_password_reset_email.delay(instance.email)
#
#
# @receiver(post_save, sender=Employee)
# def send_activation_email_for_new_employee(sender, instance, created, **kwargs):
#     if created and not instance.user.is_active:
#         activation_token = instance.user.generate_activation_token()
#         activation_url = instance.user.company.get_domain() + reverse('activate_and_set_password', args=[activation_token])
#         send_activation_email.delay(instance.user.email, activation_url)


# @receiver(post_save, sender=Profile)
# def assign_user_to_group(sender, instance, created, **kwargs):
#     def assign_group():
#         if instance.group_name:
#             group_name = instance.group_name
#             group, group_created = Group.objects.get_or_create(name=group_name)
#             instance.user.groups.clear()
#             instance.user.groups.add(group)
#             instance.user.save()
#
#     transaction.on_commit(assign_group)


# @receiver(post_save, sender=Profile)
# def update_user_staff_status(sender, instance, **kwargs):
#
#     if instance.user.is_staff != instance.is_company_admin:
#         instance.user.is_staff = instance.is_company_admin
#         instance.user.save(update_fields=['is_staff'])

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance: UserModel, created: bool, **kwargs):

    if not created:
        return

    if hasattr(instance, 'skip_profile_creation') and instance.skip_profile_creation:
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

