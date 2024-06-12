from django.contrib import admin
from django.urls import include, path

# global URLs
urlpatterns = [
    # Demos
    path("elements/", include("main.views.playground.elements")),
    path("page/", include("main.views.playground.page")),
    path("form/", include("main.views.form")),
    path("demos/", include("main.views.demos")),
    path("demo_address_book/", include("demo_address_book.views")),
    # Internal
    path("__adm__/", admin.site.urls),
    path("__debug__/", include("debug_toolbar.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
]
