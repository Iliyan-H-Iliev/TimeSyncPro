# from celery import shared_task
# from django.db.models.signals import post_save
# from django.dispatch import receiver
#
# from TimeSyncPro.shifts.models import Shift
# from .tasks import generate_shift_working_dates_task
#
#
# @receiver(post_save, sender=Shift)
# def handle_shift_save(sender, instance, created, **kwargs):
#     if created:
#         generate_shift_working_dates_task.delay(instance.id)
#     else:
#         generate_shift_working_dates_task.delay(instance.id, is_edit=True)
