from django.apps import AppConfig

from TimeSyncPro import accounts


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'TimeSyncPro.accounts'

    def ready(self):
        import TimeSyncPro.accounts.signals
