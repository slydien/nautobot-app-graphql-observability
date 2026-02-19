# Getting Started

This guide walks you through installing `graphene-django-observability` and sending your first instrumented GraphQL query.

## Prerequisites

- A working Django project with [graphene-django](https://docs.graphene-python.org/projects/django/) installed and a GraphQL schema configured.
- Prometheus (optional, but needed to actually scrape metrics).

## Step 1 — Install the package

```shell
pip install graphene-django-observability
```

## Step 2 — Configure Django

Add the following to your `settings.py`:

```python
INSTALLED_APPS = [
    ...
    "graphene_django_observability",
]

MIDDLEWARE = [
    ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "graphene_django_observability.django_middleware.GraphQLObservabilityDjangoMiddleware",
]

GRAPHENE = {
    "SCHEMA": "myapp.schema.schema",   # your existing schema path
    "MIDDLEWARE": [
        "graphene_django_observability.middleware.PrometheusMiddleware",
    ],
}
```

## Step 3 — Expose the metrics endpoint

Add the URL pattern to your `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    ...
    path("graphql-observability/", include("graphene_django_observability.urls")),
]
```

Prometheus metrics are now available at `http://localhost:8000/graphql-observability/metrics/`.

## Step 4 — Send a GraphQL query

With your Django development server running (`python manage.py runserver`), send a query:

```shell
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "query GetUsers { users { id username } }"}'
```

## Step 5 — Check the metrics

```shell
curl http://localhost:8000/graphql-observability/metrics/ | grep graphql
```

You should see output similar to:

```
# HELP graphql_requests_total Total number of GraphQL requests
# TYPE graphql_requests_total counter
graphql_requests_total{operation_name="GetUsers",operation_type="query",status="success"} 1.0
# HELP graphql_request_duration_seconds Duration of GraphQL request execution in seconds
# TYPE graphql_request_duration_seconds histogram
graphql_request_duration_seconds_bucket{le="0.01",operation_name="GetUsers",operation_type="query"} 1.0
...
```

## Step 6 — Enable query logging (optional)

Add the logging middleware and enable it via settings:

```python
# settings.py
GRAPHENE = {
    "SCHEMA": "myapp.schema.schema",
    "MIDDLEWARE": [
        "graphene_django_observability.logging_middleware.GraphQLQueryLoggingMiddleware",
        "graphene_django_observability.middleware.PrometheusMiddleware",
    ],
}

GRAPHENE_OBSERVABILITY = {
    "query_logging_enabled": True,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "graphene_django_observability.graphql_query_log": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
```

After sending a query you will see a structured log line:

```
graphql_query operation_type=query operation_name=GetUsers user=anonymous duration_ms=12.3 status=success
```

## Next Steps

- See [Configuration Reference](../admin/install.md#configuration-reference) for all available options.
- See [Use Cases](app_use_cases.md) for common patterns like slow-query alerting and per-user tracking.
- See [Extending](../dev/extending.md) to add custom metrics.
