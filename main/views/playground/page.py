# from datetime import datetime
#
# from django.shortcuts import render
# from django.urls import path, reverse
# from django_htmx.middleware import HtmxDetails
# from icecream import ic
#
# from hyperpony import param, inject_params
#
#
# @inject_params()
# def levels_page(request, source=param("page")):
#     htmx: HtmxDetails = request.htmx
#     ic(htmx.target)
#
#     return render(
#         request,
#         "playground/page/LevelsPage.html",
#         {
#             "timestamp": datetime.now().microsecond,
#             "source": source,
#             "url": reverse("levels_page"),
#         },
#     )
#
#
# urlpatterns = [
#     path("", levels_page, name="levels_page"),
# ]
