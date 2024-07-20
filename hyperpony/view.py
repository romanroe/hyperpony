import functools
from typing import Callable, cast, Optional

import wrapt
from django import views
from django.contrib.auth import decorators as auth_decorators
from django.http import HttpRequest, HttpResponse, QueryDict
from django.utils.datastructures import MultiValueDict

import hyperpony
from hyperpony.utils import VIEW_FN, text_response_to_str_or_none
from hyperpony.view_stack import view_stack


class IsolatedRequest(wrapt.ObjectProxy):
    @classmethod
    def wrap(
        cls,
        request: HttpRequest,
        get_querydict: Optional[QueryDict] = None,
        post_querydict: Optional[QueryDict] = None,
    ):
        return IsolatedRequest(request)

    @property
    def method(self):
        return "GET"

    @property
    def GET(self):  # noqa: N802
        return QueryDict()

    @property
    def POST(self):  # noqa: N802
        return QueryDict()

    @property
    def FILES(self):  # noqa: N802
        return MultiValueDict()


class ViewResponse(wrapt.ObjectProxy):
    def __str__(self):
        response = cast(HttpResponse, self)
        response_string = text_response_to_str_or_none(response)
        return response_string if response_string is not None else super().__str__()

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


class NestedView(views.View):
    isolate_request = True

    def as_str(
        self,
        request: HttpRequest,
        *args,
        **kwargs,
    ):
        if self.isolate_request:
            request = IsolatedRequest.wrap(request)

        self.setup(request, *args, **kwargs)
        response = self.dispatch(request, *args, **kwargs)
        response_string = text_response_to_str_or_none(response)
        return response_string if response_string is not None else str(response)


class ElementIdMixin:
    element_id: Optional[str] = None

    def get_element_id(self) -> str:
        return self.element_id or self.__class__.__name__
