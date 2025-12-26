from rest_framework import serializers
from .models import Category, Tag, Post


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['id', 'slug']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id', 'slug']


class PostListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'excerpt', 'author_name', 'category_name', 'tags', 'featured_image', 'status', 'publish_date', 'created_at', 'views', 'comment_count']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'views', 'comment_count']


class PostDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'excerpt', 'content', 'author_name', 'category', 'tags', 'featured_image', 'status', 'publish_date', 'created_at', 'updated_at', 'views', 'comment_count']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'views', 'comment_count']


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)

    class Meta:
        model = Post
        fields = ['title', 'excerpt', 'content', 'category', 'tags', 'featured_image', 'status', 'publish_date']

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)
        self._handle_tags(post, tags_data)
        return post

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        self._handle_tags(instance, tags_data)
        return instance

    def _handle_tags(self, post, tags_data):
        if tags_data:
            tags = []
            for tag_name in tags_data:
                tag, created = Tag.objects.get_or_create(name=tag_name.strip())
                tags.append(tag)
            post.tags.set(tags)