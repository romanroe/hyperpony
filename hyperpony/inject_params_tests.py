import typing
from typing import Any, Optional
from urllib.parse import urlencode
from uuid import uuid4

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.test import RequestFactory
from django.views import View
from django.views.generic import TemplateView

from hyperpony import inject_params, param, NestedView
from hyperpony.inject_params import InjectParamsView, ObjectDoesNotExistWithPk
from main.models import AppUser

#######################################################################
### classed-based views
#######################################################################


def test_cbv(rf: RequestFactory):
    class V(InjectParamsView):
        p1: str = param()

        def get(self, request):
            assert self.p1 == "aaa"
            return HttpResponse()

    V.as_view()(rf.get("/?p1=aaa"))


def test_cbv_template_view(rf: RequestFactory):
    class V(InjectParamsView, TemplateView):
        template_name = "hyperpony/tests/TemplateResponse.html"
        p1: str = param()

        def get_context_data(self, **kwargs):
            assert self.p1 == "aaa"
            return {"foo": "bar"}

    V.as_view()(rf.get("/?p1=aaa"))


def test_cbv_type_conversion_list_annotated(rf: RequestFactory):
    class V(InjectParamsView, View):
        p1: list[int] = param()

        def get(self, request):
            assert isinstance(self.p1, list)
            assert 1 in self.p1
            assert 2 in self.p1
            return HttpResponse()

    V.as_view()(rf.get("/?p1=1&p1=2"))


def test_cbv_params_are_optional_when_passed_as_constructor_param(rf: RequestFactory):
    class V(NestedView):
        p1: str = param()

        def dispatch(self, request, *args, **kwargs):
            return HttpResponse(self.p1)

    response = V(p1="aaa").as_str(rf.get("/"))
    response_str = str(response)
    assert response_str == "aaa"


def test_cbv_constructor_params_can_not_be_overridden_by_query_args(rf: RequestFactory):
    class V(NestedView):
        p1: str = param()

        def dispatch(self, request, *args, **kwargs):
            return HttpResponse(self.p1)

    response = V(p1="aaa").as_str(rf.get("/?p1=bbb"))
    response_str = str(response)
    assert response_str == "aaa"


def test_cbv_params_can_be_passed_with_as_str_method(rf: RequestFactory):
    class V(InjectParamsView, NestedView):
        p1: str = param()

        def dispatch(self, request, *args, **kwargs):
            return HttpResponse(self.p1)

    response = V().as_str(rf.get("/?p1=bbb"), p1="aaa")
    response_str = str(response)
    assert response_str == "aaa"


def test_cbv_request_is_isolated_by_default(rf: RequestFactory):
    class V(InjectParamsView, NestedView):
        p1: str = param("aaa")

        def dispatch(self, request, *args, **kwargs):
            return HttpResponse(self.p1)

    response = V().as_str(rf.post("/?p1=bbb"))
    response_str = str(response)
    assert response_str == "aaa"


def test_cbv_unisolated_request_class_setting(rf: RequestFactory):
    class V(InjectParamsView, NestedView):
        isolate_request = False
        p1: str = param("aaa")

        def dispatch(self, request, *args, **kwargs):
            return HttpResponse(self.p1)

    response = V().as_str(rf.post("/?p1=bbb"))
    response_str = str(response)
    assert response_str == "bbb"


def test_cbv_unisolated_request_method_setting(rf: RequestFactory):
    class V(InjectParamsView, NestedView):
        isolate_request = False
        p1: str = param("parent")

        def dispatch(self, request, *args, **kwargs):
            return HttpResponse(self.p1)

    response = V().as_str(rf.post("/?p1=aaa"))
    response_str = str(response)
    assert response_str == "aaa"


def test_cbv_default_values_are_set_in_instance(rf: RequestFactory):
    class V(InjectParamsView, NestedView):
        p1: str = param("aaa")
        p2: int = param(123)

    view = V()
    assert view.p1 == "aaa"
    assert view.p2 == 123


#######################################################################
### function-based views
#######################################################################


def test_without_type_annotation(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1=param(), p2=param()):
        assert p1 == "aaa"
        assert p2 == "bbb"
        return HttpResponse("")

    result = viewfn(rf.get("/?p1=aaa&p2=bbb"))
    assert result.status_code == 200


def test_param_default_defines_target_type(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1=param(default=123)):
        assert p1 == 999
        return HttpResponse("")

    result = viewfn(rf.get("/?p1=999"))
    assert result.status_code == 200


def test_missing_param_raises_exception(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1=param()):
        assert p1 == 1

    def test():
        viewfn(rf.get("/"))

    with pytest.raises(Exception):
        test()


def test_optional(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: Optional[str] = param()):
        assert p1 is None

    viewfn(rf.get("/"))


def test_optional_as_union(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: str | None = param()):
        assert p1 is None

    viewfn(rf.get("/"))


def test_optional_as_union_with_default_none(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: str | None = param(None)):
        assert p1 is None

    viewfn(rf.get("/"))


