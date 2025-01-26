from django.http import HttpRequest, HttpResponse
from django.views import View
from htpy import Node, render_node  # type: ignore


class HtpyView(View):
    # noinspection PyUnusedLocal
    def get(self, request, *args, **kwargs):
        return HttpResponse(render_node(self.render(request, *args, **kwargs)))

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def render(self, request: HttpRequest, *args, **kwargs) -> Node:
        raise NotImplementedError()
