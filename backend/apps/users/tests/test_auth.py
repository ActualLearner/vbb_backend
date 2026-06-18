from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User

from tests.factories import create_admin, create_facility, create_user


class JWTAuthTests(TestCase):
    def setUp(self):
        self.facility = create_facility(name="Auth", woreda=1)
        self.user = create_user(
            username="pro1",
            facility=self.facility,
            email="pro1@example.com",
            phone_number="+251911111111",
        )
        self.client = APIClient()

    def _login(self, identifier, password="password"):
        return self.client.post(
            "/api/v1/auth/login/",
            {"username": identifier, "password": password},
            format="json",
        )

    def test_obtain_token_by_email(self):
        resp = self._login("pro1@example.com")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertIn("access", resp.json())

    def test_obtain_token_by_phone(self):
        resp = self._login("+251911111111")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_token_carries_role_and_facility_claims(self):
        import jwt

        access = self._login("pro1@example.com").json()["access"]
        payload = jwt.decode(access, options={"verify_signature": False})
        self.assertEqual(payload["role"], User.Role.PROFESSIONAL)
        self.assertEqual(payload["facility_id"], str(self.facility.id))

    def test_inactive_user_rejected(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        resp = self._login("pro1@example.com")
        self.assertEqual(resp.status_code, 401)

    def test_refresh_works(self):
        refresh = self._login("pro1@example.com").json()["refresh"]
        resp = self.client.post(
            "/api/v1/auth/refresh/", {"refresh": refresh}, format="json"
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertIn("access", resp.json())

    def test_protected_endpoint_requires_token(self):
        resp = self.client.get("/api/v1/dashboard/")
        self.assertEqual(resp.status_code, 401)

    def test_bearer_token_grants_access(self):
        access = self._login("pro1@example.com").json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        resp = self.client.get("/api/v1/dashboard/")
        self.assertEqual(resp.status_code, 200, resp.content)


class ProfileAndPasswordTests(TestCase):
    def setUp(self):
        self.facility = create_facility(name="Prof", woreda=1)
        self.user = create_user(username="pp", facility=self.facility)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_view_and_update_profile(self):
        resp = self.client.get("/api/v1/auth/me/")
        self.assertEqual(resp.status_code, 200)
        resp = self.client.patch(
            "/api/v1/auth/me/",
            {"full_name": "New Name", "phone_number": "+251922222222"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "New Name")

    def test_change_password_enforces_complexity(self):
        resp = self.client.post(
            "/api/v1/auth/change-password/",
            {"current_password": "password", "new_password": "weak"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_change_password_success(self):
        resp = self.client.post(
            "/api/v1/auth/change-password/",
            {"current_password": "password", "new_password": "Str0ng!Pass1"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Str0ng!Pass1"))


class ForcedPasswordChangeTests(TestCase):
    def setUp(self):
        self.facility = create_facility(name="Forced", woreda=1)
        self.user = create_user(username="forced", facility=self.facility)
        self.user.must_change_password = True
        self.user.save(update_fields=["must_change_password"])
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_locked_out_until_password_changed(self):
        resp = self.client.get("/api/v1/dashboard/")
        self.assertEqual(resp.status_code, 403)
        # Change password unlocks access.
        self.client.post(
            "/api/v1/auth/change-password/",
            {"current_password": "password", "new_password": "Str0ng!Pass1"},
            format="json",
        )
        resp = self.client.get("/api/v1/dashboard/")
        self.assertEqual(resp.status_code, 200, resp.content)


class AdminUserManagementTests(TestCase):
    def setUp(self):
        self.facility = create_facility(name="Mgmt", woreda=1)
        self.admin = create_admin(username="boss", facility=self.facility)
        self.pro = create_user(username="worker", facility=self.facility)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_admin_creates_user_with_temp_password(self):
        resp = self.client.post(
            "/api/v1/users/",
            {
                "username": "newbie",
                "full_name": "New Bie",
                "phone_number": "+251933333333",
                "role": User.Role.PROFESSIONAL,
                "facility": str(self.facility.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertTrue(resp.json()["temporary_password"])
        created = User.objects.get(username="newbie")
        self.assertTrue(created.must_change_password)

    def test_deactivate_blocks_login(self):
        resp = self.client.post(f"/api/v1/users/{self.pro.id}/deactivate/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.pro.refresh_from_db()
        self.assertFalse(self.pro.is_active)

    def test_cannot_deactivate_self(self):
        resp = self.client.post(f"/api/v1/users/{self.admin.id}/deactivate/")
        self.assertEqual(resp.status_code, 400)

    def test_assign_role(self):
        resp = self.client.post(
            f"/api/v1/users/{self.pro.id}/assign-role/",
            {"role": User.Role.ADMIN},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.pro.refresh_from_db()
        self.assertEqual(self.pro.role, User.Role.ADMIN)

    def test_professional_cannot_manage_users(self):
        self.client.force_authenticate(self.pro)
        resp = self.client.get("/api/v1/users/")
        self.assertEqual(resp.status_code, 403)
