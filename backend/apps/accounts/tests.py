from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from .models import Role

User = get_user_model()


class AuthenticationApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.student_role = Role.objects.get(name=Role.Name.STUDENT)
        self.supervisor_role = Role.objects.get(name=Role.Name.SUPERVISOR)
        self.administrator_role = Role.objects.get(name=Role.Name.ADMINISTRATOR)
        self.student = User.objects.create_user(
            email="student@example.com", name="Student", password="ComplexPass123!", role=self.student_role
        )
        self.supervisor = User.objects.create_user(
            email="supervisor@example.com", name="Supervisor", password="ComplexPass123!", role=self.supervisor_role
        )
        self.administrator = User.objects.create_user(
            email="admin@example.com", name="Administrator", password="ComplexPass123!", role=self.administrator_role
        )
        self.client = APIClient()

    def login(self, email: str, password: str = "ComplexPass123!"):
        return self.client.post(reverse("login"), {"email": email, "password": password}, format="json")

    def authenticate_client(self, user: User):
        response = self.login(user.email)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return response

    def test_registration_creates_student_with_hashed_password(self):
        response = self.client.post(
            reverse("register"),
            {"name": "New Student", "email": "new@example.com", "password": "ComplexPass123!"},
            format="json",
        )
        user = User.objects.get(email="new@example.com")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(user.role.name, Role.Name.STUDENT)
        self.assertTrue(user.check_password("ComplexPass123!"))
        self.assertNotEqual(user.password, "ComplexPass123!")
        self.assertNotIn("password", response.data["user"])

    def test_valid_login_issues_access_and_refresh_tokens(self):
        response = self.login(self.student.email)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], Role.Name.STUDENT)

    def test_invalid_credentials_are_rejected(self):
        response = self.login(self.student.email, "wrong-password")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Invalid email or password.")

    def test_five_failed_logins_trigger_a_temporary_lock(self):
        for _ in range(5):
            self.assertEqual(self.login(self.student.email, "wrong-password").status_code, 401)
        response = self.login(self.student.email)
        self.assertEqual(response.status_code, 429)

    def test_inactive_user_is_denied_login(self):
        self.student.status = User.Status.DEACTIVATED
        self.student.save()
        response = self.login(self.student.email)
        self.assertEqual(response.status_code, 401)

    def test_protected_endpoint_rejects_unauthenticated_requests(self):
        response = self.client.get(reverse("current-user"))
        self.assertEqual(response.status_code, 401)

    def test_token_authentication_returns_current_user(self):
        self.authenticate_client(self.student)
        response = self.client.get(reverse("current-user"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], Role.Name.STUDENT)

    def test_only_administrator_can_change_role_or_status(self):
        for user in (self.student, self.supervisor):
            self.client.credentials()
            self.authenticate_client(user)
            response = self.client.patch(
                reverse("user-management", args=[self.student.pk]), {"status": User.Status.SUSPENDED}, format="json"
            )
            self.assertEqual(response.status_code, 403)

        self.client.credentials()
        self.authenticate_client(self.administrator)
        response = self.client.patch(
            reverse("user-management", args=[self.student.pk]),
            {"role": Role.Name.SUPERVISOR, "status": User.Status.SUSPENDED},
            format="json",
        )
        self.student.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.student.role.name, Role.Name.SUPERVISOR)
        self.assertFalse(self.student.is_active)

    def test_only_administrator_can_list_users(self):
        for user in (self.student, self.supervisor):
            self.client.credentials()
            self.authenticate_client(user)
            self.assertEqual(self.client.get(reverse("user-list")).status_code, 403)

        self.client.credentials()
        self.authenticate_client(self.administrator)
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_refresh_rotation_blacklists_old_refresh_token(self):
        login = self.login(self.student.email)
        refresh = login.data["refresh"]
        refreshed = self.client.post(reverse("token-refresh"), {"refresh": refresh}, format="json")
        self.assertEqual(refreshed.status_code, 200)
        reused = self.client.post(reverse("token-refresh"), {"refresh": refresh}, format="json")
        self.assertEqual(reused.status_code, 401)

    def test_logout_blacklists_refresh_token(self):
        login = self.login(self.student.email)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        logout = self.client.post(reverse("logout"), {"refresh": login.data["refresh"]}, format="json")
        self.assertEqual(logout.status_code, 204)
        reused = self.client.post(reverse("token-refresh"), {"refresh": login.data["refresh"]}, format="json")
        self.assertEqual(reused.status_code, 401)

    def test_malformed_refresh_token_is_rejected(self):
        response = self.client.post(reverse("token-refresh"), {"refresh": "not-a-token"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_expired_access_token_is_rejected(self):
        token = AccessToken.for_user(self.student)
        token.set_exp(from_time=timezone.now(), lifetime=timedelta(seconds=-1))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(reverse("current-user"))
        self.assertEqual(response.status_code, 401)
