import functools
from typing import Callable, cast, Optional

import wrapt
from django.contrib.auth import decorators as auth_decorators
from django.http import HttpRequest, HttpResponse

import hyperpony
from hyperpony.utils import is_response_processable, response_to_str, VIEW_FN
from hyperpony.view_stack import view_stack


class ViewResponse(wrapt.ObjectProxy):
    def __str__(self):
        response = cast(HttpResponse, self)
        if is_response_processable(response, "text/"):
            return response_to_str(response)

        return super().__str__()

    def as_response(self) -> HttpResponse:
        return cast(HttpResponse, self)


def view(
    *,
    decorators: Optional[list[Callable]] = None,
    login_required=False,
    inject_params=True,
) -> Callable[[VIEW_FN], VIEW_FN]:
    if decorators is None:
        decorators = []

    if login_required:
        decorators = [auth_decorators.login_required(), *decorators]

    def decorator(fn: VIEW_FN) -> VIEW_FN:
        if inject_params:
            fn = hyperpony.inject_params()(fn)

        if decorators is not None:
            for d in reversed(decorators):
                fn = d(fn)

        @functools.wraps(fn)
        def inner(*args, **kwargs) -> HttpResponse:
            view_request: HttpRequest = args[0]
            # stack = get_view_fn_call_stack_from_request(view_request)
            try:
                # stack.append(fn)
                response = fn(view_request, *args[1:], **kwargs)
                response = (
                    ViewResponse(response)
                    if not isinstance(response, ViewResponse)
                    else response
                )
                return response
            finally:
                # stack.pop()
                pass

        return cast(VIEW_FN, view_stack()(inner))

    return decorator
