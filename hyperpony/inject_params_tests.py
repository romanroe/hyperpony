from typing import Optional
from uuid import uuid4

import orjson.orjson
import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import path
from django.views import View
from django.views.generic import TemplateView
from pytest_mock import MockerFixture

from hyperpony import param
from hyperpony.inject_params import InjectParamsMixin, ObjectDoesNotExistWithPk
from hyperpony.testutils import view_from_response
from hyperpony.utils import response_to_str
from hyperpony.views import invoke_view, embed_view
from main.models import AppUser


# #######################################################################
# ### CBVs
# #######################################################################


class ViewWithSelfInResponse(View):
    def dispatch(self, request, *args, **kwargs):
        res = HttpResponse("")
        res.view = self
        return res


class TViewP1(InjectParamsMixin, ViewWithSelfInResponse):
    p1: str = param("aaa")

    def dispatch(self, request, *args, **kwargs):
        return HttpResponse(self.p1)


class TViewOrigins(InjectParamsMixin, ViewWithSelfInResponse):
    p_get: str = param("")
    p_post: str = param("")
    p_post_only: str = param("", origins=["POST"])
    p_put: str = param("")
    p_patch: str = param("")
    p_delete: str = param("")
    p_path: str = param("")
    p_kwargs: str = param("")
    p_view_kwargs: str = param("", origins=["KWARGS"])


class TViewModel(InjectParamsMixin, ViewWithSelfInResponse):
    p1: AppUser = param()


class TViewModelRouteParam(InjectParamsMixin, View):
    user: AppUser = param()

    def dispatch(self, request, *args, **kwargs):
        return HttpResponse(f"{self.user.id} {self.user.username}")


class TViewModelLoaderFn(InjectParamsMixin, ViewWithSelfInResponse):
    p1: AppUser = param(model_loader=lambda v: AppUser(id=v, username=f"created_{v}"))


urlpatterns = [
    path("tviewp1/", TViewP1.as_view(), name="tviewp1"),
    path("tview_origins/<str:p_path>", TViewOrigins.as_view(p_kwargs="ddd"), name="tview-origins"),
    path("tview_model/", TViewModel.as_view(), name="tview-model"),
    path(
        "TViewModelRouteParam/<uuid:user>",
        TViewModelRouteParam.as_view(),
        name="tview-model-route-param",
    ),
    path("tview_model_loader_fn/", TViewModelLoaderFn.as_view(), name="tview-model-loader-fn"),
]


#######################################################################
### common views
#######################################################################


