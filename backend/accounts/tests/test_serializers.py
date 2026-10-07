from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Profile
from accounts.serializers import ProfileUpdateSerializer, RegisterSerializer

User = get_user_model()


def registration_data(**overrides):
    data = {
        "username": "player_one",
        "email": "player@example.com",
        "nickname": "MountainKnight",
        "password": "example-password",
        "password_confirm": "example-password",
    }
    data.update(overrides)
    return data


class RegisterSerializerTests(TestCase):
    def test_creates_user_and_profile(self):
        serializer = RegisterSerializer(data=registration_data())

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertTrue(user.check_password("example-password"))
        self.assertEqual(user.profile.nickname, "MountainKnight")
        self.assertNotIn("password", serializer.data)
        self.assertNotIn("password_confirm", serializer.data)

    def test_rejects_weak_password(self):
        serializer = RegisterSerializer(
            data=registration_data(password="123", password_confirm="123")
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)


class ProfileUpdateSerializerTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="a", email="a@example.com", password="x")
        self.profile = Profile.objects.create(user=user, nickname="Knight")

    def test_rejects_unknown_avatar(self):
        serializer = ProfileUpdateSerializer(
            self.profile, data={"avatar_key": "dragon"}, partial=True
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("avatar_key", serializer.errors)

    def test_keeps_own_nickname_valid(self):
        serializer = ProfileUpdateSerializer(
            self.profile, data={"nickname": "Knight"}, partial=True
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
