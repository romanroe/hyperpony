# ruff: noqa: F401

from .client_state import ClientStateMixin
from .element import ElementResponse, ElementMixin
from .inject_params import param, InjectParamsMixin
from .views import SingletonPathMixin, ViewUtilsMixin


class HyperponyMixin(InjectParamsMixin, ViewUtilsMixin):
    pass


class HyperponyElementMixin(InjectParamsMixin, ClientStateMixin, ViewUtilsMixin, ElementMixin):
    pass
