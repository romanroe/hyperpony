from django.urls import path
from django.views.generic import TemplateView

from hyperpony.inject_params import InjectParamsView, param


class ParamsPage(InjectParamsView, TemplateView):
    template_name = "playground/params/params_page.html"
    value: str = param("undefined")

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **{
                "url": self.request.path,
                "value": self.value,
            }
        )

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


urlpatterns = [
    path("", ParamsPage.as_view(), name="playground-params-page"),
]
