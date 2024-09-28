from typing import Optional

from django.urls import path

from hyperpony import HyperponyElementView, param, HyperponyView, SingletonPathMixin
from hyperpony.client_state import client_state


class ClientStatePage(HyperponyView):
    template_name = "playground/client_state/client_state_page.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "element": ClientStateElement().as_str(self.request)
        }


class ClientStateElement(SingletonPathMixin, HyperponyElementView):
    template_name = "playground/client_state/client_state_element.html"
    met: Optional[str] = param()
    foo: int = client_state(100, client_to_server=True)
    bar: str = client_state('abc"def', client_to_server=True)
    baz: str = client_state("ghi'jkl")

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


urlpatterns = [
    path("", ClientStatePage.as_view(), name="client-state-page"),
    ClientStateElement.create_path(),
]
