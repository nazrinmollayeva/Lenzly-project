# auth_system/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenViewBase
from rest_framework_simplejwt.tokens import RefreshToken

from django.utils.crypto import get_random_string
from django.core.mail import send_mail

from .models import User, EmailVerification
from .serializers import UsernameLoginSerializer, RegisterSerializer, VerifyEmailSerializer, EmptySerializer

class CustomTokenObtainPairView(TokenViewBase):
    serializer_class = UsernameLoginSerializer

class AuthViewSet(viewsets.GenericViewSet):
    """
    register:       POST  /api/auth/register/
    verify:         POST  /api/auth/verify/
    token (login):  POST  /api/auth/token/
    logout:         POST  /api/auth/logout/
    delete_account: DELETE /api/auth/delete_account/
    """
    queryset = User.objects.all()
    serializer_class = EmptySerializer  # default serializer

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], serializer_class=RegisterSerializer)
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create & send code
        code = get_random_string(6, allowed_chars='0123456789')
        EmailVerification.objects.create(user=user, code=code)
        send_mail(
            subject="Email Verification Code",
            message=f"Your verification code is {code}",
            from_email=None,
            recipient_list=[user.email],
        )
        return Response({"detail": "Verification code sent to email."}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], serializer_class=VerifyEmailSerializer)
    def verify(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        user.is_email_verified = True
        user.is_active = True
        user.save()

        return Response({"detail": "Email verified. You can now log in."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def token(self, request):
        # SimpleJWT-nin TokenObtainPairView-i çağırılır
        return TokenObtainPairView.as_view()(request._request)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        refresh = request.data.get('refresh')
        if not refresh:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh).blacklist()
        except Exception:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)

    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        request.user.delete()
        return Response({"detail": "Account deleted."}, status=status.HTTP_204_NO_CONTENT)
