# import functools
# import typing
# from typing import Callable
#
# from django.http import HttpRequest, HttpResponse
# from typing_extensions import deprecated
#
# from hyperpony.utils import VIEW_FN
#
#
# @deprecated("use CBV")
# def view_stack() -> Callable[[VIEW_FN], VIEW_FN]:
#     def decorator(fn: VIEW_FN) -> VIEW_FN:
#         if getattr(fn, "hyperpony_view_stack_aware", False):
#             return fn
#
#         setattr(fn, "hyperpony_view_stack_aware", True)
#
#         @functools.wraps(fn)
#         def inner(*args, **kwargs) -> HttpResponse:
#             request: HttpRequest = args[0]
#             stack = get_view_fn_call_stack_from_request(request)
#             try:
#                 stack.append(fn)
#                 response = fn(request, *args[1:], **kwargs)
#                 return response
#             finally:
#                 stack.pop()
#
#         return typing.cast(VIEW_FN, inner)
#
#     return decorator
#
#
# @typing.overload
# @deprecated("use CBV")
# def get_view_fn_call_stack_from_request(request: HttpRequest) -> list[Callable]: ...

#
# @typing.overload
# @deprecated("use CBV")
# def get_view_fn_call_stack_from_request(
#     request: HttpRequest, create: bool
# ) -> typing.Optional[list[Callable]]: ...
#
#
# @deprecated("use CBV")
# def get_view_fn_call_stack_from_request(
#     request: HttpRequest, create=True
# ) -> typing.Optional[list[Callable]]:
#     call_stack = getattr(request, "__hyperpony_view_fn_call_stack", None)
#     call_stack = [] if call_stack is None and create else call_stack
#     setattr(request, "__hyperpony_view_fn_call_stack", call_stack)
#     return call_stack
#
#
# @deprecated("use CBV")
# def get_view_fn_call_stack_from_request_or_raise(
#     request: HttpRequest,
# ) -> list[Callable]:
#     stack = get_view_fn_call_stack_from_request(request, create=False)
#     if stack is None or len(stack) == 0:
#         raise Exception("This function can only be called from within a Hyperpony view.")
#     return stack
#
#
# @deprecated("use CBV")
# def is_view_stack_at_root(request: HttpRequest) -> bool:
#     stack = get_view_fn_call_stack_from_request_or_raise(request)
#     return len(stack) == 1
# return True
#
