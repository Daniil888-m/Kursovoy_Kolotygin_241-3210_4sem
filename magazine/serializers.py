from rest_framework import serializers
from .models import Article, Author

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

class ArticleSerializer(serializers.ModelSerializer):
    # author = AuthorSerializer(read_only=True)
    class Meta:
        model = Article
        fields = '__all__'
        extra_kwargs = {'content': {'write_only': True}}
