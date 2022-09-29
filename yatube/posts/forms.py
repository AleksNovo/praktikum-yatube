from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group','image')
        labels = {
            'text': _('Текст поста *'),
            'group': _('Группа поста'),
        }
        help_texts = {
            'text': _('Текст публикации'),
            'group': _('Группа, к которой будет относиться пост')
        }
        error_messages = {
            'text': {
                'required': _('Это поле обязательно для заполнения.'),
            },
        }
        widgets = {
            'text': forms.Textarea(attrs={'cols': 79, 'rows': 10}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': _('Текст комментария'),
        }
