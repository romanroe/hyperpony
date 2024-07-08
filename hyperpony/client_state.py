import dataclasses
import inspect
from dataclasses import dataclass
from typing import Any, cast, Optional
from typing import get_type_hints, TypeVar, Tuple

import orjson
from django.http import HttpRequest
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic.base import ContextMixin
from pydantic import create_model, BaseModel

from hyperpony.view import ElementIdMixin


@dataclass()
class ClientState:
    default: Any = dataclasses.field(default=None)
    client_to_server: bool = dataclasses.field(default=True)
    model: Optional[Any] = dataclasses.field(default=None)


T = TypeVar("T")


def client_state(
    default: T, *, client_to_server=False, model: Optional[Any] = None
) -> T:
    return cast(
        T, ClientState(default=default, client_to_server=client_to_server, model=model)
    )


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


class Meta(type):
    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)
        print("Meta.__new__", x)
        return x


class ClientStateView(ElementIdMixin, ContextMixin, View, metaclass=Meta):
    _client_state_client_to_server_exludes: list[str] = []
    _client_state_schema: type[BaseModel]
    is_client_state_present = False

    def __new__(cls, *args, **kwargs):
        ths = get_type_hints(cls)
        cls.__params_view_parameters = []
        schema_fields: dict[str, Tuple[Any, Any]] = {}
        instance_fields: dict[str, ClientState] = {}
        for member_name, ip in inspect.getmembers(cls):
            if isinstance(ip, ClientState):
                if not ip.client_to_server:
                    cls._client_state_client_to_server_exludes.append(member_name)
                target_type = (
                    ip.model
                    if ip.model is not None
                    else ths.get(
                        member_name, type(ip.default) if ip.default is not None else str
                    )
                )
                schema_fields[member_name] = (target_type, ip.default)
                instance_fields[member_name] = ip

        cls._client_state_schema = create_model(
            f"{cls.__name__}ClientState",
            **schema_fields,  # type: ignore
        )
        instance = super().__new__(cls)
        for k, v in instance_fields.items():
            setattr(instance, k, v.default)
        return instance

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if request.htmx and not hasattr(request, "_hyperpony_client_state"):
            setattr(request, "_hyperpony_client_state", _extract_client_states(request))

        if client_state := getattr(request, "_hyperpony_client_state", None):
            client_state_element = client_state.get(self.get_element_id(), None)
            if client_state_element is not None:
                self.is_client_state_present = True
                model = self._client_state_schema.model_validate_json(
                    client_state_element
                )
                data = model.model_dump()
                for k, v in data.items():
                    if k not in self._client_state_client_to_server_exludes:
                        setattr(self, k, v)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "hyperpony_client_state_attrs": self.get_client_state_attrs(),
        }

    def get_client_state_attrs(self):
        data = {}
        for k, v in self._client_state_schema.model_fields.items():
            data[k] = getattr(self, k)

        model: BaseModel = self._client_state_schema(**data)
        client_state_json = model.model_dump_json()

        client_to_server_excludes_json = orjson.dumps(
            self._client_state_client_to_server_exludes
        )
        x_data = (
            " x-data='{client_state:"
            + client_state_json
            + ",client_to_server_excludes:"
            + client_to_server_excludes_json.decode("utf-8")
            + "}' "
        )
        attrs = f" __hyperpony_client_state__ = '{self.get_element_id()}' f{x_data} "
        return mark_safe(attrs)
