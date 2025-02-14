import uuid
from typing import cast

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import path
from django.views import View

from hyperpony import ViewUtilsMixin, SingletonPathMixin, param, InjectParamsMixin
from hyperpony.testutils import view_from_response
from hyperpony.utils import response_to_str, text_response_to_str_or_none
from hyperpony.views import invoke_view, is_embedded_request, EmbeddedRequest, is_get
from main.models import AppUser


# #######################################################################
# ### CBVs
# #######################################################################


class TView(ViewUtilsMixin, View):
    def dispatch(self, request, *args, **kwargs):
        res = HttpResponse("")
        res.view = self
        return res


class TViewKwargs(TView):
    foo: str
    bar: int


class TViewSingleton(SingletonPathMixin, TView):
    pass


class TViewSingletonPathStart(TViewSingleton):
    pass


class TViewSingletonPathEnd(TViewSingleton):
    pass


class TViewSingletonPathEndParam(TViewSingleton):
    pass


class TViewSingletonPathStartPathEnd(TViewSingleton):
    pass


class TViewSingletonWithCustomName(TViewSingleton):
    pass


class TViewSingletonLookup(TViewSingleton):
    pass


class TViewModelRouteParam(InjectParamsMixin, TViewSingleton):
    user: AppUser = param()


urlpatterns = [
    path("view1/", TView.as_view(), name="view1"),
    path("viewkwargs/", TViewKwargs.as_view(), name="view_kwargs"),
    path("view1/<param1>", TView.as_view(), name="view-param1"),
    TViewSingleton.create_path(),
    TViewSingletonPathStart.create_path(full_path="full_path"),
    TViewSingletonPathEnd.create_path("path_suffix"),
    TViewSingletonPathEndParam.create_path("<param1>"),
    TViewSingletonPathStartPathEnd.create_path(full_path="full_path/<param1>"),
    TViewSingletonWithCustomName.create_path(name="custom_name"),
    path("tview-singelton-lookup", TViewSingletonLookup.as_view()),
    TViewModelRouteParam.create_path("<user>"),
]


# #######################################################################
# ### text_response_to_str
# #######################################################################


def test_text_response_to_str_or_none():
    assert response_to_str(HttpResponse("response")) == "response"


def test_text_response_to_str_or_none_content_type_json():
    res = HttpResponse("{}", content_type="application/json")
    assert text_response_to_str_or_none(res) is None


# #######################################################################
# ### create_embedded_request
# #######################################################################


def test_create_embedded_request(rf: RequestFactory):
    req = rf.get("/")
    req.user = AppUser()
    ereq = EmbeddedRequest.create(req)
    assert ereq.user is not None
    assert ereq.user == req.user
    assert ereq.scheme == req.scheme
    assert ereq.method == "GET"
    assert ereq.path == ""
    assert ereq.META == req.META
    assert ereq.GET == req.GET
    assert ereq.POST == req.POST
    assert ereq.COOKIES == req.COOKIES
    assert ereq.FILES == req.FILES
    assert ereq.body == req.body


# #######################################################################
# ### embedded request
# #######################################################################


@pytest.mark.urls("hyperpony.views_tests")
def test_is_embedded_request(rf: RequestFactory):
    view = view_from_response(TView, invoke_view(rf.get("/"), "view1"))
    assert is_embedded_request(view.request)


@pytest.mark.urls("hyperpony.views_tests")
def test_viewutil_is_embedded_request(rf: RequestFactory):
    view = view_from_response(TView, invoke_view(rf.post("/"), "view1"))
    assert view.is_embedded_view()


@pytest.mark.urls("hyperpony.views_tests")
def test_embedded_view_request_is_always_get(rf: RequestFactory):
    view = view_from_response(TView, invoke_view(rf.post("/"), "view1"))
    assert is_get(view.request)


# #######################################################################
# ### SingletonPathMixin
# #######################################################################


