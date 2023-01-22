from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

User = get_user_model()


class Post(models.Model):
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]

    def get_absolute_url(self):
        return reverse('post', kwargs={'post_detail': self.pk})


class Group (models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
    )
    slug = models.SlugField(
        blank=True,
        null=True,
        unique=True,
        verbose_name='Параметр',
    )
    description = models.TextField(
        verbose_name='Описание'
    )

    class Meta:
        verbose_name = 'Название группы'
        verbose_name_plural = 'Названия группы'

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='comments',
        verbose_name='Пост',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    text = models.TextField(
        'Коментарий',
        help_text='Введите текст комментария',
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан',
    )

    class Meta:
        ordering = ('-created',)
        verbose_name_plural = 'Коментарии'
        verbose_name = 'Коментарий'

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='subscription_unique'
            ),
        )
        verbose_name_plural = 'Подписки'
        verbose_name = 'Подписка'

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
