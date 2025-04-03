from django.db import models
from ..products.models import Product
from django.conf import settings


class Wishlist(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlist_product")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_user")
    date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        verbose_name = "wishlist item"
        verbose_name_plural = "wishlist items"
