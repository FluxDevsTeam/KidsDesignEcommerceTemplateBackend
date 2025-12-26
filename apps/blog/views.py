from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Tag, Post
from .serializers import CategorySerializer, TagSerializer, PostListSerializer, PostDetailSerializer, PostCreateUpdateSerializer
from .permissions import IsAdminOrAuthorOrReadOnly, IsAdminOrReadOnly
from .pagination import CustomPagination


class ApiBlogCategory(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name"]
    ordering = ['name']


class ApiBlogTag(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name"]
    ordering = ['name']


class ApiBlogPost(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrAuthorOrReadOnly]
    search_fields = ["title", "content", "excerpt"]
    filterset_fields = ["category", "tags", "status", "author"]
    ordering_fields = ["publish_date", "created_at", "views"]

    def get_queryset(self):
        queryset = Post.objects.select_related('author', 'category').prefetch_related('tags')
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='published')
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PostDetailSerializer
        if self.request.method == "GET":
            return PostListSerializer
        return PostCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'])
    def retrieve_by_slug(self, request, slug=None):
        post = get_object_or_404(self.get_queryset(), slug=slug)
        post.views += 1
        post.save(update_fields=['views'])
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)

        total_posts = Post.objects.count()
        total_views = Post.objects.aggregate(total=models.Sum('views'))['total'] or 0
        total_comments = Post.objects.aggregate(total=models.Sum('comment_count'))['total'] or 0
        posts_by_category = Post.objects.values('category__name').annotate(count=models.Count('id')).order_by('-count')

        return Response({
            "total_posts": total_posts,
            "total_views": total_views,
            "total_comments": total_comments,
            "posts_by_category": posts_by_category
        })