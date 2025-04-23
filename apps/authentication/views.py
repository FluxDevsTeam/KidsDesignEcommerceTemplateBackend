from django.contrib.auth import get_user_model
from django.conf import settings
import random
import datetime
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.contrib.auth.hashers import make_password
from rest_framework.exceptions import AuthenticationFailed
from .serializers import (
    UserSignupSerializer, LoginSerializer, ViewUserProfileSerializer,
    ResendOtpPasswordSerializer, VerifyOtpPasswordSerializer, SetNewPasswordSerializer,
    RefreshTokenSerializer, EmailChangeSerializer,
    VerifyEmailChangeSerializer, ProfileChangeSerializer, VerifyProfileChangeSerializer,
    PasswordChangeSerializer, VerifyPasswordChangeSerializer, RequestForgotPasswordSerializer,
    UserSignupSerializerVerify, UserSignupResendOTPSerializer, LogoutSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import swagger_helper
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import EmailChangeRequest, PasswordChangeRequest, ForgotPasswordRequest, NameChangeRequest
from django.utils.timezone import now
from .tasks import is_celery_healthy, send_auth_success_email, send_email_synchronously, send_generic_email_task
import logging
from django.conf import settings

User = get_user_model()
logger = logging.getLogger(__name__)

frontend_url = f"{settings.SITE_URL}/change-password"


class ForgotPasswordViewSet(viewsets.ModelViewSet):
    queryset = ForgotPasswordRequest.objects.all()

    def get_serializer_class(self):
        if self.action == 'request_forgot_password':
            return RequestForgotPasswordSerializer
        if self.action == 'resend_otp':
            return ResendOtpPasswordSerializer
        if self.action == 'verify_otp':
            return VerifyOtpPasswordSerializer
        if self.action == 'set_new_password':
            return SetNewPasswordSerializer

    @swagger_helper("ForgotPassword", "")
    @action(detail=False, methods=['post'], url_path='request-forgot-password')
    def request_forgot_password(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"data": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"data": "No user found with this email."}, status=status.HTTP_400_BAD_REQUEST)

        reset_url = f"{frontend_url}?email={email}"
        ForgotPasswordRequest.objects.filter(user=user).delete()
        ForgotPasswordRequest.objects.create(user=user)

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending reset link email synchronously.")
            send_email_synchronously(
                user_email=email,
                email_type="reset_link",
                subject="Password Reset Request",
                action="Password Reset",
                message="Click the link below to reset your password. This link will expire in 10 minutes.",
                link=reset_url,
                link_text="Reset Password"
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': email,
                    'email_type': "reset_link",
                    'subject': "Password Reset Request",
                    'action': "Password Reset",
                    'message': "Click the link below to reset your password. This link will expire in 10 minutes.",
                    'link': reset_url,
                    'link_text': "Reset Password"
                }
            )

        return Response({"data": "A password reset link has been sent to your email."}, status=status.HTTP_200_OK)

    @swagger_helper("ForgotPassword", "")
    @action(detail=False, methods=['post'], url_path='set-new-password')
    def set_new_password(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not email or not new_password or not confirm_password:
            return Response({"data": "Email, new_password, and confirm_password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({"data": "Password must be at least 8 characters long."},
                            status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"data": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"data": "No user found with this email."}, status=status.HTTP_400_BAD_REQUEST)
        forgot_password_request = ForgotPasswordRequest.objects.filter(user=user).first()
        expiration_time = forgot_password_request.created_at + datetime.timedelta(minutes=10)
        if timezone.now() > expiration_time:
            return Response({"data": "The reset link has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        ForgotPasswordRequest.objects.filter(user=user).delete()
        otp = random.randint(100000, 999999)

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending OTP email synchronously.")
            send_email_synchronously(
                user_email=email,
                email_type="otp",
                subject="Forgot Password OTP",
                action="Password Reset",
                message="Use the OTP below to reset your password.",
                otp=otp
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': email,
                    'email_type': "otp",
                    'subject': "Forgot Password OTP",
                    'action': "Password Reset",
                    'message': "Use the OTP below to reset your password.",
                    'otp': otp
                }
            )
        hashed_new_password = make_password(new_password)
        ForgotPasswordRequest.objects.create(user=user, otp=otp, new_password=hashed_new_password)

        return Response({"data": "An OTP has been sent to your email."}, status=status.HTTP_200_OK)

    @swagger_helper("ForgotPassword", "")
    @action(detail=False, methods=['post'], url_path='verify-otp')
    def verify_otp(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({"data": "Email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"data": "No user found with this email."}, status=status.HTTP_400_BAD_REQUEST)

        forgot_password_request = ForgotPasswordRequest.objects.filter(user=user).first()
        if not forgot_password_request:
            return Response({"data": "No pending forgot password request found."}, status=status.HTTP_400_BAD_REQUEST)

        if str(forgot_password_request.otp) != str(otp):
            return Response({"data": "Incorrect OTP."}, status=status.HTTP_400_BAD_REQUEST)

        otp_age = (timezone.now() - forgot_password_request.created_at).total_seconds()
        if otp_age > 300:
            return Response({"data": "OTP has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        user.password = forgot_password_request.new_password
        if not user.is_verified:
            user.is_verified = True
        user.save()

        forgot_password_request.delete()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending confirmation email synchronously.")
            send_email_synchronously(
                user_email=user.email,
                email_type="confirmation",
                subject="Password Changed Successfully",
                action="Password Change",
                message="Your password has been successfully updated, and you are now securely logged into your account."
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': user.email,
                    'email_type': "confirmation",
                    'subject': "Password Changed Successfully",
                    'action': "Password Change",
                    'message': "Your password has been successfully updated, and you are now securely logged into your account."
                }
            )

        return Response({
            'message': 'Password reset successful.',
            'access_token': access_token, 'refresh_token': str(refresh)}, status=status.HTTP_201_CREATED)

    @swagger_helper("ForgotPassword", "")
    @action(detail=False, methods=['post'], url_path='resend-otp')
    def resend_otp(self, request):
        email = request.data.get('email')

        if not email:
            return Response({"data": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"data": "No user found with this email."}, status=status.HTTP_400_BAD_REQUEST)

        forgot_password_request = ForgotPasswordRequest.objects.filter(user=user).first()
        if not forgot_password_request:
            return Response({"data": "No pending forgot password request found."}, status=status.HTTP_400_BAD_REQUEST)

        otp = random.randint(100000, 999999)
        forgot_password_request.otp = otp
        forgot_password_request.created_at = timezone.now()
        forgot_password_request.save()

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending OTP email synchronously.")
            send_email_synchronously(
                user_email=email,
                email_type="otp",
                subject="Forgot Password OTP - Resent",
                action="Password Reset",
                message="Use the OTP below to reset your password.",
                otp=otp
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': email,
                    'email_type': "otp",
                    'subject': "Forgot Password OTP - Resent",
                    'action': "Password Reset",
                    'message': "Use the OTP below to reset your password.",
                    'otp': otp
                }
            )
        return Response({"data": "A new OTP has been sent to your email and the expiration time has been extended."}, status=status.HTTP_200_OK)


class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'request_email_change':
            return EmailChangeSerializer
        if self.action == 'verify_email_change':
            return VerifyEmailChangeSerializer
        if self.action == 'request_profile_change':
            return ProfileChangeSerializer
        if self.action == 'verify_profile_change':
            return VerifyProfileChangeSerializer
        if self.action == 'retrieve':
            return ViewUserProfileSerializer

    @swagger_helper("UserProfile", "profile", "view user profile. requires authentication (JWT)")
    def retrieve(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user, context={'request': request})
        return Response(serializer.data)

    @swagger_helper("UserProfile", "")
    @action(detail=False, methods=['post'], url_path='request-email-change')
    def request_email_change(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_email = serializer.validated_data.get('new_email')
        password = serializer.validated_data.get('password')

        if not user.check_password(password):
            return Response({"data": "Incorrect password."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=new_email).exists():
            return Response({"data": "This email is already in use."}, status=status.HTTP_400_BAD_REQUEST)

        existing_request = EmailChangeRequest.objects.filter(user=user).first()
        if existing_request:
            otp = random.randint(100000, 999999)
            existing_request.new_email = new_email
            existing_request.otp = otp
            existing_request.created_at = timezone.now()
            existing_request.save()
        else:
            otp = random.randint(100000, 999999)
            EmailChangeRequest.objects.create(user=user, new_email=new_email, otp=otp)

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending OTP email synchronously.")
            send_email_synchronously(
                user_email=new_email,
                email_type="otp",
                subject="Email Change OTP",
                action="Email Change",
                message="Use the OTP below to verify your new email address.",
                otp=otp
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': new_email,
                    'email_type': "otp",
                    'subject': "Email Change OTP",
                    'action': "Email Change",
                    'message': "Use the OTP below to verify your new email address.",
                    'otp': otp
                }
            )

        return Response({"data": "OTP sent to the new email address."}, status=status.HTTP_200_OK)

    @swagger_helper("UserProfile", "", "Resend OTP. requires authentication (JWT)")
    @action(detail=False, methods=['post'], url_path='resend-email-change-otp')
    def resend_email_change_otp(self, request):
        user = request.user
        email_change_request = EmailChangeRequest.objects.filter(user=user).first()

        if not email_change_request:
            return Response({"data": "No pending email change request found."}, status=status.HTTP_400_BAD_REQUEST)

        time_since_last_otp = (timezone.now() - email_change_request.created_at).total_seconds()
        if time_since_last_otp < 60:
            return Response({"data": "Please wait before requesting a new OTP."}, status=status.HTTP_400_BAD_REQUEST)

        otp = random.randint(100000, 999999)
        email_change_request.otp = otp
        email_change_request.created_at = timezone.now()
        email_change_request.save()

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending OTP email synchronously.")
            send_email_synchronously(
                user_email=email_change_request.new_email,
                email_type="otp",
                subject="Resend Email Change OTP",
                action="Email Change",
                message="Use the OTP below to verify your new email address.",
                otp=otp
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': email_change_request.new_email,
                    'email_type': "otp",
                    'subject': "Resend Email Change OTP",
                    'action': "Email Change",
                    'message': "Use the OTP below to verify your new email address.",
                    'otp': otp
                }
            )

        return Response({"data": "New OTP sent to the new email address."}, status=status.HTTP_200_OK)

    @swagger_helper("UserProfile", "")
    @action(detail=False, methods=['post'], url_path='verify-email-change')
    def verify_email_change(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        otp = serializer.validated_data.get('otp')

        email_change_request = EmailChangeRequest.objects.filter(user=user).first()
        if not email_change_request:
            return Response({"data": "No pending email change request found."}, status=status.HTTP_400_BAD_REQUEST)

        if str(email_change_request.otp) != str(otp):
            return Response({"data": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        otp_age = (timezone.now() - email_change_request.created_at).total_seconds()
        if otp_age > 300:
            return Response({"data": "OTP has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        user.email = email_change_request.new_email
        user.save()
        email_change_request.delete()

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending confirmation email synchronously.")
            send_email_synchronously(
                user_email=user.email,
                email_type="confirmation",
                subject="Email Change Confirmation",
                action="Email Change",
                message="Your email address has been successfully changed."
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': user.email,
                    'email_type': "confirmation",
                    'subject': "Email Change Confirmation",
                    'action': "Email Change",
                    'message': "Your email address has been successfully changed."
                }
            )

        return Response({"data": "Email updated successfully."}, status=status.HTTP_200_OK)

    @swagger_helper("UserProfile", "")
    @action(detail=False, methods=['post'], url_path='request-profile-change')
    def request_profile_change(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_first_name = serializer.validated_data.get('new_first_name')
        new_last_name = serializer.validated_data.get('new_last_name')
        new_phone_number = serializer.validated_data.get('new_phone_number')

        if not new_first_name and not new_last_name and not new_phone_number:
            return Response({"data": "At least one of new_first_name or new_last_name or new_phone_number is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        NameChangeRequest.objects.filter(user=user).delete()
        NameChangeRequest.objects.create(
            user=user,
            new_first_name=new_first_name,
            new_last_name=new_last_name,
            new_phone_number=new_phone_number,
        )

        return Response({"data": "Name change request submitted successfully."}, status=status.HTTP_200_OK)

    @swagger_helper("UserProfile", "")
    @action(detail=False, methods=['post'], url_path='verify-profile-change')
    def verify_profile_change(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        password = serializer.validated_data.get('password')

        if not user.check_password(password):
            return Response({"data": "Incorrect password."}, status=status.HTTP_400_BAD_REQUEST)

        name_change_request = NameChangeRequest.objects.filter(user=user).first()
        if not name_change_request:
            return Response({"data": "No pending name change request found."}, status=status.HTTP_400_BAD_REQUEST)

        if name_change_request.new_first_name:
            user.first_name = name_change_request.new_first_name
        if name_change_request.new_last_name:
            user.last_name = name_change_request.new_last_name
        if name_change_request.new_phone_number:
            user.phone_number = name_change_request.new_phone_number

        user.save()
        name_change_request.delete()

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending confirmation email synchronously.")
            send_email_synchronously(
                user_email=user.email,
                email_type="confirmation",
                subject="Profile Change Confirmation",
                action="Profile Change",
                message="Your profile has been successfully updated."
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': user.email,
                    'email_type': "confirmation",
                    'subject': "Profile Change Confirmation",
                    'action': "Profile Change",
                    'message': "Your profile has been successfully updated."
                }
            )

        return Response({"data": "Name updated successfully."}, status=status.HTTP_200_OK)


class PasswordChangeRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = PasswordChangeRequest.objects.all()

    def get_serializer_class(self):
        if self.action == 'request_password_change':
            return PasswordChangeSerializer
        if self.action == 'verify_password_change':
            return VerifyPasswordChangeSerializer

    @swagger_helper("ChangePassword", "")
    @action(detail=False, methods=['post'], url_path='request-password-change')
    def request_password_change(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not old_password:
            return Response({"data": "Old password is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({"data": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        if old_password == new_password:
            return Response({"data": "New password cannot be the same as the old password."}, status=status.HTTP_400_BAD_REQUEST)

        if not new_password or not confirm_password:
            return Response({"data": "Both new_password and confirm_password are required."}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"data": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({"data": "Password must be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)

        PasswordChangeRequest.objects.filter(user=user).delete()
        otp = random.randint(100000, 999999)
        hashed_new_password = make_password(new_password)

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending OTP email synchronously.")
            send_email_synchronously(
                user_email=user.email,
                email_type="otp",
                subject="Password Change OTP",
                action="Password Change",
                message="Use the OTP below to change your password.",
                otp=otp
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': user.email,
                    'email_type': "otp",
                    'subject': "Password Change OTP",
                    'action': "Password Change",
                    'message': "Use the OTP below to change your password.",
                    'otp': otp
                }
            )

        PasswordChangeRequest.objects.create(user=user, otp=otp, new_password=hashed_new_password)

        return Response({"data": "An OTP has been sent to your email."}, status=status.HTTP_200_OK)

    @swagger_helper("ChangePassword", "")
    @action(detail=False, methods=['post'], url_path='resend-otp')
    def resend_otp(self, request):
        user = request.user
        password_change_request = PasswordChangeRequest.objects.filter(user=user).first()

        if not password_change_request:
            return Response({"data": "No pending password change request found."}, status=status.HTTP_400_BAD_REQUEST)

        otp = random.randint(100000, 999999)
        password_change_request.otp = otp
        password_change_request.created_at = timezone.now()
        password_change_request.save()

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending OTP email synchronously.")
            send_email_synchronously(
                user_email=user.email,
                email_type="otp",
                subject="Password Change OTP - Resent",
                action="Password Change",
                message="Use the OTP below to change your password.",
                otp=otp
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': user.email,
                    'email_type': "otp",
                    'subject': "Password Change OTP - Resent",
                    'action': "Password Change",
                    'message': "Use the OTP below to change your password.",
                    'otp': otp
                }
            )
        return Response({"data": "A new OTP has been sent to your email."}, status=status.HTTP_200_OK)

    @swagger_helper("ChangePassword", "")
    @action(detail=False, methods=['post'], url_path='verify-password-change')
    def verify_password_change(self, request):
        otp = request.data.get('otp')

        if not otp:
            return Response({"data": "OTP is required."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        password_change_request = PasswordChangeRequest.objects.filter(user=user).first()

        if not password_change_request:
            return Response({"data": "No pending password change request found."}, status=status.HTTP_400_BAD_REQUEST)

        if str(password_change_request.otp) != str(otp):
            return Response({"data": "Incorrect OTP."}, status=status.HTTP_400_BAD_REQUEST)

        otp_age = (timezone.now() - password_change_request.created_at).total_seconds()
        if otp_age > 300:
            return Response({"data": "OTP has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        user.password = make_password(password_change_request.new_password)
        user.save()

        password_change_request.delete()

        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as e:
                raise AuthenticationFailed('Refresh token is invalid or expired.')

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending confirmation email synchronously.")
            send_email_synchronously(
                user_email=user.email,
                email_type="confirmation",
                subject="Password Changed Successfully",
                action="Password Change",
                message="Your password has been successfully changed. You have been logged out. Please log in with your new password."
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': user.email,
                    'email_type': "confirmation",
                    'subject': "Password Changed Successfully",
                    'action': "Password Change",
                    'message': "Your password has been successfully changed. You have been logged out. Please log in with your new password."
                }
            )

        return Response({"data": "Password changed successfully. You have been logged out."},
                        status=status.HTTP_200_OK)


class UserSignupViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        if self.action == 'verify':
            return UserSignupSerializerVerify
        if self.action == 'resend_otp':
            return UserSignupResendOTPSerializer
        if self.action == 'create':
            return UserSignupSerializer

    @swagger_helper("Signup", "")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        phone_number = serializer.validated_data['phone_number']

        user = User.objects.filter(email=email).first()

        if user:
            if not user.is_verified:
                otp = random.randint(100000, 999999)
                user.otp = otp
                user.otp_created_at = now()
                user.save()

                if not is_celery_healthy():
                    logger.warning("Celery is not healthy. Sending OTP email synchronously.")
                    send_email_synchronously(
                        user_email=email,
                        email_type="otp",
                        subject="Verify Your Email",
                        action="Email Verification",
                        message="Use the OTP below to verify your email address.",
                        otp=otp
                    )
                else:
                    send_generic_email_task.apply_async(
                        kwargs={
                            'user_email': email,
                            'email_type': "otp",
                            'subject': "Verify Your Email",
                            'action': "Email Verification",
                            'message': "Use the OTP below to verify your email address.",
                            'otp': otp
                        }
                    )

                return Response({"data": f"User already exists but is not verified. OTP resent."},
                                status=status.HTTP_200_OK)
            else:
                return Response({"data": "User already exists and is verified."}, status=status.HTTP_400_BAD_REQUEST)

        otp = random.randint(100000, 999999)
        User.objects.create(
            first_name=serializer.validated_data['first_name'],
            last_name=serializer.validated_data['last_name'],
            email=email,
            password=make_password(password),
            phone_number=phone_number,
            otp=otp,
            otp_created_at=now()
        )

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending emails synchronously.")
            send_email_synchronously(
                user_email=email,
                email_type="otp",
                subject="Verify Your Email",
                action="Email Verification",
                message="Use the OTP below to verify your email address.",
                otp=otp
            )
            send_email_synchronously(
                user_email=email,
                action="signup"
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': email,
                    'email_type': "otp",
                    'subject': "Verify Your Email",
                    'action': "Email Verification",
                    'message': "Use the OTP below to verify your email address.",
                    'otp': otp
                }
            )
            send_auth_success_email.apply_async(
                kwargs={
                    'user_email': email,
                    'action': "signup"
                }
            )
        return Response({"data": f"Signup successful. OTP sent to your email "}, status=status.HTTP_201_CREATED)

    @swagger_helper("Signup", "")
    @action(detail=False, methods=['post'], url_path='verify-otp')
    def verify(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"data": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return Response({"data": "User is already verified."}, status=status.HTTP_400_BAD_REQUEST)

        if str(user.otp) != otp:
            return Response({"data": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if now() - user.otp_created_at > datetime.timedelta(minutes=5):
            return Response({"data": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_verified = True
        user.otp = None
        user.save()

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending confirmation email synchronously.")
            send_email_synchronously(
                user_email=email,
                email_type="confirmation",
                subject="Signup Successful",
                action="Signup",
                message="You have finished the signup verification for ASLuxeryOriginals.com. Welcome!"
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': email,
                    'email_type': "confirmation",
                    'subject': "Signup Successful",
                    'action': "Signup",
                    'message': "You have finished the signup verification for ASLuxeryOriginals.com. Welcome!"
                }
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            'message': 'Signup successful.',
            'access_token': access_token,
            'refresh_token': str(refresh),
        }, status=status.HTTP_200_OK)

    @swagger_helper("Signup", "")
    @action(detail=False, methods=['post'], url_path='resend-otp')
    def resend_otp(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"data": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return Response({"data": "User is already verified."}, status=status.HTTP_400_BAD_REQUEST)

        otp = random.randint(100000, 999999)
        user.otp = otp
        user.otp_created_at = now()
        user.save()

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending OTP email synchronously.")
            send_email_synchronously(
                user_email=email,
                email_type="otp",
                subject="Resend OTP",
                action="Email Verification",
                message="Use the OTP below to verify your email address.",
                otp=otp
            )
        else:
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': email,
                    'email_type': "otp",
                    'subject': "Resend OTP",
                    'action': "Email Verification",
                    'message': "Use the OTP below to verify your email address.",
                    'otp': otp
                }
            )
        return Response({"data": f"OTP resent to your email."}, status=status.HTTP_200_OK)


class UserLoginViewSet(viewsets.ModelViewSet):

    def get_serializer_class(self):
        if self.action == 'create':
            return LoginSerializer
        if self.action == 'refresh_token':
            return RefreshTokenSerializer

    @swagger_helper("Login", "")
    def create(self, request, *args, **kwargs):
        if request.method != 'POST':
            return Response({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        data = request.data
        email = data.get('email')
        password = data.get('password')

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'message': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_verified:
            return Response({'message': 'Please verify your email first'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({'message': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        if not is_celery_healthy():
            logger.warning("Celery is not healthy. Sending auth success email synchronously.")
            send_email_synchronously(
                user_email=email,
                action="login"
            )
        else:
            send_auth_success_email.apply_async(
                kwargs={
                    'user_email': email,
                    'action': "login"
                }
            )

        return Response({
            'message': 'Login successful.',
            'access_token': access_token,
            'refresh_token': str(refresh),
        }, status=status.HTTP_200_OK)

    @swagger_helper("Login", "")
    @action(detail=False, methods=['post'], url_path='refresh-token')
    def refresh_token(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            refresh_token = serializer.validated_data['refresh_token']
            try:
                refresh = RefreshToken(refresh_token)
                access_token = str(refresh.access_token)
                return Response({
                    'message': 'Access token generated successfully.',
                    'access_token': access_token,
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'message': 'Invalid or expired refresh token'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "logout":
            return LogoutSerializer

    @swagger_helper("Logout", "", "Authentication required for logout. just pass auth key (JWT)")
    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": "Error during logout.", "data": str(e)}, status=status.HTTP_400_BAD_REQUEST)
