class DynamicPermissionMixin:

    @staticmethod
    def get_object_class_name(obj):
        if obj.__class__.__name__ == 'TSPUser':
            if obj.profile.is_company_admin:
                return 'company_admin'

            if obj.profile.role:
                return obj.profile.role.lower().replace(' ', '_')

            if obj.is_superuser:
                return 'superuser'

            if obj.is_staff:
                return 'staff'

        return obj.__class__.__name__.lower()

    def get_action_permission_codename(self, obj, action: str):
        obj_class_name = self.get_object_class_name(obj)
        return f"{action}_{obj_class_name}"

    def get_action_permission(self, obj, action: str):
        obj_app_label = obj._meta.app_label
        permission_codename = self.get_action_permission_codename(obj, action)
        return f"{obj_app_label}.{permission_codename}"

    def has_needed_permission(self, user, obj, action):
        try:
            needed_permission_codename = self.get_action_permission_codename(obj, action)
            # Use cached permissions
            if hasattr(user, 'user_permissions_codenames'):
                return needed_permission_codename in user.user_permissions_codenames

            # Fallback if not cached
            all_permissions = user.get_all_permissions()
            user.user_permissions_codenames = {
                perm.split('.')[-1] for perm in all_permissions
            }
            return needed_permission_codename in user.user_permissions_codenames

        except AttributeError:
            return False


class EmployeeButtonPermissionMixin:
    def is_holiday_approver(self, target_profile):
        return self.request.user.profile == target_profile.get_holiday_approver()

    def get_button_permissions(self):
        """Get permissions for showing/hiding buttons"""
        user = self.request.user
        target_profile = self.get_target_profile()

        return {
            'can_view_requests': any([
                user.has_perm('absences.view_all_holidays_requests'),
                user.has_perm('absences.view_department_holidays_requests') and self.is_same_department(target_profile),
                user.has_perm('absences.view_team_holidays_requests') and self.is_same_team(target_profile),
                self.request.user.profile == target_profile.get_holiday_approver()  # Direct check
            ]),
            'can_view_absences': any([
                user.has_perm('absences.view_all_absences'),
                user.has_perm('absences.view_department_absences') and self.is_same_department(target_profile),
                user.has_perm('absences.view_team_absences') and self.is_same_team(target_profile)
            ]),
            'is_holiday_approver': self.request.user.profile == target_profile.get_holiday_approver()  # Direct check
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_button_permissions())
        return context