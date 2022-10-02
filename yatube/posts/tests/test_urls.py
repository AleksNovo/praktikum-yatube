from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from http import HTTPStatus

from ..models import Post, Group

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user
        )
        cls.index_url = '/'
        cls.group_url = f'/group/{cls.group.slug}/'
        cls.profile_url = f'/profile/{cls.post.author}/'
        cls.post_url = f'/posts/{cls.post.id}/'
        cls.create_url = '/create/'
        cls.edit_url = f'/posts/{cls.post.id}/edit/'
        cls.comment_url = f'/posts/{cls.post.id}/comment/'
        cls.follow_url = '/follow/'
        cls.profile_follow_url = f'/profile/{cls.user.username}/follow/'
        cls.profile_unfollow_url = f'/profile/{cls.user.username}/unfollow/'
        cls.free_access_url_list = [cls.index_url, cls.group_url,
                                    cls.profile_url, cls.post_url]
        cls.restricted_access_url_list = [cls.create_url,
                                          cls.edit_url,
                                          cls.follow_url]
        cls.free_access_page_templates = ['posts/index.html',
                                          'posts/group_list.html',
                                          'posts/profile.html',
                                          'posts/post_detail.html']
        cls.restricted_access_page_templates = ['posts/create_post.html',
                                                'posts/create_post.html',
                                                'posts/follow.html']

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    # Проверяем общедоступные страницы
    def test_free_access_pages(self):
        """Страницы /, /group/<slug>/, /profile/<username>/ и /posts/<post_id>
        доступны любому пользователю."""
        for url in self.free_access_url_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_restricted_access_pages(self):
        """Страницы /create/ и /posts/<post_id>/edit/>
        доступны только авторизованным пользователям."""
        for url in self.restricted_access_url_list:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get(self.comment_url)
        self.assertRedirects(response, self.post_url)

    def test_restricted_access_pages_redirect(self):
        """Страницы /create/ и /posts/<post_id>/edit/> перенаправляют
        неавторизованных пользователей на страницу авторизации."""
        for url in self.restricted_access_url_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, f'/auth/login/?next={url}')
        response = self.guest_client.get(self.comment_url)
        self.assertRedirects(response, f'/auth/login/?next={self.comment_url}')

    def test_create_redirects_not_author(self):
        """Страница /posts/<post_id>/edit/> перенаправляет
        авторизованного пользователя на страницу поста, если тот не автор."""
        foreign_author = User.objects.create_user(username='SomeDude')
        foreign_post = Post.objects.create(
            text='Чужой пост',
            author=foreign_author
        )
        response = self.authorized_client.get(
            f'/posts/{foreign_post.id}/edit/', follow=True)
        self.assertRedirects(response, f'/posts/{foreign_post.id}/')

    def test_urls_use_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        free_access_url_template_dict = dict(zip(self.free_access_url_list,
                                             self.free_access_page_templates))
        restricted_access_url_template_dict = (dict(
            zip(self.restricted_access_url_list,
                self.restricted_access_page_templates)))
        for address, template in free_access_url_template_dict.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
        for address, template in restricted_access_url_template_dict.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_non_existant_page_404(self):
        """При запросе неусществующего URL-адреса происходит ошибка 404."""
        url = '/unexisting_page/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_custom_error_pages(self):
        """При запросе неусществующего URL-адреса
        срабатывает наша ошибка 404."""
        url = '/unexisting_page/'
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'core/404.html')
