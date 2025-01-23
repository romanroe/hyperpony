import django
import lxml.html


from django.http import HttpResponse, HttpResponseBase
from django.test import RequestFactory
from django.views import View
from django.views.generic import TemplateView

from hyperpony import ElementMixin
from hyperpony.element import ElementMeta, ElementResponse
from hyperpony.utils import response_to_str


def _assert_element_values(
    response: HttpResponseBase,
    tag="div",
    element_id="TView",
    hx_target="this",
    hx_swap="outerHTML",
):
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    assert parsed.tag == tag
    assert parsed.attrib["id"] == element_id
    assert parsed.attrib["hx-target"] == hx_target
    assert parsed.attrib["hx-swap"] == hx_swap
    assert "hyperpony-element" in parsed.attrib


def test_element_view_defaults(rf: RequestFactory):
    class TView(ElementMixin, View):
        def get(self, request, *args, **kwargs):
            return HttpResponse("")

    res = TView.as_view()(rf.get("/"))
    _assert_element_values(res)


def test_element_view_attrib_change(rf: RequestFactory):
    class TView(ElementMixin, View):
        element_id = "foo"
        tag = "spam"
        hx_swap = "egg"

        def get(self, request, *args, **kwargs):
            return HttpResponse("")

    res = TView.as_view()(rf.get("/"))
    _assert_element_values(res, element_id="foo", tag="spam", hx_swap="egg")


def test_element_view_attrs(rf: RequestFactory):
    class TView(ElementMixin, View):
        attrs = {"class": "bar"}

        def get(self, request, *args, **kwargs):
            return HttpResponse("")

    res = TView.as_view()(rf.get("/"))
    _assert_element_values(res)
    assert 'class="bar"' in response_to_str(res)


def test_element_return_another_element(rf: RequestFactory):
    class TViewParent(ElementMixin, View):
        def get(self, request, *args, **kwargs):
            return TViewChild.as_view()(request)

    class TViewChild(ElementMixin, View):
        def get(self, request, *args, **kwargs):
            return HttpResponse("2")

    res = TViewParent.as_view()(rf.get("/"))
    _assert_element_values(res, element_id="TViewChild")


def test_element_return_element_response(rf: RequestFactory):
    class TView(ElementMixin, View):
        def get(self, request, *args, **kwargs):
            return ElementResponse.wrap(HttpResponse("body"), ElementMeta(element_id="override"))

    res = TView.as_view()(rf.get("/"))
    _assert_element_values(res, element_id="override")


def test_element_nowrap(rf: RequestFactory):
    class TView(ElementMixin, View):
        def get(self, request, *args, **kwargs):
            return ElementResponse.nowrap(HttpResponse("body"))

    content = response_to_str(TView.as_view()(rf.get("/")))
    assert content == "body"


def test_element_return_template_http_response(rf: RequestFactory):
    django.setup()

    class TView(ElementMixin, TemplateView):
        template_name = "hyperpony/tests/TemplateResponse.html"

        def get_context_data(self, **kwargs):
            return {"foo": "bar"}

    c = response_to_str(TView.as_view()(rf.get("/")))
    assert "<div id='TView' hx-target='this' hx-swap='outerHTML'  hyperpony-element>" in c
    assert "bar" in c
