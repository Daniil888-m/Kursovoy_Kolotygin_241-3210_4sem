from django.db.models import Avg, Count, Q
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .filters import ArtworkFilter
from .models import Artwork
from .serializers import ArtworkSerializer


@api_view(["GET"])
def artwork_api_list(request):
    """Возвращает опубликованные работы в формате JSON."""
    artworks = Artwork.objects.filter(is_published=True).select_related(
        "artist", "category", "style", "technique"
    ).annotate(
        average_rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)),
        approved_comments_count=Count(
            "comments", filter=Q(comments__is_approved=True), distinct=True
        ),
    )

    filterset = ArtworkFilter(request.query_params, queryset=artworks)
    if not filterset.is_valid():
        return Response({"errors": filterset.errors}, status=400)

    serializer = ArtworkSerializer(
        filterset.qs, many=True, context={"request": request}
    )
    return Response(serializer.data)
