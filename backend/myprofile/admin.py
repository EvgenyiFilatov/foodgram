from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from myprofile.models import MyProfile, Subscription


@admin.register(MyProfile)
class MyUserAdmin(UserAdmin):
    list_display = (
        'username',
        'subscriptions_count',
        'recipes_count',
        'display_avatar'
    )

    @mark_safe
    @admin.display(description='Изображение')
    def display_avatar(self, obj):
        if obj.avatar:
            return (
                f'<img src="{obj.avatar.url}"'
                'style="max-width: 100px; height: auto;" />'
            )
        return 'Нет изображения'
    display_avatar.allow_tags = True


@admin.register(Subscription)
class Subscription(admin.ModelAdmin):
    list_display = ('subscriber', 'subscribe_to')
    search_fields = ('subscriber__username', 'subscriber__email',)
