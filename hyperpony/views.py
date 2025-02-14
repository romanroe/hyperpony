from io import BytesIO
from typing import cast, Optional, Union, Any, Callable

from django.db.models import Model
from django.http import HttpRequest, HttpResponse, QueryDict
from django.urls import path, reverse, ResolverMatch, resolve, get_urlconf, get_resolver

from hyperpony.htmx import swap_oob
from hyperpony.response_handler import RESPONSE_HANDLER, add_response_handler
from hyperpony.utils import response_to_str


def is_head(request: HttpRequest) -> bool:
    return request.method == "HEAD"


def is_get(request: HttpRequest) -> bool:
    return request.method == "GET"


def is_post(request: HttpRequest) -> bool:
    return request.method == "POST"


def is_put(request: HttpRequest) -> bool:
    return request.method == "PUT"


def is_patch(request: HttpRequest) -> bool:
    return request.method == "PATCH"


def is_delete(request: HttpRequest) -> bool:
    return request.method == "DELETE"


class ViewUtilsMixin:
    """
    This mixin serves as a helper that simplifies request method
    detection, response management, and additional request-specific handling logic.
    """

    def pre_dispatch(self, request, *args, **kwargs):
        """
        Pre-processes the request before it is dispatched to the corresponding handler.
        """
        pass

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        self.pre_dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)  # type: ignore

    @property
    def path(self) -> str:
        """
        Convenience method for accessing the path of the current request.
        """
        # rm = self.request.resolver_match  # type: ignore
        # return reverse(rm.view_name, args=rm.args, kwargs=rm.kwargs)
        return self.request.path  # type: ignore

    def add_response_handler(self, handler: RESPONSE_HANDLER):
        """
        Adds a response handler to the current request process to handle
        responses in a custom way. The provided handler should conform to the specified
        RESPONSE_HANDLER interface and is applied during the request handling lifecycle.
        """
        add_response_handler(self.request, handler)  # type: ignore

    def add_swap_oob(
        self,
        additional: HttpResponse | list[HttpResponse],
        hx_swap_oob_method="outerHTML",
    ):
        """
        Adds an out-of-band (OOB) "swap" operation.

        Parameters:
            additional: HttpResponse or list[HttpResponse]
                Represents one or multiple HTTP responses that contain the data or markup
                needed to update the DOM.
                **Important:** The responses must only contain a single element with an 'id' attribute.
            hx_swap_oob_method: str, optional
                Specifies the HTMX swap method, determining how the OOB content should
                replace or modify the targeted DOM element. Defaults to "outerHTML".
        """
        self.add_response_handler(
            lambda response: swap_oob(response, additional, hx_swap_oob_method)
        )

    # noinspection PyPep8Naming
    def add_swap_oob_view(
        self,
        path_name: str,
        *,
        GET: Union[QueryDict, dict, None] = None,  # noqa: N803
        POST: Union[QueryDict, dict, None] = None,  # noqa: N803
        args=None,
        kwargs: dict | None = None,
        view_kwargs: dict | None = None,
        hx_swap_oob_method="outerHTML",
    ):
        self.add_swap_oob(
            invoke_view(
                self.request,  # type: ignore
                path_name,
                GET=GET,
                POST=POST,
                args=args,
                kwargs=kwargs,
                view_kwargs=view_kwargs,
            ),
            hx_swap_oob_method=hx_swap_oob_method,
        )

    def is_embedded_view(self):
        return is_embedded_request(self.request)  # type: ignore


def invoke_view(
    request: HttpRequest,
    path_name: str | Callable,
    *,
    GET: Union[QueryDict, dict, None] = None,  # noqa: N803
    POST: Union[QueryDict, dict, None] = None,  # noqa: N803
    args=None,
    kwargs: dict | None = None,
    view_kwargs: dict | None = None,
) -> HttpResponse:
    if isinstance(GET, dict):
        get_qd = QueryDict(mutable=True)
        get_qd.update(GET)
    elif GET is None:
        get_qd = QueryDict()
    else:
        get_qd = GET
    if isinstance(POST, dict):
        post_qd = QueryDict(mutable=True)
        post_qd.update(POST)
    else:
        post_qd = POST

    embedded_req = EmbeddedRequest.create(request, get_qd, post_qd)

    # enrich missing kwargs with view_kwargs
    urlconf = get_urlconf()
    resolver = get_resolver(urlconf)
    if entry := resolver.reverse_dict.get(path_name):
        _, _, _, params = entry
        for k in params.keys():
            if (kwargs is None or k not in kwargs) and view_kwargs and k in view_kwargs:
                kwargs = kwargs if kwargs else {}
                kwargs[k] = view_kwargs[k]

    reverse_args = [_cleanup_value_path_reverse(a) for a in args] if args is not None else None
    reverse_kwargs = (
        {k: _cleanup_value_path_reverse(v) for k, v in kwargs.items()}
        if kwargs is not None
        else None
    )

    url = reverse(path_name, args=reverse_args, kwargs=reverse_kwargs)
    rm: ResolverMatch = resolve(url)
    embedded_req.path = url
    embedded_req.path_info = url
    embedded_req.resolver_match = rm

    invoke_kwargs = {
        **rm.kwargs,
        **(view_kwargs or {}),
    }

    # store model instances in hyperpony_params_bypass_values
    if kwargs is not None:
        for k, v in kwargs.items():
            if isinstance(v, Model):
                embedded_req.hyperpony_params_bypass_values[k] = v

    response = rm.func(embedded_req, *rm.args, **invoke_kwargs)
    return response


def _cleanup_value_path_reverse(value):
    if isinstance(value, Model):
        return str(value.pk)
    return value


