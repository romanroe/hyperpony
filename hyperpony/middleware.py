from django.http import HttpResponse

from hyperpony.htmx import enrich_response_with_oob_contents
from hyperpony.response_handler import process_response


class HyperponyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request) -> HttpResponse:
        response: HttpResponse = self.get_response(request)
        response = process_response(request, response)
        enrich_response_with_oob_contents(response)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        pass
