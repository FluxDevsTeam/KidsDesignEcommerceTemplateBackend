from django.contrib import admin
from .models import Category, Tag, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'publish_date', 'views']
    list_filter = ['status', 'publish_date', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    actions = ['publish_posts']

    def publish_posts(self, request, queryset):
        updated = queryset.update(status='published')
        if updated == 1:
            message = "1 post was successfully published."
        else:
            message = f"{updated} posts were successfully published."
        self.message_user(request, message)

    publish_posts.short_description = "Publish selected posts"