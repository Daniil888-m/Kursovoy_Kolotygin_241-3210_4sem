from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Artwork, Category, Comment, ContactRequest, Review, Style, Technique


class PublicGalleryTests(TestCase):
    def setUp(self):
        artist = get_user_model().objects.create_user(username="test_artist")
        category = Category.objects.create(name="Живопись")
        style = Style.objects.create(name="Абстракция")
        technique = Technique.objects.create(name="Акрил", style=style)

        artwork_data = {
            "artist": artist,
            "category": category,
            "style": style,
            "technique": technique,
            "description": "Описание работы",
            "materials": "Холст, акрил",
            "year_created": 2025,
            "width_cm": "30.0",
            "height_cm": "40.0",
            "image": "artworks/test.jpg",
        }
        self.published = Artwork.objects.create(
            title="Открытая работа", is_published=True, **artwork_data
        )
        self.draft = Artwork.objects.create(
            title="Скрытый черновик", is_published=False, **artwork_data
        )
        self.artist = artist

    def test_list_shows_only_published_artworks(self):
        response = self.client.get(reverse("gallery:artwork_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Открытая работа")
        self.assertNotContains(response, "Скрытый черновик")

    def test_draft_detail_returns_404(self):
        response = self.client.get(
            reverse("gallery:artwork_detail", args=[self.draft.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_search_filters_artworks(self):
        response = self.client.get(reverse("gallery:artwork_list"), {"q": "нет такого"})

        self.assertContains(response, "Работы не найдены")
        self.assertNotContains(response, "Открытая работа")

    def test_detail_shows_only_approved_feedback(self):
        visitor = get_user_model().objects.create_user(username="test_visitor")
        Review.objects.create(
            artwork=self.published, user=self.artist, rating=5,
            text="Одобренный отзыв", is_approved=True,
        )
        Review.objects.create(
            artwork=self.published, user=visitor, rating=1,
            text="Скрытый отзыв", is_approved=False,
        )
        Comment.objects.create(
            artwork=self.published, user=self.artist,
            text="Одобренный комментарий", is_approved=True,
        )
        Comment.objects.create(
            artwork=self.published, user=self.artist,
            text="Скрытый комментарий", is_approved=False,
        )

        response = self.client.get(
            reverse("gallery:artwork_detail", args=[self.published.pk])
        )

        self.assertContains(response, "Одобренный отзыв")
        self.assertContains(response, "Одобренный комментарий")
        self.assertNotContains(response, "Скрытый отзыв")
        self.assertNotContains(response, "Скрытый комментарий")

    def test_general_contact_form_creates_request(self):
        response = self.client.post(reverse("gallery:contact"), {
            "name": "Анна",
            "email": "anna@example.com",
            "message": "Здравствуйте, хочу узнать о работах.",
        })

        self.assertRedirects(response, reverse("gallery:contact_success"))
        contact = ContactRequest.objects.get()
        self.assertEqual(contact.name, "Анна")
        self.assertIsNone(contact.artwork)
        self.assertIsNone(contact.user)
        self.assertFalse(contact.is_processed)

    def test_artwork_contact_links_artwork_and_signed_in_user(self):
        self.client.force_login(self.artist)
        response = self.client.post(
            reverse("gallery:artwork_contact", args=[self.published.pk]),
            {
                "name": "Художник",
                "email": "artist@example.com",
                "message": "Вопрос об этой работе.",
            },
        )

        self.assertRedirects(response, reverse("gallery:contact_success"))
        contact = ContactRequest.objects.get()
        self.assertEqual(contact.artwork, self.published)
        self.assertEqual(contact.user, self.artist)

    def test_invalid_email_does_not_create_request(self):
        response = self.client.post(reverse("gallery:contact"), {
            "name": "Анна",
            "email": "неправильный адрес",
            "message": "Здравствуйте, хочу узнать о работах.",
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertFalse(ContactRequest.objects.exists())

    def test_draft_contact_returns_404(self):
        response = self.client.get(
            reverse("gallery:artwork_contact", args=[self.draft.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_statistics_count_only_approved_feedback(self):
        visitor_one = get_user_model().objects.create_user(username="visitor_one")
        visitor_two = get_user_model().objects.create_user(username="visitor_two")
        Review.objects.create(
            artwork=self.published, user=self.artist, rating=3, text="Первый",
            is_approved=True,
        )
        Review.objects.create(
            artwork=self.published, user=visitor_one, rating=5, text="Второй",
            is_approved=True,
        )
        Review.objects.create(
            artwork=self.published, user=visitor_two, rating=1, text="Скрытый",
            is_approved=False,
        )
        Comment.objects.create(
            artwork=self.published, user=self.artist, text="Один",
            is_approved=True,
        )
        Comment.objects.create(
            artwork=self.published, user=visitor_one, text="Два",
            is_approved=True,
        )
        Comment.objects.create(
            artwork=self.published, user=visitor_two, text="Скрытый",
            is_approved=False,
        )

        list_response = self.client.get(reverse("gallery:artwork_list"))
        list_artwork = list_response.context["artworks"].get(pk=self.published.pk)
        detail_response = self.client.get(
            reverse("gallery:artwork_detail", args=[self.published.pk])
        )
        detail_artwork = detail_response.context["artwork"]

        for artwork in (list_artwork, detail_artwork):
            self.assertEqual(artwork.average_rating, 4.0)
            self.assertEqual(artwork.approved_comments_count, 2)

    def test_statistics_without_feedback(self):
        response = self.client.get(
            reverse("gallery:artwork_detail", args=[self.published.pk])
        )

        self.assertIsNone(response.context["artwork"].average_rating)
        self.assertEqual(response.context["artwork"].approved_comments_count, 0)