# noinspection PyPep8Naming
def embed_view(
    request: HttpRequest,
    path_name: str | Callable,
    *,
    GET: Union[QueryDict, dict, None] = None,  # noqa: N803
    POST: Union[QueryDict, dict, None] = None,  # noqa: N803
    args=None,
    kwargs: dict | None = None,
    view_kwargs: dict | None = None,
) -> str:
    response = invoke_view(
        request, path_name, GET=GET, POST=POST, args=args, kwargs=kwargs, view_kwargs=view_kwargs
    )
    return response_to_str(response)


def is_embedded_request(request: HttpRequest) -> bool:
    return isinstance(request, EmbeddedRequest)


class SingletonPathMixin:
    """
    This mixin is designed to ensure a unique path for the views that implement it.
    It allows using the view directly, and various utility methods for reverse lookups
    and handling out-of-band swap responses.
    """

    @classmethod
    def create_path(
        cls,
        path_suffix: Optional[str] = None,
        *,
        full_path: Optional[str] = None,
        name: Optional[str] = None,
    ):
        if "__viewname" in cls.__dict__:
            raise Exception("create_path() can only be called once per view class.")
        if full_path is not None and path_suffix is not None:
            raise Exception("Either full_path or path_suffix can be specified, not both.")

        if full_path is None:
            path_suffix = "" if path_suffix is None else path_suffix
            full_path = cls.__name__
            full_path += "/" if len(path_suffix) > 0 and not path_suffix.startswith("/") else ""
            full_path += path_suffix

        path_name = (
            name if name is not None else f"{cls.__module__}.{cls.__name__}".replace(".", "-")
        )
        setattr(cls, "__viewname", path_name)

        return path(full_path, cast(Any, cls).as_view(), name=path_name)

    @classmethod
    def get_viewname(cls) -> str | Callable:
        if "__viewname" in cls.__dict__:
            return cls.__dict__["__viewname"]

        urlconf = get_urlconf()
        resolver = get_resolver(urlconf)
        matches = [
            k
            for k in resolver.reverse_dict.keys()
            if hasattr(k, "view_class") and k.view_class is cls
        ]
        if len(matches) == 0:
            raise Exception(f"View {cls} is not registered.")
        if len(matches) > 1:
            raise Exception(f"View {cls} is registered multiple times!")

        viewname = matches[0]
        setattr(cls, "__viewname", viewname)

        return viewname

    # noinspection PyPep8Naming
    @classmethod
    def invoke(
        cls,
        request: HttpRequest,
        *,
        GET: Union[QueryDict, dict, None] = None,  # noqa: N803
        POST: Union[QueryDict, dict, None] = None,  # noqa: N803
        args=None,
        kwargs: dict | None = None,
        view_kwargs: dict | None = None,
    ):
        path_name = cls.get_viewname()
        if path_name is None:
            raise Exception(f"View {cls} was not registered with create_path().")
        return invoke_view(
            request,
            path_name,
            GET=GET,
            POST=POST,
            args=args,
            kwargs=kwargs,
            view_kwargs=view_kwargs,
        )

    # noinspection PyPep8Naming
    @classmethod
    def embed(
        cls,
        request: HttpRequest,
        *,
        GET: Union[QueryDict, dict, None] = None,  # noqa: N803
        POST: Union[QueryDict, dict, None] = None,  # noqa: N803
        args=None,
        kwargs: dict | None = None,
        view_kwargs: dict | None = None,
    ):
        # path_name = cls.get_viewname()
        # if path_name is None:
        #     raise Exception(f"View {cls} was not registered with create_path().")
        # return embed_view(
        #     request,
        #     path_name,
        #     GET=GET,
        #     POST=POST,
        #     args=args,
        #     kwargs=kwargs,
        #     view_kwargs=view_kwargs,
        # )
        return response_to_str(
            cls.invoke(
                request, GET=GET, POST=POST, args=args, kwargs=kwargs, view_kwargs=view_kwargs
            )
        )

    # noinspection PyPep8Naming
    @classmethod
    def swap_oob(
        cls,
        request: HttpRequest,
        *,
        hx_swap="outerHTML",
        GET: Union[QueryDict, dict, None] = None,  # noqa: N803
        POST: Union[QueryDict, dict, None] = None,  # noqa: N803
        args=None,
        kwargs: dict | None = None,
        view_kwargs: dict | None = None,
    ):
        self_response = cls.invoke(
            request, GET=GET, POST=POST, args=args, kwargs=kwargs, view_kwargs=view_kwargs
        )
        add_response_handler(
            request,
            lambda response: swap_oob(response, self_response, hx_swap),
        )

    @classmethod
    def reverse(cls, *, urlconf=None, args=None, kwargs=None, current_app=None):
        return reverse(
            cls.get_viewname(), urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app
        )


class EmbeddedRequest(HttpRequest):
    hyperpony_params_bypass_values: dict

    @classmethod
    def create(
        cls,
        original_request: HttpRequest,
        get: Optional[QueryDict] = None,
        post: Optional[QueryDict] = None,
    ):
        self = cls()
        self.hyperpony_params_bypass_values = {}
        self.__original_request = original_request
        self._read_started = False
        self._stream = BytesIO()
        self.COOKIES = original_request.COOKIES
        self.META = original_request.META
        self.content_type = "text/html; charset=utf-8"
        self.content_params = {}
        self.method = "GET" if post is None else "POST"
        self.GET = cast(Any, get) if get is not None else QueryDict()
        self.POST = cast(Any, post) if post is not None else QueryDict()
        return self

    def __getattr__(self, name):
        return getattr(self.__original_request, name)


class ElementIdMixin:
    element_id: Optional[str] = None

    def get_element_id(self) -> str:
        return self.element_id or self.__class__.__name__


class ElementAttrsMixin:
    def get_attrs(self) -> dict[str, str]:
        return {}
