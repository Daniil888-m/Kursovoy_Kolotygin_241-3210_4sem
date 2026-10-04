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

    def test_guest_cannot_open_feedback_forms(self):
        for route_name in ("gallery:review_create", "gallery:comment_create"):
            form_url = reverse(route_name, args=[self.published.pk])
            response = self.client.get(form_url)

            self.assertEqual(response.status_code, 302)
            self.assertTrue(response["Location"].startswith("/login/?next="))

    def test_review_form_contains_only_public_fields(self):
        self.client.force_login(self.artist)
        response = self.client.get(
            reverse("gallery:review_create", args=[self.published.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.context["form"].fields), {"rating", "text"})
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_review_is_saved_for_current_user_and_waits_for_approval(self):
        self.client.force_login(self.artist)
        other_user = get_user_model().objects.create_user(username="other_user")
        response = self.client.post(
            reverse("gallery:review_create", args=[self.published.pk]),
            {
                "rating": "5",
                "text": "Прекрасная работа",
                "user": other_user.pk,
                "artwork": self.draft.pk,
                "is_approved": "on",
            },
            follow=True,
        )

        self.assertRedirects(
            response, reverse("gallery:artwork_detail", args=[self.published.pk])
        )
        review = Review.objects.get()
        self.assertEqual(review.user, self.artist)
        self.assertEqual(review.artwork, self.published)
        self.assertEqual(review.rating, 5)
        self.assertFalse(review.is_approved)
        self.assertContains(response, "Отзыв отправлен на проверку")
        self.assertNotContains(response, "Прекрасная работа")

    def test_second_review_is_rejected(self):
        Review.objects.create(
            artwork=self.published, user=self.artist, rating=4,
            text="Первый отзыв",
        )
        self.client.force_login(self.artist)
        response = self.client.post(
            reverse("gallery:review_create", args=[self.published.pk]),
            {"rating": "5", "text": "Второй отзыв"},
            follow=True,
        )

        self.assertRedirects(
            response, reverse("gallery:artwork_detail", args=[self.published.pk])
        )
        self.assertEqual(Review.objects.count(), 1)
        self.assertContains(response, "Вы уже оставили отзыв")

    def test_invalid_rating_does_not_create_review(self):
        self.client.force_login(self.artist)
        response = self.client.post(
            reverse("gallery:review_create", args=[self.published.pk]),
            {"rating": "7", "text": "Слишком большая оценка"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("rating", response.context["form"].errors)
        self.assertFalse(Review.objects.exists())

    def test_comment_is_saved_for_current_user_and_waits_for_approval(self):
        self.client.force_login(self.artist)
        response = self.client.post(
            reverse("gallery:comment_create", args=[self.published.pk]),
            {"text": "Очень красиво", "is_approved": "on"},
            follow=True,
        )

        self.assertRedirects(
            response, reverse("gallery:artwork_detail", args=[self.published.pk])
        )
        comment = Comment.objects.get()
        self.assertEqual(comment.user, self.artist)
        self.assertEqual(comment.artwork, self.published)
        self.assertFalse(comment.is_approved)
        self.assertContains(response, "Комментарий отправлен на проверку")
        self.assertNotContains(response, "Очень красиво")

    def test_empty_comment_does_not_create_record(self):
        self.client.force_login(self.artist)
        response = self.client.post(
            reverse("gallery:comment_create", args=[self.published.pk]),
            {"text": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("text", response.context["form"].errors)
        self.assertFalse(Comment.objects.exists())

    def test_draft_rejects_feedback(self):
        self.client.force_login(self.artist)
        for route_name in ("gallery:review_create", "gallery:comment_create"):
            response = self.client.get(reverse(route_name, args=[self.draft.pk]))
            self.assertEqual(response.status_code, 404)

    def test_search_filters_artworks(self):
        response = self.client.get(reverse("gallery:artwork_list"), {"q": "нет такого"})

        self.assertContains(response, "Работы не найдены")
        self.assertNotContains(response, "Открытая работа")

    def test_html_gallery_combines_filters(self):
        self.published.price = "25000.00"
        self.published.save(update_fields=["price"])
        response = self.client.get(reverse("gallery:artwork_list"), {
            "q": "Открытая",
            "category": "Живопись",
            "style": "Абстракция",
            "technique": "Акрил",
            "year_min": "2025",
            "year_max": "2025",
            "price_min": "20000",
            "price_max": "30000",
        })

        self.assertContains(response, "Открытая работа")
        self.assertNotContains(response, "Скрытый черновик")
        self.assertContains(response, "Сбросить")
        self.assertContains(response, 'value="Абстракция" selected')

    def test_html_gallery_filters_out_nonmatching_artwork(self):
        self.published.price = "25000.00"
        self.published.save(update_fields=["price"])
        for parameters in (
            {"style": "Реализм"},
            {"technique": "Масло"},
            {"year_min": "2026"},
            {"price_max": "20000"},
        ):
            with self.subTest(parameters=parameters):
                response = self.client.get(
                    reverse("gallery:artwork_list"), parameters
                )
                self.assertContains(response, "Работы не найдены")
                self.assertNotContains(response, "Открытая работа")

    def test_html_gallery_shows_error_for_invalid_number(self):
        response = self.client.get(
            reverse("gallery:artwork_list"), {"year_min": "не число"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("year_min", response.context["filter_form"].errors)
        self.assertContains(response, "Проверьте значения фильтров")
        self.assertContains(response, "Открытая работа")

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


class AuthenticationTests(TestCase):
    def test_registration_page_shows_form(self):
        response = self.client.get(reverse("gallery:register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Имя пользователя")
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_registration_creates_user_and_logs_in(self):
        password = "StrongUniquePass123!"
        response = self.client.post(reverse("gallery:register"), {
            "username": "new_visitor",
            "password1": password,
            "password2": password,
        })

        self.assertRedirects(response, reverse("gallery:artwork_list"))
        user = get_user_model().objects.get(username="new_visitor")
        self.assertTrue(user.check_password(password))
        self.assertNotEqual(user.password, password)
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        self.assertFalse(user.is_staff)

    def test_registration_rejects_different_passwords(self):
        response = self.client.post(reverse("gallery:register"), {
            "username": "new_visitor",
            "password1": "StrongUniquePass123!",
            "password2": "AnotherStrongPass123!",
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("password2", response.context["form"].errors)
        self.assertFalse(get_user_model().objects.exists())

    def test_registration_rejects_existing_username(self):
        get_user_model().objects.create_user(username="existing_visitor")
        response = self.client.post(reverse("gallery:register"), {
            "username": "existing_visitor",
            "password1": "StrongUniquePass123!",
            "password2": "StrongUniquePass123!",
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("username", response.context["form"].errors)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_valid_login_opens_session(self):
        user = get_user_model().objects.create_user(
            username="returning_visitor", password="StrongUniquePass123!"
        )
        response = self.client.post(reverse("gallery:login"), {
            "username": "returning_visitor",
            "password": "StrongUniquePass123!",
        })

        self.assertRedirects(response, reverse("gallery:artwork_list"))
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    def test_wrong_password_does_not_log_in(self):
        get_user_model().objects.create_user(
            username="returning_visitor", password="StrongUniquePass123!"
        )
        response = self.client.post(reverse("gallery:login"), {
            "username": "returning_visitor",
            "password": "wrong_password",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post_and_closes_session(self):
        user = get_user_model().objects.create_user(username="visitor")
        self.client.force_login(user)

        get_response = self.client.get(reverse("gallery:logout"))
        self.assertEqual(get_response.status_code, 405)
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

        post_response = self.client.post(reverse("gallery:logout"))
        self.assertRedirects(post_response, reverse("gallery:artwork_list"))
        self.assertNotIn("_auth_user_id", self.client.session)
