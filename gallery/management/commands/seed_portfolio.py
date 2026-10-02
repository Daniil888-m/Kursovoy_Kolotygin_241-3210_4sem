"""Заполняет портфолио демонстрационными данными без удаления существующих записей."""

from decimal import Decimal
from io import BytesIO
from random import Random

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageDraw

from gallery.models import (
    Artwork,
    Category,
    Comment,
    ContactRequest,
    Review,
    Style,
    Technique,
)


SERIES = (
    {
        'category': 'Живопись',
        'style': 'Реализм',
        'techniques': ('Масло на холсте', 'Темпера'),
        'materials': ('Холст, масло', 'Бумага, темпера'),
        'palette': ((36, 62, 83), (168, 180, 158), (232, 196, 139), (105, 129, 112)),
        'works': (
            ('Утро у старой пристани', 'Мягкий утренний свет ложится на лодки и деревянный причал.'),
            ('Дом у озера', 'Тихий берег и отражение дома создают ощущение спокойствия.'),
            ('Берёзовая аллея', 'Солнечные пятна ведут взгляд зрителя вдоль аллеи.'),
            ('Тихий двор', 'Знакомое городское пространство показано в конце летнего дня.'),
            ('Полевые цветы', 'Букет полевых цветов собран в живую и немного свободную композицию.'),
            ('Свет в мастерской', 'Предметы в мастерской освещены низким вечерним солнцем.'),
        ),
    },
    {
        'category': 'Живопись',
        'style': 'Импрессионизм',
        'techniques': ('Масло мастихином', 'Пастель'),
        'materials': ('Холст, масло', 'Бумага, пастель'),
        'palette': ((100, 95, 151), (228, 168, 164), (248, 219, 150), (132, 167, 190)),
        'works': (
            ('Сиреневый вечер', 'Вечерние оттенки меняются по мере ухода света.'),
            ('Тёплый дождь', 'Блики на мокрой дороге передают движение летнего дождя.'),
            ('Сад в июне', 'Цветущий сад изображён свободными короткими мазками.'),
            ('Последний трамвай', 'Огни вечернего города растворяются в сумерках.'),
            ('Солнечные блики', 'Свет проходит сквозь листву и дробится на цветные пятна.'),
            ('Площадь после дождя', 'Отражения зданий делают привычную площадь новой.'),
        ),
    },
    {
        'category': 'Акварель',
        'style': 'Акварельная живопись',
        'techniques': ('Акварель по-сырому', 'Акварель лессировкой'),
        'materials': ('Бумага, акварель', 'Хлопковая бумага, акварель'),
        'palette': ((68, 121, 136), (186, 218, 215), (243, 228, 195), (133, 171, 182)),
        'works': (
            ('Туман над рекой', 'Очертания дальнего берега исчезают в утреннем тумане.'),
            ('Листья и ветер', 'Лёгкие слои цвета создают ощущение движения воздуха.'),
            ('Зимнее окно', 'Холодный свет за окном противопоставлен теплу комнаты.'),
            ('Розовый горизонт', 'На границе воды и неба смешиваются мягкие оттенки.'),
            ('Кафе на углу', 'Небольшой городской сюжет передан прозрачными слоями краски.'),
            ('Осенняя тропа', 'Листья и влажная земля складываются в спокойный пейзаж.'),
        ),
    },
    {
        'category': 'Абстракция',
        'style': 'Абстракционизм',
        'techniques': ('Акрил', 'Смешанная техника'),
        'materials': ('Холст, акрил', 'Холст, акрил и коллаж'),
        'palette': ((47, 40, 89), (109, 63, 119), (239, 121, 85), (241, 195, 106)),
        'works': (
            ('Пульс города', 'Ритм линий и цветовых пятен напоминает движение улиц.'),
            ('Северный свет', 'Контраст холодных и тёплых форм создаёт напряжение.'),
            ('Точка равновесия', 'Несколько крупных форм удерживают композицию в балансе.'),
            ('Движение цвета', 'Пересекающиеся формы создают ощущение скорости.'),
            ('Синий ритм', 'Повторяющиеся синие элементы задают спокойный темп.'),
            ('Тихая геометрия', 'Простые фигуры собираются в сдержанную композицию.'),
        ),
    },
    {
        'category': 'Цифровое искусство',
        'style': 'Цифровое искусство',
        'techniques': ('Цифровая живопись', 'Цифровой коллаж'),
        'materials': ('Цифровой планшет', 'Цифровой коллаж'),
        'palette': ((22, 43, 83), (90, 70, 154), (69, 184, 205), (244, 195, 91)),
        'works': (
            ('Город будущего', 'Высотные силуэты и световые полосы создают образ будущего.'),
            ('Ночной сад', 'Фантастические растения светятся на фоне тёмного неба.'),
            ('Лунная станция', 'Воображаемая станция окружена холодным лунным светом.'),
            ('Полёт над облаками', 'Плавные линии передают высоту и свободу движения.'),
            ('Огни мегаполиса', 'Множество световых точек складывается в ночной город.'),
            ('Память о море', 'Фрагменты берегового пейзажа соединены в цифровой коллаж.'),
        ),
    },
    {
        'category': 'Графика',
        'style': 'Графика',
        'techniques': ('Тушь и перо', 'Линогравюра'),
        'materials': ('Бумага, тушь', 'Бумага, линогравюра'),
        'palette': ((45, 53, 62), (174, 176, 169), (231, 224, 208), (156, 90, 75)),
        'works': (
            ('Набросок улицы', 'Быстрые линии передают характер старой улицы.'),
            ('Старые ворота', 'Контраст света и тени подчёркивает фактуру ворот.'),
            ('Портрет незнакомки', 'Выразительный силуэт построен экономными линиями.'),
            ('Линии моста', 'Повторение опор и пролётов задаёт графический ритм.'),
            ('Окна напротив', 'Геометрия окон превращает фасад в композицию.'),
            ('Дерево у дороги', 'Тонкие ветви выделяются на светлом фоне.'),
        ),
    },
)

