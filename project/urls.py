from django.contrib import admin
from django.urls import include, path

# global URLs
urlpatterns = [
    # Demos
    # path("playground/params/", include("main.views.playground.params")),
    path("playground/elements/", include("main.views.playground.elements")),
    # path("playground/page/", include("main.views.playground.page")),
    path("playground/client_state/", include("main.views.playground.client_state")),
    # path("form/", include("main.views.form")),
    # path("demos/", include("main.views.demos")),
    # path("demo_address_book/fbv/", include("demo_address_book.views_fbv")),
    # path("demo_address_book/cbv/", include("demo_address_book.views_cbv")),
    # Internal
    path("__adm__/", admin.site.urls),
    path("__debug__/", include("debug_toolbar.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
]
