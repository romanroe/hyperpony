# import lxml.html
# from django.http import HttpResponseBase, HttpRequest
#
# from hyperpony.utils import is_response_processable, response_to_str
#
#
# class ActionMixin:
#     def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
#         response = super().dispatch(request, *args, **kwargs)  # type: ignore
#
#         if is_response_processable(response, "text/html"):
#             oob_content = response_to_str(response).strip()
#             parsed: lxml.html.Element = lxml.html.fromstring(oob_content)
#             # ic(parsed)
#
#             # x = parsed.xpath("/*/@hp-action-click")
#             x = parsed.xpath("//*[@hp-action-click]")
#             # ic(x)
#
#         return response
