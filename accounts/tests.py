from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()

PASSWORD = "Str0ng!Pass"


def make_user(username, **flags):
    return User.objects.create_user(
        email=f"{username}@example.com",
        username=username,
        password=PASSWORD,
        first_name=username.title(),
        last_name="Test",
        **flags,
    )


@patch("accounts.serializers.send_welcome_email")
@patch("accounts.serializers.send_account_created_by_admin_email")
class AccountPermissionTests(APITestCase):
    def setUp(self):
        self.superuser = make_user("root", is_superuser=True, is_staff=True)
        self.manager = make_user("manager", is_dhow_manager=True)
        self.supervisor = make_user("supervisor", is_supervisor=True)
        self.agent = make_user("agent", is_agent=True)

    def detail_url(self, user):
        return f"/api/v1/auth/{user.usercode}/"

    # User list

    def test_user_list_requires_login(self, *_):
        self.assertEqual(self.client.get("/api/v1/auth/").status_code, 401)

    def test_user_list_hidden_from_supervisors_and_agents(self, *_):
        for user in (self.supervisor, self.agent):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get("/api/v1/auth/").status_code, 403)

    def test_user_list_visible_to_managers_and_superusers(self, *_):
        for user in (self.manager, self.superuser):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get("/api/v1/auth/").status_code, 200)

    # User detail

    def test_user_cannot_view_or_edit_someone_else(self, *_):
        self.client.force_authenticate(self.supervisor)
        self.assertEqual(self.client.get(self.detail_url(self.agent)).status_code, 403)
        res = self.client.patch(self.detail_url(self.agent), {"first_name": "X"})
        self.assertEqual(res.status_code, 403)

    def test_manager_can_view_but_not_edit_others(self, *_):
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.client.get(self.detail_url(self.agent)).status_code, 200)
        res = self.client.patch(self.detail_url(self.agent), {"first_name": "X"})
        self.assertEqual(res.status_code, 403)

    def test_user_can_edit_own_profile_and_password(self, *_):
        self.client.force_authenticate(self.supervisor)
        res = self.client.patch(
            self.detail_url(self.supervisor),
            {"first_name": "Amina", "password": "N3w!Passw0rd"},
        )
        self.assertEqual(res.status_code, 200)
        self.supervisor.refresh_from_db()
        self.assertEqual(self.supervisor.first_name, "Amina")
        self.assertTrue(self.supervisor.check_password("N3w!Passw0rd"))

    def test_user_cannot_promote_themselves(self, *_):
        self.client.force_authenticate(self.supervisor)
        res = self.client.patch(
            self.detail_url(self.supervisor), {"is_superuser": True, "is_staff": True}
        )
        self.assertEqual(res.status_code, 400)
        self.supervisor.refresh_from_db()
        self.assertFalse(self.supervisor.is_superuser)
        self.assertFalse(self.supervisor.is_staff)

    def test_superuser_can_edit_role_and_status(self, *_):
        self.client.force_authenticate(self.superuser)
        res = self.client.patch(
            self.detail_url(self.agent),
            {"is_agent": False, "is_supervisor": True, "is_active": False, "last_name": "New"},
        )
        self.assertEqual(res.status_code, 200)
        self.agent.refresh_from_db()
        self.assertTrue(self.agent.is_supervisor)
        self.assertFalse(self.agent.is_agent)
        self.assertFalse(self.agent.is_active)
        self.assertEqual(self.agent.last_name, "New")

    def test_superuser_cannot_change_own_role_or_status(self, *_):
        self.client.force_authenticate(self.superuser)
        res = self.client.patch(self.detail_url(self.superuser), {"is_active": False})
        self.assertEqual(res.status_code, 400)

    def test_superuser_cannot_set_another_users_password(self, *_):
        self.client.force_authenticate(self.superuser)
        res = self.client.patch(self.detail_url(self.agent), {"password": "N3w!Passw0rd"})
        self.assertEqual(res.status_code, 400)

    def test_staff_cannot_grant_admin_access(self, *_):
        staff = make_user("staff", is_staff=True)
        self.client.force_authenticate(staff)
        res = self.client.patch(self.detail_url(self.agent), {"is_superuser": True})
        self.assertEqual(res.status_code, 400)
        res = self.client.patch(self.detail_url(self.agent), {"is_active": False})
        self.assertEqual(res.status_code, 200)

    # Signup endpoints

    def test_public_guest_signup_ignores_role_flags(self, *_):
        res = self.client.post(
            "/api/v1/auth/guests/signup/",
            {
                "email": "evil@example.com",
                "username": "evil",
                "first_name": "Evil",
                "last_name": "Guest",
                "password": PASSWORD,
                "is_superuser": True,
                "is_staff": True,
                "is_dhow_manager": True,
            },
        )
        self.assertEqual(res.status_code, 201)
        user = User.objects.get(email="evil@example.com")
        self.assertTrue(user.is_guest)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_dhow_manager)

    def test_superuser_can_create_supervisor(self, *_):
        self.client.force_authenticate(self.superuser)
        res = self.client.post(
            "/api/v1/auth/supervisors/signup/",
            {"email": "s2@example.com", "username": "s2", "first_name": "S", "last_name": "Two"},
        )
        self.assertEqual(res.status_code, 201)
        self.assertTrue(User.objects.get(email="s2@example.com").is_supervisor)

    def test_only_superusers_can_create_superusers(self, *_):
        payload = {
            "email": "root2@example.com",
            "username": "root2",
            "first_name": "Root",
            "last_name": "Two",
            "password": PASSWORD,
        }
        for user in (self.manager, self.supervisor, self.agent):
            self.client.force_authenticate(user)
            res = self.client.post("/api/v1/auth/superusers/signup/", payload)
            self.assertEqual(res.status_code, 403)

        self.client.force_authenticate(self.superuser)
        res = self.client.post("/api/v1/auth/superusers/signup/", payload)
        self.assertEqual(res.status_code, 201)
        self.assertTrue(User.objects.get(email="root2@example.com").is_superuser)

    def test_superuser_password_must_be_strong(self, *_):
        self.client.force_authenticate(self.superuser)
        res = self.client.post(
            "/api/v1/auth/superusers/signup/",
            {
                "email": "weak@example.com",
                "username": "weak",
                "first_name": "Weak",
                "last_name": "Pass",
                "password": "password",
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertFalse(User.objects.filter(email="weak@example.com").exists())

    def test_status_logs_include_references(self, *_):
        self.client.force_authenticate(self.superuser)
        for url in ("/api/v1/booking-status-logs/", "/api/v1/refund-logs/"):
            self.assertEqual(self.client.get(url).status_code, 200)
