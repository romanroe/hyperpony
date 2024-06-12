from datetime import datetime

from django.http import HttpRequest
from django.shortcuts import render
from django.urls import path, reverse

from hyperpony import param, inject_params


@inject_params()
def levels_page(request: HttpRequest, source=param("page")):
    return render(
        request,
        "playground/page/LevelsPage.html",
        {
            "timestamp": datetime.now().microsecond,
            "source": source,
            "url": reverse("levels_page"),
        },
    )


urlpatterns = [
    path("", levels_page, name="levels_page"),
]
