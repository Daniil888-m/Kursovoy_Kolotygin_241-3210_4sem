from django_filters import rest_framework as filters

from .models import Artwork


class ArtworkFilter(filters.FilterSet):
    style = filters.CharFilter(field_name="style__name", lookup_expr="iexact")
    technique = filters.CharFilter(field_name="technique__name", lookup_expr="iexact")
    year_min = filters.NumberFilter(
        field_name="year_created", lookup_expr="gte", min_value=1, decimal_places=0
    )
    year_max = filters.NumberFilter(
        field_name="year_created", lookup_expr="lte", min_value=1, decimal_places=0
    )
    price_min = filters.NumberFilter(
        field_name="price", lookup_expr="gte", min_value=0
    )
    price_max = filters.NumberFilter(
        field_name="price", lookup_expr="lte", min_value=0
    )

    class Meta:
        model = Artwork
        fields = (
            "style", "technique", "year_min", "year_max", "price_min", "price_max"
        )
