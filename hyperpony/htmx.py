from typing import cast, Any, Literal

from django.http import HttpResponse
from django_htmx.http import reswap as htmx_reswap
from django_htmx.http import retarget as htmx_retarget

from hyperpony.utils import is_response_processable, response_to_str, parse_html, lxml_to_str


def _create_missing_id_exception(eg_help: str):
    return ValueError(
        f"The additional response must either contain exactly one element with an id attribute"
        f"or the id must be specified with the hx_swap parameter, e.g. '{eg_help}'."
    )


def swap_oob(
    response: HttpResponse,
    additional: HttpResponse | list[HttpResponse],
    hx_swap: Literal[True] | str = "outerHTML",
) -> HttpResponse:
    if not is_response_processable(response, "text/html"):
        raise Exception("Unable to add OOB content. The response's content type must be text/html.")

    if hx_swap is True:
        hx_swap = "outerHTML"

    if not isinstance(additional, list):
        additional = [additional]

    hyperpony_swap_oob = getattr(response, "_hyperpony_swap_oob", [])
    for a in additional:
        oob_content = response_to_str(a)
        if hx_swap is True or hx_swap.startswith("outerHTML"):
            parsed = parse_html(oob_content)
            if ":" not in hx_swap and parsed.attrib.get("id") is None:
                raise _create_missing_id_exception("outerHTML:#my-element")
            parsed.attrib["hx-swap-oob"] = f"{hx_swap}"
            oob_wrapped = lxml_to_str(parsed)
            hyperpony_swap_oob.append(oob_wrapped)
        else:
            if ":" not in hx_swap:
                parsed = parse_html(oob_content)
                id = parsed.attrib.get("id")
                if id is None:
                    raise _create_missing_id_exception("innerHTML:#my-element")
                hx_swap = f"{hx_swap}:#{id}"
            hyperpony_swap_oob.append(f"<div hx-swap-oob='{hx_swap}'>{oob_content}</div>")

    setattr(response, "_hyperpony_swap_oob", hyperpony_swap_oob)

    return response


def swap_body(response: HttpResponse) -> HttpResponse:
    response = htmx_retarget(response, "body")
    response = htmx_reswap(response, cast(Any, "innerHTML"))
    return response


def enrich_response_with_oob_contents(response: HttpResponse):
    if is_response_processable(response, "text/html"):
        content = response_to_str(response)
        bcontent = bytes(content, "UTF-8")
        hyperpony_swap_oob = getattr(response, "_hyperpony_swap_oob", [])
        for oob in hyperpony_swap_oob:
            bcontent += oob if isinstance(oob, bytes) else oob.encode()
        response.content = bcontent
    return response
