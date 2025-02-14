import pytest
from django.http import HttpResponse
import lxml.html

from hyperpony.htmx import swap_oob, enrich_response_with_oob_contents
from hyperpony.utils import response_to_str, parse_html


def test_htmx_swap_oob_outer_html():
    res1 = HttpResponse("<div id='main'>main</div>")
    res2 = HttpResponse("<div id='oob'>oob</div>")
    res = enrich_response_with_oob_contents(swap_oob(res1, res2))
    parsed = parse_html(response_to_str(res))
    assert parsed[0].attrib["id"] == "main"
    assert parsed[1].attrib["id"] == "oob"
    assert parsed[1].attrib["hx-swap-oob"] == "outerHTML"

    res = enrich_response_with_oob_contents(swap_oob(res1, res2, hx_swap=True))
    parsed = lxml.html.fromstring(response_to_str(res))
    assert parsed[0].attrib["id"] == "main"
    assert parsed[1].attrib["id"] == "oob"
    assert parsed[1].attrib["hx-swap-oob"] == "outerHTML"


def test_htmx_swap_oob_outer_html_with_id():
    res1 = HttpResponse("<div id='main'>main</div>")
    res2 = HttpResponse("<div id='oob'>oob</div>")
    res = enrich_response_with_oob_contents(swap_oob(res1, res2, hx_swap="outerHTML:#target"))
    parsed = parse_html(response_to_str(res))
    assert parsed[0].attrib["id"] == "main"
    assert parsed[1].attrib["id"] == "oob"
    assert parsed[1].attrib["hx-swap-oob"] == "outerHTML:#target"


def test_htmx_swap_oob_outer_html_error_on_missing_id():
    res1 = HttpResponse("<div id='main'>main</div>")
    res2 = HttpResponse("<div>oob</div>")
    with pytest.raises(ValueError, match=r"must either.*outerHTML"):
        enrich_response_with_oob_contents(swap_oob(res1, res2, hx_swap="outerHTML"))


def test_htmx_swap_oob_inner_html():
    res1 = HttpResponse("<div id='main'>main</div>")
    res2 = HttpResponse("<div id='oob'>oob</div>")
    res = enrich_response_with_oob_contents(swap_oob(res1, res2, hx_swap="innerHTML"))
    parsed = parse_html(response_to_str(res))
    assert parsed[0].attrib["id"] == "main"
    assert parsed[1].attrib["hx-swap-oob"] == "innerHTML:#oob"
    assert parsed[1][0].attrib["id"] == "oob"


def test_htmx_swap_oob_inner_html_with_id():
    res1 = HttpResponse("<div id='main'>main</div>")
    res2 = HttpResponse("<div id='oob'>oob</div>")
    res = enrich_response_with_oob_contents(swap_oob(res1, res2, hx_swap="innerHTML:#target"))
    parsed = parse_html(response_to_str(res))
    assert parsed[0].attrib["id"] == "main"
    assert parsed[1].attrib["hx-swap-oob"] == "innerHTML:#target"
    assert parsed[1][0].attrib["id"] == "oob"


def test_htmx_swap_oob_inner_html_error_on_missing_id():
    res1 = HttpResponse("<div id='main'>main</div>")
    res2 = HttpResponse("<div>oob</div>")
    with pytest.raises(ValueError, match=r"must either.*innerHTML"):
        enrich_response_with_oob_contents(swap_oob(res1, res2, hx_swap="innerHTML"))
