from django.apps import AppConfig


class AbsencesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "TimeSyncPro.absences"

    def ready(self):
        import TimeSyncPro.absences.signals
