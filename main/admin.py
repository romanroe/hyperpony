from django.contrib import admin

from main.models import AppUser


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "first_name", "last_name", "email", "date_joined")
    list_display_links = ("id", "username")
    ordering = ("date_joined",)
    search_fields = list_display
    date_hierarchy = "date_joined"
