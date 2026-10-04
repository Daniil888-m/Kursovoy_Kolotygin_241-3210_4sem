from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, ContactRequestForm, ReviewForm
from .models import Artwork, Category, Review


# Публичные страницы показывают только опубликованные и одобренные данные.
def artwork_list(request):
    """Показывает опубликованные работы с поиском и фильтром по категории."""
    artworks = Artwork.objects.filter(is_published=True).select_related(
        "artist", "category", "style", "technique"
    ).annotate(
        average_rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)),
        approved_comments_count=Count(
            "comments", filter=Q(comments__is_approved=True), distinct=True
        ),
    )

    query = request.GET.get("q", "").strip()
    category_name = request.GET.get("category", "").strip()

    if query:
        artworks = artworks.filter(title__icontains=query)

    if category_name:
        artworks = artworks.filter(category__name=category_name)

    context = {
        "artworks": artworks,
        "categories": Category.objects.all(),
        "query": query,
        "selected_category": category_name,
    }
    return render(request, "gallery/artwork_list.html", context)


def artwork_detail(request, pk):
    """Показывает одну опубликованную работу и одобренные отклики."""
    published_artworks = Artwork.objects.filter(is_published=True).select_related(
        "artist", "category", "style", "technique"
    ).annotate(
        average_rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)),
        approved_comments_count=Count(
            "comments", filter=Q(comments__is_approved=True), distinct=True
        ),
    )
    artwork = get_object_or_404(published_artworks, pk=pk)
    user_review = None
    if request.user.is_authenticated:
        user_review = artwork.reviews.filter(user=request.user).first()

    context = {
        "artwork": artwork,
        "reviews": artwork.reviews.filter(is_approved=True).select_related("user"),
        "comments": artwork.comments.filter(is_approved=True).select_related("user"),
        "user_review": user_review,
    }
    return render(request, "gallery/artwork_detail.html", context)


def contact_request(request, pk=None):
    """Показывает форму и сохраняет корректное обращение посетителя."""
    artwork = None
    if pk is not None:
        artwork = get_object_or_404(Artwork, pk=pk, is_published=True)

    if request.method == "POST":
        form = ContactRequestForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.artwork = artwork
            if request.user.is_authenticated:
                contact.user = request.user
            contact.save()
            return redirect("gallery:contact_success")
    else:
        form = ContactRequestForm()

    return render(request, "gallery/contact_form.html", {"form": form, "artwork": artwork})


def contact_success(request):
    """Подтверждает посетителю, что обращение сохранено."""
    return render(request, "gallery/contact_success.html")


def register(request):
    """Регистрирует посетителя и открывает для него сеанс входа."""
    if request.user.is_authenticated:
        return redirect("gallery:artwork_list")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("gallery:artwork_list")
    else:
        form = UserCreationForm()

    return render(request, "gallery/register.html", {"form": form})


@login_required
def review_create(request, pk):
    """Сохраняет один отзыв пользователя для опубликованной работы."""
    artwork = get_object_or_404(Artwork, pk=pk, is_published=True)
    if Review.objects.filter(artwork=artwork, user=request.user).exists():
        messages.info(request, "Вы уже оставили отзыв об этой работе.")
        return redirect("gallery:artwork_detail", pk=artwork.pk)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.artwork = artwork
            review.user = request.user
            review.save()
            messages.success(request, "Отзыв отправлен на проверку.")
            return redirect("gallery:artwork_detail", pk=artwork.pk)
    else:
        form = ReviewForm()

    return render(request, "gallery/feedback_form.html", {
        "form": form,
        "artwork": artwork,
        "heading": "Оставить отзыв",
        "description": "Поставьте оценку от 1 до 5 и напишите отзыв.",
        "submit_label": "Отправить отзыв",
    })


@login_required
def comment_create(request, pk):
    """Сохраняет комментарий пользователя к опубликованной работе."""
    artwork = get_object_or_404(Artwork, pk=pk, is_published=True)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.artwork = artwork
            comment.user = request.user
            comment.save()
            messages.success(request, "Комментарий отправлен на проверку.")
            return redirect("gallery:artwork_detail", pk=artwork.pk)
    else:
        form = CommentForm()

    return render(request, "gallery/feedback_form.html", {
        "form": form,
        "artwork": artwork,
        "heading": "Добавить комментарий",
        "description": "Поделитесь впечатлением об этой работе.",
        "submit_label": "Отправить комментарий",
    })
