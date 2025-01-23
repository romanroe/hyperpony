from typing import cast, Any

from django.http import HttpResponseBase


# noinspection PyUnusedLocal
def view_from_response[T](view_class: type[T], response: HttpResponseBase) -> T:
    return cast(Any, cast(Any, response).view)
