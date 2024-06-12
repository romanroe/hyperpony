import functools
from dataclasses import dataclass, field
from typing import Any, Callable, cast, Optional

from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.views import View
from django_htmx.http import reswap as htmx_reswap
from django_htmx.http import retarget as htmx_retarget

from hyperpony.utils import is_response_processable, response_to_str
from hyperpony.view import view, VIEW_FN, ViewResponse


# def split_content_and_swap_oob(content: str) -> Tuple[str, str]:
#     if "hx-swap-oob" not in content.lower():
#         return content, ""
#
#     parsed: lxml.html.HtmlElement = lxml.html.fromstring(content)
#     main = ""
#     swaps = ""
#     for el in parsed:
#         el_str = str(lxml.html.tostring(el))
#         if "hx-swap-oob" not in el.attrib:
#             main += el_str
#         else:
#             swaps += el_str
#
#     return main, swaps


@dataclass()
class ElementMeta:
    element_id: Optional[str] = None
    tag: str = "div"
    hx_target: str = "this"
    hx_swap: str = "outerHTML"
    attrs: dict[str, str] = field(default_factory=dict)
    nowrap: bool = False

    # @staticmethod
    # def set_in_request(request) -> "ElementMeta":
    #     meta = ElementMeta()
    #     setattr(request, "__hyperpony_element_meta", meta)
    #     return meta
    #
    # @staticmethod
    # def get_from_request(request: HttpRequest, create=False) -> Optional["ElementMeta"]:
    #     meta = getattr(request, "__hyperpony_element_meta", None)
    #     if meta is None and create:
    #         meta = ElementMeta.set_in_request(request)
    #     return meta


class ElementResponse(ViewResponse):
    @staticmethod
    def empty() -> HttpResponse:
        return ElementResponse(HttpResponse()).as_response()

    @staticmethod
    def wrap(response: HttpResponseBase, meta: ElementMeta) -> HttpResponseBase:
        if not isinstance(response, HttpResponseBase):
            raise TypeError(
                f"View function returned {type(response)}, expected HttpResponseBase"
            )

        if isinstance(response, ElementResponse):
            return response.as_response()

        if meta.nowrap:
            return response

        if is_response_processable(response, "text/html"):
            attr_id = f"id='{meta.element_id}'" if meta.element_id is not None else ""
            attr_hx_target = f"hx-target='{meta.hx_target}'" if meta.hx_target else ""
            attr_hx_swap = f"hx-swap='{meta.hx_swap}'" if meta.hx_swap else ""
            attrs_str = " ".join(f'{k}="{v}"' for k, v in meta.attrs.items())
            content = response_to_str(response)
            wrapped = (
                f"""<{meta.tag} {attr_id} {attr_hx_target} {attr_hx_swap} {attrs_str} hyperpony-element>"""
                f"""{content}"""
                f"""</{meta.tag}>"""
            )
            response.content = bytes(wrapped, "UTF-8")

        return ElementResponse(response).as_response()


def body_response(response: HttpResponse, hx_swap="outerHTML") -> HttpResponse:
    response = htmx_retarget(response, "body")
    response = htmx_reswap(response, cast(Any, hx_swap))
    return response


def element(
    element_id: Optional[str] = None,
    *,
    tag="div",
    hx_target="this",
    hx_swap="outerHTML",
    attrs: dict[str, str] | None = None,
    inject_params=True,
    decorators: Optional[list[Callable]] = None,
    login_required=False,
) -> Callable[[VIEW_FN], VIEW_FN]:
    def decorator(f: VIEW_FN) -> VIEW_FN:
        use_element_id = element_id if isinstance(element_id, str) else f.__name__
        f = view(
            inject_params=inject_params,
            decorators=decorators,
            login_required=login_required,
        )(f)

        @functools.wraps(f)
        def inner(*args, **kwargs) -> HttpResponseBase:
            request: HttpRequest = args[0]
            response = f(request, *args[1:], **kwargs)
            return ElementResponse.wrap(
                response,
                ElementMeta(
                    element_id=use_element_id,
                    tag=tag,
                    hx_target=hx_target,
                    hx_swap=hx_swap,
                    attrs=attrs or {},
                ),
            )

        return cast(VIEW_FN, inner)

    return decorator


class ElementView(View):
    element_id: Optional[str] = None
    tag: str = "div"
    hx_target: str = "this"
    hx_swap: str = "outerHTML"
    attrs: Optional[dict[str, str]] = None
    nowrap: bool = False

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        return ElementResponse.wrap(
            response,
            ElementMeta(
                element_id=self.element_id or self.__class__.__name__,
                tag=self.tag,
                hx_target=self.hx_target,
                hx_swap=self.hx_swap,
                attrs=self.attrs or {},
            ),
        )
