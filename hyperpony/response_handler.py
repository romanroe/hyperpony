from typing import Callable, Literal, Optional, TypeAlias

from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django_htmx.http import push_url

from hyperpony.htmx import enrich_response_with_oob_contents, swap_oob


RESPONSE_HANDLER: TypeAlias = Callable[[HttpResponse], Optional[HttpResponse]]


def get_response_handlers_from_request(request: HttpRequest) -> list[RESPONSE_HANDLER]:
    handlers = getattr(request, "__hyperpony_view_response_handlers", [])
    setattr(request, "__hyperpony_view_response_handlers", handlers)
    return handlers


def add_response_handler(request: HttpRequest, handler: RESPONSE_HANDLER):
    # get_view_fn_call_stack_from_request_or_raise(request)
    handlers = get_response_handlers_from_request(request)
    handlers.append(handler)


def process_response(request: HttpRequest, response: HttpResponseBase) -> HttpResponseBase:
    handlers = get_response_handlers_from_request(request)
    for handler in handlers:
        result = handler(response)
        response = result if result is not None else response

    enrich_response_with_oob_contents(response)
    return response


def hook_push_url(request: HttpRequest, url: str | Literal[False]):
    add_response_handler(request, lambda response: push_url(response, url))


def hook_swap_oob(
    request: HttpRequest,
    additional: HttpResponse | list[HttpResponse],
    hx_swap_oob_method="outerHTML",
) -> None:
    add_response_handler(
        request, lambda response: swap_oob(response, additional, hx_swap_oob_method)
    )
