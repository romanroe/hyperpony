# ruff: noqa: F401
from django.views.generic import TemplateView

from .client_state import ClientStateView
from .element import element, ElementResponse, ElementView
from .inject_params import inject_params, param, InjectParamsView
from .view_stack import is_delete, is_get, is_head, is_patch, is_post, is_put
from .views import view, NestedView, SingletonPathMixin


class HyperponyView(
    ClientStateView, InjectParamsView, SingletonPathMixin, TemplateView
):
    pass


class HyperponyElementView(
    ElementView, ClientStateView, InjectParamsView, SingletonPathMixin, TemplateView
):
    pass
