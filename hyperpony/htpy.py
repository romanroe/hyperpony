import inspect
import json
from typing import ClassVar, Any

from django.http import HttpRequest, HttpResponse, QueryDict
from django.views import View
from htpy import Node, render_node  # type: ignore


class HtpyView(View):
    # noinspection PyUnusedLocal
    def get(self, request, *args, **kwargs):
        return HttpResponse(render_node(self.render(request, *args, **kwargs)))

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def render(self, request: HttpRequest, *args, **kwargs) -> Node:
        raise NotImplementedError()


class HtPyActionsMixin:
    hp_action_params_meta: ClassVar[dict[str, set[str]]]

    def _get_action_method(self, action: str):
        method = getattr(self, f"action_{action}", None)
        if method is None:
            raise Exception(
                f"Unknown action: '{action}' ({self} doesn't implement the method 'action_{action}(**kwargs)')."
            )

        if not hasattr(self.__class__, "hp_action_params_meta"):
            self.__class__.hp_action_params_meta = {}

        meta = self.__class__.hp_action_params_meta
        if method.__name__ not in meta:
            meta[method.__name__] = set()
            signature = inspect.signature(method)
            for param in signature.parameters.values():
                if param.kind == inspect.Parameter.VAR_KEYWORD:
                    meta[method.__name__].add("**kwargs")
                else:
                    meta[method.__name__].add(param.name)

        return method

    def create_action(self, name: str, **kwargs):
        """
        Validates and prepares parameters for an action method call.

        Parameters
        ----------
        name : str
            The name of the action method to be invoked.
        kwargs : dict
            Additional parameters to be passed to the action method.

        Returns
        -------
        dict
            A dictionary containing the necessary `hx-patch` and `hx-vals` entries.
            The intended use is to **spread** this dictionary during the invocation of HtpPy elements,
            e.g.
            `div(**self.action_kwargs("my_action", param1="value1"), hx_trigger="click")[click me]`

        Raises
        ------
        Exception
            If any parameter in `kwargs` is not defined in the action method's parameter
            metadata or if the action method does not accept `**kwargs`.
        """
        method = self._get_action_method(name)  # raises exception on missing action method
        hp_action_params_meta = self.__class__.hp_action_params_meta[method.__name__]
        for k in kwargs.keys():
            if "**kwargs" not in hp_action_params_meta and k not in hp_action_params_meta:
                raise Exception(
                    f"Unknown action parameter: '{k}' ({self.__class__.__name__}#{method.__name__} doesn't accept the parameter '{k}' or **kwargs)."
                )

        return {
            "hx-patch": self.path,  # type: ignore
            **hx_vals(__hp_action=name, **{f"__hp_action_param_{k}": v for k, v in kwargs.items()}),
        }

    def patch(self, request: HttpRequest, *args, **kwargs):
        qd = QueryDict(request.body, encoding=request.encoding)
        if (action := qd.get("__hp_action")) is not None:
            action_params = {}
            for k, v in qd.items():
                ks = k.split("__hp_action_param_")
                if len(ks) == 2:
                    action_params[ks[1]] = v

            response = self._get_action_method(action)(**action_params)
            if response is not None:
                return response

        return self.get(request, *args, **kwargs)  # type: ignore


def hx_vals(**kwargs) -> dict[str, Any]:
    return {"hx-vals": json.dumps({str(k): v for k, v in kwargs.items()})}
