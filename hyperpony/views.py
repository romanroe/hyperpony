import functools
from typing import Callable, cast, Optional, ClassVar, Any

import wrapt
from django import views
from django.contrib.auth import decorators as auth_decorators
from django.http import HttpRequest, HttpResponse, QueryDict
from django.urls import path, reverse
from django.utils.datastructures import MultiValueDict
from django.utils.decorators import method_decorator

import hyperpony
from hyperpony.response_handler import RESPONSE_HANDLER, add_response_handler
from hyperpony.utils import VIEW_FN, text_response_to_str_or_none
from hyperpony.view_stack import view_stack


class IsolatedRequest(wrapt.ObjectProxy):
    @classmethod
    def wrap(cls, request: HttpRequest):
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
            try:
                response = fn(view_request, *args[1:], **kwargs)
                response = (
                    ViewResponse(response)
                    if not isinstance(response, ViewResponse)
                    else response
                )
                return response
            finally:
                pass

        return cast(VIEW_FN, view_stack()(inner))

    return decorator


@method_decorator(view_stack(), name="dispatch")
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

    def add_response_handler(self, handler: RESPONSE_HANDLER):
        add_response_handler(self.request, handler)


class ElementIdMixin:
    element_id: Optional[str] = None

    def get_element_id(self) -> str:
        return self.element_id or self.__class__.__name__


class ElementAttrsMixin:
    def get_attrs(self) -> dict[str, str]:
        return {}


class SingletonPathMixin:
    url_name: ClassVar[Optional[str]] = None

    @classmethod
    def create_path(cls: Any, path_segment: Optional[str] = None):
        if cls.url_name is not None:
            raise Exception("create_path() can only be called once per view class.")
        if path_segment is None:
            path_segment = cls.__name__
        url_name = f"{cls.__module__}.{cls.__name__}".replace(".", "-")
        cls.url_name = url_name
        view = cls.as_view()
        return path(path_segment, view, name=url_name)

    def url(self) -> str:
        if self.url_name is None:
            raise Exception("View was not registered with create_path().")
        return reverse(self.url_name)
