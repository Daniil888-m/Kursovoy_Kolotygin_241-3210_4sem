from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from datetime import timedelta
from .models import Article, Author, Tag
from .serializers import ArticleSerializer, AuthorSerializer

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name']
    filterset_fields = ['name']

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().order_by('-pub_date')
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'content']
    filterset_fields = ['category', 'author', 'pub_date']

    @action(detail=False, methods=['get'])
    def recent(self, request):
        recent = self.queryset.filter(pub_date__gte=timezone.now() - timedelta(days=30))
        serializer = self.get_serializer(recent, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_tag(self, request, pk=None):
        """POST /magazine/api/articles/{id}/toggle_tag/"""
        article = self.get_object()
        tag_name = request.data.get('tag', 'featured')

        # 1. Получаем или создаем тег (это работало)
        tag, created = Tag.objects.get_or_create(name=tag_name)

        # 2. ИСПРАВЛЕНИЕ: Используем article.tags (так называется ваше поле в models.py)
        if tag in article.tags.all():
            article.tags.remove(tag)
            status = 'тег удалён'
        else:
            article.tags.add(tag)
            status = 'тег добавлен'

        return Response({
            'status': status,
            'tags_count': article.tags.count(),  # Было article.tag_set (ошибка) -> стало article.tags
            'has_featured': article.tags.filter(name='featured').exists()
        })

