from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Package, PackageTag
from .serializers import PackageTagSerializer, PackageListSerializer, PackageDetailSerializer, PackageCreateUpdateSerializer, PackageSimpleSerializer
from .permissions import IsAdminOrReadOnly
from .pagination import CustomPagination


class ApiPackageTag(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = PackageTag.objects.all()
    serializer_class = PackageTagSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name"]
    ordering = ['name']


class ApiPackage(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name", "description", "short_description", "tags__name"]
    filterset_fields = ["is_active", "is_featured", "tags"]
    ordering_fields = ["price", "created_at", "is_featured", "featured_position"]

    def get_queryset(self):
        queryset = Package.objects.prefetch_related('tags').filter(is_active=True)
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PackageDetailSerializer
        if self.request.method == "GET":
            return PackageListSerializer
        return PackageCreateUpdateSerializer

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured packages"""
        featured_packages = self.get_queryset().filter(is_featured=True).order_by('featured_position', '-created_at')
        page = self.paginate_queryset(featured_packages)
        if page is not None:
            serializer = PackageSimpleSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = PackageSimpleSerializer(featured_packages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search packages"""
        query = request.query_params.get("search", "").strip()

        if not query:
            return Response({"count": 0, "next": None, "previous": None, "results": []})

        search_data = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

        page = self.paginate_queryset(search_data)
        if page is not None:
            serializer = PackageListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = PackageListSerializer(search_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def on_sale(self, request):
        """Get packages that are on sale"""
        sale_packages = self.get_queryset().filter(
            undiscounted_price__isnull=False,
            undiscounted_price__gt=0
        ).order_by('-created_at')

        page = self.paginate_queryset(sale_packages)
        if page is not None:
            serializer = PackageListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = PackageListSerializer(sale_packages, many=True)
        return Response(serializer.data)