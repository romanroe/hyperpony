from types import UnionType
from typing import Any, TypeVar, Callable, get_origin, Union, get_args, Optional

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


def is_response_processable(response: HttpResponseBase, content_type_start: str) -> bool:
    if isinstance(response, HttpResponse) and response.streaming:
        return False

    if not response["Content-Type"].startswith(content_type_start.lower().strip()):
        return False

    return True


def text_response_to_str_or_none(response: HttpResponseBase) -> str | None:
    if is_response_processable(response, "text/"):
        return response_to_str(response)
    return None


def is_none_compatible(type_hint):
    # Get the origin of the type hint (e.g., Union, Optional, etc.)
    origin = get_origin(type_hint)

    # Handle Union and Optional (Optional[X] is Union[X, None])
    if origin is Union:
        args = get_args(type_hint)
        return type(None) in args

    # Handle direct usage of NoneType
    if type_hint is type(None):
        return True

    # Handle the union operator (|) in Python 3.10+
    if isinstance(type_hint, UnionType):
        return type(None) in get_args(type_hint)

    # Handle direct usage of Optional (which is Optional[X] == Union[X, None])
    if type_hint is Optional:
        return True

    return False
