import dataclasses
import inspect
from dataclasses import dataclass
from typing import Any, cast, Optional, Tuple
from typing import TypeVar

import orjson
from django.http import HttpRequest, QueryDict
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic.base import ContextMixin
from pydantic import BaseModel, create_model

from hyperpony.view_stack import view_stack
from hyperpony.views import ElementIdMixin, ElementAttrsMixin


@dataclass()
class ClientStateField:
    default: Any = dataclasses.field(default=None)
    client_to_server: bool = dataclasses.field(default=True)
    schema: Optional[Any] = dataclasses.field(default=None)


T = TypeVar("T")


def client_state(
    default: Optional[T] = None,
    *,
    client_to_server=False,
    schema: Optional[Any] = None,
) -> T:
    return cast(
        T,
        ClientStateField(
            default=default,
            client_to_server=client_to_server,
            schema=schema,
        ),
    )


@dataclass()
class ClientStateViewConfig:
    schema_out: type[BaseModel]
    schema_in: type[BaseModel]
    client_state_fields: dict[str, ClientStateField]
    client_to_server_includes: list[str]


@method_decorator(view_stack(), name="dispatch")
class ClientStateView(ElementAttrsMixin, ElementIdMixin, ContextMixin, View):
    is_client_state_present = False

    def __new__(cls):
        view_class = super().__new__(cls)
        if hasattr(cls, "__hyperpony_client_state_config"):
            return view_class

        client_state_fields: dict[str, ClientStateField] = {}
        schema_out_fields: dict[str, Tuple[Any, Any]] = {}
        schema_in_fields: dict[str, Tuple[Any, Any]] = {}
        client_to_server_includes: list[str] = []

        for attrname, attrval in inspect.getmembers(cls):
            if isinstance(attrval, ClientStateField):
                client_state_fields[attrname] = attrval
                target_type = (
                    attrval.schema
                    if attrval.schema is not None
                    else type(attrval.default)
                    if attrval.default is not None
                    else str
                )
                schema_out_fields[attrname] = (target_type, attrval.default)
                if attrval.client_to_server:
                    client_to_server_includes.append(attrname)
                    schema_in_fields[attrname] = (target_type, attrval.default)

                setattr(cls, attrname, attrval.default)

        prefix = f"{cls.__name__}ClientState"
        schema_out = create_model(f"{prefix}Out", **schema_out_fields)  # type: ignore
        schema_in = create_model(f"{prefix}In", **schema_in_fields)  # type: ignore

        setattr(
            cls,
            "__hyperpony_client_state_config",
            ClientStateViewConfig(
                schema_out, schema_in, client_state_fields, client_to_server_includes
            ),
        )

        return view_class

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k, v in self._hyperpony_client_state_config().client_state_fields.items():
            setattr(self, k, v.default)

    @classmethod
    def _hyperpony_client_state_config(cls) -> ClientStateViewConfig:
        return getattr(cls, "__hyperpony_client_state_config")

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        if getattr(request, "htmx", False) and not hasattr(
            request, "_hyperpony_client_state"
        ):
            setattr(request, "_hyperpony_client_state", _extract_client_states(request))

        if client_state := getattr(request, "_hyperpony_client_state", None):
            if client_state_element := client_state.get(self.get_element_id(), None):
                self.is_client_state_present = True
                config = self._hyperpony_client_state_config()
                model = config.schema_in.model_validate_json(client_state_element)
                data = model.model_dump()
                for k, v in data.items():
                    setattr(self, k, v)

    def get_context_data(self, **kwargs):
        kwargs.setdefault("client_state_attrs", self.get_client_state_attrs())
        return super().get_context_data(**kwargs)

    def get_attrs(self) -> dict[str, str]:
        return {
            **super().get_attrs(),
            **self.get_client_state_dict(),
            "x-cloak": "",
        }

    def get_client_state_dict(self) -> dict[str, str]:
        meta = self._hyperpony_client_state_config()
        data = {}
        for k in meta.schema_out.model_fields.keys():
            data[k] = getattr(self, k)

        model: BaseModel = meta.schema_out(**data)
        x_data = {
            "client_state": model.model_dump(),
            "client_to_server_includes": meta.client_to_server_includes,
        }
        x_data_str = escape(orjson.dumps(x_data).decode())
        return {
            "__hyperpony_client_state__": self.get_element_id(),
            "x-data": x_data_str,
        }

    def get_client_state_attrs(self):
        joined = " ".join(
            f' {k}="{v}" ' for k, v in self.get_client_state_dict().items()
        )
        return mark_safe(joined)


def _extract_client_states(request: HttpRequest) -> dict[str, Any]:
    qd = {
        **request.POST,
    }

    # Since HTMX 2.0, HTTP DELETE requests use parameters, rather than form encoded bodies,
    # for their payload (This is in accordance w/ the spec.).
    if request.method == "DELETE":
        qd.update(request.GET)

    if (
        request.method != "POST"
        and request.content_type == "application/x-www-form-urlencoded"
    ):
        qd.update(QueryDict(request.body, encoding=request.encoding))

    client_states = {}
    for key, value in qd.items():
        if key.startswith("__hyperpony_cs__"):
            client_states[key[len("__hyperpony_cs__") :]] = value[0]

    return client_states
