from django.core.management.base import BaseCommand
from django.utils import timezone
from magazine.models import Article, Author, Category

class Command(BaseCommand):
    help = 'Наполняет базу тестовыми данными'

    def handle(self, *args, **kwargs):
        # 1. Создаем автора и категорию
        author, _ = Author.objects.get_or_create(name='ИИ Редактор', bio='Генерирует контент')
        category, _ = Category.objects.get_or_create(name='Тестовая рубрика')

        # 2. Создаем 3 статьи
        for i in range(1, 4):
            Article.objects.create(
                title=f'Тестовая статья №{i}',
                content=f'Это текст статьи номер {i}, созданный автоматически.',
                author=author,
                category=category,
                pub_date=timezone.now()
            )
            self.stdout.write(self.style.SUCCESS(f'Статья {i} создана!'))
