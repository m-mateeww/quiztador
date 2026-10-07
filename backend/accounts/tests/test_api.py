from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import Profile

User = get_user_model()

PASSWORD = "example-password"


def create_player(username="player_one", nickname="MountainKnight"):
    user = User.objects.create_user(
        username=username, email=f"{username}@example.com", password=PASSWORD
    )
    Profile.objects.create(user=user, nickname=nickname)
    return user


class AuthApiTestCase(APITestCase):
    register_url = reverse("accounts:register")
    login_url = reverse("accounts:login")
    logout_url = reverse("accounts:logout")
    me_url = reverse("accounts:me")
    csrf_url = reverse("accounts:csrf")

    def login(self, username="player_one"):
        return self.client.post(
            self.login_url, {"username": username, "password": PASSWORD}, format="json"
        )


class RegistrationTests(AuthApiTestCase):
    payload = {
        "username": "player_one",
        "email": "player@example.com",
        "nickname": "MountainKnight",
        "password": PASSWORD,
        "password_confirm": PASSWORD,
    }

    def test_successful_registration(self):
        response = self.client.post(self.register_url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="player_one")
        self.assertEqual(user.profile.nickname, "MountainKnight")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(
            response.data,
            {
                "id": user.id,
                "username": "player_one",
                "email": "player@example.com",
                "profile": {"nickname": "MountainKnight", "avatar_key": "knight-1"},
            },
        )
        self.assertNotIn("password", response.data)

    def test_invalid_registration(self):
        existing = create_player(username="taken", nickname="TakenKnight")
        cases = [
            ("username", {"username": existing.username}),
            ("email", {"email": existing.email}),
            ("nickname", {"nickname": "TakenKnight"}),
            ("password_confirm", {"password_confirm": "different-password"}),
        ]

        for field, overrides in cases:
            with self.subTest(field=field):
                response = self.client.post(
                    self.register_url, {**self.payload, **overrides}, format="json"
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data["errors"])
                self.assertEqual(User.objects.count(), 1)


class LoginTests(AuthApiTestCase):
    def setUp(self):
        self.user = create_player()

    def test_successful_login(self):
        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("sessionid", response.cookies)

        me = self.client.get(self.me_url)
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["id"], self.user.id)

    def test_failed_login(self):
        response = self.client.post(
            self.login_url,
            {"username": "player_one", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
        self.assertNotIn("sessionid", response.cookies)
        self.assertEqual(
            self.client.get(self.me_url).status_code, status.HTTP_403_FORBIDDEN
        )


class MeTests(AuthApiTestCase):
    def setUp(self):
        self.user = create_player()
        self.other = create_player(username="player_two", nickname="RiverKnight")

    def test_anonymous_access_is_denied(self):
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data["errors"])

    def test_returns_only_current_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "player_one")
        self.assertEqual(response.data["profile"]["nickname"], "MountainKnight")

    def test_update_profile(self):
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            self.me_url, {"nickname": "NewKnight", "avatar_key": "knight-3"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.nickname, "NewKnight")
        self.assertEqual(self.user.profile.avatar_key, "knight-3")

    def test_protected_fields_cannot_be_changed(self):
        self.client.force_authenticate(self.user)

        response = self.client.patch(self.me_url, {"is_staff": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_staff", response.data["errors"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)

    def test_nickname_of_other_user_is_rejected(self):
        self.client.force_authenticate(self.user)

        response = self.client.patch(self.me_url, {"nickname": "RiverKnight"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nickname", response.data["errors"])


class LogoutTests(AuthApiTestCase):
    def test_logout_ends_session(self):
        create_player()
        self.login()

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            self.client.get(self.me_url).status_code, status.HTTP_403_FORBIDDEN
        )

    def test_logout_requires_authentication(self):
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CsrfTests(AuthApiTestCase):
    def setUp(self):
        create_player()
        self.client = APIClient(enforce_csrf_checks=True)

    def get_csrf_token(self):
        response = self.client.get(self.csrf_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        return response.cookies["csrftoken"].value

    def test_unsafe_request_requires_token(self):
        token = self.get_csrf_token()
        self.assertEqual(
            self.client.post(
                self.login_url,
                {"username": "player_one", "password": PASSWORD},
                format="json",
                HTTP_X_CSRFTOKEN=token,
            ).status_code,
            status.HTTP_200_OK,
        )
        token = self.client.cookies["csrftoken"].value  # rotated on login

        without_token = self.client.patch(self.me_url, {"nickname": "NoToken"}, format="json")
        self.assertEqual(without_token.status_code, status.HTTP_403_FORBIDDEN)

        with_token = self.client.patch(
            self.me_url, {"nickname": "WithToken"}, format="json", HTTP_X_CSRFTOKEN=token
        )
        self.assertEqual(with_token.status_code, status.HTTP_200_OK)
        self.assertEqual(with_token.data["profile"]["nickname"], "WithToken")

    def test_login_requires_token(self):
        response = self.client.post(
            self.login_url, {"username": "player_one", "password": PASSWORD}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
