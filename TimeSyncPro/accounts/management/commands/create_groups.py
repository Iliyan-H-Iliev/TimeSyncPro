from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

from TimeSyncPro.accounts.models import Profile


class Command(BaseCommand):
    help = "Create user groups and assign permissions"

    def handle(self, *args, **options):
        # Create groups
        company_administrator_group, created = Group.objects.get_or_create(name="Company_Admin")
        hr_group, created = Group.objects.get_or_create(name="HR")
        manager_group, created = Group.objects.get_or_create(name="Manager")
        team_leader_group, created = Group.objects.get_or_create(name="Team Leader")
        staff_group, created = Group.objects.get_or_create(name="Staff")

        # staff_permissions_list = []
        #
        # team_leader_permissions_list = staff_permissions_list + []
        #
        # manager_permissions_list = team_leader_permissions_list + [
        #     "add_manager",
        #     "change_manager",
        #     "delete_manager",
        #     "view_manager",
        #     "add_teamleader"
        #     "change_teamleader",
        #     "delete_teamleader",
        #     "view_teamleader",
        #     "add_employee",
        #     "change_employee",
        #     "delete_employee",
        #     "view_employee",
        #     "add_shift_pattern",
        #     "change_shift_pattern",
        #     "delete_shift_pattern",
        #     "view_shift_pattern",
        #     "add_team",
        #     "change_team",
        #     "delete_team",
        #     "view_team",
        # ]
        #
        # hr_permissions_list = manager_permissions_list + []
        #
        # company_admin_permissions_list = hr_permissions_list + []

        # Fetch permissions
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
                "add_department",
                "change_department",
                "delete_department",
                "view_department",
            ]
        )

        hr_permissions = Permission.objects.filter(
            codename__in=[
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
                "add_teamleader"
                "change_teamleader",
                "delete_teamleader",
                "view_teamleader",
                "add_employee",
                "change_employee",
                "delete_employee",
                "view_employee",
                "add_shift",
                "change_shift",
                "delete_shift",
                "view_shift",
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
        company_administrator_group.permissions.set(company_admin_permissions)
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
