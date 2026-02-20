# Extending

## Adding a Custom Metric Label

Subclass `PrometheusMiddleware` and override `resolve()` to add extra labels.
Make sure the new label is also added to the metric definition in `metrics.py`.

```python
from graphene_django_observability.middleware import PrometheusMiddleware
from graphene_django_observability.metrics import graphql_requests_total
from prometheus_client import Counter

# Redefine the counter with the extra label
graphql_requests_with_tenant = Counter(
    "graphql_requests_with_tenant_total",
    "GraphQL requests with tenant label",
    ["operation_type", "operation_name", "status", "tenant"],
)


class TenantAwarePrometheusMiddleware(PrometheusMiddleware):
    def resolve(self, next, root, info, **kwargs):
        if root is not None:
            return next(root, info, **kwargs)

        tenant = getattr(info.context, "tenant", "unknown")
        result = super().resolve(next, root, info, **kwargs)
        # record with tenant label
        graphql_requests_with_tenant.labels(
            operation_type=info.operation.operation.value,
            operation_name=self._get_operation_name(info),
            status="success",
            tenant=tenant,
        ).inc()
        return result
```

## Adding a Custom Histogram Bucket

Override `metrics.py` in your project to redefine the histogram with custom buckets:

```python
from prometheus_client import Histogram

graphql_request_duration_seconds = Histogram(
    "graphql_request_duration_seconds",
    "Duration of GraphQL request execution in seconds",
    ["operation_type", "operation_name"],
    buckets=[0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)
```

!!! warning
    The `prometheus_client` library raises an error if you try to register a metric with the same name twice.
    Either override the metric **before** the library is loaded, or use a custom registry.

## Adding Custom Query Logging Fields

Subclass `GraphQLQueryLoggingMiddleware` to capture additional context:

```python
from graphene_django_observability.logging_middleware import GraphQLQueryLoggingMiddleware


class AuditLoggingMiddleware(GraphQLQueryLoggingMiddleware):
    def resolve(self, next, root, info, **kwargs):
        result = super().resolve(next, root, info, **kwargs)
        if root is None:
            request = info.context
            meta = getattr(request, "_graphql_logging_meta", None)
            if meta is not None:
                meta["ip_address"] = request.META.get("REMOTE_ADDR", "unknown")
        return result
```
