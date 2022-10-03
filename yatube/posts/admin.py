from django.contrib import admin

from .models import Post, Group, Comment, Follow


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'description',
        'slug')
    search_fields = ('title', 'description',)
    list_filter = ('title',)
    empty_value_display = '-пусто-'


class PostAdmin(admin.ModelAdmin):
    # Перечисляем поля, которые должны отображаться в админке
    list_display = ('pk', 'text', 'pub_date', 'author', 'group',)
    # Добавляем интерфейс для поиска по тексту постов
    list_editable = ('group',)
    search_fields = ('text',)
    # Добавляем возможность фильтрации по дате
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'
# При регистрации модели Post источником конфигурации для неё назначаем
# класс PostAdmin


class CommentAdmin(admin.ModelAdmin):
    """Класс для настройки отображения модели
     Comment в интерфейсе админки."""
    list_display = (
        'post',
        'text',
        'created',
        'author',
    )
    search_fields = ('comment',)
    empty_value_display = '-пусто-'



class FollowAdmin(admin.ModelAdmin):
    """Класс для настройки отображения модели
     Follow в интерфейсе админки."""
    list_display = (
        'user',
        'author',
    )
    search_fields = ('follow',)
    empty_value_display = '-пусто-'

admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)