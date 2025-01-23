from django.http import HttpResponse
from django.test import RequestFactory
from django.views import View

from hyperpony import ViewUtilsMixin
from hyperpony.response_handler import process_response
from hyperpony.utils import response_to_str


def test_viewutils_add_swap_oob(rf: RequestFactory):
    class ViewWithOOBContent(ViewUtilsMixin, View):
        def dispatch(self, request, *args, **kwargs):
            self.add_swap_oob(HttpResponse("<div id='oob'>OOB</div>"))
            return HttpResponse("main")

    req = rf.get("/")
    res = ViewWithOOBContent.as_view()(req)
    res = process_response(req, res)
    res_str = response_to_str(res)
    assert res_str == 'main<div id="oob" hx-swap-oob="outerHTML:#oob">OOB</div>'
