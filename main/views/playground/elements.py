from datetime import datetime

from django.http import HttpResponse, HttpRequest
from django.urls import path
from django.views import View
from django.views.generic import TemplateView
from htpy import br, render_node, h3, Node, button
from icecream import ic

from hyperpony import SingletonPathMixin, HyperponyElementMixin, param, HyperponyMixin
from hyperpony.htmx import swap_body
from hyperpony.views import invoke_view


class _HtpyView(View):
    # noinspection PyUnusedLocal
    def get(self, request, *args, **kwargs):
        return HttpResponse(render_node(self.render(request, *args, **kwargs)))

    # noinspection PyMethodMayBeStatic
    def render(self, request: HttpRequest, *args, **kwargs) -> Node:
        return None


class Level1PageView(SingletonPathMixin, HyperponyMixin, TemplateView):
    template_name = "playground/elements/Level1Page.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "timestamp": datetime.now().microsecond,
            "level2_element": Level2Element.embed(self.request, GET={"source": "page"}),
        }


class Level2Element(SingletonPathMixin, HyperponyElementMixin, TemplateView):
    template_name = "playground/elements/Level2Element.html"
    source = param("???")

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "timestamp": datetime.now().microsecond,
            "source": self.source,
            "level3a_element": Level3AElement.embed(self.request, GET={"source": self.source}),
            "level3b_element": Level3BElement.embed(self.request, GET={"source": self.source}),
        }


class Level3AElement(SingletonPathMixin, HyperponyElementMixin, TemplateView):
    template_name = "playground/elements/Level3AElement.html"
    action = param("")
    source = param("???")

    def dispatch(self, request, *args, **kwargs):
        match self.action:
            case "page":
                res = swap_body(invoke_view(self.request, "level1_page"))
                return res
            case "2":
                Level2Element.swap_oob(self.request, GET={"source": "Level3AElement"})
            case "3a_3b":
                Level3BElement.swap_oob(self.request, GET={"source": "Level3AElement"})
            case "replace":
                return Level3BElement.invoke(self.request)

        response = super().dispatch(request, *args, **kwargs)
        return response

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "timestamp": datetime.now().microsecond,
            "source": self.source,
        }


class Level3BElement(SingletonPathMixin, HyperponyElementMixin, _HtpyView):
    element_id = "l3b"
    tag = "span"
    source = param("???")

    def post(self, request, *args, **kwargs):
        ic("Level3BElement.post")
        return self.get(request, *args, **kwargs)

    def render(self, request, *args, **kwargs):
        return [
            h3["Level3BElement"],
            datetime.now().microsecond,
            br,
            self.source,
            button(hx_post=self.path)["refresh"],
        ]


urlpatterns = [
    path("", Level1PageView.as_view(), name="level1_page"),
    Level2Element.create_path(),
    Level3AElement.create_path(),
    Level3BElement.create_path(),
]
