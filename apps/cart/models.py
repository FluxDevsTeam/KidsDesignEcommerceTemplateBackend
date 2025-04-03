import uuid
from django.db import models
from django.conf import settings
from ..products.models import Product


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_user")
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    delivery_address = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Cart - {self.id} - {self.user.email}"


class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cartitem_product")
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cartitem_cart")
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"Cart item for cart - {self.cart.id} - {self.cart.user.email}"