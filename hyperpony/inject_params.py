import dataclasses
import functools
import inspect
import typing
import uuid
from dataclasses import dataclass
from types import UnionType
from typing import (
    Any,
    Callable,
    cast,
    get_args,
    get_origin,
    Optional,
    Type,
    TypeVar,
)

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.http import HttpRequest, HttpResponse, QueryDict
from django.utils.decorators import method_decorator
from django.views import View

from hyperpony.utils import _get_request_from_args, VIEW_FN, is_none_compatible
from hyperpony.view_stack import view_stack, is_view_stack_at_root


def inject_params() -> Callable[[VIEW_FN], VIEW_FN]:
    def decorator(fn: VIEW_FN) -> VIEW_FN:
        parameters: list[inspect.Parameter] = list(
            inspect.signature(fn).parameters.values()
        )
        injected_params = _extract_injected_params(fn, parameters)
        arg_names = [p.name for p in parameters]

        @functools.wraps(fn)
        def inner(*args, **kwargs) -> HttpResponse:
            supplied_args = arg_names[: len(args)]
            for name, ip in injected_params.items():
                if name not in kwargs and name not in supplied_args:
                    kwargs[name] = ip.get_value(args, kwargs)
                    replace_response = ip.replace_response(
                        _get_request_from_args(cast(Any, args)), kwargs[name]
                    )
                    if replace_response is not None:
                        return replace_response

            return fn(*args, **kwargs)

        return cast(VIEW_FN, view_stack()(inner))

    return decorator


# class InjectParamsViewBase(type):
#     def __new__(cls, name, bases, attrs):
#         parents = [b for b in bases if isinstance(b, InjectParamsViewBase)]
#         if not parents:
#             return super().__new__(cls, name, bases, attrs)
#
#         params: dict[str, QueryParam] = {}
#         type_hints = attrs["__annotations__"] if "__annotations__" in attrs else {}
#         for member_name, qp in attrs.items():
#             if isinstance(qp, QueryParam):
#                 qp.ignore_view_stack = True  # CBVs do not rely on the view stack
#                 qp.name = member_name
#                 qp.target_type = type_hints.get(
#                     member_name, type(qp.default) if qp.default is not None else str
#                 )
#                 qp.check()
#                 params[member_name] = qp
#                 attrs[member_name] = qp.default
#
#         view_class: Any = super().__new__(cls, name, bases, attrs)
#         setattr(view_class, "_hyperpony_params", params)
#         return view_class


@method_decorator(view_stack(), name="dispatch")
class InjectParamsView(View):
    def __new__(cls, *args, **kwargs):
        view_class = super().__new__(cls)
        if hasattr(cls, "__hyperpony_params"):
            return view_class

        ths = typing.get_type_hints(cls)
        params: dict[str, QueryParam] = {}
        for member_name, ip in inspect.getmembers(cls):
            if isinstance(ip, QueryParam):
                ip.ignore_view_stack = True  # CBVs do not rely on the view stack
                ip.name = member_name
                ip.target_type = ths.get(
                    member_name, type(ip.default) if ip.default is not None else str
                )
                ip.check()
                params[member_name] = ip
                delattr(cls, member_name)

        setattr(cls, "__hyperpony_params", params)
        return view_class

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k, v in kwargs.items():
            if qp := self._hyperpony_params().get(k, None):
                qp.default = v

        for k, v in self._hyperpony_params().items():
            if v.default is not _REQUIRED:
                setattr(self, k, v.default)

    @classmethod
    def _hyperpony_params(cls) -> dict[str, "QueryParam"]:
        return getattr(cls, "__hyperpony_params")

    def setup(self, request, *args, **kwargs):
        for attrvalue in self._hyperpony_params().values():
            value = attrvalue.get_value([request], kwargs)
            setattr(self, attrvalue.name, value)

        return super().setup(request, *args, **kwargs)


@dataclass
class InjectedParam:
    name: str = dataclasses.field(init=False)
    target_type: type = dataclasses.field(init=False)

    def check(self):
        pass

    def get_value(self, args: Any, kwargs: dict[str, Any]) -> Any:
        pass

    def replace_response(
        self, request: HttpRequest, value: Any
    ) -> Optional[HttpResponse]:
        pass


def _extract_injected_params(
    view_fn: Callable[[Any], Any], parameters: list[inspect.Parameter]
) -> dict[str, InjectedParam]:
    """
    Extracts all injected parameters from the given list of function arguments.
    """
    result: dict[str, InjectedParam] = {}

    # skip first request parameter
    parameters = parameters[1:]

    for arg in parameters:
        if isinstance(arg.default, InjectedParam):
            ip: InjectedParam = arg.default
            result[ip.name] = _setup_fn_injected_param(view_fn, ip, arg.name, arg)

    return result


def _setup_fn_injected_param(
    view_fn: Callable[[Any], Any],
    ip: InjectedParam,
    name: str,
    parameter: inspect.Parameter,
):
    ip.name = name
    ip.target_type = (
        parameter.annotation
        if parameter.annotation is not inspect.Signature.empty
        else type(parameter.default)
        if parameter.default is not inspect.Parameter.empty
        and not isinstance(parameter.default, InjectedParam)
        else type(parameter.default.default)
        if isinstance(parameter.default, QueryParam)
        and parameter.default.default is not None
        else str
    )
    # ip.view_fn = view_fn
    ip.check()
    return ip


################################################################################
### request params to args
################################################################################


