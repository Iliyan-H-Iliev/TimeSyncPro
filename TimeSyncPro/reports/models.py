from django.db import models


class Report(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("generate_all_reports", "Can generate all reports"),
            ("generate_department_reports", "Can generate department reports"),
            ("generate_team_reports", "Can generate team reports"),
            ("generate_reports", "Can generate own reports"),
        )
