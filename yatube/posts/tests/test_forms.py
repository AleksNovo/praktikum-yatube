import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Описание',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=''
        )
        cls.comment = Comment.objects.create(
            text='Тестовый коммент',
            post=cls.post,
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.form_data = {
            'text': 'Новый тестовый текст',
            'group': self.group.pk,
            'author': self.user,
            'image': self.uploaded,
        }
        self.new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug='new-test-slug',
            description='Новое тестовое описание',
        )
        self.new_form_data = {
            'group': self.new_group.pk,
            'text': 'Cамый новый тестовый текст',
        }

    def test_create_post_authorized(self):
        """При отправке валидной формы создаётся новая запись в базе данных и
        идет редирект на страницу profile/<str:username>/ пользователя,
        создавшего пост."""
        post_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        added_post = Post.objects.all().first()
        added_post_check_dict = {
            added_post.text: self.form_data['text'],
            added_post.group.pk: self.form_data['group'],
            added_post.author: self.form_data['author'],

        }
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username':
                                     self.post.author.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        for expected, real in added_post_check_dict.items():
            with self.subTest(expected=expected):
                self.assertEqual(expected, real)

    def test_edit_post_authorized(self):
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'}),
            data=self.new_form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}))
        new_version = Post.objects.get(id=self.post.id)
        self.assertEqual(new_version.text, self.new_form_data['text'])
        self.assertEqual(new_version.group, self.new_group)

    def test_create_post_guest(self):
        post_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('users:login') + '?next='
                             + reverse('posts:post_create'))
        self.assertEqual(Post.objects.count(), post_count)

    def test_edit_post_guest(self):
        post_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'}),
            data=self.new_form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('users:login') + '?next='
                             + reverse('posts:post_edit',
                             kwargs={'post_id': f'{self.post.id}'}))
        self.assertEqual(Post.objects.count(), post_count)

    def test_create_comment_authorized(self):
        comment_count = Comment.objects.count()
        new_comment_data = {'text': 'Новый тестовый коммент'}
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.post.id}'}),
            data=new_comment_data,
            follow=True
        )
        added_comment = Comment.objects.all().first()
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(added_comment.text, new_comment_data['text'])
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}))

    def test_create_comment_guest(self):
        comment_count = Comment.objects.count()
        new_comment_data = {'text': 'Новый тестовый коммент'}
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.post.id}'}),
            data=new_comment_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertRedirects(response, reverse('users:login') + '?next='
                             + reverse('posts:add_comment',
                             kwargs={'post_id': f'{self.post.id}'}))
