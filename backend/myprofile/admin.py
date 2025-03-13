from django.contrib import admin
from myprofile.models import MyProfile, Subscription


@admin.register(MyProfile)
class MyUserAdmin(admin.ModelAdmin):
    list_display = ('username',)


@admin.register(Subscription)
class Subscription(admin.ModelAdmin):
    list_display = ('subscriber', 'subscribe_to')
    search_fields = ('username', 'email',)
