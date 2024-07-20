from typing import Optional

from django.db.models import Q
from django import forms
from django.http import HttpResponse
from django.urls import path, reverse
from django.views.generic import TemplateView, FormView
from icecream import ic

from demo_address_book.models import Person
from hyperpony import NestedView, param
from hyperpony.element import ElementView
from hyperpony.form import create_form


class AddressBookPage(NestedView, TemplateView):
    template_name = "demo_address_book_cbv/address_book_page.html"
    person: Optional[Person] = param()

    def get_context_data(self, **kwargs):
        ic(self.person)
        return {
            "list_element": ListElement(person_id=self.person).as_str(
                self.request, person=self.person
            ),
            # "detail_element": DetailElement(person=self.person).embed(self.request),
        }


class ListElement(ElementView, TemplateView):
    template_name = "demo_address_book_cbv/list_element.html"
    selected_person: Optional[Person] = param()
    filter_text: str = param("")
    page: int = param(0)

    def get_context_data(self, **kwargs):
        ic(self.selected_person)
        persons = Person.objects.all()
        filter_text = self.filter_text.strip()
        if filter_text:
            persons = persons.filter(
                Q(first_name__icontains=filter_text)
                | Q(last_name__icontains=filter_text)
            )
        persons = persons.order_by("first_name", "last_name")

        page_size = 5
        persons = persons[self.page * page_size : ((self.page + 1) * page_size) + 1]

        return {
            "url": reverse("address-book-list-element-cbv"),
            "page": self.page,
            "has_more_pages": len(persons) > page_size,
            "filter_text": filter_text,
            "persons": persons,
            "selected_person": self.selected_person,
            # "detail_element": detail_element,
        }


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ["first_name", "last_name"]


class DetailElement(ElementView, FormView):
    template_name = "demo_address_book_cbv/detail_element.html"
    person: Optional[Person] = param()
    form_class = PersonForm

    def get_form(self, form_class=None):
        return create_form(self.request, PersonForm, instance=self.person)

    def get_context_data(self, **kwargs):
        return super().get_context_data() | {
            "person": self.person,
        }

    def form_valid(self, form):
        form.save()
        return HttpResponse()


urlpatterns = [
    path("<uuid:person>", AddressBookPage.as_view(), name="address-book-page-cbv"),
    path("", AddressBookPage.as_view(), name="address-book-page-cbv"),
    path("list/", ListElement.as_view(), name="address-book-list-element-cbv"),
    path(
        "detail/<person>",
        DetailElement.as_view(),
        name="address-book-detail-element-cbv",
    ),
]
