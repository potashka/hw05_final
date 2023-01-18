from django.conf import settings
from django.test import TestCase

from ..models import Group, Post, User

LEN_OF_POSTS = settings.LEN_OF_POSTS


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='random_name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для тестирования созданных моделей',
            group=cls.group,
        )

    def test_model_post_have_correct_object_names(self):
        """Проверяем, что у модели Пост корректно работает __str__."""
        error_name = f"Вывод не имеет {LEN_OF_POSTS} символов"
        self.assertEqual(self.post.__str__(),
                         self.post.text[:LEN_OF_POSTS],
                         error_name)

    def test_model_group_have_correct_object_names(self):
        """Проверяем, что у модели Группа корректно работает __str__."""
        error = (f'Название {self.group.title} не совпадает с '
                 f'моделью {self.group.__str__()}')
        self.assertEqual(self.group.__str__(),
                         self.group.title,
                         error)

    def test_title_label(self):
        '''Проверка заполнения verbose_name в модели Post'''
        field_verboses = {'text': 'Текст поста',
                          'pub_date': 'Дата публикации',
                          'group': 'Группа',
                          'author': 'Автор'}
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                error = f'Поле {field} ожидало значение {expected_value}'
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value, error)

    def test_title_help_text(self):
        '''Проверка заполнения help_text в модели Пост'''
        field_help_texts = {'text': 'Введите текст поста',
                            'group': 'Группа, к которой будет относиться пост'}
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                error_name = f'Поле {field} ожидало значение {expected_value}'
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value, error_name)
