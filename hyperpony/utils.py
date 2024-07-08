from typing import Any, TypeVar, Callable

from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe, SafeString


VIEW_FN = TypeVar("VIEW_FN", bound=Callable[..., HttpResponse])


def _get_request_from_args(args: list[Any]) -> HttpRequest:
    return args[0]


def response_to_str(response: HttpResponseBase | TemplateResponse) -> SafeString:
    if isinstance(response, TemplateResponse):
        response = response.render()

    return mark_safe(str(response.content, "utf-8"))


def is_response_processable(
    response: HttpResponseBase, content_type_start: str
) -> bool:
    if isinstance(response, HttpResponse) and response.streaming:
        return False

    if not response["Content-Type"].startswith(content_type_start.lower().strip()):
        return False

    return True


def text_response_to_str_or_none(response: HttpResponseBase) -> str | None:
    if is_response_processable(response, "text/"):
        return response_to_str(response)
    return None
