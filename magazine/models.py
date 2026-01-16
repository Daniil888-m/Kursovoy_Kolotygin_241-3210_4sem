from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Рубрика')
    def __str__(self): return self.name

class Author(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя автора')
    bio = models.TextField(blank=True, verbose_name='Биография')
    def __str__(self): return self.name

class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Текст статьи')
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name='Автор')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Рубрика')
    def __str__(self): return self.title

class Issue(models.Model):
    number = models.IntegerField(verbose_name='Номер выпуска')
    pub_date = models.DateField(verbose_name='Дата выпуска')
    articles = models.ManyToManyField(Article, verbose_name='Статьи')
    def __str__(self): return f'Выпуск #{self.number}'

class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name='Статья')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    text = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'Коммент к {self.article.title}'

class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name='Тег')
    articles = models.ManyToManyField(Article, verbose_name='Статьи')
    def __str__(self): return self.name
