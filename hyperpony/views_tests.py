import json
from typing import cast

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import path, re_path
from django.views import View

from hyperpony import ViewUtilsMixin, SingletonPathMixin
from hyperpony.testutils import view_from_response
from hyperpony.utils import response_to_str, text_response_to_str_or_none
from hyperpony.views import invoke_view, is_embedded_request, EmbeddedRequest
from main.models import AppUser


# #######################################################################
# ### CBVs
# #######################################################################


class TView(ViewUtilsMixin, View):
    def dispatch(self, request, *args, **kwargs):
        res = HttpResponse(json.dumps({"args": self.args, "kwargs": self.kwargs}))
        res.view = self
        return res


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


urlpatterns = [
    path("view1/", TView.as_view(), name="view1"),
    re_path("view1/<param1>", TView.as_view(), name="view1_param"),
    TViewSingleton.create_path(),
    TViewSingletonPathStart.create_path(full_path="full_path"),
    TViewSingletonPathEnd.create_path("path_suffix"),
    TViewSingletonPathEndParam.create_path("<param1>"),
    TViewSingletonPathStartPathEnd.create_path(full_path="full_path/<param1>"),
    TViewSingletonWithCustomName.create_path(name="custom_name"),
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
    assert view.is_get()


def test_viewutils_http_methods(rf: RequestFactory):
    assert view_from_response(TView, TView.as_view()(rf.get("/"))).is_get()
    assert view_from_response(TView, TView.as_view()(rf.post("/"))).is_post()
    assert view_from_response(TView, TView.as_view()(rf.put("/"))).is_put()
    assert view_from_response(TView, TView.as_view()(rf.patch("/"))).is_patch()
    assert view_from_response(TView, TView.as_view()(rf.delete("/"))).is_delete()


# #######################################################################
# ### SingletonPathMixin
# #######################################################################


@pytest.mark.urls("hyperpony.views_tests")
def test_singleton_path_mixin(rf: RequestFactory):
    # get_path_name
    assert (
        TViewSingletonPathStartPathEnd.get_path_name()
        == "hyperpony-views_tests-TViewSingletonPathStartPathEnd"
    )

    # invoke
    data = view_from_response(
        TViewSingletonPathStartPathEnd,
        TViewSingletonPathStartPathEnd.invoke(rf.get("/"), None, None, "foo1"),
    )
    assert data.kwargs == {"param1": "foo1"}

    # embed
    content = TViewSingletonPathStartPathEnd.embed(rf.get("/"), None, None, "foo2")
    data = json.loads(content)
    assert data["kwargs"] == {"param1": "foo2"}


# #######################################################################
# ### ViewUtils
# #######################################################################


@pytest.mark.urls("hyperpony.views_tests")
def test_viewutils_url(rf: RequestFactory):
    assert view_from_response(ViewUtilsMixin, invoke_view(rf.post("/"), "view1")).url() == "/view1/"

    res = invoke_view(rf.get("/"), cast(str, TViewSingleton.get_path_name()))
    assert view_from_response(ViewUtilsMixin, res).url() == "/TViewSingleton"

    res = invoke_view(rf.get("/"), cast(str, TViewSingletonPathStart.get_path_name()))
    assert view_from_response(ViewUtilsMixin, res).url() == "/full_path"

    res = invoke_view(rf.get("/"), cast(str, TViewSingletonPathEnd.get_path_name()))
    assert view_from_response(ViewUtilsMixin, res).url() == "/TViewSingletonPathEnd/path_suffix"

    pn = cast(str, TViewSingletonPathEndParam.get_path_name())
    res = invoke_view(rf.get("/"), pn, kwargs={"param1": "foo"})
    assert view_from_response(ViewUtilsMixin, res).url() == "/TViewSingletonPathEndParam/foo"

    pn = cast(str, TViewSingletonPathStartPathEnd.get_path_name())
    res = invoke_view(rf.get("/"), pn, kwargs={"param1": "foo"})
    assert view_from_response(ViewUtilsMixin, res).url() == "/full_path/foo"

    res = invoke_view(rf.get("/"), "custom_name")
    assert view_from_response(ViewUtilsMixin, res).url() == "/TViewSingletonWithCustomName"
