from django.contrib.auth import views as auth_views
from django.urls import path

from . import api_views, views


app_name = "gallery"

urlpatterns = [
    path("", views.artwork_list, name="artwork_list"),
    path("api/artworks/", api_views.artwork_api_list, name="artwork_api_list"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="gallery/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("contact/", views.contact_request, name="contact"),
    path("contact/success/", views.contact_success, name="contact_success"),
    path("artworks/<int:pk>/", views.artwork_detail, name="artwork_detail"),
    path("artworks/<int:pk>/contact/", views.contact_request, name="artwork_contact"),
    path("artworks/<int:pk>/review/", views.review_create, name="review_create"),
    path("artworks/<int:pk>/comment/", views.comment_create, name="comment_create"),
]
