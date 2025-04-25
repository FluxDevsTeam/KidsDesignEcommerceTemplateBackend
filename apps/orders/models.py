from django.db import models
from django.conf import settings
from ..products.models import Product
import uuid

# Status choices
STATUS_CHOICES = (
    ('PAID', 'Paid'),
    ('SHIPPED', 'Shipped'),
    ('DELIVERED', 'Delivered'),
    ('CANCELLED', 'Cancelled'),
    ('REFUNDED', 'Refunded'),
)


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="order_user")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(null=True)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    delivery_address = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=50)
    order_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    payment_provider = models.CharField(max_length=20, null=True, blank=True)
    estimated_delivery = models.CharField(max_length=100)

    def __str__(self):
        return f"Order - {self.id} - {self.user.email}"


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="orderitem_product")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="orderitem_order")
    quantity = models.PositiveIntegerField()
    # create duplicate of products
    name = models.CharField(max_length=100)
    description = models.TextField()
    colour = models.CharField(max_length=100)
    image1 = models.ImageField(upload_to="order_images/")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=50) 

    def __str__(self):
        return f"Order item for order - {self.order.id} - {self.order.user.email}"
