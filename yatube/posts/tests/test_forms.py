from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Comment, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='random_name')
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание группы'
        )
        # cls.form = PostForm()
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
            text='Тестовый пост',
            author=cls.author,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author.force_login(self.author)

    def test_create_post_form(self):
        '''Проверка формы создания новой записи'''
        Post.objects.all().delete()
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(),
                         posts_count + 1,
                         'Ошибка: поcт не добавлен.')
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image, 'posts/small.gif')

    def test_edit_post_form(self):
        '''Проверка формы редактирования записи'''
        group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-group2',
            description='Тестовое описание группы'
        )
        form_data = {'text': 'Текст',
                     'group': group2.id}
        self.assertEqual(
            Post.objects.count(),
            1,
            'Постов больше одного'
        )
        response = self.authorized_author.post(
            reverse('posts:post_edit', args=(self.post.pk,)),
            data=form_data,
            follow=True)
        self.assertEqual(
            Post.objects.count(),
            1,
            'Количество постов изменилось при редактировании'
        )
        post = Post.objects.first()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(post.text == form_data['text'])
        self.assertTrue(post.author == post.author)
        self.assertTrue(post.group.id == form_data['group'])
        response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_not_authorised_user_create_post(self):
        '''Проверка запрета создания поста неавторизованным пользователем'''
        posts_count = Post.objects.count()
        form_data = {'text': 'Текст записанный в форму',
                     'group': self.group.id}
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(Post.objects.count(),
                            posts_count + 1,
                            'Неваторизованный пользователь добавил пост')

    def test_authorised_user_add_comment(self):
        """Проверка создания комментария авторизованным пользователем"""
        Comment.objects.all().delete()
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Комменатирй',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                args=(self.post.pk,)
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(),
                         comments_count + 1,
                         'Ошибка: комментарий не добавлен.')
        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data['text'])

    def test_not_authorised_user_add_comment(self):
        '''Проверка запрета создания комментария без авторизации'''
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Комментарий',
        }
        response = self.client.post(
            reverse(
                'posts:add_comment',
                args=(self.post.pk,)
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(
            Comment.objects.count(),
            comments_count + 1,
            'Неваторизованный пользователь добавил комментарий'
        )
