from django.contrib import admin

from .models import Artwork, Category, Comment, ContactRequest, Review, Style, Technique


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


admin.site.register(Category, CategoryAdmin)


class StyleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


admin.site.register(Style, StyleAdmin)


class TechniqueAdmin(admin.ModelAdmin):
    list_display = ('name', 'style')
    list_filter = ('style',)
    search_fields = ('name',)
    list_select_related = ('style',)


admin.site.register(Technique, TechniqueAdmin)


class ArtworkAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'artist', 'category', 'style', 'technique',
        'price', 'is_published', 'created_at',
    )
    list_filter = ('category', 'style', 'technique', 'is_published')
    search_fields = ('title', 'description')
    list_editable = ('is_published',)
    list_select_related = ('artist', 'category', 'style', 'technique')
    readonly_fields = ('created_at',)


admin.site.register(Artwork, ArtworkAdmin)


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('artwork', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved')
    search_fields = ('text', 'artwork__title', 'user__username')
    list_editable = ('is_approved',)
    list_select_related = ('artwork', 'user')
    readonly_fields = ('created_at',)


admin.site.register(Review, ReviewAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('artwork', 'user', 'is_approved', 'created_at')
    list_filter = ('is_approved',)
    search_fields = ('text', 'artwork__title', 'user__username')
    list_editable = ('is_approved',)
    list_select_related = ('artwork', 'user')
    readonly_fields = ('created_at',)


admin.site.register(Comment, CommentAdmin)


class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'artwork', 'is_processed', 'created_at')
    list_filter = ('is_processed',)
    search_fields = ('name', 'email', 'message')
    list_editable = ('is_processed',)
    list_select_related = ('artwork', 'user')
    readonly_fields = ('created_at',)


admin.site.register(ContactRequest, ContactRequestAdmin)
