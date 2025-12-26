from django.db import models
from django.utils.text import slugify


class PackageTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Package(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    short_description = models.TextField(blank=True, help_text="Brief description for listings")

    # Images - up to 5 images
    image1 = models.ImageField(upload_to="package_images/")
    image2 = models.ImageField(upload_to="package_images/", null=True, blank=True)
    image3 = models.ImageField(upload_to="package_images/", null=True, blank=True)
    image4 = models.ImageField(upload_to="package_images/", null=True, blank=True)
    image5 = models.ImageField(upload_to="package_images/", null=True, blank=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    undiscounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Tags
    tags = models.ManyToManyField(PackageTag, blank=True, related_name='packages')

    # Status and availability
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    featured_position = models.PositiveIntegerField(null=True, blank=True)

    # Additional info
    duration_days = models.PositiveIntegerField(default=0, help_text="Duration in days")
    includes = models.TextField(blank=True, help_text="What's included in the package")
    requirements = models.TextField(blank=True, help_text="Requirements or prerequisites")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', 'featured_position', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def discount_percentage(self):
        if self.undiscounted_price and self.undiscounted_price > self.price:
            return round(((self.undiscounted_price - self.price) / self.undiscounted_price) * 100, 1)
        return 0

    @property
    def is_on_sale(self):
        return self.undiscounted_price is not None and self.undiscounted_price > self.price