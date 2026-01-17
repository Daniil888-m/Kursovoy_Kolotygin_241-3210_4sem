from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'articles', views.ArticleViewSet)
router.register(r'authors', views.AuthorViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
