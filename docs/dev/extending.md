# Extending the App

Contributions and extensions are welcome. Please open an issue first to discuss the proposed change before submitting a PR.

## Adding Custom Metrics

To add a new Prometheus metric:

1. Define the metric in `nautobot_app_graphql_observability/metrics.py`:

    ```python
    from prometheus_client import Counter

    graphql_deprecated_fields_total = Counter(
        "graphql_deprecated_fields_total",
        "Total usage of deprecated GraphQL fields",
        ["type_name", "field_name"],
    )
    ```

2. Import and record it in the appropriate method of `PrometheusMiddleware` in `nautobot_app_graphql_observability/middleware.py`.

3. If the metric should be optional, add a new boolean setting to `NautobotAppGraphqlObservabilityConfig.default_settings` in `__init__.py` and gate the recording behind a config check in the middleware.

## Adding New Labels to Existing Metrics

Adding labels to existing metrics is a **breaking change** for Prometheus (it creates a new time series). If you need additional labels:

1. Consider creating a new metric instead.
2. If modifying an existing metric, update the label list in `metrics.py` and all `.labels()` calls in `middleware.py`.
3. Update tests to include the new label values.

## Customizing Histogram Buckets

The default histogram buckets are defined in `metrics.py`. To customize them for your deployment, you can fork the metric definitions. A future enhancement may allow bucket configuration via `PLUGINS_CONFIG`.

## Extending the Logging Middleware

The `GraphQLQueryLoggingMiddleware` in `nautobot_app_graphql_observability/logging_middleware.py` can be extended to add custom fields to log entries. The middleware uses Python's standard `logging` module with the logger name `nautobot_app_graphql_observability.graphql_query_log`.

To add custom log fields, subclass `GraphQLQueryLoggingMiddleware` and override `_log_query()`:

```python
from nautobot_app_graphql_observability.logging_middleware import GraphQLQueryLoggingMiddleware

class CustomLoggingMiddleware(GraphQLQueryLoggingMiddleware):
    @staticmethod
    def _log_query(config, operation_type, operation_name, user, start_time, info, error=None):
        # Call parent to emit the standard log entry
        GraphQLQueryLoggingMiddleware._log_query(
            config, operation_type, operation_name, user, start_time, info, error
        )
        # Add custom logic here
```
