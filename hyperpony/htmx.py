import lxml.html
from django.http import HttpResponse

from hyperpony.utils import is_response_processable, response_to_str


def swap_oob(
    response: HttpResponse,
    additional: HttpResponse | list[HttpResponse],
    hx_swap_oob_method="outerHTML",
) -> HttpResponse:
    if not is_response_processable(response, "text/html"):
        return response

    if not isinstance(additional, list):
        additional = [additional]

    for a in additional:
        oob_content = response_to_str(a).strip()
        parsed: lxml.html.Element = lxml.html.fromstring(oob_content)
        id = parsed.attrib.get("id")
        if id is None:
            raise Exception(
                "The additional response does not contain exactly one element with an id attribute."
            )

        parsed.attrib["hx-swap-oob"] = f"{hx_swap_oob_method}:#{id}"
        oob_wrapped = lxml.html.tostring(parsed)

        hyperpony_swap_oob = getattr(response, "_hyperpony_swap_oob", [])
        setattr(response, "_hyperpony_swap_oob", hyperpony_swap_oob + [oob_wrapped])

    return response


def enrich_response_with_oob_contents(response: HttpResponse):
    if is_response_processable(response, "text/html"):
        content = response_to_str(response)
        bcontent = bytes(content, "UTF-8")
        hyperpony_swap_oob = getattr(response, "_hyperpony_swap_oob", [])
        for oob in hyperpony_swap_oob:
            bcontent += oob
        response.content = bcontent
