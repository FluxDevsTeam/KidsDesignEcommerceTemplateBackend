from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# forgot password serializers
class RequestForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class SetNewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs


class VerifyOtpPasswordSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, required=True)
    email = serializers.EmailField(required=True)


class ResendOtpPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


# user profile serializers
class EmailChangeSerializer(serializers.Serializer):
    new_email = serializers.CharField(write_only=True, required=False, min_length=8)
    password = serializers.CharField(write_only=True, required=False)


class VerifyEmailChangeSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, required=False)


class ViewUserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number',]


class ProfileChangeSerializer(serializers.Serializer):
    new_first_name = serializers.CharField(write_only=True, required=False, min_length=2)
    new_last_name = serializers.CharField(write_only=True, required=False, min_length=2)
    new_phone_number = serializers.CharField(write_only=True, required=False, min_length=11)


class VerifyProfileChangeSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=False)


# password change serializers
class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs


class VerifyPasswordChangeSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, required=True)


# user sugnup serializers
class UserSignupSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    verify_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):

        if data['password'] != data['verify_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data


class UserSignupSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    phone_number = serializers.CharField(max_length=15, required=False)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    verify_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):

        if data['password'] != data['verify_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data


class UserSignupSerializerVerify(serializers.Serializer):
    otp = serializers.CharField(max_length=6)
    email = serializers.EmailField()


class UserSignupResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class UserSignupSerializerResendOTP(serializers.Serializer):
    email = serializers.EmailField()


# login serializer
class LoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=50, min_length=6, write_only=True)
    email = serializers.EmailField(max_length=50, min_length=2)

    class Meta:
        model = User
        fields = ['email', 'password']


# refresh serializer
class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)

    def validate_refresh_token(self, value):
        try:
            token = RefreshToken(value)
            token.verify()
            return value
        except Exception as e:
            raise serializers.ValidationError("Invalid or expired refresh token")


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)

    def validate_refresh_token(self, value):
        try:
            token = RefreshToken(value)
            token.verify()
            return value
        except Exception as e:
            raise serializers.ValidationError("Invalid or expired refresh token")


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=True)