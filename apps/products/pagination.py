from rest_framework.pagination import PageNumberPagination
from drf_yasg import openapi
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
        })


PAGINATION_PARAMS = [
    openapi.Parameter(
        'page',
        openapi.IN_QUERY,
        description="Page number",
        type=openapi.TYPE_INTEGER
    ),
    openapi.Parameter(
        'page_size',
        openapi.IN_QUERY,
        description="Items per page (max: 100)",
        type=openapi.TYPE_INTEGER
    )
]

PRODUCT_PAGINATION_PARAMS = [
    openapi.Parameter(
        'search',
        openapi.IN_QUERY,
        description="Search keyword",
        type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        'page',
        openapi.IN_QUERY,
        description="Page number",
        type=openapi.TYPE_INTEGER
    ),
    openapi.Parameter(
        'page_size',
        openapi.IN_QUERY,
        description="Items per page (max: 100)",
        type=openapi.TYPE_INTEGER
    ),
    # Filter fields from ProductFilter
    openapi.Parameter(
        'sub_category',
        openapi.IN_QUERY,
        description="Filter by sub-category ID",
        type=openapi.TYPE_INTEGER
    ),
    openapi.Parameter(
        'sub_category__category',
        openapi.IN_QUERY,
        description="Filter by category ID",
        type=openapi.TYPE_INTEGER
    ),
    openapi.Parameter(
        'min_price',
        openapi.IN_QUERY,
        description="Minimum price (inclusive)",
        type=openapi.TYPE_NUMBER
    ),
    openapi.Parameter(
        'max_price',
        openapi.IN_QUERY,
        description="Maximum price (inclusive)",
        type=openapi.TYPE_NUMBER
    ),
    openapi.Parameter(
        'is_available',
        openapi.IN_QUERY,
        description="Filter by availability",
        type=openapi.TYPE_BOOLEAN
    ),
    openapi.Parameter(
        'latest_item',
        openapi.IN_QUERY,
        description="Filter by latest items",
        type=openapi.TYPE_BOOLEAN
    ),
    openapi.Parameter(
        'top_selling_items',
        openapi.IN_QUERY,
        description="Filter by top-selling items",
        type=openapi.TYPE_BOOLEAN
    ),
    openapi.Parameter(
        'discount',
        openapi.IN_QUERY,
        description="Filter by discounted items",
        type=openapi.TYPE_BOOLEAN
    ),
]


HOMEPAGE_PAGINATION_PARAMS = [
    openapi.Parameter(
        'page_size',
        openapi.IN_QUERY,
        description="Items per page (default: 10, max: 100)",
        type=openapi.TYPE_INTEGER
    ),
]
