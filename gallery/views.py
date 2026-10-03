from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ContactRequestForm
from .models import Artwork, Category


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

    context = {
        "artwork": artwork,
        "reviews": artwork.reviews.filter(is_approved=True).select_related("user"),
        "comments": artwork.comments.filter(is_approved=True).select_related("user"),
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
