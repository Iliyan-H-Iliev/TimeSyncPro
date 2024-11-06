from django.contrib import admin
from .models import History


@admin.register(History)
class ModelHistoryAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'action', 'changed_by', 'timestamp']
    list_filter = ['content_type', 'action', 'timestamp']
    search_fields = ['changed_by__email', 'changes']
    readonly_fields = ['content_type', 'action', 'changed_by', 'timestamp', 'changes']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