def test_optional_with_type_conversion(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: Optional[int] = param()):
        assert p1 == 1

    viewfn(rf.get("/?p1=1"))


def test_type_conversion_int(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: int = param()):
        assert p1 == 1

    viewfn(rf.get("/?p1=1"))


def test_type_conversion_with_exception(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: int | ValueError = param()):
        assert isinstance(p1, ValueError)

    viewfn(rf.get("/?p1=a"))


def test_type_conversion_float(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: float = param()):
        assert p1 == 1.1
        # assert type(p1) == float
        assert isinstance(p1, float)

    viewfn(rf.get("/?p1=1.1"))


def test_type_conversion_bool(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: bool = param(), p2: bool = param(), p3: bool = param()):
        assert not p1
        assert not p2
        assert not p3

    viewfn(rf.get("/?p1=false&p2=False&p3"))


def test_type_conversion_list_unannotated(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: list = param()):
        assert isinstance(p1, list)
        assert "a" in p1
        assert "b" in p1

    viewfn(rf.get("/?p1=a&p1=b"))


def test_type_conversion_list_annotated(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: list[int] = param()):
        assert isinstance(p1, list)
        assert 1 in p1
        assert 2 in p1

    viewfn(rf.get("/?p1=1&p1=2"))


@pytest.mark.django_db
def test_type_conversion_model(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: AppUser = param()):
        assert user is not None

    app_user = AppUser.objects.create(username="testuser")
    viewfn(rf.get(f"/?user={app_user.id}"))


@pytest.mark.django_db
def test_type_conversion_model_wrong_id_object_does_not_exist_type(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: AppUser | ObjectDoesNotExist = param()):
        assert isinstance(user, ObjectDoesNotExist)

    viewfn(rf.get(f"/?user={uuid4()}"))


@pytest.mark.django_db
def test_type_conversion_model_wrong_id_object_does_not_exist__with_pktype(
    rf: RequestFactory,
):
    wrong_id = uuid4()

    @inject_params()
    def viewfn(_request, user: AppUser | ObjectDoesNotExistWithPk = param()):
        assert isinstance(user, ObjectDoesNotExistWithPk)
        assert user.pk == str(wrong_id)

    viewfn(rf.get(f"/?user={wrong_id}"))


@pytest.mark.django_db
def test_type_conversion_model_wrong_id_model_does_not_exist_type(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: AppUser | AppUser.DoesNotExist = param()):  # type: ignore
        assert isinstance(user, AppUser.DoesNotExist)

    viewfn(rf.get(f"/?user={uuid4()}"))


@pytest.mark.django_db
def test_type_conversion_model_with_optional(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: Optional[AppUser] = param()):
        assert user is not None

    app_user = AppUser.objects.create(username="testuser")
    viewfn(rf.get(f"/?user={app_user.id}"))


@pytest.mark.django_db
def test_type_conversion_model_with_optional_value_is_none(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: Optional[AppUser] = param()):
        assert user is None

    viewfn(rf.get("/"))


@pytest.mark.django_db
def test_type_conversion_model_with_union_none(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: AppUser | None = param()):
        assert user is not None

    app_user = AppUser.objects.create(username="testuser")
    viewfn(rf.get(f"/?user={app_user.id}"))


@pytest.mark.django_db
def test_type_conversion_model_with_union_none_value_is_none(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: AppUser | None = param()):
        assert user is None

    viewfn(rf.get("/"))


def test_post(rf: RequestFactory):
    @inject_params()
    def viewfn(
        _request, p1: str = param(methods=["POST"]), p2: str = param(methods=["POST"])
    ):
        assert p1 == "a"
        assert p2 == "b"

    viewfn(rf.post("/", {"p1": "a", "p2": "b"}))


def test_patch(rf: RequestFactory):
    @inject_params()
    def viewfn(
        _request,
        p1: str = param(methods=["PATCH"]),
        p2: str = param(methods=["PATCH"]),
    ):
        assert p1 == "aaa"
        assert p2 == "bbb"

    viewfn(
        rf.patch(
            "/",
            urlencode({"p1": "aaa", "p2": "bbb"}),
            content_type="application/x-www-form-urlencoded",
        )
    )


def test_get_and_post_order(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: str = param()):
        assert p1 == "a"

    viewfn(rf.post("/?p1=a", {"p1": "b"}))


def test_function_call_arg_overrides_param(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: str = param()):
        assert p1 == "b"

    viewfn(rf.get("/?p1=a"), "b")


def test_function_call_kwarg_overrides_param(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: str = param()):
        assert p1 == "b"

    viewfn(rf.get("/?p1=a"), p1="b")


def test_param_view_stack(rf: RequestFactory):
    @inject_params()
    def view1(request, p1: str = param()):
        assert p1 == "a"
        return view2(request)

    @inject_params()
    def view2(request, p1: str = param(default="b")):
        assert p1 == "b"

    view1(rf.get("/?p1=a"))


def test_auto_default_value(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: str = param(default="a")):
        assert p1 == "a"

    untyped_viewfn = typing.cast(Any, viewfn)
    untyped_viewfn(rf.get("/"))
