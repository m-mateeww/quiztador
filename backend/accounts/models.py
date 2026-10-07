from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        error_messages={"unique": "User with this email already exists."},
    )

    def __str__(self):
        return self.username


class Profile(models.Model):
    class Avatar(models.TextChoices):
        KNIGHT_1 = "knight-1", "Knight 1"
        KNIGHT_2 = "knight-2", "Knight 2"
        KNIGHT_3 = "knight-3", "Knight 3"
        KNIGHT_4 = "knight-4", "Knight 4"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    nickname = models.CharField(
        max_length=30,
        unique=True,
        error_messages={"unique": "Profile with this nickname already exists."},
    )
    avatar_key = models.CharField(
        max_length=30,
        choices=Avatar.choices,
        default=Avatar.KNIGHT_1,
    )

    def __str__(self):
        return self.nickname
