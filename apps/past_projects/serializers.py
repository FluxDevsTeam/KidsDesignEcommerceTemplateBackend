from rest_framework import serializers
from .models import ProjectCategory, PastProject


class ProjectCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCategory
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['id', 'slug']


class PastProjectListSerializer(serializers.ModelSerializer):
    category = ProjectCategorySerializer(read_only=True)

    class Meta:
        model = PastProject
        fields = ['id', 'title', 'slug', 'short_description', 'image1', 'category', 'location', 'completion_date', 'client_name', 'is_featured', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at']


class PastProjectDetailSerializer(serializers.ModelSerializer):
    category = ProjectCategorySerializer(read_only=True)

    class Meta:
        model = PastProject
        fields = ['id', 'title', 'slug', 'description', 'short_description', 'image1', 'image2', 'image3', 'image4', 'image5', 'category', 'location', 'completion_date', 'client_name', 'is_featured', 'featured_position', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class PastProjectCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PastProject
        fields = ['title', 'description', 'short_description', 'image1', 'image2', 'image3', 'image4', 'image5', 'category', 'is_active', 'is_featured', 'featured_position', 'location', 'completion_date', 'client_name']