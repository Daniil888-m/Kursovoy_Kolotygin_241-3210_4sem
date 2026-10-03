from django.urls import path

from . import api_views, views


app_name = "gallery"

urlpatterns = [
    path("", views.artwork_list, name="artwork_list"),
    path("api/artworks/", api_views.artwork_api_list, name="artwork_api_list"),
    path("contact/", views.contact_request, name="contact"),
    path("contact/success/", views.contact_success, name="contact_success"),
    path("artworks/<int:pk>/", views.artwork_detail, name="artwork_detail"),
    path("artworks/<int:pk>/contact/", views.contact_request, name="artwork_contact"),
]
