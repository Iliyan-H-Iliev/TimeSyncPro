from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

from TimeSyncPro.accounts.models import Company, Employee


class Command(BaseCommand):
    help = "Create user groups and assign permissions"

    def handle(self, *args, **options):
        # Create groups
        company_group, created = Group.objects.get_or_create(name="Company")
        hr_group, created = Group.objects.get_or_create(name="HR")
        manager_group, created = Group.objects.get_or_create(name="Manager")
        team_leader_group, created = Group.objects.get_or_create(name="Team Leader")
        staff_group, created = Group.objects.get_or_create(name="Staff")

        # Fetch permissions
        company_permissions = Permission.objects.filter(
            codename__in=[
                "change_company",
                "delete_company",
                "view_company",
                "add_user",
                "change_user",
                "delete_user",
                "view_user",
                "add_hr",
                "change_hr",
                "delete_hr",
                "view_hr",
                "add_manager",
                "change_manager",
                "delete_manager",
                "view_manager",
                "add_team_leader",
                "change_team_leader",
                "delete_team_leader",
                "view_team_leader",
                "add_staff",
                "change_staff",
                "delete_staff",
                "view_staff",
                "add_employee",
                "change_employee",
                "delete_employee",
                "view_employee",
                "add_shift_pattern",
                "change_shift_pattern",
                "delete_shift_pattern",
                "view_shift_pattern",
                "add_team",
                "change_team",
                "delete_team",
                "view_team",
            ]
        )

        hr_permissions = Permission.objects.filter(
            codename__in=[
                "add_user",
                "change_user",
                "delete_user",
                "view_user",
                "view_hr",
                "add_manager",
                "change_manager",
                "delete_manager",
                "view_manager",
                "add_teamleader"
                "change_teamleader",
                "delete_teamleader",
                "view_teamleader",
                "add_employee",
                "change_employee",
                "delete_employee",
                "view_employee",
                "add_shift_pattern",
                "change_shift_pattern",
                "delete_shift_pattern",
                "view_shift_pattern",
                "add_team",
                "change_team",
                "delete_team",
                "view_team",
            ]
        )

        manager_permissions = Permission.objects.filter(
            codename__in=[
                "change_employee",
                "view_employee",
            ]
        )

        team_leader_permissions = Permission.objects.filter(
            codename__in=[
                "change_employee",
                "view_employee",
            ]
        )

        staff_permissions = Permission.objects.filter(
            codename__in=[
                "view_employee",
            ]
        )

        # Assign permissions to groups
        company_group.permissions.set(company_permissions)
        hr_group.permissions.set(hr_permissions)
        manager_group.permissions.set(manager_permissions)
        staff_group.permissions.set(staff_permissions)

        # Assign users to groups
        for company in Company.objects.all():
            company.user.groups.add(company_group)
        for employee in Employee.objects.all():
            if employee.role == Employee.EmployeeRole.HR:
                employee.user.groups.add(hr_group)
            elif employee.role == Employee.EmployeeRole.MANAGER:
                employee.user.groups.add(manager_group)
            elif employee.role == Employee.EmployeeRole.TEAM_LEADER:
                employee.user.groups.add(team_leader_group)
            elif employee.role == Employee.EmployeeRole.STAFF:
                employee.user.groups.add(staff_group)

        self.stdout.write(self.style.SUCCESS("Successfully created groups and assigned permissions"))
