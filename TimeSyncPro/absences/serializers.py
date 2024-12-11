from rest_framework import serializers

from TimeSyncPro.absences.models import Holiday


class HolidayStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ("status", "review_reason", "reviewed_by")

    def validate(self, data):
        data = super().validate(data)
        request = self.context.get('request')
        holiday = self.instance
        new_status = data.get("status")
        current_status = holiday.status

        if current_status in [Holiday.StatusChoices.CANCELLED, Holiday.StatusChoices.DENIED]:
            raise serializers.ValidationError("You cannot change the status of a cancelled holiday request.")

        if new_status == Holiday.StatusChoices.CANCELLED and current_status not in [
            Holiday.StatusChoices.APPROVED,
            Holiday.StatusChoices.PENDING,
        ]:
            raise serializers.ValidationError(
                f"You can only cancel a holiday request if it is Approved or Pending. Current status: {current_status}."
            )

        if new_status == Holiday.StatusChoices.DENIED and current_status != Holiday.StatusChoices.PENDING:
            raise serializers.ValidationError(
                f"You can only deny a holiday request if it is Pending. Current status: {current_status}."
            )

        if new_status == Holiday.StatusChoices.DENIED and not data.get("review_reason"):
            raise serializers.ValidationError("A review reason is required to deny the holiday request.")

        if new_status in [Holiday.StatusChoices.APPROVED, Holiday.StatusChoices.DENIED]:
            data['reviewed_by'] = request.user.profile

        return data

