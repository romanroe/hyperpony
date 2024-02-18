import pytest
from django.test import RequestFactory
from django.http import HttpResponse

from hyperpony import element, view
from hyperpony.response_handler import add_response_handler
from hyperpony.testutils import call_with_middleware


def test_process_response_can_only_be_called_from_hyperpony_views(rf: RequestFactory):
    def root(request):
        add_response_handler(request, lambda response: response)
        return HttpResponse("")

    with pytest.raises(
        Exception,
        match="This function can only be called from within a Hyperpony view.",
    ):
        root(rf.get("/"))


def test_process_response_hook(rf: RequestFactory):
    state = []

    @view()
    def root(request):
        add_response_handler(request, lambda response: state.append(1))
        return HttpResponse("")

    call_with_middleware(rf, root)
    assert state[0] == 1


def test_process_response_hook_with_nested_elements(rf: RequestFactory):
    state = []

    @view()
    def root(request):
        add_response_handler(request, lambda response: state.append(1))
        return HttpResponse(f"{child(request)}")

    @element()
    def child(request):
        add_response_handler(request, lambda response: state.append(2))
        return HttpResponse("child")

    call_with_middleware(rf, root)
    assert len(state) == 2
    assert state[0] == 1
    assert state[1] == 2
