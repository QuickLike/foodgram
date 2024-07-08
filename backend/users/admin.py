from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import MyUser, Subscription


@admin.register(MyUser)
class UserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('avatar',)}),
    )


@admin.register(Subscription)
class SubscriptionsAdmin(admin.ModelAdmin):
    list_display = (
        'follower',
        'following',
    )
    search_fields = (
        'follower',
        'following',
    )
    list_filter = (
        'follower',
        'following',
    )
    list_display_links = (
        'follower',
    )
