from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ProjectCategory, PastProject
from .serializers import ProjectCategorySerializer, PastProjectListSerializer, PastProjectDetailSerializer, PastProjectCreateUpdateSerializer
from .permissions import IsAdminOrReadOnly
from .pagination import CustomPagination


class ApiProjectCategory(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = ProjectCategory.objects.all()
    serializer_class = ProjectCategorySerializer
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name"]
    ordering = ['name']


class ApiPastProject(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["title", "description", "short_description", "category__name"]
    filterset_fields = ["is_active", "is_featured", "category"]

    def get_queryset(self):
        queryset = PastProject.objects.select_related('category').filter(is_active=True)
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PastProjectDetailSerializer
        if self.request.method == "GET":
            return PastProjectListSerializer
        return PastProjectCreateUpdateSerializer

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured projects"""
        featured_projects = self.get_queryset().filter(is_featured=True).order_by('featured_position', '-created_at')
        page = self.paginate_queryset(featured_projects)
        if page is not None:
            serializer = PastProjectListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = PastProjectListSerializer(featured_projects, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get projects by category"""
        category_slug = request.query_params.get('category')
        if not category_slug:
            return Response({"error": "Category parameter is required"}, status=400)

        try:
            category = ProjectCategory.objects.get(slug=category_slug)
            projects = self.get_queryset().filter(category=category)
            page = self.paginate_queryset(projects)
            if page is not None:
                serializer = PastProjectListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = PastProjectListSerializer(projects, many=True)
            return Response(serializer.data)
        except ProjectCategory.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)