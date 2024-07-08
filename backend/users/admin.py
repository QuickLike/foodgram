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
        'user',
        'subscribe_on',
    )
    search_fields = (
        'user',
        'subscribe_on',
    )
    list_filter = (
        'user',
        'subscribe_on',
    )
    list_display_links = (
        'user',
    )
