import logging

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import HttpResponse
from rest_framework.authtoken.models import Token
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from accounts.serializers import (
    BaseUserSerializer,
    UserLoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    DhowManagerSerializer,
    GuestUserSerializer,
    AgentUserSerializer,
)
from accounts.permissions import IsSystemAdminOrReadOnly

User = get_user_model()

logger = logging.getLogger(__name__)


class TokenView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            user = authenticate(email=email, password=password)

            # TODO: Implement 2FA, OTP, or token expiration

            if user:
                if user.is_active:
                    token, created = Token.objects.get_or_create(user=user)
                    user_details = {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "usercode": user.usercode,
                        "phone_number": user.phone_number,
                        "is_guest": user.is_guest,
                        "is_dhow_manager": user.is_dhow_manager,
                        "is_agent": user.is_agent,
                        "is_active": user.is_active,
                        "is_staff": user.is_staff,
                        "is_superuser": user.is_superuser,
                        "last_login": user.last_login,
                        "token": token.key,
                        "reference": user.reference,
                    }
                    return Response(user_details, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {"detail": ("User account is not verified.")},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {"detail": ("Unable to log in with provided credentials.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""
All Users
"""
class UserListView(generics.ListAPIView):
    permission_classes = (IsSystemAdminOrReadOnly,)
    serializer_class = BaseUserSerializer
    queryset = User.objects.all()

class UserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BaseUserSerializer
    queryset = User.objects.all()
    lookup_field = "usercode"


"""
Create Users
"""


class DhowManagerCreateView(generics.CreateAPIView):
    permission_classes = (IsSystemAdminOrReadOnly,)
    serializer_class = DhowManagerSerializer
    queryset = User.objects.all()


class GuestUserCreateView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = GuestUserSerializer
    queryset = User.objects.all()


class AgentUserCreateView(generics.CreateAPIView):
    permission_classes = (IsSystemAdminOrReadOnly,)
    serializer_class = AgentUserSerializer
    queryset = User.objects.all()


"""
Password Reset
"""


class ForgotPasswordView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Reset code sent to your email"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Password has been reset successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""
Acivate Account
"""

class ActivateAccountView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, uidb64=None, token=None):
        uidb64 = uidb64 or request.data.get("uidb64")
        token = token or request.data.get("token")
        password = request.data.get("password")

        if not all([uidb64, token, password]):
            return Response(
                {"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"error": "Invalid activation link"}, status=status.HTTP_400_BAD_REQUEST
            )

        token_generator = PasswordResetTokenGenerator()
        if token_generator.check_token(user, token):
            # Validate password using the serializer
            serializer = BaseUserSerializer(
                user, data={"password": password}, partial=True
            )

            if serializer.is_valid():
                user = serializer.save()
                user.is_active = True  # Activate the account
                user.save()

                return Response(
                    {"detail": "Your account has been activated successfully. You can now log in."},
                    status=status.HTTP_200_OK,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {"error": "Invalid or expired activation link"},
            status=status.HTTP_400_BAD_REQUEST,
        )