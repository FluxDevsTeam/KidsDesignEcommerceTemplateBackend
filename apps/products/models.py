from django.db import models


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
        verbose_name_plural = "product subcategories"

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
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sizes")
    size = models.CharField(max_length=100, unique=True)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} -- {self.size}"
