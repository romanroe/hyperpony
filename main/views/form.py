from django import forms
from django.http import HttpRequest
from django.shortcuts import render
from django.urls import path
from django.views import View
from htpy import Node, form, button, div
from icecream import ic
from widget_tweaks.templatetags.widget_tweaks import add_class

from hyperpony import SingletonPathMixin, HyperponyElementMixin, HyperponyMixin
from hyperpony.form import create_form, is_valid_submit, get_form_data
from hyperpony.htpy import HtpyView


class FormPage(HyperponyMixin, View):
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        return render(
            request,
            "base.html",
            {
                "title": "Hyperpony Form Demo",
                "body": div(".p-3")[FormElement.embed(request)],
            },
        )


class FormPageForm(forms.Form):
    f1 = forms.CharField(min_length=3)
    f2 = forms.CharField(min_length=3)
    names = forms.ChoiceField(choices=[("a", "A"), ("b", "B")], required=False)

    def is_valid(self):
        valid = super().is_valid()

        for field in self:
            if len(field.errors) > 0:
                field.field.widget.attrs["class"] = "invalid"

        return valid


class FormElement(SingletonPathMixin, HyperponyElementMixin, HtpyView):
    form: FormPageForm

    def pre_dispatch(self, request, *args, **kwargs):
        self.form = create_form(request, FormPageForm)

    def patch(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if is_valid_submit(request, self.form):
            print("form.cleaned_data", self.form.cleaned_data)
        return self.get(request, *args, **kwargs)

    def render(self, request: HttpRequest, *args, **kwargs) -> Node:
        data = get_form_data(self.form)
        show_f2 = len(data.get("f1", "")) > 5

        f1_row = div(".row")[
            div(".col-2")[self.form["f1"].label],
            div(".col")[
                add_class(self.form["f1"], "form-control"),
                div[self.form["f1"].errors],
            ],
        ]
        f2_row = div(".row")[
            div(".col-2")[self.form["f2"].label],
            div(".col")[
                add_class(self.form["f2"], "form-control"),
                div[self.form["f2"].errors],
            ],
        ]

        ic(self.form.is_valid())

        return form(hx_post=self.path, hx_swap="merge")[
            div(hx_patch=self.path, hx_trigger="input")[
                f1_row,
                f2_row if show_f2 else None,
                button(".btn.btn-primary", disabled=not show_f2)["Submit"],
            ]
        ]


urlpatterns = [
    path("", FormPage.as_view(), name="form_page"),
    FormElement.create_path(),
]
