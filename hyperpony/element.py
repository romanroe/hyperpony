from dataclasses import dataclass, field
from typing import cast, Optional

import wrapt
from django.http import HttpResponse, HttpResponseBase

from hyperpony.utils import is_response_processable, response_to_str
from hyperpony.views import (
    ElementIdMixin,
    ElementAttrsMixin,
)


@dataclass()
class ElementMeta:
    element_id: Optional[str] = None
    tag: str = "div"
    hx_target: str = "this"
    hx_swap: str = "outerHTML"
    attrs: dict[str, str] = field(default_factory=dict)
    nowrap: bool = False


class ElementResponse(wrapt.ObjectProxy):
    @staticmethod
    def empty() -> HttpResponse:
        return cast(HttpResponse, ElementResponse(HttpResponse()))

    @staticmethod
    def wrap(response: HttpResponseBase, meta: ElementMeta) -> HttpResponseBase:
        if not isinstance(response, HttpResponseBase):
            raise TypeError(f"View function returned {type(response)}, expected HttpResponseBase")

        if isinstance(response, ElementResponse):
            return cast(HttpResponseBase, response)

        if meta.nowrap:
            return cast(
                HttpResponseBase,
                (response if isinstance(response, ElementResponse) else ElementResponse(response)),
            )

        if is_response_processable(response, "text/html"):
            attr_id = f"id='{meta.element_id}'" if meta.element_id is not None else ""
            attr_hx_target = f"hx-target='{meta.hx_target}'" if meta.hx_target else ""
            attr_hx_swap = f"hx-swap='{meta.hx_swap}'" if meta.hx_swap else ""
            attrs_str = " ".join(f' {k}="{v}" ' for k, v in meta.attrs.items())
            content = response_to_str(response)
            wrapped = (
                f"""<{meta.tag} {attr_id} {attr_hx_target} {attr_hx_swap} {attrs_str} hyperpony-element>"""
                f"""{content}"""
                f"""</{meta.tag}>"""
            )
            response.content = bytes(wrapped, "UTF-8")

        return cast(HttpResponseBase, ElementResponse(response))

    @classmethod
    def nowrap(cls, response: HttpResponseBase):
        return cls.wrap(response, ElementMeta(nowrap=True))


class ElementMixin(ElementAttrsMixin, ElementIdMixin):
    tag: str = "div"
    hx_target: str = "this"
    hx_swap: str = "outerHTML"
    attrs: Optional[dict[str, str]] = None
    nowrap: bool = False

    def get_attrs(self) -> dict[str, str]:
        return {**super().get_attrs(), **(self.attrs or {})}

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)  # type: ignore
        return ElementResponse.wrap(
            response,
            ElementMeta(
                element_id=self.get_element_id(),
                tag=self.tag,
                hx_target=self.hx_target,
                hx_swap=self.hx_swap,
                attrs=self.get_attrs(),
            ),
        )
