from django import forms
from django.http import HttpResponse
from django.test import RequestFactory

from hyperpony.form import create_form, get_form_data, is_valid_submit


class TForm(forms.Form):
    p1 = forms.CharField(required=False)
    p2 = forms.IntegerField()
    p3 = forms.MultipleChoiceField(
        required=False,
        choices=[
            ("a", "choice1"),
            ("b", "choice2"),
            ("c", "choice3"),
            ("d", "choice4"),
        ],
    )


def test_get_form(rf: RequestFactory):
    form = create_form(rf.get("/"), TForm)
    res = HttpResponse(form)
    assert b"""<input type="text" name="p1" id="id_p1">""" in res.content
    assert b"""<input type="number" name="p2" required id="id_p2">""" in res.content
    assert b"""<select name="p3" id="id_p3" multiple>""" in res.content
    assert b"""<option value="a">choice1</option>""" in res.content
    assert b"""<option value="b">choice2</option>""" in res.content
    assert b"""<option value="c">choice3</option>""" in res.content
    assert b"""<option value="d">choice4</option>""" in res.content


def test_get_data(rf: RequestFactory):
    form = create_form(rf.get("/"), TForm)
    data = get_form_data(form)
    assert data.get("p1", None) is None


def test_get_data_iter_len(rf: RequestFactory):
    form = create_form(rf.get("/"), TForm, initial={"p1": "aaa", "p2": "123", "p3": ["a", "b"]})
    data = get_form_data(form)
    assert list(iter(data)) == ["p1", "p2", "p3"]
    assert len(data) == 3


def test_get_with_initial_form(rf: RequestFactory):
    form = create_form(rf.get("/"), TForm, initial={"p1": "aaa", "p2": "123", "p3": ["a", "b"]})
    assert form.initial["p1"] == "aaa"
    assert form.initial["p2"] == "123"
    assert form.initial["p3"] == ["a", "b"]


def test_get_with_initial_data(rf: RequestFactory):
    form = create_form(rf.get("/"), TForm, initial={"p1": "aaa", "p2": "123", "p3": ["a", "b"]})
    data = get_form_data(form)
    assert data["p1"] == "aaa"
    assert data["p2"] == 123
    assert data["p3"] == ["a", "b"]


def test_patch_form(rf: RequestFactory):
    form = create_form(
        rf.patch(
            "/view", "p1=aaa&p2=123&p3=a&p3=b", content_type="application/x-www-form-urlencoded"
        ),
        TForm,
    )
    assert form.initial["p1"] == "aaa"
    assert form.initial["p2"] == "123"
    assert form.initial["p3"] == ["a", "b"]


def test_patch_form_with_additional_parameter_in_request(rf: RequestFactory):
    form = create_form(
        rf.patch(
            "/view",
            "p1=aaa&p2=123&p3=a&p3=b&extra=foo",
            content_type="application/x-www-form-urlencoded",
        ),
        TForm,
    )
    assert form.initial["p1"] == "aaa"
    assert form.initial["p2"] == "123"
    assert form.initial["p3"] == ["a", "b"]


def test_patch_data(rf: RequestFactory):
    form = create_form(
        rf.patch(
            "/view",
            "p1=aaa&p2=123&p3=a&p3=b",
            content_type="application/x-www-form-urlencoded",
        ),
        TForm,
    )
    data = get_form_data(form)
    assert data["p1"] == "aaa"
    assert data["p2"] == 123
    assert data["p3"] == ["a", "b"]


def test_patch_with_initial_form(rf: RequestFactory):
    form = create_form(
        rf.patch(
            "/view",
            "p2=456&p3=c&p3=d",
            content_type="application/x-www-form-urlencoded",
        ),
        TForm,
        initial={"p1": "aaa", "p2": "123", "p3": ["a", "b"]},
    )
    assert form.initial["p1"] == "aaa"
    assert form.initial["p2"] == "456"
    assert form.initial["p3"] == ["c", "d"]


def test_patch_with_initial_data(rf: RequestFactory):
    form = create_form(
        rf.patch(
            "/view",
            "p2=456&p3=c&p3=d",
            content_type="application/x-www-form-urlencoded",
        ),
        TForm,
        initial={"p1": "aaa", "p2": "123", "p3": ["a", "b"]},
    )
    data = get_form_data(form)
    assert data["p1"] == "aaa"
    assert data["p2"] == 456
    assert data["p3"] == ["c", "d"]


def test_post_form(rf: RequestFactory):
    request = rf.post("/view", {"p1": "aaa", "p2": 123, "p3": ["a", "b"]})
    form = create_form(request, TForm)
    assert is_valid_submit(request, form)
    assert form.cleaned_data["p1"] == "aaa"
    assert form.cleaned_data["p2"] == 123
    assert form.cleaned_data["p3"] == ["a", "b"]


def test_post_data(rf: RequestFactory):
    request = rf.post("/view", {"p1": "aaa", "p2": 123, "p3": ["a", "b"]})
    form = create_form(request, TForm)
    data = get_form_data(form)
    assert is_valid_submit(request, form)
    assert data["p1"] == "aaa"
    assert data["p2"] == 123
    assert data["p3"] == ["a", "b"]


def test_post_data_fields_are_calculated_lazy(rf: RequestFactory):
    request = rf.post("/view", {"p1": "aaa", "p3": ["a", "b"]})
    form = create_form(request, TForm)
    form.fields["p3"].choices = []
    data = get_form_data(form)
    assert data["p1"] == "aaa"
    assert "p3" not in data
    form.fields["p3"].choices = [("a", "choice1"), ("b", "choice2")]
    form.full_clean()
    assert data["p3"] == ["a", "b"]


def test_post_with_initial_form(rf: RequestFactory):
    request = rf.post("/view", {"p2": 123, "p3": ["a", "b"]})
    form = create_form(request, TForm, initial={"p1": "aaa", "p2": "123", "p3": ["a", "b"]})
    assert is_valid_submit(request, form)
    assert form.cleaned_data["p1"] == ""
    assert form.cleaned_data["p2"] == 123
    assert form.cleaned_data["p3"] == ["a", "b"]


def test_post_with_initial_data(rf: RequestFactory):
    request = rf.post("/view", {"p2": 123, "p3": ["a", "b"]})
    form = create_form(request, TForm, initial={"p1": "aaa", "p2": "123", "p3": ["a", "b"]})
    data = get_form_data(form)
    assert is_valid_submit(request, form)
    assert data["p1"] == ""
    assert data["p2"] == 123
    assert data["p3"] == ["a", "b"]


def test_post_data_iter_len(rf: RequestFactory):
    form = create_form(rf.post("/view", {"p2": 123, "p3": ["a", "b"]}), TForm)
    data = get_form_data(form)
    assert list(iter(data)) == ["p1", "p2", "p3"]
    assert len(data) == 3
