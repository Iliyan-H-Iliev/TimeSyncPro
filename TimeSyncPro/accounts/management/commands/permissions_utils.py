from django.contrib.auth.models import Permission

ADMIN_PERMISSIONS = [
    'add_user', 'change_user', 'view_user', 'delete_user',
    'add_profile', 'change_profile', 'view_profile', 'delete_profile',
    'add_holiday', 'change_holiday', 'view_holiday', 'delete_holiday',
    'add_absence', 'change_absence', 'view_absence', 'delete_absence',
]


def get_admin_permissions():
    return Permission.objects.filter(codename__in=ADMIN_PERMISSIONS)