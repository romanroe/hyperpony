from django.contrib import admin

from demo_address_book.models import Person
from main.models import Todo


@admin.register(Person)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "created_at")
    list_display_links = ("id", "first_name")
    # ordering = ("date_joined",)
    # search_fields = list_display
    # date_hierarchy = "date_joined"


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "completed")
    list_display_links = ("id", "title")
    # ordering = ("date_joined",)
    # search_fields = list_display
    # date_hierarchy = "date_joined"
