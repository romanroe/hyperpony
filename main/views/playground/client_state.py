from typing import Optional

from django.views.generic import TemplateView
from icecream import ic

from hyperpony import param, HyperponyView, SingletonPathMixin, HyperponyElementMixin
from hyperpony.client_state import client_state


class ClientStatePage(TemplateView, HyperponyView, SingletonPathMixin):
    template_name = "playground/client_state/client_state_page.html"

    def dispatch(self, request, *args, **kwargs):
        ic("A", self.url())
        ic("A", self.is_embedded_view)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            # "element": ClientStateElement().as_str(self.request)
            # "element": nest_view(self.request, "client-state-element")
            "element": ClientStateElement.embed(self.request)
        }


class ClientStateElement(
    # ActionMixin,
    SingletonPathMixin,
    TemplateView,
    HyperponyElementMixin,
):
    template_name = "playground/client_state/ClientStateElement.html"
    met: Optional[str] = param()
    foo = client_state(100, client_to_server=True)
    bar = client_state('abc"def', client_to_server=True)
    baz = client_state("ghi'jkl")

    def dispatch(self, request, *args, **kwargs):
        ic("B", self.url())
        ic("B", self.is_embedded_view)
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
    # path("", ClientStatePage.as_view(), name="client-state-page"),
    ClientStatePage.create_path(""),
    # path("client-state-element", ClientStateElement.as_view(), name="client-state-element"),
    ClientStateElement.create_path(),
]
