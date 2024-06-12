# Views

!!! info "Why does this feature exists?"

    Django views are designed to be called by the Django framework and not to be called by user code. A caller can't identify the required GET or POST parameter and the returned `HttpResponse` can't easily be used for composition (e.g. embed the response as an element in the caller's template).

## `@view()` decorator

Apply the `@view()` decorator to a view to create a "Hyperpony view". The decorator does not alter existing behaviour
but only adds new features. It is therefore safe to apply the decorator to existing views without changing their
behaviour.

Example:

```python
from django.http import HttpResponse
from hyperpony import view  # <-- import the decorator


@view()  # <-- apply the decorator
def simple_view(request):
    return HttpResponse("a simple response")
```

### Stringable response

The `@view()` decorator wraps the response in a `hyperpony.views.ViewResponse` object, which proxies the response and adds a `__str__` method. This allows the response to be easily used in the caller's response.

Example:

```python
from django.http import HttpResponse
from hyperpony import view


@view() 
def child_view(request):
    return HttpResponse("child")

def root_view(request):
    child_response = child_view(request)
    return HttpResponse(f"response from child: {child_response}")
```

The above example directly constructs the response content with a string. In a real-world application, the `child_response` could also be used as a context variable in the template. 

### Parameter extraction


