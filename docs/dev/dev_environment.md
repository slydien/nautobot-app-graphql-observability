# Development Environment

## Prerequisites

- Python 3.10+ (use [pyenv](https://github.com/pyenv/pyenv) to manage versions)
- [Poetry](https://python-poetry.org/) 2.0+

## Setup

```shell
# Clone the repository
git clone https://github.com/slydien/nautobot-app-graphql-observability.git
cd nautobot-app-graphql-observability

# Install all dependencies (including dev and docs groups)
poetry install

# Activate the virtual environment
poetry shell
```

## Running Tests

```shell
python -m django test graphene_django_observability --settings=test_settings --verbosity=2
```

With coverage:

```shell
coverage run -m django test graphene_django_observability --settings=test_settings
coverage report
```

## Linting

```shell
# Check formatting
ruff format --check .

# Auto-fix formatting
ruff format .

# Lint
ruff check .

# YAML lint
yamllint .
```

## Building the Documentation

```shell
# Serve locally with live reload at http://127.0.0.1:8001
mkdocs serve

# One-shot build (strict — fails on warnings)
mkdocs build --strict
```

## Project Layout

```
graphene_django_observability/
├── __init__.py              # Django AppConfig
├── middleware.py            # PrometheusMiddleware (Graphene layer)
├── django_middleware.py     # GraphQLObservabilityDjangoMiddleware (HTTP layer)
├── logging_middleware.py    # GraphQLQueryLoggingMiddleware (Graphene layer)
├── metrics.py               # Prometheus metric definitions
├── utils.py                 # Query depth/complexity helpers
├── views.py                 # metrics_view
├── urls.py                  # URL patterns
└── tests/
    ├── test_middleware.py
    ├── test_django_middleware.py
    ├── test_logging_middleware.py
    └── test_utils.py

test_settings.py             # Minimal Django settings for running tests
```
