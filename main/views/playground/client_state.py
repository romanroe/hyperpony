from django.urls import path, reverse
from django.views.generic import TemplateView
from ninja import ModelSchema

from demo_address_book.models import Person
from hyperpony.client_state import ClientStateView, client_state


class PersonClientState(ModelSchema):
    class Meta:
        model = Person
        fields = "__all__"


class ClientStatePage(TemplateView, ClientStateView):
    template_name = "playground/client_state/client_state_page.html"
    foo: int = client_state(1, client_to_server=True)
    # persons: list[Person] = client_state([], model=list[PersonClientState])

    def get_context_data(self, **kwargs):
        # self.persons = Person.objects.all()[:10]
        print(self.is_client_state_present, self.foo)

        return super().get_context_data(**kwargs) | {
            "url": reverse("client-state-page")
        }

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
]
