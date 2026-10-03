from rest_framework import serializers

from .models import Artwork


class ArtworkSerializer(serializers.ModelSerializer):
    artist = serializers.CharField(source="artist.username", read_only=True)
    category = serializers.CharField(source="category.name", read_only=True)
    style = serializers.CharField(source="style.name", read_only=True)
    technique = serializers.CharField(source="technique.name", read_only=True)
    formatted_dimensions = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True)
    approved_comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Artwork
        fields = (
            "id",
            "title",
            "description",
            "materials",
            "year_created",
            "price",
            "artist",
            "category",
            "style",
            "technique",
            "formatted_dimensions",
            "image_url",
            "average_rating",
            "approved_comments_count",
        )

    def get_formatted_dimensions(self, obj):
        return f"{obj.width_cm} × {obj.height_cm} см"

    def get_image_url(self, obj):
        if not obj.image:
            return None

        request = self.context.get("request")
        if request is None:
            return obj.image.url
        return request.build_absolute_uri(obj.image.url)
