import dataclasses
from dataclasses import dataclass
from typing import Any, cast, Optional, Tuple
from typing import TypeVar

import orjson
from django.http import HttpRequest
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic.base import ContextMixin
from pydantic import BaseModel, create_model

from hyperpony.view import ElementIdMixin


@dataclass()
class ClientState:
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
        ClientState(
            default=default,
            client_to_server=client_to_server,
            schema=schema,
        ),
    )


@dataclass()
class ClientStateViewConfig:
    schema_out: type[BaseModel]
    schema_in: type[BaseModel]
    client_state_fields: dict[str, ClientState]
    client_to_server_excludes: list[str]


class ClientStateViewBase(type):
    def __new__(cls, name, bases, attrs):
        parents = [b for b in bases if isinstance(b, ClientStateViewBase)]
        if not parents:
            return super().__new__(cls, name, bases, attrs)

        schema_out_fields: dict[str, Tuple[Any, Any]] = {}
        schema_in_fields: dict[str, Tuple[Any, Any]] = {}
        client_to_server_excludes: list[str] = []
        client_state_fields: dict[str, ClientState] = {}

        for attrname, attrval in attrs.items():
            if isinstance(attrval, ClientState):
                client_state_fields[attrname] = attrval
                target_type = (
                    attrval.schema
                    if attrval.schema is not None
                    else type(attrval.default)
                    if attrval.default is not None
                    else str
                )
                schema_out_fields[attrname] = (target_type, attrval.default)
                if not attrval.client_to_server:
                    client_to_server_excludes.append(attrname)
                else:
                    schema_in_fields[attrname] = (target_type, attrval.default)

                attrs[attrname] = attrval.default

        prefix = f"{name}ClientState"
        schema_out = create_model(f"{prefix}Out", **schema_out_fields)  # type: ignore
        schema_in = create_model(f"{prefix}In", **schema_in_fields)  # type: ignore

        view_class: Any = super().__new__(cls, name, bases, attrs)
        setattr(
            view_class,
            "_hyperpony_client_state_config",
            ClientStateViewConfig(
                schema_out, schema_in, client_state_fields, client_to_server_excludes
            ),
        )
        return view_class


class ClientStateView(
    ElementIdMixin, ContextMixin, View, metaclass=ClientStateViewBase
):
    is_client_state_present = False

    def hyperpony_client_state_config(self) -> ClientStateViewConfig:
        return getattr(self, "_hyperpony_client_state_config")

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        if getattr(request, "htmx", False) and not hasattr(
            request, "_hyperpony_client_state"
        ):
            setattr(request, "_hyperpony_client_state", _extract_client_states(request))

        if client_state := getattr(request, "_hyperpony_client_state", None):
            client_state_element = client_state.get(self.get_element_id(), None)
            if client_state_element is not None:
                self.is_client_state_present = True
                config = self.hyperpony_client_state_config()
                model = config.schema_in.model_validate_json(client_state_element)
                data = model.model_dump()
                for k, v in data.items():
                    setattr(self, k, v)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "hyperpony_client_state_attrs": self.get_client_state_attrs(),
        }

    def get_client_state_attrs(self):
        meta = self.hyperpony_client_state_config()
        data = {}
        for k in meta.schema_out.model_fields.keys():
            data[k] = getattr(self, k)

        model: BaseModel = meta.schema_out(**data)
        client_state_json = model.model_dump_json()

        client_to_server_excludes_json = orjson.dumps(meta.client_to_server_excludes)
        x_data = (
            ' x-data=\'{"client_state":'
            + client_state_json
            + ',"client_to_server_excludes":'
            + client_to_server_excludes_json.decode("utf-8")
            + "}' "
        )
        attrs = f" __hyperpony_client_state__ = '{self.get_element_id()}' f{x_data} "
        return mark_safe(attrs)


def _extract_client_states(request: HttpRequest) -> dict[str, Any]:
    qd = {
        **request.POST,
        **request.GET,
    }
    client_states = {}
    for key, value in qd.items():
        if key.startswith("__hyperpony_cs__"):
            client_states[key[len("__hyperpony_cs__") :]] = value[0]

    return client_states
