# FAQ

## Why do I not see metrics immediately after installation?

Prometheus counters and histograms only appear in the output **after the first observation**.  Send at least one GraphQL query and then check `/graphql-observability/metrics/`.

## I already have a `/metrics/` endpoint from `django-prometheus`. Will this conflict?

No.  The library registers its metrics in the **default Prometheus registry** (`prometheus_client.REGISTRY`).  Any endpoint that calls `generate_latest()` on the default registry — including `django-prometheus`'s endpoint — will include the GraphQL metrics automatically.  You do not need to mount `graphene_django_observability.urls` in that case.

## What is the performance overhead?

The overhead is very low.  By default, counters and histograms are recorded once per root field resolution and once per HTTP request.  Only `track_field_resolution: True` adds overhead proportional to the number of fields returned — avoid it in high-traffic production environments.

## Does the middleware work with multi-process deployments (Gunicorn, uWSGI)?

Yes, with the standard `prometheus_client` multi-process setup.  Set the `PROMETHEUS_MULTIPROC_DIR` environment variable to a writable directory:

```shell
export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
```

The metrics endpoint will aggregate metrics from all worker processes automatically.

## How do I suppress the `graphql_query_log` output in tests?

The logger name is `graphene_django_observability.graphql_query_log`.  In your test settings, set its level to `CRITICAL`:

```python
LOGGING = {
    "version": 1,
    "loggers": {
        "graphene_django_observability.graphql_query_log": {
            "level": "CRITICAL",
        },
    },
}
```

## Can I use only the Prometheus middleware without the query logging middleware?

Yes.  The two middlewares are fully independent.  Include only the ones you need in `GRAPHENE["MIDDLEWARE"]`.

## Can I use only the query logging middleware without Prometheus?

Yes.  The `GraphQLQueryLoggingMiddleware` has no dependency on the `PrometheusMiddleware`.

## What happens to anonymous (unnamed) GraphQL queries?

When a query has no explicit `operationName`, the library uses the sorted, comma-joined list of root field names as the operation name label (e.g. `"devices,locations"`).  This avoids a high-cardinality `anonymous` label.

## Does this work with Django REST Framework (DRF) views?

Yes.  The `PrometheusMiddleware` and `GraphQLQueryLoggingMiddleware` stash metadata on both the DRF request wrapper and the underlying `WSGIRequest`, so the Django HTTP middleware can read the data regardless of the view layer.
