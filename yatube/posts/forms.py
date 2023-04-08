from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Введите текст',
            'group': 'Выберите группу',
            'image': 'Приложите картинку'
        }
        help_texts = {
            'text': 'Любой текст',
            'group': 'Из уже существующих',
            'image': 'Картинка'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Введите текст комментария'}
        help_texts = {'text': 'Комментарии по поводу поста'}
