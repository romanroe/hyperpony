from django.contrib import admin

from demo_address_book.models import Person


@admin.register(Person)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "created_at")
    list_display_links = ("id", "first_name")
    # ordering = ("date_joined",)
    # search_fields = list_display
    # date_hierarchy = "date_joined"
