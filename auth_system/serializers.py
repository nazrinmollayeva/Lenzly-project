# auth_system/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import User, EmailVerification
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password']

    def create(self, validated_data):
        # User yaradılır, amma defaultda is_active=False
        return User.objects.create_user(**validated_data)


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs.get('email')
        code = attrs.get('code')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        # Yeni göndərilən kodu yoxla
        qs = EmailVerification.objects.filter(user=user).order_by('-created_at')
        if not qs.exists() or qs.first().code != code:
            raise serializers.ValidationError("Invalid or expired code")

        # 1 saatdan köhnə kodu rədd et
        if timezone.now() - qs.first().created_at > timezone.timedelta(hours=1):
            raise serializers.ValidationError("Verification code expired")

        attrs['user'] = user
        return attrs


class UsernameLoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Token-ə əlavə məlumat əlavə etmək istəsən:
        token['username'] = user.username
        return token

    def validate(self, attrs):
        # default olaraq username sahəsi axtarılır (biz də USERNAME_FIELD dəyişmişik)
        return super().validate(attrs)

class EmptySerializer(serializers.Serializer):
    pass
