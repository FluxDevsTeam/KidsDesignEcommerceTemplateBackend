from rest_framework import serializers
from .models import Package, PackageTag


class PackageTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageTag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id', 'slug']


class PackageListSerializer(serializers.ModelSerializer):
    tags = PackageTagSerializer(many=True, read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = ['id', 'name', 'slug', 'short_description', 'image1', 'price', 'undiscounted_price', 'discount_percentage', 'is_on_sale', 'is_featured', 'duration_days', 'tags', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_discount_percentage(self, obj):
        return obj.discount_percentage

    def get_is_on_sale(self, obj):
        return obj.is_on_sale


class PackageDetailSerializer(serializers.ModelSerializer):
    tags = PackageTagSerializer(many=True, read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = ['id', 'name', 'slug', 'description', 'short_description', 'image1', 'image2', 'image3', 'image4', 'image5', 'price', 'undiscounted_price', 'discount_percentage', 'is_on_sale', 'is_featured', 'featured_position', 'duration_days', 'includes', 'requirements', 'tags', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_discount_percentage(self, obj):
        return obj.discount_percentage

    def get_is_on_sale(self, obj):
        return obj.is_on_sale


class PackageCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)

    class Meta:
        model = Package
        fields = ['name', 'description', 'short_description', 'image1', 'image2', 'image3', 'image4', 'image5', 'price', 'undiscounted_price', 'tags', 'is_active', 'is_featured', 'featured_position', 'duration_days', 'includes', 'requirements']

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        package = Package.objects.create(**validated_data)
        self._handle_tags(package, tags_data)
        return package

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        self._handle_tags(instance, tags_data)
        return instance

    def _handle_tags(self, package, tags_data):
        if tags_data:
            tags = []
            for tag_name in tags_data:
                tag, created = PackageTag.objects.get_or_create(name=tag_name.strip())
                tags.append(tag)
            package.tags.set(tags)


class PackageSimpleSerializer(serializers.ModelSerializer):
    discount_percentage = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = ['id', 'name', 'slug', 'short_description', 'image1', 'price', 'undiscounted_price', 'discount_percentage', 'is_on_sale', 'is_featured', 'duration_days']
        read_only_fields = ['id', 'name', 'slug', 'short_description', 'image1', 'price', 'undiscounted_price', 'discount_percentage', 'is_on_sale', 'is_featured', 'duration_days']

    def get_discount_percentage(self, obj):
        return obj.discount_percentage

    def get_is_on_sale(self, obj):
        return obj.is_on_sale