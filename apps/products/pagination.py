from rest_framework.pagination import PageNumberPagination
from drf_yasg import openapi


class CustomPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100

#
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
#     @swagger_auto_schema(manual_parameters=PAGINATION_PARAMS, operation_id="list product category", operation_description="retrieve a list of product categories", tags=["ProductCategory"])
