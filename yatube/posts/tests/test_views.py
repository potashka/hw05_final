import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User
from posts.forms import PostForm

NUM_POSTS_PAG_TEST = settings.NUM_POSTS_PAG_TEST
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
QUANTITY_OF_POSTS = settings.QUANTITY_OF_POSTS


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='random_name')
        cls.author = cls.user
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание группы',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def sample_context_test_func(self, context, post=False):
        """Шаблон фнукции для тестирования контекста"""
        if post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)

    def test_index_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:main_page'))
        self.sample_context_test_func(response.context)

    def test_group_list_shows_correct_context(self):
        """Шаблон группы сформирован с правильным контектсом"""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    args=(self.group.slug,))
        )
        self.assertEqual(
            response.context['group'],
            self.group
        )
        self.sample_context_test_func(response.context)

    def test_profile_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    args=(self.user.username,))
        )
        self.assertEqual(
            response.context['author'],
            self.user,
            'Ошибка: шаблон сформирован с неправильным контекстом'
        )
        self.sample_context_test_func(response.context)

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.pk,))
        )
        self.sample_context_test_func(response.context, post=True)

    def test_create_edit_post_shows_correct_context(self):
        """Шаблоны post_create и eidt_post сформированы
            с правильным контекстом"""
        pages = (
            ('posts:post_create', None,),
            ('posts:post_edit', (self.post.pk,),),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField}
        for page, args in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(reverse(page, args=args))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value)
                        self.assertIsInstance(form_field, expected)

    def test_post_another_group_conflict(self):
        """Пост не попал в другую группу"""
        group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-group2',
            description='Тестовое описание группы',
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', args=(group2.slug,))
        )
        self.assertEqual(len(response.context['page_obj']), 0)
        posts_count = Post.objects.filter(group=self.group).count()
        post = Post.objects.create(
            text='Тестовый пост ',
            author=self.user,
            group=group2)
        self.assertTrue(post.group, 'У поста есть группа')
        group1 = Post.objects.filter(group=self.group).count()
        group2 = Post.objects.filter(group=self.group).count()
        self.assertEqual(group1, posts_count, 'Пост попал в первую группу')
        self.assertEqual(group2, 1, 'Нет поста')
        self.assertNotEqual(self.group, post.group, 'Другая группа')

    def test_cache_index_page(self):
        """Проверка работы кеширования страницы index"""
        Post.objects.all().delete()
        post = Post.objects.create(
            text='Пост для кэширования',
            author=self.user)
        cache_added = self.authorized_client.get(
            reverse('posts:main_page')).content
        post.delete()
        cache_stored = self.authorized_client.get(
            reverse('posts:main_page')).content
        self.assertEqual(cache_added, cache_stored)
        cache.clear()
        cache_cleared = self.authorized_client.get(
            reverse('posts:main_page')).content
        self.assertNotEqual(cache_added, cache_cleared)


class PaginatorViewsTest(TestCase):

    def setUp(self):
        # self.author = User.objects.create_user(username='random_author')
        self.user = User.objects.create_user(username='random_name')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test_group')
        posts = []
        for post in range(NUM_POSTS_PAG_TEST):
            posts.append(
                Post(text=f'Тестовый пост {post}',
                     group=self.group,
                     author=self.user)
            )
        Post.objects.bulk_create(posts)
        Follow.objects.create(
            user=self.user,
            author=self.user)

    def test_page_contains_records(self):
        '''Проверка количества постов на странице'''
        page_urls = (
            ('posts:main_page', None),
            ('posts:profile',
                (self.user.username,)),
            ('posts:group_list',
                (self.group.slug,)),
            ('posts:follow_index', None),
        )
        pages = (
            ('?page=1', QUANTITY_OF_POSTS),
            ('?page=2', (NUM_POSTS_PAG_TEST - QUANTITY_OF_POSTS)),
        )
        for url, args in page_urls:
            with self.subTest():
                for page, count in pages:
                    with self.subTest():
                        if url == 'posts:follow_index':
                            response = self.authorized_client.get(
                            reverse(url, args=args)
                            + page
                        )
                        else:
                            response = self.client.get(
                            reverse(url, args=args)
                            + page
                        )
                        self.assertEqual(
                            len(response.context['page_obj']),
                            count,
                            'Ошибка:неверное количество постов.'
                        )


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='random_name')
        cls.author = User.objects.create_user(username='random_author')
        cls.post = Post.objects.create(
            text='test_follower',
            author=cls.author,
        )

    def setUp(self):
        cache.clear()
        self.authorised_client = Client()
        self.authorised_client.force_login(self.user)
        self.authorised_author = Client()
        self.authorised_author.force_login(self.author)

    def test_follower(self):
        """Авторизованный пользователь может подписываться на
        других пользователей"""
        count_follow = Follow.objects.count()
        self.authorised_client.post(
            reverse(
                'posts:profile_follow',
                args=(self.author,)
            )
        )
        followed_author = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(followed_author.user_id, self.user.id)
        self.assertEqual(followed_author.author_id, self.author.id)

    def test_unfollow_author(self):
        """Авторизованный пользователь может удалять авторов из подписки"""
        Follow.objects.create(
            user=self.user,
            author=self.author)
        count_follow = Follow.objects.count()
        self.authorised_client.post(
            reverse(
                'posts:profile_unfollow',
                args=(self.author,)
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_follow_on_authors(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан"""
        Post.objects.all().delete()
        unfollower_user = User.objects.create_user(username='unfollower_user')
        authorized_unfollower_user = Client()
        authorized_unfollower_user.force_login(unfollower_user)
        post = Post.objects.create(
            text='test_follower',
            author=self.author,
        )
        Follow.objects.create(
            user=self.user,
            author=self.author)
        response = self.authorised_client.get(
            reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'])
        response = authorized_unfollower_user.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'])

    def test_double_follow(self):
        """Проверка невозможности подписки на пользователя два раза"""
        Follow.objects.all().delete()
        self.authorised_client.post(
            reverse(
                'posts:profile_follow',
                args=(self.author,)
            )
        )
        self.assertEqual(Follow.objects.count(), 1)
        self.authorised_client.post(
            reverse(
                'posts:profile_follow',
                args=(self.author,)
            )
        )
        self.assertEqual(Follow.objects.count(), 1)

    def test_no_self_follow(self):
        """Отсутствие подписки на себя"""
        self.authorised_author.post(
            reverse(
                'posts:profile_follow',
                args=(self.author,)
            )
        )
        self.assertEqual(Follow.objects.count(), 0)
