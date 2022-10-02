import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Follow, Post, Group, User
from yatube.settings import PAG_NUM

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='Name')
        cls.leo_user = User.objects.create_user(username='Leo')
        cls.unfollower_user = User.objects.create_user(username='Mark')
        cls.group = Group.objects.create(
            title='Тестовое заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )
        cls.index_reverse = reverse('posts:index')
        cls.group_list_reverse = reverse('posts:group_list',
                                         kwargs={'slug': cls.group.slug})
        cls.profile_reverse = reverse('posts:profile',
                                      kwargs={'username': cls.user.username})
        cls.post_detail_reverse = reverse('posts:post_detail',
                                          kwargs={'post_id': cls.post.id})
        cls.post_edit_reverse = reverse('posts:post_edit',
                                        kwargs={'post_id': cls.post.id})
        cls.post_create_reverse = reverse('posts:post_create')
        cls.profile_follow_reverse = reverse('posts:profile_follow',
                                             kwargs={'username':
                                                     cls.leo_user.username})
        cls.profile_unfollow_reverse = reverse('posts:profile_unfollow',
                                               kwargs={'username':
                                                       cls.leo_user.username})
        cls.follow_reverse = reverse('posts:follow_index')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_leo_user = Client()
        self.authorized_unfollower_user = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_leo_user.force_login(self.leo_user)
        self.authorized_unfollower_user.force_login(self.unfollower_user)

    def post_info_massage(self, context):
        with self.subTest(context=context):
            self.assertEqual(context.text, self.post.text)
            self.assertEqual(context.pub_date, self.post.pub_date)
            self.assertEqual(context.author, self.post.author)
            self.assertEqual(context.group.id, self.post.group.id)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            self.index_reverse: 'posts/index.html',
            self.group_list_reverse: 'posts/group_list.html',
            self.profile_reverse: 'posts/profile.html',
            self.post_detail_reverse: 'posts/post_detail.html',
            self.post_edit_reverse: 'posts/create_post.html',
            self.post_create_reverse: 'posts/create_post.html',
        }

        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон home.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.index_reverse)
        self.post_info_massage(response.context['page_obj'][0])

    def test_group_page_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.group_list_reverse)
        self.assertEqual(response.context['group'], self.group)
        self.post_info_massage(response.context['page_obj'][0])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.profile_reverse)
        self.assertEqual(response.context['author'], self.user)
        self.post_info_massage(response.context['page_obj'][0])

    def test_detail_page_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.post_detail_reverse)
        self.post_info_massage(response.context['post'])

    def test_index_page_cache(self):
        """Записть хранится в кеше 20 секунд или до очистки кэша."""
        test_post = Post.objects.create(
            text='Тестовый текст для кеша',
            author=self.user,
            group=self.group
        )
        response = self.authorized_client.get(self.index_reverse).content
        test_post.delete()
        self.assertEqual(response,
                         self.authorized_client.get(self.index_reverse).
                         content)
        cache.clear()
        self.assertNotEqual(response,
                            self.authorized_client.get(self.index_reverse).
                            content)


class FollowingTest(TestCase):
    """Класс тестирования подписок."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='auth'),
            text='Тестовый пост',
        )

    def setUp(self):
        self.user = User.objects.create_user(username='noname')
        self.authorised_client = Client()
        self.authorised_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.post.author)
        self.user_other = User.objects.create_user(username='other')
        self.authorised_other_client = Client()
        self.authorised_other_client.force_login(self.user_other)

        Follow.objects.create(
            user=self.user_other, author=self.post.author
        )
        Follow.objects.create(
            user=self.post.author, author=self.user
        )
        self.new_post = Post.objects.create(
            author=self.user,
            text='Новый пост автора',
        )
        self.response = self.author_client.get(reverse('posts:follow_index'))
        self.response_other = self.authorised_other_client.get(
            reverse('posts:follow_index')
        )

        self.first_object = self.response.context['page_obj'][0]
        self.first_object_other = self.response_other.context['page_obj'][0]


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Name')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.test_posts = []
        for i in range(13):
            cls.test_posts.append(Post(
                text=f'Тестовый пост №{i}',
                group=cls.group,
                author=cls.user))
        Post.objects.bulk_create(cls.test_posts)
        cls.index_reverse = reverse('posts:index')
        cls.group_list_reverse = reverse('posts:group_list',
                                         kwargs={'slug': cls.group.slug})
        cls.profile_reverse = reverse('posts:profile',
                                      kwargs={'username': cls.user.username})
        cls.pagination_pages_names = {
            cls.index_reverse: 'posts/index.html',
            cls.group_list_reverse: 'posts/group_list.html',
            cls.profile_reverse: 'posts/profile.html',
        }

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Проверка количества постов на первой странице."""
        for reverse_name, template in self.pagination_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']),
                                 PAG_NUM)

    def test_second_page_contains_correct_number_of_records(self):
        """Проверка количества постов на второй странице."""
        if (Post.objects.all().count() > PAG_NUM
                and Post.objects.all().count() % PAG_NUM == 0):
            current_page = PAG_NUM
        else:
            current_page = Post.objects.all().count() % PAG_NUM
        for reverse_name, template in self.pagination_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 current_page)

    def test_pages_show_correct_context(self):
        """Проверка контекста для множества постов на
        страницах с пагинацией"""
        for reverse_name, template in self.pagination_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                post = Post.objects.all()
                response = self.authorized_client.get(reverse_name)
                for i in range(0, PAG_NUM):
                    object_post = response.context['page_obj'][i].id
                    self.assertEqual(object_post, post[i].id)
