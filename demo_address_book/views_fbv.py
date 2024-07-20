from uuid import UUID

from django import forms
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import render
from django.urls import path, reverse
from icecream import ic

from demo_address_book.models import Person
from hyperpony import element, param, view
from hyperpony.form import create_form, is_valid_submit


@view()
def address_book_page(request: HttpRequest, person_id: UUID | None = param()):
    return render(
        request,
        "demo_address_book_fbv/address_book_page.html",
        {
            "list_element": list_element(request, person_id=person_id),
            "detail_element": detail_element(
                request, person_id=str(person_id) if person_id is not None else "new"
            ),
        },
    )


@element()
def list_element(
    request: HttpRequest,
    filter_text: str = param(""),
    page: int = param(0),
    person_id: UUID | None = param(methods=["POST"]),
):
    persons = Person.objects.all()
    filter_text = filter_text.strip()
    if filter_text:
        persons = persons.filter(
            Q(first_name__icontains=filter_text) | Q(last_name__icontains=filter_text)
        )
    persons = persons.order_by("first_name", "last_name")

    page_size = 5
    persons = persons[page * page_size : ((page + 1) * page_size) + 1]

    return render(
        request,
        "demo_address_book_fbv/list_element.html",
        {
            "url": reverse("address-book-list-element"),
            "view": list_element,
            "page": page,
            "has_more_pages": len(persons) > page_size,
            "filter_text": filter_text,
            "persons": persons,
            "person_id": person_id,
            "detail_element": detail_element,
        },
    )


# @view()
# def action_open_person(request: HttpRequest, person_id: UUID):
#     hook_swap_oob(
#         request,
#         [
#             list_element(request, person_id=person_id),
#             detail_element(request, person_id=str(person_id)),
#         ],
#     )
#     return push_url(
#         reswap(HttpResponse(), "none"),
#         f"""{reverse("address-book-page")}?person_id={person_id}""",
#     )


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ["first_name", "last_name"]


@element()
def detail_element(request: HttpRequest, person_id: str):
    person = Person.objects.get(id=person_id) if person_id != "new" else None
    ic(person)
    form = create_form(request, PersonForm, instance=person)

    if is_valid_submit(request, form):
        form.save()
        # return action_open_person(request, person_id=person.id)

    return render(
        request,
        "demo_address_book_fbv/detail_element.html",
        {
            "url": reverse(
                "address-book-detail-element", kwargs={"person_id": person_id}
            ),
            "person": person,
            "form": form,
        },
    )


urlpatterns = [
    path("", address_book_page, name="address-book-page"),
    path("list/", list_element, name="address-book-list-element"),
    path("detail/<person_id>", detail_element, name="address-book-detail-element"),
    ###
    ###
    # path(
    #     "action_open_person/<uuid:person_id>",
    #     action_open_person,
    #     name="address-book-page-action-open-person",
    # ),
]