def test_without_type_annotation(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1 = param()  # type: ignore
        p2 = param()  # type: ignore

    view = view_from_response(V, V.as_view()(rf.get("/?p1=123&p2=456")))
    assert view.p1 == "123"
    assert view.p2 == "456"


def test_missing_param_raises_exception(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: str = param()

    with pytest.raises(Exception):
        V.as_view()(rf.get(""))


def test_inject_params_simple_view(rf: RequestFactory):
    rs = response_to_str(TViewP1.as_view()(rf.get("/?p1=abc")))
    assert rs == "abc"


def test_inject_params_values_can_be_passed_with_kwargs(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: str = param("aaa")
        p2: int = param(123)

    view = view_from_response(V, V.as_view(p1="bbb", p2=456)(rf.get("/")))
    assert view.p1 == "bbb"
    assert view.p2 == 456


@pytest.mark.urls("hyperpony.inject_params_tests")
def test_inject_params_request_is_isolated_by_default(rf: RequestFactory):
    rs = response_to_str(invoke_view(rf.post("/?p1=bbb"), "tviewp1"))
    assert rs == "aaa"


def test_inject_params_template_view(rf: RequestFactory):
    class V(InjectParamsMixin, TemplateView):
        template_name = "hyperpony/tests/TemplateResponse.html"
        p1: str = param()

        def get_context_data(self, **kwargs):
            assert self.p1 == "aaa"
            return {"foo": "bar"}

    V.as_view()(rf.get("/?p1=aaa"))


def test_inject_params_json_body(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: str = param("aaa")
        p2: int = param(123)

    data = orjson.dumps({"p1": "bbb", "p2": 456})
    view = view_from_response(
        V, V.as_view()(rf.post("/", data=data, content_type="application/json"))
    )
    assert view.p1 == "bbb"
    assert view.p2 == 456


#######################################################################
### default values
#######################################################################


def test_inject_params_default_values(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: str = param("aaa")
        p2: int = param(123)

    view = view_from_response(V, V.as_view()(rf.get("/")))
    assert view.p1 == "aaa"
    assert view.p2 == 123


def test_inject_params_default_values_are_overridden_by_query_args(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: str = param("aaa")
        p2: int = param(123)

    view = view_from_response(V, V.as_view()(rf.get("/?p1=bbb")))
    assert view.p1 == "bbb"
    assert view.p2 == 123


def test_param_default_defines_target_type(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1 = param(123)

    view = view_from_response(V, V.as_view()(rf.get("/?p1=999")))
    assert view.p1 == 999


#######################################################################
### optional
#######################################################################


def test_optional(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: Optional[str] = param()

    view = view_from_response(V, V.as_view()(rf.get("/")))
    assert view.p1 is None


def test_optional_as_union(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: str | None = param()

    view = view_from_response(V, V.as_view()(rf.get("/")))
    assert view.p1 is None


def test_optional_as_union_with_default_none(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: str | None = param(None)

    view = view_from_response(V, V.as_view()(rf.get("/")))
    assert view.p1 is None


def test_optional_with_type_conversion(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: Optional[int] = param()

    view = view_from_response(V, V.as_view()(rf.get("/?p1=1")))
    assert view.p1 == 1


def test_optional_as_union_with_type_conversion(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: int | None = param()

    view = view_from_response(V, V.as_view()(rf.get("/?p1=1")))
    assert view.p1 == 1


#######################################################################
### origins
#######################################################################


def test_inject_params_origins(rf: RequestFactory):
    as_view = TViewOrigins.as_view(p_kwargs="kwargs")

    # GET/POST
    view = view_from_response(TViewOrigins, as_view(rf.post("?p_get=get", {"p_post": "post"})))
    assert view.p_get == "get"
    assert view.p_post == "post"
    assert view.p_put == ""
    assert view.p_patch == ""
    assert view.p_delete == ""
    assert view.p_kwargs == "kwargs"

    # PUT
    view = view_from_response(
        TViewOrigins,
        as_view(rf.put("?p_get=get", {"p_put": "put"}, "application/json")),
    )
    assert view.p_get == "get"
    assert view.p_post == ""
    assert view.p_put == "put"
    assert view.p_patch == ""
    assert view.p_delete == ""
    assert view.p_kwargs == "kwargs"

    # PATCH
    view = view_from_response(
        TViewOrigins,
        as_view(rf.put("?p_get=get", {"p_patch": "patch"}, "application/json")),
    )
    assert view.p_get == "get"
    assert view.p_post == ""
    assert view.p_put == ""
    assert view.p_patch == "patch"
    assert view.p_delete == ""
    assert view.p_kwargs == "kwargs"


@pytest.mark.urls("hyperpony.inject_params_tests")
def test_inject_params_origins_embedded_request(rf: RequestFactory):
    view = view_from_response(
        TViewOrigins,
        invoke_view(
            rf.post("/?"),
            "tview-origins",
            GET={"p_get": "aaa"},
            POST={"p_post": "bbb"},
            kwargs=dict(p_path="ccc"),
            view_kwargs={"p_view_kwargs": "vvv"},
        ),
    )
    assert view.p_get == "aaa"
    assert view.p_post == "bbb"
    assert view.p_path == "ccc"
    assert view.p_kwargs == "ddd"
    assert view.p_view_kwargs == "vvv"


@pytest.mark.urls("hyperpony.inject_params_tests")
def test_inject_params_origins_specified(rf: RequestFactory):
    as_view = TViewOrigins.as_view()

    # GET/POST
    view = view_from_response(
        TViewOrigins,
        as_view(rf.put("?p_get=get", {"p_post_only": "post_only"}, "application/json")),
    )
    assert view.p_get == "get"
    assert view.p_post_only == ""


#######################################################################
### type conversions
#######################################################################


def test_type_conversion_with_exception(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: int | ValueError = param()

    view = view_from_response(V, V.as_view()(rf.get("/?p1=a")))
    assert isinstance(view.p1, ValueError)


def test_inject_params_type_conversion_int(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: int = param()

    view = view_from_response(V, V.as_view()(rf.get("/?p1=123")))
    assert view.p1 == 123


def test_type_conversion_float(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: float = param()

    view = view_from_response(V, V.as_view()(rf.get("/?p1=1.1")))
    assert isinstance(view.p1, float)
    assert view.p1 == 1.1


def test_type_conversion_bool(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: bool = param()
        p2: bool = param()
        p3: bool = param()

    view = view_from_response(V, V.as_view()(rf.get("/?p1=false&p2=False&p3")))
    assert not view.p1
    assert not view.p2
    assert not view.p3


def test_inject_params_type_conversion_list_annotated(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: list[int] = param()

    view = view_from_response(V, V.as_view()(rf.get("/?p1=1&p1=2")))
    assert isinstance(view.p1, list)
    assert 1 in view.p1
    assert 2 in view.p1


def test_inject_params_type_conversion_list_unannotated(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        p1: list = param()

    view = view_from_response(V, V.as_view()(rf.get("/?p1=1&p1=2")))
    assert isinstance(view.p1, list)
    assert "1" in view.p1
    assert "2" in view.p1


@pytest.mark.django_db
@pytest.mark.urls("hyperpony.inject_params_tests")
def test_inject_params_type_conversion_model(rf: RequestFactory):
    app_user = AppUser.objects.create(username="testuser")

    # pass model's PK
    view = view_from_response(
        TViewModel, invoke_view(rf.get("/"), "tview-model", GET=dict(p1=app_user.id))
    )
    assert view.p1 == app_user

    # pass model instance
    view = view_from_response(
        TViewModel, invoke_view(rf.get("/"), "tview-model", view_kwargs=dict(p1=app_user))
    )
    assert view.p1 == app_user


@pytest.mark.django_db
@pytest.mark.urls("hyperpony.inject_params_tests")
def test_inject_params_type_conversion_model_with_pk_as_route_param(
    rf: RequestFactory, mocker: MockerFixture
):
    app_user = AppUser.objects.create(username="testuser")

    # spy
    spy = mocker.spy(AppUser.objects, "get")

    # pass model's PK to route
    content = embed_view(rf.get("/"), "tview-model-route-param", kwargs=dict(user=app_user.id))
    assert f"{app_user.id} {app_user.username}" in content
    spy.assert_called_once_with(pk=app_user.id)


@pytest.mark.django_db
@pytest.mark.urls("hyperpony.inject_params_tests")
def test_inject_params_type_conversion_model_with_instance_as_route_param(
    rf: RequestFactory, mocker: MockerFixture
):
    app_user = AppUser.objects.create(username="testuser")
    spy = mocker.spy(AppUser.objects, "get")

    # pass model instance to route
    content = embed_view(rf.get("/"), "tview-model-route-param", kwargs=dict(user=app_user))
    assert f"{app_user.id} {app_user.username}" in content
    assert spy.call_count == 0


@pytest.mark.django_db
@pytest.mark.urls("hyperpony.inject_params_tests")
def test_inject_params_type_conversion_model_provide_instance_with_view_kwargs(
    rf: RequestFactory, mocker: MockerFixture
):
    app_user = AppUser.objects.create(username="testuser")
    spy = mocker.spy(AppUser.objects, "get")
    content = embed_view(
        rf.get("/"),
        "tview-model-route-param",
        kwargs=dict(user=uuid4()),
        view_kwargs=dict(user=app_user),
    )
    assert f"{app_user.id} {app_user.username}" in content
    assert spy.call_count == 0


@pytest.mark.django_db
@pytest.mark.urls("hyperpony.inject_params_tests")
def test_inject_params_type_conversion_model_loader_fn(rf: RequestFactory):
    view = view_from_response(
        TViewModelLoaderFn, invoke_view(rf.get("/"), "tview-model-loader-fn", GET=dict(p1=1))
    )
    assert view.p1.id == 1
    assert view.p1.username == "created_1"


@pytest.mark.django_db
def test_type_conversion_model_wrong_id_object_does_not_exist(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        user: AppUser | ObjectDoesNotExist = param()

    view = view_from_response(V, V.as_view()(rf.get(f"/?user={uuid4()}")))
    assert isinstance(view.user, ObjectDoesNotExist)


@pytest.mark.django_db
def test_type_conversion_model_wrong_id_object_does_not_exist_with_pktype(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        user: AppUser | ObjectDoesNotExistWithPk = param()

    u = uuid4()
    view = view_from_response(V, V.as_view()(rf.get(f"/?user={u}")))
    assert isinstance(view.user, ObjectDoesNotExistWithPk)
    assert view.user.pk == str(u)


@pytest.mark.django_db
def test_type_conversion_model_wrong_id_object_does_not_exist_type(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        user: AppUser | AppUser.DoesNotExist = param()  # type: ignore

    view = view_from_response(V, V.as_view()(rf.get(f"/?user={uuid4()}")))
    assert isinstance(view.user, AppUser.DoesNotExist)


@pytest.mark.django_db
def test_type_conversion_model_wrong_id_union_optional(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        user: AppUser | None = param()

    view = view_from_response(V, V.as_view()(rf.get(f"/?user={uuid4()}")))
    assert view.user is None


@pytest.mark.django_db
def test_type_conversion_model_wrong_id_optional(rf: RequestFactory):
    class V(InjectParamsMixin, ViewWithSelfInResponse):
        user: Optional[AppUser] = param()

    view = view_from_response(V, V.as_view()(rf.get(f"/?user={uuid4()}")))
    assert view.user is None


# def test_get_and_post_order(rf: RequestFactory):
#     @inject_params()
#     def viewfn(_request, p1: str = param()):
#         assert p1 == "a"
#
#     viewfn(rf.post("/?p1=a", {"p1": "b"}))
#
#
# def test_function_call_kwarg_overrides_param(rf: RequestFactory):
#     @inject_params()
#     def viewfn(_request, p1: str = param()):
#         assert p1 == "b"
#
#     viewfn(rf.get("/?p1=a"), p1="b")
#
#
#
#
# def test_auto_default_value(rf: RequestFactory):
#     @inject_params()
#     def viewfn(_request, p1: str = param(default="a")):
#         assert p1 == "a"
#
#     untyped_viewfn = typing.cast(Any, viewfn)
#     untyped_viewfn(rf.get("/"))
#
