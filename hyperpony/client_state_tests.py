import lxml.html
import orjson
from django.http import HttpResponse
from django.test import RequestFactory

from hyperpony.client_state import ClientStateView, client_state
from hyperpony.utils import response_to_str


class V(ClientStateView):
    foo: str = client_state("foo", client_to_server=True)
    bar: int = client_state(123, client_to_server=True)
    baz: str = client_state("baz")

    def get(self, request):
        response = HttpResponse(
            f"""
        <div {self.get_client_state_attrs()}>
            foo={self.foo}
            bar={self.bar}
        </div>
        """
        )
        response.view = self
        return response

    def post(self, request):
        return self.get(request)


def test_client_state_default_values_are_set_in_instance(rf: RequestFactory):
    view = V()
    assert view.foo == "foo"
    assert view.bar == 123
    assert view.baz == "baz"


def test_server_to_client(rf: RequestFactory):
    req = rf.get("/")
    response = V.as_view()(req)
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    attr_x_data = parsed.attrib["x-data"]
    x_data = orjson.loads(attr_x_data)
    data = x_data["client_state"]
    assert data["foo"] == "foo"
    assert data["bar"] == 123

    response = V.as_view()(req)
    parsed = lxml.html.fromstring(response_to_str(response))
    attr_x_data = parsed.attrib["x-data"]
    x_data = orjson.loads(attr_x_data)
    data = x_data["client_state"]
    assert data["foo"] == "foo"
    assert data["bar"] == 123


def test_client_to_server(rf: RequestFactory):
    req = rf.post(
        "/",
        data={"__hyperpony_cs__V": orjson.dumps({"foo": "oof", "bar": 456}).decode()},
    )
    req.htmx = True
    response = V.as_view()(req)

    v: V = response.view
    assert v.foo == "oof"
    assert v.bar == 456


def test_client_to_server_false(rf: RequestFactory):
    req = rf.post(
        "/",
        data={"__hyperpony_cs__V": orjson.dumps({"baz": "wrong"}).decode()},
    )
    req.htmx = True
    response = V.as_view()(req)

    v: V = response.view
    assert v.baz == "baz"
