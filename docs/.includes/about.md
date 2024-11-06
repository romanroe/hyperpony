Hyperpony is a Django library for building modern [hypermedia-driven web applications](https://hypermedia.systems). It provides a set of tools and patterns (e.g. decorators) for writing componentized applications using [htmx](https://htmx.org).

Even though you can use htmx and Django without Hyperpony, Django lacks first-class support for implementing the pattern used in [Hypermedia Systems](https://hypermedia.systems/htmx-in-action/), e.g.:

- splitting a page into components to be updated independently
- composable out-of-band swaps during a request
- using Django forms with e.g., hx-patch for form validations
- Template tags for easily generating `hx-vals`

**Hyperpony is not an all-or-nothing library!** You can cherry-pick the parts you like and use them in your existing Django projects, and you only need to apply them in views where appropriate.
