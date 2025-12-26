from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Package, Consultation
from .serializers import PackageSerializer, ConsultationSerializer, ConsultationCreateSerializer
from .permissions import IsAdminOrOwner, IsAdminOrReadOnly
from .pagination import CustomPagination


class ApiConsultationPackage(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = Package.objects.filter(is_active=True)
    serializer_class = PackageSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name", "description"]
    ordering = ['name']


class ApiConsultation(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrOwner]
    search_fields = ["user__username", "user__first_name", "user__last_name", "package__name"]
    filterset_fields = ["status", "scheduled_date", "package"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Consultation.objects.select_related('user', 'package')
        return Consultation.objects.filter(user=user).select_related('user', 'package')

    def get_serializer_class(self):
        if self.action == "create":
            return ConsultationCreateSerializer
        return ConsultationSerializer

    def perform_create(self, serializer):
        consultation = serializer.save(user=self.request.user)
        # Send confirmation email to user
        from .tasks import send_consultation_request_confirmation_email
        send_consultation_request_confirmation_email.delay(consultation.id)
        # Send notification email to admin
        from .tasks import send_admin_consultation_notification_email
        send_admin_consultation_notification_email.delay(consultation.id)

    @action(detail=False, methods=['get'])
    def my_consultations(self, request):
        """Get current user's consultations"""
        consultations = self.get_queryset().filter(user=request.user)
        page = self.paginate_queryset(consultations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(consultations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)

        consultation = self.get_object()
        consultation.status = 'confirmed'
        consultation.save()

        # Send confirmation email
        from .tasks import send_consultation_confirmation_email
        send_consultation_confirmation_email.delay(consultation.id)

        serializer = self.get_serializer(consultation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        consultation = self.get_object()
        if not request.user.is_staff and consultation.user != request.user:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        consultation.status = 'cancelled'
        consultation.save()

        # Send cancellation email
        from .tasks import send_consultation_update_email
        send_consultation_update_email.delay(consultation.id, 'cancelled')

        serializer = self.get_serializer(consultation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)

        consultation = self.get_object()
        consultation.status = 'completed'
        consultation.save()

        # Send completion email
        from .tasks import send_consultation_update_email
        send_consultation_update_email.delay(consultation.id, 'completed')

        serializer = self.get_serializer(consultation)
        return Response(serializer.data)