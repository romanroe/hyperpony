from typing import Optional

from django.views.generic import TemplateView
from icecream import ic

from hyperpony import param, HyperponyMixin, SingletonPathMixin, HyperponyElementMixin
from hyperpony.client_state import client_state


class ClientStatePage(SingletonPathMixin, HyperponyMixin, TemplateView):
    template_name = "playground/client_state/client_state_page.html"

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "element": ClientStateElement.embed(self.request)
        }


class ClientStateElement(SingletonPathMixin, HyperponyElementMixin, TemplateView):
    template_name = "playground/client_state/ClientStateElement.html"
    met: Optional[str] = param()
    foo = client_state(100, client_to_server=True)
    bar = client_state('abc"def', client_to_server=True)
    baz = client_state("ghi'jkl")

    def dispatch(self, request, *args, **kwargs):
        ic(self.foo, self.bar, self.baz)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


urlpatterns = [
    ClientStatePage.create_path(full_path=""),
    ClientStateElement.create_path(),
]
