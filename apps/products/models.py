from django.db import models

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


class ProductCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "product categories"

    def __str__(self):
        return self.name


class ProductSubCategory(models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "product sub-categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    sub_category = models.ForeignKey(ProductSubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    colour = models.CharField(max_length=100)
    image1 = models.ImageField(upload_to="product_images/")
    image2 = models.ImageField(upload_to="product_images/", null=True, blank=True)
    image3 = models.ImageField(upload_to="product_images/", null=True, blank=True)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.CharField(max_length=50, choices=WEIGHT_CHOICES, default="Light")
    dimensional_size = models.CharField(max_length=50, choices=SIZE_CHOICES, default="Small")
    is_available = models.BooleanField(default=True)
    latest_item = models.BooleanField(default=False)
    latest_item_position = models.PositiveIntegerField(null=True, blank=True)
    top_selling_items = models.BooleanField(default=False)
    top_selling_position = models.PositiveIntegerField(null=True, blank=True)
    date_created = models.DateField(auto_now_add=True)
    date_updated = models.DateField(auto_now=True)

    def __str__(self):
        return self.name


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sizes")
    size = models.CharField(max_length=100, unique=True)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} -- {self.size}"
