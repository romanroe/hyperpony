from functools import cached_property
from typing import Any, cast, Mapping, TypeVar

from django.forms import BaseForm, BoundField, Field
from django.http import HttpRequest, QueryDict

from hyperpony import is_patch, is_post, is_put


T_FORM = TypeVar("T_FORM", bound=BaseForm)


def create_form(
    request: HttpRequest, form_class: type[T_FORM], *, initial=None, **kwargs
) -> T_FORM:
    """
    Instantiate a form of type `form_class` and returns it.

    If the request method is GET, the form will be created with the `initial` values.

    If the request method is PATCH, the `initial` values will be updated with
    request's body.

    If the request method is POST or PUT, the form will be bound with the POST data.
    """
    if is_post(request) or is_put(request):
        form = form_class(data=request.POST, files=request.FILES, **kwargs)
    elif is_patch(request):
        initial = {} if initial is None else initial
        qd = QueryDict(request.body, encoding=request.encoding, mutable=True)
        for key in qd.keys():
            if key in form_class.base_fields:
                f: Field = form_class.base_fields[key]
                value = f.widget.value_from_datadict(qd, request.FILES, key)
                initial[key] = value

        form = form_class(initial=initial, **kwargs)
    else:
        form = form_class(initial=initial, **kwargs)

    return cast(T_FORM, form)


class _FormStateProxy(Mapping[str, Any]):
    __form: BaseForm

    def __init__(self, form: BaseForm):
        self.__form = form

    @property
    def __data(self) -> Mapping[str, Any]:
        if not self.__form.is_bound:
            return self.__initial_normalized

        self.__form.is_valid()
        return self.__form.cleaned_data

    @cached_property
    def __initial_normalized(self) -> Mapping[str, Any]:
        data = dict()
        for k in self.__form.initial.keys():
            bf: BoundField = self.__form[k]
            f: Field = bf.field
            data[k] = f.to_python(bf.value())
        return data

    def __getitem__(self, name: str) -> Any:
        return self.__data[name]

    def __iter__(self):
        return self.__data.__iter__()

    def __len__(self):
        return self.__data.__len__()

    def __str__(self):
        return str(self.__data)


def get_form_data(form: BaseForm) -> Mapping[str, Any]:
    """
    Returns a state proxy for the form instance. The state proxy can be used to
    read from the form's underlying data structure.

    If the form is bound, `is_valid()` will be called on the form and the
    state proxy will reflect the form's `cleaned_data`.

    If the form is not bound, the state proxy will reflect the form's `initial` values,
    passed through the corresponding field's `to_python()` method. This means that,
    depending on the form's fields, the returned data may not be exactly the same as
    the initial data.
    """
    return _FormStateProxy(form)


def is_valid_submit(request: HttpRequest, form: BaseForm) -> bool:
    return is_post(request) and form.is_valid()
