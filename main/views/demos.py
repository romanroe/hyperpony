# from typing import Optional
# from uuid import UUID
#
# from django.http import HttpRequest, HttpResponse
# from django.urls import path
#
# from hyperpony import param, view
# from main.models import AppUser
#
#
# @view()
# def demo_param_model_page(
#     _request: HttpRequest,
#     user1: AppUser = param(),
#     user2: AppUser | UUID | None = param(),
#     user3: AppUser | None = param(),
#     user4: Optional[AppUser] = param(),
# ):
#     return HttpResponse(
#         f"""
#     {user1}
#     {user2}
#     {user3}
#     {user4}
#     """
#     )
#
#
# urlpatterns = [path("param_model", demo_param_model_page, name="demo-param-model-page")]
