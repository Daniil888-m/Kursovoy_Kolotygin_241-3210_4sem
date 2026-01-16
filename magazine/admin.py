from django.contrib import admin
from .models import Category, Author, Article, Issue, Comment, Tag
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class ArticleResource(resources.ModelResource):
    class Meta:
        model = Article
        fields = ('title', 'author', 'category', 'pub_date', 'content')

class AuthorResource(resources.ModelResource):
    class Meta:
        model = Author
        fields = ('name', 'bio')

admin.site.register(Category, admin.ModelAdmin(
    list_display=['name'],
    search_fields=['name'],
    list_display_links=['name']
))

admin.site.register(Author, ImportExportModelAdmin(
    resource_class=AuthorResource,
    list_display=['name', 'bio'],
    search_fields=['name'],
    list_filter=['name']
))

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1

class ArticleAdmin(ImportExportModelAdmin):
    resource_class = ArticleResource
    list_display = ['title', 'author', 'category', 'pub_date']  # ← pub_date!
    list_filter = ['category', 'author', 'pub_date']  # ← pub_date!
    search_fields = ['title', 'content']
    date_hierarchy = 'pub_date'  # ← pub_date!
    list_display_links = ['title']
    inlines = [CommentInline]

admin.site.register(Article, ArticleAdmin)

admin.site.register(Issue, admin.ModelAdmin(
    list_display=['number', 'pub_date'],  # ← pub_date!
    filter_horizontal=['articles'],
    list_filter=['pub_date']
))

admin.site.register(Comment, admin.ModelAdmin(
    list_display=['article', 'author', 'createdat'],
    list_filter=['createdat', 'article'],
    readonly_fields=['createdat']
))

admin.site.register(Tag, admin.ModelAdmin(
    list_display=['name'],
    filter_horizontal=['articles'],
    search_fields=['name']
))
