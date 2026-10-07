from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from accounts.models import Profile

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_hashes_password(self):
        user = User.objects.create_user(
            username="player_one", email="player@example.com", password="secret-pass-1"
        )

        self.assertNotEqual(user.password, "secret-pass-1")
        self.assertTrue(user.check_password("secret-pass-1"))

    def test_email_is_unique(self):
        User.objects.create_user(username="a", email="same@example.com", password="x")

        with self.assertRaises(IntegrityError):
            User.objects.create_user(username="b", email="same@example.com", password="x")


class ProfileModelTests(TestCase):
    def test_profile_defaults_and_relation(self):
        user = User.objects.create_user(username="a", email="a@example.com", password="x")
        profile = Profile.objects.create(user=user, nickname="Knight")

        self.assertEqual(profile.avatar_key, "knight-1")
        self.assertEqual(user.profile, profile)

    def test_nickname_is_unique(self):
        first = User.objects.create_user(username="a", email="a@example.com", password="x")
        second = User.objects.create_user(username="b", email="b@example.com", password="x")
        Profile.objects.create(user=first, nickname="Knight")

        with self.assertRaises(IntegrityError):
            Profile.objects.create(user=second, nickname="Knight")
