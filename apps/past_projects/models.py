from django.db import models
from django.utils.text import slugify


class ProjectCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "project categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PastProject(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    short_description = models.TextField(blank=True, help_text="Brief description for listings")

    # Images - up to 5 images
    image1 = models.ImageField(upload_to="past_projects/")
    image2 = models.ImageField(upload_to="past_projects/", null=True, blank=True)
    image3 = models.ImageField(upload_to="past_projects/", null=True, blank=True)
    image4 = models.ImageField(upload_to="past_projects/", null=True, blank=True)
    image5 = models.ImageField(upload_to="past_projects/", null=True, blank=True)

    # Category and tags
    category = models.ForeignKey(ProjectCategory, on_delete=models.CASCADE, related_name='projects')

    # Status and visibility
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    featured_position = models.PositiveIntegerField(null=True, blank=True)

    # Additional info
    location = models.CharField(max_length=200, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    client_name = models.CharField(max_length=200, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', 'featured_position', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title