from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Style(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')

    class Meta:
        verbose_name = 'Стиль'
        verbose_name_plural = 'Стили'
        ordering = ['name']

    def __str__(self):
        return self.name


class Technique(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    style = models.ForeignKey(
        Style,
        on_delete=models.PROTECT,
        related_name='techniques',
        verbose_name='Стиль',
    )

    class Meta:
        verbose_name = 'Техника'
        verbose_name_plural = 'Техники'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['style', 'name'],
                name='unique_technique_in_style',
            ),
        ]

    def __str__(self):
        return self.name


class Artwork(models.Model):
    artist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='artworks',
        verbose_name='Художник',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='artworks',
        verbose_name='Категория',
    )
    style = models.ForeignKey(
        Style,
        on_delete=models.PROTECT,
        related_name='artworks',
        verbose_name='Стиль',
    )
    technique = models.ForeignKey(
        Technique,
        on_delete=models.PROTECT,
        related_name='artworks',
        verbose_name='Техника',
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    materials = models.CharField(max_length=200, verbose_name='Материалы')
    year_created = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Год создания',
    )
    width_cm = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('0.1'))],
        verbose_name='Ширина, см',
    )
    height_cm = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('0.1'))],
        verbose_name='Высота, см',
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        null=True,
        blank=True,
        verbose_name='Цена',
    )
    image = models.ImageField(upload_to='artworks/', verbose_name='Изображение')
    is_published = models.BooleanField(default=False, verbose_name='Опубликована')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлена')

    class Meta:
        verbose_name = 'Работа'
        verbose_name_plural = 'Работы'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['artist', 'title'],
                name='unique_artwork_title_per_artist',
            ),
        ]

    def clean(self):
        if self.style_id and self.technique_id:
            if self.technique.style_id != self.style_id:
                raise ValidationError({
                    'technique': 'Техника не относится к выбранному стилю.',
                })

    def __str__(self):
        return self.title


class Review(models.Model):
    artwork = models.ForeignKey(
        Artwork,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Работа',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='artwork_reviews',
        verbose_name='Пользователь',
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оценка',
    )
    text = models.TextField(verbose_name='Текст отзыва')
    is_approved = models.BooleanField(default=False, verbose_name='Одобрен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['artwork', 'user'],
                name='unique_review_per_user_artwork',
            ),
        ]

    def __str__(self):
        return f'Отзыв пользователя {self.user} о работе {self.artwork}'


class Comment(models.Model):
    artwork = models.ForeignKey(
        Artwork,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Работа',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='artwork_comments',
        verbose_name='Пользователь',
    )
    text = models.TextField(verbose_name='Текст комментария')
    is_approved = models.BooleanField(default=False, verbose_name='Одобрен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created_at']

    def __str__(self):
        return f'Комментарий пользователя {self.user} к работе {self.artwork}'


class ContactRequest(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_requests',
        verbose_name='Пользователь',
    )
    artwork = models.ForeignKey(
        Artwork,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_requests',
        verbose_name='Работа',
    )
    name = models.CharField(max_length=100, verbose_name='Имя')
    email = models.EmailField(verbose_name='Электронная почта')
    message = models.TextField(verbose_name='Сообщение')
    is_processed = models.BooleanField(default=False, verbose_name='Обработано')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Отправлено')

    class Meta:
        verbose_name = 'Обращение'
        verbose_name_plural = 'Обращения'
        ordering = ['-created_at']

    def __str__(self):
        return f'Обращение от {self.name}'
