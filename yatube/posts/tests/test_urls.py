from http import HTTPStatus

from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='random_name')
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author.force_login(self.author)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            ('posts:main_page', None, 'posts/index.html'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.user.username,), 'posts/profile.html'),
            ('posts:post_detail', (self.post.pk,), 'posts/post_detail.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:post_edit', (self.post.pk,), 'posts/create_post.html'),
        )
        for name, args, template in templates_url_names:
            with self.subTest(name=name):
                response = self.authorized_author.get(
                    reverse(name, args=args))
                error = f'Ошибка: {name} ожидал шаблон {template}'
                self.assertTemplateUsed(response, template, error)

    def test_url_names(self):
        """Проверка соответствия url ссылок именам"""
        url_names = (
            ('posts:main_page', None,
                '/'),
            ('posts:post_create', None,
                '/create/'),
            ('posts:group_list', (self.group.slug,),
                f'/group/{self.group.slug}/'),
            ('posts:profile', (self.user.username,),
                f'/profile/{self.user.username}/'),
            ('posts:post_detail', (self.post.pk,),
                f'/posts/{self.post.pk}/'),
            ('posts:post_edit', (self.post.pk,),
                f'/posts/{self.post.pk}/edit/'),
        )
        for name, args, url in url_names:
            with self.subTest(name=name):
                self.assertEqual(reverse(name, args=args), url)

    def test_urls_author(self):
        """Доступ автора к страницам"""
        pages = (
            ('posts:main_page', None,
                '/'),
            ('posts:post_create', None,
                '/create/'),
            ('posts:group_list', (self.group.slug,),
                f'/group/{self.group.slug}/'),
            ('posts:profile', (self.user.username,),
                f'/profile/{self.user.username}/'),
            ('posts:post_detail', (self.post.pk,),
                f'/posts/{self.post.pk}/'),
            ('posts:post_edit', (self.post.pk,),
                f'/posts/{self.post.pk}/edit/'),
        )
        for name, args, url in pages:
            with self.subTest(name=name):
                response = self.authorized_author.get(reverse(name, args=args))
                error = f'Ошибка: нет доступа к странице {url}'
                self.assertEqual(response.status_code, HTTPStatus.OK, error)

    def test_urls_authorized_client(self):
        """Доступ авторизованного пользователя"""
        pages = (
            ('posts:main_page', None,
                '/'),
            ('posts:group_list', (self.group.slug,),
                f'/group/{self.group.slug}/'),
            ('posts:profile', (self.user.username,),
                f'/profile/{self.user.username}/'),
            ('posts:post_detail', (self.post.pk,),
                f'/posts/{self.post.pk}/'),
            ('posts:post_create', None,
                '/create/'),
            ('posts:post_edit', (self.post.pk,),
                f'/posts/{self.post.pk}/edit/'),
        )
        for name, args, url in pages:
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=args))
                error = f'Ошибка: нет доступа к странице {url}'
                if name == 'posts:post_edit':
                    self.assertRedirects(
                        response,
                        reverse('posts:post_detail',
                                args=(self.post.pk,))
                    )
                else:
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.OK,
                        error
                    )

    def test_urls_anonymous_guest_client(self):
        """Доступ неавторизованного пользователя"""
        pages = (
            ('posts:main_page', None,
                '/'),
            ('posts:group_list', (self.group.slug,),
                f'/group/{self.group.slug}/'),
            ('posts:profile', (self.user.username,),
                f'/profile/{self.user.username}/'),
            ('posts:post_detail', (self.post.pk,),
                f'/posts/{self.post.pk}/'),
            ('posts:post_create', None,
                '/create/'),
            ('posts:post_edit', (self.post.pk,),
                f'/posts/{self.post.pk}/edit/'),
        )
        create_edit_names = ['posts:post_create', 'posts:post_edit']
        for name, args, url in pages:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=args))
                error = f'Ошибка: нет доступа к странице {url}'
                if name in create_edit_names:
                    reverse_login = reverse('users:login')
                    reverse_name = reverse(name, args=args)
                    self.assertRedirects(
                        response,
                        f'{reverse_login}?next={reverse_name}'
                    )
                else:
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.OK,
                        error
                    )

    def test_page_404(self):
        """Доступ к несуществующей странице"""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
