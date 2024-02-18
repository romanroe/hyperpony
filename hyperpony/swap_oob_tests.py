import lxml.html
import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from hyperpony import element
from hyperpony.htmx import swap_oob
from hyperpony.response_handler import hook_swap_oob
from hyperpony.testutils import call_with_middleware
from hyperpony.utils import response_to_str
from hyperpony.view import view


def _oob1(_request):
    return HttpResponse("<div id='oob1'>oob1</div>")


def _oob2(_request):
    return HttpResponse("<div id='oob2'>oob2</div>")


def test_append_swap_oob(rf: RequestFactory):
    def view1(request):
        response = HttpResponse("<div id='foo'>foo</foo>")
        return swap_oob(response, _oob1(request))

    response = call_with_middleware(rf, view1)
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    assert parsed.attrib["id"] == "foo"
    assert parsed[0].attrib["id"] == "oob1"
    assert parsed[0].attrib["hx-swap-oob"] == "outerHTML:#oob1"


def test_append_swap_oob_multiple(rf: RequestFactory):
    def view1(request):
        response = HttpResponse("<div id='foo'>foo</foo>")
        return swap_oob(response, [_oob1(request), _oob2(request)])

    response = call_with_middleware(rf, view1)

    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    assert parsed.attrib["id"] == "foo"
    assert parsed[0].attrib["id"] == "oob1"
    assert parsed[0].attrib["hx-swap-oob"] == "outerHTML:#oob1"
    assert parsed[1].attrib["id"] == "oob2"
    assert parsed[1].attrib["hx-swap-oob"] == "outerHTML:#oob2"


def test_swap_parent_from_element_fn(rf: RequestFactory):
    @element()
    def parent(_request):
        return HttpResponse("parent")

    @element()
    def child(request):
        hook_swap_oob(request, parent(request))
        return HttpResponse("child")

    response = call_with_middleware(rf, child)
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    assert parsed[0].attrib["id"] == "child"
    assert parsed[1].attrib["id"] == "parent"
    assert parsed[1].attrib["hx-swap-oob"] == "outerHTML:#parent"


def test_swap_parent_from_view_fn(rf: RequestFactory):
    @element()
    def parent(_request):
        return HttpResponse("parent")

    @view()
    def child(request):
        hook_swap_oob(request, parent(request))
        return HttpResponse("<dummy></dummy>")

    response = call_with_middleware(rf, child)
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    assert parsed[0].tag == "dummy"
    assert parsed[1].attrib["id"] == "parent"
    assert parsed[1].attrib["hx-swap-oob"] == "outerHTML:#parent"


def test_append_swap_oob_exception_if_additional_has_more_than_one_root_element():
    original = HttpResponse("<div id='foo'>foo</foo>")
    oob = HttpResponse("<span id='oob1'>oob1</span><span id='oob2'>oob2</span>")

    def test():
        swap_oob(original, oob)

    with pytest.raises(Exception, match="one element"):
        test()


def test_swap_oob_exception_if_additional_has_no_id():
    original = HttpResponse("<div id='foo'>foo</foo>")
    oob = HttpResponse("<span>oob1</span>")

    def test():
        swap_oob(original, oob)

    with pytest.raises(Exception, match="id attribute"):
        test()
