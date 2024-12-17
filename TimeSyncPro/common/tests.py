from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from TimeSyncPro.absences.models import Absence
from TimeSyncPro.accounts.models import Profile
from TimeSyncPro.companies.models import Company

UserModel = get_user_model()


class IntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserModel.objects.create_user(
            email="testuser@abv.bg", password="testpassword"
        )
        cls.company = Company.objects.create(
            name="Test Company",
            slug="test-company",
            annual_leave=20,
            time_zone="Europe/Sofia",
            max_carryover_leave=5,
            minimum_leave_notice=5,
            maximum_leave_days_per_request=5,
            working_on_local_holidays=False,
        )

        cls.profile, created = Profile.objects.get_or_create(
            user=cls.user,
            defaults={
                "company": cls.company,
                "first_name": "Test",
                "last_name": "User",
                "role": "staff",
                "employee_id": "12345",
                "date_of_hire": "2021-01-01",
                "remaining_leave_days": 20,
                "phone_number": "1234567890",
                "date_of_birth": "1990-01-01",
            },
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="testuser@abv.bg", password="testpassword")

    def test_home_page(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 302)

    def test_about_page(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)

    def test_contact_page(self):
        response = self.client.get(reverse("contact"))
        self.assertEqual(response.status_code, 200)

    def test_create_profile_company(self):
        response = self.client.get(
            reverse("create_profile_company", kwargs={"slug": self.user.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_privacy_policy(self):
        response = self.client.get(reverse("privacy_policy"))
        self.assertEqual(response.status_code, 200)

    def test_terms_and_conditions(self):
        response = self.client.get(reverse("terms_and_conditions"))
        self.assertEqual(response.status_code, 200)

    def test_terms_of_use(self):
        response = self.client.get(reverse("terms_of_use"))
        self.assertEqual(response.status_code, 200)

    def test_admin_access(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)

    def test_profile_page(self):
        response = self.client.get(reverse("profile", kwargs={"slug": self.user.slug}))
        self.assertEqual(response.status_code, 200)

    def test_absence_list(self):
        response = self.client.get(
            reverse("company_absences", kwargs={"company_slug": self.company.slug})
        )
        self.assertEqual(response.status_code, 302)

    def test_absence_detail(self):
        absence = Absence.objects.create(
            start_date="2021-01-01",
            end_date="2021-01-03",
            absentee=self.profile,
            absence_type="sick",
            added_by=self.profile,
            reason="Flu",
            days_of_absence=3,
        )
        response = self.client.get(
            reverse(
                "employee_absences",
                kwargs={"slug": self.user.slug, "company_slug": self.company.slug},
            )
        )
        self.assertEqual(response.status_code, 302)

    def test__create_absence_with_correct_data(self):
        response = self.client.post(
            reverse(
                "add_absence",
                kwargs={"slug": self.user.slug, "company_slug": self.company.slug},
            ),
            {
                "start_date": "2021-01-01",
                "end_date": "2021-01-03",
                "absentee": self.profile,
                "absence_type": "sick",
                "added_by": self.profile,
                "reason": "Flu",
                "days_of_absence": 3,
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_absence(self):
        absence = Absence.objects.create(
            start_date="2021-01-01",
            end_date="2021-01-03",
            absentee=self.profile,
            absence_type="sick",
            added_by=self.profile,
            reason="Flu",
            days_of_absence=3,
        )
        response = self.client.post(
            reverse("delete_absence", kwargs={"pk": absence.pk})
        )

        self.assertEqual(response.status_code, 302)

    def test_profile_update(self):
        response = self.client.post(
            reverse("update_profile", kwargs={"slug": self.user.slug}),
            {
                "user": self.user.id,
                "company": self.company.id,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_company_update(self):
        response = self.client.post(
            reverse("update_company", kwargs={"company_slug": self.company.slug}),
            {"name": "Updated Company Name"},
        )
        self.assertEqual(response.status_code, 302)

    def test_user_login(self):
        self.client.logout()
        response = self.client.post(
            reverse("sign_in"),
            {"username": "testuser@abv.bg", "password": "testpassword"},
        )
        self.assertEqual(response.status_code, 302)

    def test_user_registration(self):
        response = self.client.post(
            reverse("sign_up_administrator"),
            {
                "email": "newuserass@abv.bg",
                "password1": "newpassword",
                "password2": "newpassword",
            },
        )
        self.assertEqual(response.status_code, 302)
