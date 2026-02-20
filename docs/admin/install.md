# Installation & Configuration

## Requirements

- Python 3.10, 3.11, 3.12, or 3.13
- Django 3.2+
- graphene-django 3.0+

## Install

```shell
pip install graphene-django-observability
```

## Django Configuration

### 1. Add to `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    ...
    "graphene_django_observability",
]
```

### 2. Register the Django HTTP middleware

Add the Django middleware to `MIDDLEWARE`.  It must be placed **after** any session/auth middleware so that the authenticated user is available:

```python
MIDDLEWARE = [
    ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "graphene_django_observability.django_middleware.GraphQLObservabilityDjangoMiddleware",
]
```

### 3. Register the Graphene middlewares

Add one or both middlewares to the `GRAPHENE` setting:

```python
GRAPHENE = {
    "SCHEMA": "myapp.schema.schema",
    "MIDDLEWARE": [
        # Prometheus metrics (required for metric collection)
        "graphene_django_observability.middleware.PrometheusMiddleware",
        # Structured query logging (optional)
        "graphene_django_observability.logging_middleware.GraphQLQueryLoggingMiddleware",
    ],
}
```

### 4. Expose the `/metrics/` endpoint (optional)

The library provides a ready-made Prometheus scrape endpoint.  Mount it anywhere in your URL configuration:

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...
    path("graphql-observability/", include("graphene_django_observability.urls")),
]
```

Metrics will then be available at `/graphql-observability/metrics/`.

!!! tip "Existing Prometheus endpoint"
    If your project already exposes a `/metrics/` endpoint (e.g. via `django-prometheus`), the
    library's metrics are automatically included there — you do **not** need the URL above.

## Configuration Reference

All settings are optional.  Configure via `GRAPHENE_OBSERVABILITY` in `settings.py`:

```python
GRAPHENE_OBSERVABILITY = {
    # --- General ---
    # URL paths that should be instrumented (default: ["/graphql/"])
    "graphql_paths": ["/graphql/"],

    # --- Prometheus metrics ---
    "graphql_metrics_enabled": True,   # Master switch for all metric collection
    "track_query_depth": True,          # Histogram of query nesting depth
    "track_query_complexity": True,     # Histogram of total field count
    "track_field_resolution": False,    # Per-field resolver duration (high overhead)
    "track_per_user": True,             # Per-user request counter

    # --- Query logging ---
    "query_logging_enabled": False,     # Structured log entries per query
    "log_query_body": False,            # Include the full query text in logs
    "log_query_variables": False,       # Include query variables in logs (may log sensitive data)
}
```

### Prometheus Metrics Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `graphql_metrics_enabled` | `bool` | `True` | Enable or disable all metrics collection. |
| `track_query_depth` | `bool` | `True` | Record a histogram of GraphQL query nesting depth. |
| `track_query_complexity` | `bool` | `True` | Record a histogram of GraphQL query complexity (total field count). |
| `track_field_resolution` | `bool` | `False` | Record per-field resolver duration. **Warning:** adds significant overhead for queries with many fields. |
| `track_per_user` | `bool` | `True` | Record a per-user request counter using the authenticated username. |

### Query Logging Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `query_logging_enabled` | `bool` | `False` | Enable or disable GraphQL query logging. |
| `log_query_body` | `bool` | `False` | Include the full GraphQL query text in log entries. |
| `log_query_variables` | `bool` | `False` | Include query variables in log entries. **Warning:** may log sensitive data. |

## Multi-Process Deployments

If you run Django with multiple worker processes (e.g. Gunicorn), set `PROMETHEUS_MULTIPROC_DIR` so that `prometheus_client` can aggregate metrics across processes:

```shell
export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
```

The metrics endpoint will automatically aggregate metrics from all worker processes when this variable is set.
