# Changelog

<!-- releases -->

## 0.71.16 (2025-01-26)

## 0.71.0 (2025-01-23)

## 0.70.2 (2025-01-22)

-  add PATH to param's methods
- fixed request.user bug

## 0.70.1 (2025-01-22)

-  `SingletonPathMixin.create_path()` now accepts optional `name` parameter

## 0.70.0 (2025-01-21)

- only support for CBV

## 0.61.3 (2024-09-28)

- internal changes

## 0.61.2 (2024-09-28)

- internal changes

## 0.61.1 (2024-08-18)

- added `SingletonPathView` to __init__.py


## 0.61.0 (2024-08-18)

- added `SingletonPathView`
- `ElementView` now automatically embeds `ClientState` attrs

- fixed client_state escaping

## 0.60.6 (2024-08-18)

- fixed client_state escaping

## 0.60.5 (2024-08-18)

- CBVs are now view stack aware

## 0.60.4 (2024-08-17)

- fixed: do not create client_state on GET requests

## 0.60.3 (2024-08-17)

- support for HTMX 2.0

## 0.60.2 (2024-08-14)

- fixed Optional params with default value of None

## 0.60.1 (2024-07-21)

- BETA: client state support (via Alpine.js)

## 0.51.0 (2024-03-03)

- unified view stack behaviour

## 0.50.1 (2024-02-25)

- fixed Python dependency version

## 0.50.0 (2024-02-25)

- middleware is now async aware

## 0.48.0 (2024-02-18)

- renamed project from DFV to Hyperpony

**breaking change**

- renamed module `dfv` to `hyperpony`
- renamed middleware `dfv.middleware.DFVMiddleware` to `hyperpony.middleware.HyperponyMiddleware`


 
