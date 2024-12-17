from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

from TimeSyncPro.accounts.management.commands.permissions_utils import get_admin_permissions
from TimeSyncPro.accounts.models import Profile


class Command(BaseCommand):
    help = "Create user groups and assign permissions"

    def handle(self, *args, **options):

        company_administrator_group, created = Group.objects.get_or_create(name="Company_Admin")
        hr_group, created = Group.objects.get_or_create(name="HR")
        manager_group, created = Group.objects.get_or_create(name="Manager")
        team_leader_group, created = Group.objects.get_or_create(name="Team Leader")
        staff_group, created = Group.objects.get_or_create(name="Staff")

        company_admin_permissions = Permission.objects.filter(
            codename__in=[
                "add_company",
                "change_company",
                "delete_company",
                "view_company",
                "add_user",
                "change_user",
                "delete_user",
                "view_user",
                "activate_user",
                "deactivate_user",
                "reset_user_password",
                "add_company_admin",
                "change_company_admin",
                "delete_company_admin",
                "view_company_admin",
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
                "add_department",
                "change_department",
                "delete_department",
                "view_department",
                "add_shift",
                "change_shift",
                "delete_shift",
                "view_shift",
                "add_team",
                "change_team",
                "delete_team",
                "view_team",
                "add_employee",
                "change_employee",
                "delete_employee",
                "view_employee",
                "view_employees",
                "add_department",
                "change_department",
                "delete_department",
                "view_department",
                "view_all_holidays_requests",
                "update_holiday_requests_status",
                "view_absences",
                "add_absence",
                "view_all_absences",
                "view_all_employees",
                "generate_all_reports",
                "generate_reports",
                "generate_all_reports",
                "view_history",
            ]
        )

        hr_permissions = Permission.objects.filter(
            codename__in=[
                "view_company",
                "view_employee",
                "add_user",
                "change_user",
                "delete_user",
                "view_user",
                "activate_user",
                "deactivate_user",
                "reset_user_password",
                "view_hr",
                "add_manager",
                "change_manager",
                "delete_manager",
                "view_manager",
                "add_teamleader",
                "change_teamleader",
                "delete_teamleader",
                "view_teamleader",
                "add_employee",
                "change_employee",
                "delete_employee",
                "view_employee",
                "view_employees",
                "add_department",
                "change_department",
                "delete_department",
                "view_department",
                "add_shift",
                "change_shift",
                "delete_shift",
                "view_shift",
                "add_team",
                "change_team",
                "delete_team",
                "view_team",
                "view_all_holidays_requests",
                "view_holidays_requests",
                "update_holiday_requests_status",
                "add_absence",
                "view_absences",
                "view_all_absences",
                "view_all_employees",
                "generate_all_reports",
                "generate_reports",
                "generate_all_reports",
                "view_history",
            ]
        )

        manager_permissions = Permission.objects.filter(
            codename__in=[
                "add_staff",
                "change_staff",
                "delete_staff",
                "view_staff",
                "view_company",
                "view_departments",
                "view_shift",
                "view_team",
                "view_employee",
                "change_employee",
                "view_department_employee",
                "view_department_holidays_requests",
                "view_holidays_requests",
                "view_department_absences",
                "view_absences",
                "view_all_employees",
                "view_department_employees",
                "generate_department_reports",
                "generate_reports",
                "generate_department_reports",
            ]
        )

        team_leader_permissions = Permission.objects.filter(
            codename__in=[
                "view_staff",
                "view_company",
                "view_employee",
                "view_shift",
                "view_team",
                "view_all_employees",
                "view_team_employee",
                "view_team_holidays_requests",
                "view_holidays_requests",
                "view_absences",
                "view_team_absences",
                "view_team_employees",
                "generate_team_reports",
                "generate_reports",
                "generate_team_reports",
            ]
        )

        staff_permissions = Permission.objects.filter(
            codename__in=[
            ]
        )

        admin_permissions = list(company_admin_permissions) + list(get_admin_permissions())
        company_administrator_group.permissions.set(admin_permissions)
        hr_group.permissions.set(hr_permissions)
        manager_group.permissions.set(manager_permissions)
        team_leader_group.permissions.set(team_leader_permissions)
        staff_group.permissions.set(staff_permissions)

        for employee in Profile.objects.all():
            if employee.is_company_admin:
                employee.user.groups.add(company_administrator_group)
            elif employee.role == Profile.EmployeeRoles.HR:
                employee.user.groups.add(hr_group)
            elif employee.role == Profile.EmployeeRoles.MANAGER:
                employee.user.groups.add(manager_group)
            elif employee.role == Profile.EmployeeRoles.TEAM_LEADER:
                employee.user.groups.add(team_leader_group)
            elif employee.role == Profile.EmployeeRoles.STAFF:
                employee.user.groups.add(staff_group)

        self.stdout.write(self.style.SUCCESS("Successfully created groups and assigned permissions"))