@dataclasses.dataclass
class QueryParam(InjectedParam):
    query_param_name: Optional[str] = dataclasses.field(default=None)
    default: Any = dataclasses.field(default=None)
    ignore_view_stack: bool = dataclasses.field(default=False)
    methods: typing.Iterable[
        typing.Literal["GET", "POST", "PUT", "DELETE", "PATCH", "PATH", "__all__"]
    ] = dataclasses.field(default=("GET",))
    # parse_form_urlencoded_body: bool = dataclasses.field(default=True)

    def __post_init__(self):
        if "__all__" in self.methods:
            self.methods = ("GET", "POST", "PUT", "DELETE", "PATCH", "PATH")

    def check(self):
        if self.query_param_name is None:
            self.query_param_name = self.name

    def _create_lookup_dict(self, request: HttpRequest, **kwargs):
        source = QueryDict(mutable=True)
        getqd = cast(QueryDict, request.GET)
        postqd = cast(QueryDict, request.POST)

        if request.method in self.methods:
            # Order matters! GET overrides POST
            source.update({name: postqd.getlist(name) for name in postqd})
            source.update({name: getqd.getlist(name) for name in getqd})

            if (
                # self.parse_form_urlencoded_body and
                request.content_type == "application/x-www-form-urlencoded"
            ):
                patchqd = QueryDict(request.body, encoding=request.encoding)
                source.update({name: patchqd.getlist(name) for name in patchqd})

        # if "POST" in self.methods:
        #     postqd = cast(QueryDict, request.POST)
        #     postd = {name: postqd.getlist(name) for name in postqd}
        #     source.update(postd)
        #
        # if "GET" in self.methods:
        #     getqd = cast(QueryDict, request.GET)
        #     getd = {name: getqd.getlist(name) for name in getqd}
        #     source.update(getd)
        #
        # if "PATH" in self.methods and request.resolver_match:
        #     for key, value in request.resolver_match.kwargs.items():
        #         if key not in source:
        #             source[key] = [value]
        #
        # if (
        #     request.method in self.methods
        #     and self.parse_form_urlencoded_body
        #     and request.content_type == "application/x-www-form-urlencoded"
        # ):
        #     formqd = QueryDict(mutable=True)
        #     formqd.update(
        #         QueryDict(request.body, mutable=True, encoding=request.encoding)
        #     )
        #     for name in formqd.keys():
        #         if name not in source:
        #             source[name] = formqd.getlist(name)

        for k, v in kwargs.items():
            source[k] = [v]

        return source

    def get_value(self, args: Any, kwargs: dict[str, Any]):
        request = _get_request_from_args(args)
        lookup_dict = self._create_lookup_dict(request, **kwargs)

        if self.ignore_view_stack or is_view_stack_at_root(request):
            values = lookup_dict.get(self.query_param_name, None)
        else:
            values = None

        if values is None:
            if is_none_compatible(self.target_type):
                return None
            if self.default is not _REQUIRED:
                values = [self.default]
            else:
                raise Exception(
                    f"No value found for non-optional request parameter '{self.query_param_name}'"
                )

        return _convert_value_to_type(values, self.target_type)


T = TypeVar("T")

_REQUIRED = object()


def param(
    default: T = cast(Any, _REQUIRED),
    *,
    methods: typing.Iterable[
        typing.Literal["GET", "POST", "PUT", "DELETE", "PATCH", "__all__"]
    ] = ("__all__",),
    # parse_form_urlencoded_body: bool = True,
    ignore_view_stack=False,
) -> T:
    return cast(
        T,
        QueryParam(
            default=default,
            ignore_view_stack=ignore_view_stack,
            methods=methods,
            # parse_form_urlencoded_body=parse_form_urlencoded_body,
        ),
    )


def check_and_return_model_type(target_type: Any) -> Type[models.Model] | None:
    if get_origin(target_type) is typing.Union or isinstance(target_type, UnionType):
        # union type
        for t in get_args(target_type):
            if issubclass(t, models.Model):
                return cast(Type[models.Model], t)
    elif issubclass(target_type, models.Model):
        # no union type
        return cast(Type[models.Model], target_type)

    return None


class ObjectDoesNotExistWithPk(ObjectDoesNotExist):
    pk: Any

    def __init__(self, pk: Any):
        super().__init__(f"Object with pk {pk} does not exist")
        self.pk = pk


def _convert_value_to_type(values: list[Any], target_type: type):
    # List type
    if get_origin(target_type) is list:
        list_type = get_args(target_type)[0]
        return [_convert_value_to_type([v], list_type) for v in values]

    if target_type is list:
        return [_convert_value_to_type([v], str) for v in values]

    # Scalar types
    value = values[0]

    try:
        if value is None:
            pass  # trigger ValueError
        elif model_type := check_and_return_model_type(target_type):
            try:
                return model_type.objects.get(pk=value)
            except model_type.DoesNotExist as e:
                if issubclass(ObjectDoesNotExistWithPk, target_type):
                    raise ObjectDoesNotExistWithPk(value)
                raise e
        elif isinstance(value, target_type):
            return value  # nothing to do
        elif issubclass(str, target_type):
            return str(value)
        elif issubclass(int, target_type):
            return int(value)
        elif issubclass(float, target_type):
            return float(value)
        elif issubclass(bool, target_type):
            return False if value in (False, "", "false", "False") else True
        elif issubclass(uuid.UUID, target_type):
            return uuid.UUID(value)
    except Exception as error:
        if isinstance(error, target_type):
            return error
        raise error

    raise ValueError(f"Unsupported type: {target_type} for value: {value}")