@pytest.mark.urls("hyperpony.views_tests")
def test_singleton_path_mixin(rf: RequestFactory):
    # get_path_name
    assert (
        TViewSingletonPathStartPathEnd.get_viewname()
        == "hyperpony-views_tests-TViewSingletonPathStartPathEnd"
    )

    # invoke
    data = view_from_response(
        TViewSingletonPathStartPathEnd,
        TViewSingletonPathStartPathEnd.invoke(rf.get("/"), args=["foo1"]),
    )
    assert data.kwargs == {"param1": "foo1"}


@pytest.mark.urls("hyperpony.views_tests")
def test_singleton_path_mixin_lookup(rf: RequestFactory):
    data = view_from_response(TViewSingletonLookup, TViewSingletonLookup.invoke(rf.get("/")))
    assert isinstance(data, TViewSingletonLookup)


@pytest.mark.django_db
@pytest.mark.urls("hyperpony.views_tests")
def test_singleton_path_mixin_model_missing_route_param_filled_from_view_kwargs(rf: RequestFactory):
    au = AppUser.objects.create(username="testuser")
    # do not pass PK for route creation!
    view = view_from_response(
        TViewModelRouteParam,
        TViewModelRouteParam.invoke(
            rf.get("/"),
            view_kwargs=dict(user=au),
        ),
    )
    assert view.user is au


# #######################################################################
# ### ViewUtils
# #######################################################################


@pytest.mark.urls("hyperpony.views_tests")
def test_viewutils_url(rf: RequestFactory):
    assert view_from_response(ViewUtilsMixin, invoke_view(rf.post("/"), "view1")).path == "/view1/"

    res = invoke_view(rf.get("/"), cast(str, TViewSingleton.get_viewname()))
    assert view_from_response(ViewUtilsMixin, res).path == "/TViewSingleton"

    res = invoke_view(rf.get("/"), cast(str, TViewSingletonPathStart.get_viewname()))
    assert view_from_response(ViewUtilsMixin, res).path == "/full_path"

    res = invoke_view(rf.get("/"), cast(str, TViewSingletonPathEnd.get_viewname()))
    assert view_from_response(ViewUtilsMixin, res).path == "/TViewSingletonPathEnd/path_suffix"

    path_name = cast(str, TViewSingletonPathEndParam.get_viewname())
    res = invoke_view(rf.get("/"), path_name, kwargs=dict(param1="foo"))
    assert view_from_response(ViewUtilsMixin, res).path == "/TViewSingletonPathEndParam/foo"

    path_name = cast(str, TViewSingletonPathStartPathEnd.get_viewname())
    res = invoke_view(rf.get("/"), path_name, kwargs=dict(param1="foo"))
    assert view_from_response(ViewUtilsMixin, res).path == "/full_path/foo"

    res = invoke_view(rf.get("/"), "custom_name")
    assert view_from_response(ViewUtilsMixin, res).path == "/TViewSingletonWithCustomName"


@pytest.mark.urls("hyperpony.views_tests")
@pytest.mark.django_db
def test_viewutils_params(rf: RequestFactory):
    r = rf.get("/")
    view = view_from_response(TView, invoke_view(r, "view-param1", kwargs=dict(param1="foo")))
    assert view.kwargs == {"param1": "foo"}
    view = view_from_response(TView, invoke_view(r, "view-param1", args=["foo"]))
    assert view.kwargs == {"param1": "foo"}
    view = view_from_response(TView, invoke_view(r, "view-param1", kwargs=dict(param1=1)))
    assert view.kwargs == {"param1": "1"}

    u = uuid.uuid4()
    view = view_from_response(TView, invoke_view(r, "view-param1", kwargs=dict(param1=u)))
    assert view.kwargs == {"param1": str(u)}

    app_user = AppUser.objects.create(username="testuser")
    view = view_from_response(TView, invoke_view(r, "view-param1", kwargs=dict(param1=app_user)))
    assert view.kwargs == {"param1": str(app_user.id)}
