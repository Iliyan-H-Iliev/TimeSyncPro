from rest_framework import serializers

from TimeSyncPro.history.models import History


class HistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.StringRelatedField()
    change_summary = serializers.CharField(read_only=True)

    class Meta:
        model = History
        fields = ["timestamp", "action", "changed_by", "changes", "change_summary"]
