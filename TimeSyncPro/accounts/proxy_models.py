from TimeSyncPro.accounts.models import Employee


class ManagerProxy(Employee):
    class Meta:
        proxy = True

    def assign_task(self, task, employee):
        return f"Manager {self.first_name} assigned task '{task}' to {employee.first_name}"

    def approve_leave(self, leave_request):
        return f"Manager {self.first_name} approved leave request for {leave_request.employee.first_name}"


class HRProxy(Employee):
    class Meta:
        proxy = True

    def process_leave_request(self, leave_request):
        return f"HR {self.first_name} processed leave request for {leave_request.employee.first_name}"

    def update_employee_info(self, employee, **updates):
        for key, value in updates.items():
            setattr(employee, key, value)
        employee.save()
        return f"HR {self.first_name} updated info for {employee.first_name}"


class TeamLeaderProxy(Employee):
    class Meta:
        proxy = True

    def schedule_team_meeting(self, date, time):
        return f"Team Leader {self.first_name} scheduled a team meeting for {date} at {time}"


class StaffProxy(Employee):
    class Meta:
        proxy = True

    def request_leave(self, start_date, end_date):
        return f"Staff {self.first_name} requested leave from {start_date} to {end_date}"
