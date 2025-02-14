from django.forms import ModelForm
from django.http import HttpRequest
from django.shortcuts import render
from django.urls import path
from django.views import View
from htpy import div, h1, Node, form, button, input
from widget_tweaks.templatetags.widget_tweaks import add_class

from hyperpony import HyperponyElementMixin, SingletonPathMixin, param
from hyperpony.form import create_form, is_valid_submit
from hyperpony.htpy import HtpyView, HtPyActionsMixin, hx_vals
from main.models import Todo


class TodoAppPage(View):
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        return render(
            request,
            "base.html",
            {
                "title": "Hyperpony To-Do App Demo",
                "body": div[
                    div(".container")[
                        h1(".text-center.py-4")["Hyperpony To-Do App Demo"],
                        TodoListElement.embed(request),
                    ],
                ],
            },
        )


class TodoListElement(HyperponyElementMixin, SingletonPathMixin, HtpyView):
    def render(self, request: HttpRequest, *args, **kwargs) -> Node:
        todos_open = Todo.objects.filter(completed=False).order_by("title")
        todos_completed = Todo.objects.filter(completed=True).order_by("title")

        return [
            (TodoElement.embed(request, view_kwargs=dict(todo=t)) for t in todos_open),
            (TodoElement.embed(request, view_kwargs=dict(todo=t)) for t in todos_completed),
        ]


def _todo_loader(_, pk):
    return Todo() if pk == "new" else Todo.objects.get(pk=pk)


class TodoForm(ModelForm):
    class Meta:
        model = Todo
        fields = ["completed", "title"]


class TodoElement(HyperponyElementMixin, SingletonPathMixin, HtPyActionsMixin, HtpyView):
    todo: Todo = param(model_loader=_todo_loader)
    full_view = param(False)
    form: TodoForm

    def pre_dispatch(self, request: HttpRequest, *args, **kwargs):
        self.element_id = f"todo{self.todo.pk}"
        if self.full_view:
            self.enable_preserve_on_outer_swap()

        self.form = create_form(request, TodoForm, instance=self.todo)

    def action_toggle(self, value: bool):
        self.todo.completed = not self.todo.completed
        self.todo.save()
        TodoListElement.swap_oob(self.request)

    def post(self, request, *args, **kwargs):
        if is_valid_submit(request, self.form):
            TodoListElement.swap_oob(request)
            self.form.save()

        return self.get(request, *args, **kwargs)

    def render(self, request: HttpRequest, *args, **kwargs) -> Node:
        if not self.full_view:
            return div(".my-3.d-flex.align-items-center")[
                input(
                    ".form-check-input.me-2",
                    self.create_action("toggle", value=(not self.todo.completed)),
                    type="checkbox",
                    checked=self.todo.completed,
                    hx_trigger="input",
                ),
                div(
                    hx_vals(full_view=True),
                    hx_get=self.path,
                    class_={
                        "text-secondary fst-italic text-decoration-line-through": self.todo.completed
                    },
                )[self.todo.title],
            ]

        return div(".p-3.border.rounded.shadow")[
            form(hx_post=self.path)[
                div(".d-flex.align-items-center")[
                    add_class(self.form["completed"], "form-check-input me-2"),
                    add_class(self.form["title"], "form-control"),
                ],
                div(".d-flex.align-items-center.mt-3")[
                    div[button(".btn.btn-primary.me-3")["Save"]],
                    div[button(".btn.btn-secondary", type="button", hx_get=self.path)["Discard"]],
                ],
            ]
        ]


urlpatterns = [
    path("", TodoAppPage.as_view(), name="todo_page"),
    TodoListElement.create_path(),
    TodoElement.create_path("<todo>"),
]
