from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import Profile

User = get_user_model()

NICKNAME_TAKEN = "Profile with this nickname already exists."


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("nickname", "avatar_key")


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "profile")
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(max_length=30, write_only=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = ("username", "email", "nickname", "password", "password_confirm")

    def validate_nickname(self, value):
        if Profile.objects.filter(nickname__iexact=value).exists():
            raise serializers.ValidationError(NICKNAME_TAKEN)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": ["Passwords do not match."]}
            )

        candidate = User(username=attrs["username"], email=attrs["email"])
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data["username"],
                email=validated_data["email"],
                password=validated_data["password"],
            )
            Profile.objects.create(user=user, nickname=validated_data["nickname"])
        return user

    def to_representation(self, instance):
        return UserSerializer(instance, context=self.context).data


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["username"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        attrs["user"] = user
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Updates only the current user's own profile fields."""

    class Meta:
        model = Profile
        fields = ("nickname", "avatar_key")

    def validate_nickname(self, value):
        others = Profile.objects.filter(nickname__iexact=value)
        if self.instance is not None:
            others = others.exclude(pk=self.instance.pk)
        if others.exists():
            raise serializers.ValidationError(NICKNAME_TAKEN)
        return value

    def validate(self, attrs):
        forbidden = sorted(set(self.initial_data) - set(self.Meta.fields))
        if forbidden:
            raise serializers.ValidationError(
                {field: ["This field cannot be changed."] for field in forbidden}
            )
        return attrs
