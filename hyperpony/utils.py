from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseBase, QueryDict
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe, SafeString


def querydict_key_removed(querydict: dict, key) -> QueryDict:
    temp = QueryDict(mutable=True)
    temp.update(querydict)
    del temp[key]
    return temp


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
