from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile
from .serializers import (
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)


class CsrfProtectedMixin:
    """
    DRF checks CSRF only for users that are already authenticated by session.
    Public unsafe endpoints (register, login) are protected explicitly.
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in SAFE_METHODS:
            SessionAuthentication().enforce_csrf(request)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegisterView(CsrfProtectedMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(CsrfProtectedMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get_profile(self, user):
        # Users created outside the API (e.g. createsuperuser) get a profile lazily.
        profile, _ = Profile.objects.get_or_create(
            user=user, defaults={"nickname": user.username}
        )
        return profile

    def get(self, request):
        self.get_profile(request.user)
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        profile = self.get_profile(request.user)
        serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        request.user.refresh_from_db()
        return Response(UserSerializer(request.user).data)
