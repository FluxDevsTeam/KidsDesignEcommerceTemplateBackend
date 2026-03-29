from django.db import models


class InventoryCategory(models.Model):
    """Proxy model for KDC InventoryCategory"""
    name = models.CharField(max_length=200, unique=True)
    index = models.PositiveIntegerField(null=True, blank=True, help_text="Display order index")
    created_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_categories_created')
    edited_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_categories_edited')
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'shop_inventorycategory'
        verbose_name_plural = "inventory categories"
        ordering = ['index', 'name']

    def __str__(self):
        return f"{self.name}"


class InventorySubCategory(models.Model):
    """Proxy model for KDC InventorySubCategory"""
    category = models.ForeignKey(InventoryCategory, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'shop_inventorysubcategory'
        verbose_name_plural = "inventory sub-categories"
        ordering = ['category', 'name']
        unique_together = ['category', 'name']

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class InventoryItem(models.Model):
    """Proxy model for KDC InventoryItem"""
    OPERATION_CHOICES = [
        ('factory', 'Factory'),
        ('shop', 'Shop'),
        ('general', 'General'),
    ]

    SIZE_CHOICES = [
        ('Very Small', 'Very Small'),
        ('Small', 'Small'),
        ('Medium', 'Medium'),
        ('Large', 'Large'),
        ('Very Large', 'Very Large'),
        ('XXL', 'XXL')
    ]

    WEIGHT_CHOICES = [
        ('Very Light', 'Very Light'),
        ('Light', 'Light'),
        ('Medium', 'Medium'),
        ('Heavy', 'Heavy'),
        ('Very Heavy', 'Very Heavy'),
        ('XXHeavy', 'XXHeavy')
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(InventoryCategory, on_delete=models.SET_NULL, null=True, blank=True)
    sub_category = models.ForeignKey(InventorySubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="inventory_items")
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="shop/", blank=True, null=True)
    image1 = models.ImageField(upload_to="shop/", blank=True, null=True)
    image2 = models.ImageField(upload_to="shop/", blank=True, null=True)
    image3 = models.ImageField(upload_to="shop/", blank=True, null=True)
    colour = models.CharField(max_length=50, blank=True, null=True)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    dimensions = models.CharField(max_length=100)
    archived = models.BooleanField(default=False)
    operation_type = models.CharField(max_length=10, choices=OPERATION_CHOICES, default='shop')

    # Ecommerce fields (for website sales)
    is_available = models.BooleanField(default=True, help_text="Is item available for sale on ecommerce?")
    latest_item = models.BooleanField(default=False, help_text="Mark as new arrival for ecommerce")
    latest_item_position = models.PositiveIntegerField(null=True, blank=True, help_text="Display position for new arrivals")
    top_selling_items = models.BooleanField(default=False, help_text="Mark as top selling for ecommerce")
    top_selling_position = models.PositiveIntegerField(null=True, blank=True, help_text="Display position for top selling")
    unlimited = models.BooleanField(default=False, help_text="Unlimited stock (for ecommerce)")
    production_days = models.PositiveIntegerField(default=0, help_text="Days needed to produce this item")
    weight = models.CharField(max_length=50, choices=WEIGHT_CHOICES, null=True, blank=True, help_text="Item weight")
    dimensional_size = models.CharField(max_length=50, choices=SIZE_CHOICES, null=True, blank=True, help_text="Item size")

    created_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_items_created')
    edited_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_items_edited')
    edited_at = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'shop_inventoryitem'

    @property
    def total_price(self):
        return self.stock * self.selling_price

    @property
    def profit_per_item(self):
        return self.selling_price - self.cost_price


class ProductSize(models.Model):
    """Model for product size variants"""
    product = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='sizes')
    size = models.CharField(max_length=50, help_text="Size variant (e.g., Small, Medium, Large)")
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    undiscounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Additional price for this size")
    is_available = models.BooleanField(default=True)
    created_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='product_sizes_created')
    edited_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='product_sizes_edited')
    edited_at = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'shop_productsize'
        unique_together = ['product', 'size']
        verbose_name = "Product Size"
        verbose_name_plural = "Product Sizes"

    @property
    def total_price(self):
        return self.product.selling_price + self.price_adjustment

    def __str__(self):
        return f"{self.product.name} - {self.size}"
