from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Tryb3 Foodapp API",
        default_version="v1",
        description="""
            An API selling food.

            **Servers:**
            - Local: [http://localhost:8000](http://localhost:8000)
            - Production: [https://domain.com/](https://domain.com/)
            """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="suskidee@gmail.com"),
        license=openapi.License(name="Test License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