VISITOR_NAMES = (
    'Анна', 'Михаил', 'Елена', 'Артём', 'Мария',
    'Игорь', 'Ольга', 'Денис', 'София', 'Павел',
    'Дарья', 'Роман', 'Алина', 'Никита', 'Вера',
)

REVIEW_TEXTS = (
    'Понравилось сочетание цветов и внимание к деталям.',
    'Интересная композиция, к которой хочется возвращаться.',
    'Работа оставляет сильное впечатление и хорошо запоминается.',
    'Особенно понравились свет и настроение этой работы.',
)

COMMENT_TEXTS = (
    'Очень интересная работа. Как появилась идея?',
    'Нравится выбранная цветовая гамма.',
    'Хотелось бы увидеть больше работ в этой серии.',
    'Хорошо передано настроение.',
    'Какие материалы использовались при создании?',
    'Композиция выглядит очень выразительно.',
)


def make_demo_image(number, palette):
    """Создаёт отдельное условное изображение для учебной работы."""
    width = 960
    height = 640
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    random = Random(number)

    for y in range(height):
        part = y / (height - 1)
        color = tuple(
            round(palette[0][channel] * (1 - part) + palette[1][channel] * part)
            for channel in range(3)
        )
        draw.line((0, y, width, y), fill=color)

    for shape in range(14):
        x = random.randint(-100, width - 100)
        y = random.randint(-100, height - 100)
        size = random.randint(80, 260)
        color = palette[2 + shape % 2]

        if shape % 3 == 0:
            draw.ellipse((x, y, x + size, y + size), fill=color)
        elif shape % 3 == 1:
            draw.polygon(
                ((x, y + size), (x + size // 2, y), (x + size, y + size)),
                fill=color,
            )
        else:
            draw.rectangle((x, y, x + size, y + size // 3), fill=color)

    output = BytesIO()
    image.save(output, format='JPEG', quality=88)
    return output.getvalue()


class Command(BaseCommand):
    help = 'Добавляет демонстрационные работы и связанные данные без дубликатов.'

    def handle(self, *args, **options):
        User = get_user_model()
        artist = User.objects.filter(username='admin', is_superuser=True).first()
        if artist is None:
            raise CommandError('Сначала создайте суперпользователя с именем admin.')

        created = {
            'категорий': 0,
            'стилей': 0,
            'техник': 0,
            'посетителей': 0,
            'работ': 0,
            'отзывов': 0,
            'комментариев': 0,
            'обращений': 0,
        }
        categories = {}
        styles = {}
        techniques = {}

        for series in SERIES:
            category, is_new = Category.objects.get_or_create(name=series['category'])
            categories[series['category']] = category
            if is_new:
                created['категорий'] += 1

            style, is_new = Style.objects.get_or_create(name=series['style'])
            styles[series['style']] = style
            if is_new:
                created['стилей'] += 1

            for technique_name in series['techniques']:
                technique, is_new = Technique.objects.get_or_create(
                    style=style,
                    name=technique_name,
                )
                techniques[(style.name, technique_name)] = technique
                if is_new:
                    created['техник'] += 1

        visitors = []
        for number, first_name in enumerate(VISITOR_NAMES, start=1):
            username = f'demo_visitor_{number:02d}'
            user = User.objects.filter(username=username).first()
            if user is None:
                user = User(
                    username=username,
                    first_name=first_name,
                    email=f'demo-visitor-{number:02d}@example.test',
                )
                user.set_unusable_password()
                user.save()
                created['посетителей'] += 1
            visitors.append(user)

        artworks = []
        number = 0
        for series in SERIES:
            category = categories[series['category']]
            style = styles[series['style']]

            for position, (title, note) in enumerate(series['works']):
                number += 1
                technique_name = series['techniques'][position % 2]
                technique = techniques[(style.name, technique_name)]
                image_name = f'artworks/demo_artwork_{number:02d}.jpg'

                if not default_storage.exists(image_name):
                    image_bytes = make_demo_image(number, series['palette'])
                    default_storage.save(image_name, ContentFile(image_bytes))

                demo_title = f'Демо: {title}'
                artwork = Artwork.objects.filter(
                    artist=artist,
                    title=demo_title,
                ).first()
                if artwork is None:
                    artwork = Artwork(
                        artist=artist,
                        category=category,
                        style=style,
                        technique=technique,
                        title=demo_title,
                        description=(
                            f'{note} Стиль: {style.name}. Техника: {technique.name}. '
                            'Изображение создано для демонстрации учебного проекта.'
                        ),
                        materials=series['materials'][position % 2],
                        year_created=2019 + number % 7,
                        width_cm=Decimal(30 + number % 5 * 10),
                        height_cm=Decimal(40 + number % 4 * 10),
                        price=None if position == 5 else Decimal(12000 + number * 1500),
                        image=image_name,
                        is_published=position < 5,
                    )
                    artwork.full_clean()
                    artwork.save()
                    created['работ'] += 1
                artworks.append(artwork)

                for review_number in range(2):
                    user = visitors[(number * 2 + review_number) % len(visitors)]
                    if not Review.objects.filter(artwork=artwork, user=user).exists():
                        review = Review(
                            artwork=artwork,
                            user=user,
                            rating=3 + (number + review_number) % 3,
                            text=REVIEW_TEXTS[(number + review_number) % len(REVIEW_TEXTS)],
                            is_approved=review_number == 0,
                        )
                        review.full_clean()
                        review.save()
                        created['отзывов'] += 1

                for comment_number in range(3):
                    user = visitors[(number * 3 + comment_number) % len(visitors)]
                    text = COMMENT_TEXTS[(number + comment_number) % len(COMMENT_TEXTS)]
                    if not Comment.objects.filter(
                        artwork=artwork,
                        user=user,
                        text=text,
                    ).exists():
                        comment = Comment(
                            artwork=artwork,
                            user=user,
                            text=text,
                            is_approved=comment_number < 2,
                        )
                        comment.full_clean()
                        comment.save()
                        created['комментариев'] += 1

        for number in range(1, 21):
            email = f'demo-request-{number:02d}@example.test'
            message = (
                f'Здравствуйте! Подскажите, можно ли обсудить работу '
                f'«{artworks[(number - 1) % len(artworks)].title}»?'
            )
            if not ContactRequest.objects.filter(email=email, message=message).exists():
                request = ContactRequest(
                    user=visitors[number - 1] if number <= 10 else None,
                    artwork=artworks[number - 1] if number <= 15 else None,
                    name=f'Гость {number:02d}',
                    email=email,
                    message=message,
                    is_processed=number % 4 == 0,
                )
                request.full_clean()
                request.save()
                created['обращений'] += 1

        self.stdout.write(self.style.SUCCESS('Демонстрационные данные готовы.'))
        for label, amount in created.items():
            self.stdout.write(f'Добавлено {label}: {amount}')
