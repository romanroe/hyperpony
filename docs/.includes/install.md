## Add Hyperpony as a project dependency

=== "pip"
    ```bash
    pip install hyperpony
    ```

=== "poetry"
    ```bash
    poetry add hyperpony
    ```

## Add the Hyperpony application to your Django project

**settings.py**
```python
INSTALLED_APPS = [
    # ...
    "hyperpony",
]
```

## Add the middleware to your Django project

**settings.py**
```python
MIDDLEWARE = [
    # ...
    "hyperpony.middleware.HyperponyMiddleware",
]
```
