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

    def test_api_returns_only_published_artworks(self):
        response = self.client.get(
            reverse("gallery:artwork_api_list"), HTTP_ACCEPT="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Открытая работа")
        self.assertEqual(data[0]["category"], "Живопись")
        self.assertEqual(data[0]["formatted_dimensions"], "30.0 × 40.0 см")
        self.assertEqual(
            data[0]["image_url"], "http://testserver/media/artworks/test.jpg"
        )
        self.assertIsNone(data[0]["average_rating"])
        self.assertEqual(data[0]["approved_comments_count"], 0)
        self.assertNotIn("is_published", data[0])

    def test_api_statistics_ignore_unapproved_feedback(self):
        visitor = get_user_model().objects.create_user(username="api_visitor")
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
            artwork=self.published, user=visitor,
            text="Скрытый комментарий", is_approved=False,
        )

        response = self.client.get(
            reverse("gallery:artwork_api_list"), HTTP_ACCEPT="application/json"
        )

        self.assertEqual(response.json()[0]["average_rating"], 5.0)
        self.assertEqual(response.json()[0]["approved_comments_count"], 1)

    def test_api_rejects_post(self):
        response = self.client.post(reverse("gallery:artwork_api_list"), {
            "title": "Новая работа",
        })

        self.assertEqual(response.status_code, 405)
        self.assertEqual(Artwork.objects.count(), 2)

    def test_api_filters_by_style_and_technique(self):
        cases = (
            ({"style": "Абстракция"}, 1),
            ({"style": "Неизвестный стиль"}, 0),
            ({"technique": "Акрил"}, 1),
            ({"technique": "Неизвестная техника"}, 0),
            ({"style": "Абстракция", "technique": "Акрил"}, 1),
        )

        for parameters, expected_count in cases:
            response = self.client.get(
                reverse("gallery:artwork_api_list"), parameters,
                HTTP_ACCEPT="application/json",
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()), expected_count, str(parameters))

    def test_api_filters_by_year_and_price(self):
        self.published.price = "25000.00"
        self.published.save(update_fields=["price"])
        cases = (
            ({"year_min": "2025"}, 1),
            ({"year_min": "2026"}, 0),
            ({"year_max": "2025"}, 1),
            ({"year_max": "2024"}, 0),
            ({"price_min": "20000"}, 1),
            ({"price_min": "30000"}, 0),
            ({"price_max": "30000"}, 1),
            ({"price_max": "20000"}, 0),
            ({"year_min": "2025", "price_max": "30000"}, 1),
            ({"year_min": "2026", "price_max": "30000"}, 0),
        )

        for parameters, expected_count in cases:
            response = self.client.get(
                reverse("gallery:artwork_api_list"), parameters,
                HTTP_ACCEPT="application/json",
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()), expected_count, str(parameters))

    def test_api_rejects_invalid_number_filter(self):
        cases = (
            ("year_min", "не число"),
            ("year_min", "2022.5"),
            ("price_max", "-1"),
        )

        for field_name, value in cases:
            response = self.client.get(
                reverse("gallery:artwork_api_list"), {field_name: value},
                HTTP_ACCEPT="application/json",
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn(field_name, response.json()["errors"])
