from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Subscriber, NewsletterCampaign
from .serializers import SubscriberSerializer, SubscriberCreateSerializer, NewsletterCampaignSerializer, NewsletterCampaignCreateSerializer, NewsletterCampaignListSerializer
from .permissions import IsAdminOrReadOnly
from .pagination import CustomPagination


class ApiNewsletterSubscriber(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["email", "user__username"]
    filterset_fields = ["status"]

    def get_queryset(self):
        return Subscriber.objects.select_related('user')

    def get_serializer_class(self):
        if self.action == "subscribe":
            return SubscriberCreateSerializer
        return SubscriberSerializer

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def subscribe(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            subscriber = serializer.save()
            return Response({
                "message": "Successfully subscribed to newsletter",
                "subscriber": SubscriberSerializer(subscriber).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def unsubscribe(self, request):
        email = request.data.get('email')
        token = request.query_params.get('token')

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subscriber = Subscriber.objects.get(email=email)
            subscriber.status = 'unsubscribed'
            subscriber.save()
            return Response({"message": "Successfully unsubscribed from newsletter"})
        except Subscriber.DoesNotExist:
            return Response({"error": "Subscriber not found"}, status=status.HTTP_404_NOT_FOUND)


class ApiNewsletterCampaign(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["subject", "content"]
    filterset_fields = ["status", "recipients_filter"]

    def get_queryset(self):
        return NewsletterCampaign.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return NewsletterCampaignListSerializer
        if self.request.method == "POST":
            return NewsletterCampaignCreateSerializer
        return NewsletterCampaignSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)

        total_sent_all_time = NewsletterCampaign.objects.aggregate(total=Sum('total_sent'))['total'] or 0
        total_campaigns = NewsletterCampaign.objects.count()
        active_subscribers = Subscriber.objects.filter(status='active').count()
        total_subscribers = Subscriber.objects.count()

        # Calculate average rates
        campaigns_with_data = NewsletterCampaign.objects.filter(total_sent__gt=0)
        if campaigns_with_data.exists():
            avg_open_rate = campaigns_with_data.aggregate(avg=Sum('open_count') / Sum('total_sent'))['avg'] or 0
            avg_click_rate = campaigns_with_data.aggregate(avg=Sum('click_count') / Sum('total_sent'))['avg'] or 0
        else:
            avg_open_rate = 0
            avg_click_rate = 0

        return Response({
            "total_sent_all_time": total_sent_all_time,
            "total_campaigns": total_campaigns,
            "avg_open_rate": round(avg_open_rate * 100, 2) if avg_open_rate else 0,
            "avg_click_rate": round(avg_click_rate * 100, 2) if avg_click_rate else 0,
            "total_subscribers": total_subscribers,
            "active_subscribers": active_subscribers
        })

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)

        campaign = self.get_object()
        if campaign.status == 'sent':
            return Response({"error": "Campaign has already been sent"}, status=status.HTTP_400_BAD_REQUEST)

        # Trigger Celery task
        from .tasks import send_newsletter_campaign
        send_newsletter_campaign.delay(campaign.id)

        campaign.status = 'sent'
        campaign.sent_at = timezone.now()
        campaign.save()

        return Response({"message": "Newsletter campaign sending initiated"})