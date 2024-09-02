from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from TimeSyncPro.accounts.models import Profile

# from .models import Employee
# from .tasks import send_welcome_email, send_password_reset_email, send_activation_email
#
UserModel = get_user_model()
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


@receiver(post_save, sender=Profile)
def assign_user_to_group(sender, instance, created, **kwargs):
    def assign_group():
        group_name = instance.group_name
        group, group_created = Group.objects.get_or_create(name=group_name)
        instance.user.groups.clear()
        instance.user.groups.add(group)
        instance.user.save()

    transaction.on_commit(assign_group)
