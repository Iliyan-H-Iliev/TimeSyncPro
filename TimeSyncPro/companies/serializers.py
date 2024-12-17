from rest_framework import serializers

from TimeSyncPro.companies.models import Team


class ShiftTeamsSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="pk", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    holiday_approver_name = serializers.CharField(
        source="holiday_approver.full_name", read_only=True
    )

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "department_name",
            "holiday_approver_name",
            "employees_holidays_at_a_time",
        ]

    def to_representation(self, instance):
        """Add additional formatted data to the serialized output"""
        data = super().to_representation(instance)

        data["employee_count"] = instance.employees.count()

        data["max_holidays"] = (
            f"{instance.employees_holidays_at_a_time} "
            f"{'employee' if instance.employees_holidays_at_a_time == 1 else 'employees'} "
            f"at a time"
        )

        return data
