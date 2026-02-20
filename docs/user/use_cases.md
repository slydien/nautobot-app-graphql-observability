# Use Cases

This document describes common use-cases and scenarios for this library.

## Monitoring Query Performance

Use `graphql_request_duration_seconds` to identify slow GraphQL queries and track performance over time.

Example PromQL to find the 95th percentile query duration:

```promql
histogram_quantile(0.95, rate(graphql_request_duration_seconds_bucket[5m]))
```

## Tracking Per-User Activity

When `track_per_user` is enabled (the default), the `graphql_requests_by_user_total` counter tracks which users are making GraphQL requests. This is useful for:

- **Capacity planning**: Identify heavy API consumers.
- **Security auditing**: Detect unusual query patterns from specific users.
- **Troubleshooting**: Correlate performance issues with specific user activity.

Example PromQL to find the top 5 users by request count:

```promql
topk(5, sum by (user) (rate(graphql_requests_by_user_total[1h])))
```

## Identifying Expensive Queries

Use `graphql_query_depth` and `graphql_query_complexity` to detect queries that are deeply nested or request many fields:

```promql
# Queries with depth > 5
histogram_quantile(0.99, rate(graphql_query_depth_bucket[5m])) > 5

# Queries with complexity > 100 fields
histogram_quantile(0.99, rate(graphql_query_complexity_bucket[5m])) > 100
```

These metrics help you understand which queries may need optimization or which clients may need guidance on query best practices.

## Per-Field Resolution Debugging

When `track_field_resolution` is enabled, `graphql_field_resolution_duration_seconds` records the time spent resolving each individual field. This is useful for pinpointing slow resolvers during debugging.

!!! warning
    Enabling `track_field_resolution` adds overhead to every field resolution. Use it for short-term debugging, not in production under heavy load.

Example PromQL to find the slowest fields:

```promql
topk(10, sum by (type_name, field_name) (rate(graphql_field_resolution_duration_seconds_sum[5m])))
```

## Alerting on Error Rates

Use `graphql_errors_total` to set up alerts when GraphQL error rates spike:

```promql
# Error rate as a percentage of total requests
sum(rate(graphql_errors_total[5m])) / sum(rate(graphql_requests_total[5m])) * 100 > 5
```

## Monitoring Operation Types

Compare query vs mutation traffic to understand API usage patterns:

```promql
sum by (operation_type) (rate(graphql_requests_total[5m]))
```

## Query Logging

The library includes a separate logging middleware that emits structured log entries for every GraphQL operation. This complements the Prometheus metrics by providing per-request detail that can be searched, filtered, and forwarded to log aggregation systems.

### Enabling Query Logging

Set `query_logging_enabled` to `True` in your `GRAPHENE_OBSERVABILITY` settings:

```python
GRAPHENE_OBSERVABILITY = {
    "query_logging_enabled": True,
    "log_query_body": True,
    "log_query_variables": False,
}
```

### Log Output Format

The logging middleware emits structured records using Python's standard `logging` module under the logger name `graphene_django_observability.graphql_query_log`. Each record carries the following fields as `LogRecord` attributes (via `extra`):

| Field | Type | Description |
| ----- | ---- | ----------- |
| `event` | `str` | Always `"graphql_query"` |
| `operation_type` | `str` | `"query"` or `"mutation"` |
| `operation_name` | `str` | Named operation or comma-separated root fields for anonymous queries |
| `user` | `str` | Authenticated username, or `"anonymous"` |
| `duration_ms` | `float` | Total request duration in milliseconds |
| `status` | `str` | `"success"` or `"error"` |
| `error_type` | `str` | Exception class name — only present on error |
| `query` | `str` | Full query text — only present when `log_query_body` is enabled |
| `variables` | `str` | JSON-encoded variables — only present when `log_query_variables` is enabled |

### Structured JSON Logging with structlog

For production deployments sending logs to aggregation systems (Loki, Elasticsearch, Splunk, etc.), you can use `structlog` with `django-structlog` to emit all log output as JSON. The query log fields will appear as top-level JSON keys.

Install the optional dependencies:

```
pip install structlog django-structlog
```

Add the following to your `settings.py`:

```python
import structlog

INSTALLED_APPS = [
    ...
    "django_structlog",
]

MIDDLEWARE = [
    "django_structlog.middlewares.RequestMiddleware",
    ...
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processors": [
                structlog.stdlib.ExtraAdder(),
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
            "foreign_pre_chain": [
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
            ],
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        # graphene_django_observability.graphql_query_log must be listed directly
        # because the logging middleware sets propagate=False so records never
        # reach the root logger.
        "graphene_django_observability.graphql_query_log": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
```

Each query log entry will be emitted as a single JSON object:

```json
{
  "event": "graphql_query",
  "level": "info",
  "logger": "graphene_django_observability.graphql_query_log",
  "timestamp": "2026-02-19T08:16:31.818110Z",
  "operation_type": "query",
  "operation_name": "GetDevices",
  "user": "admin",
  "duration_ms": 162.4,
  "status": "success",
  "query": "query GetDevices { devices { name } }",
  "ip": "192.168.148.1",
  "request_id": "0e2936fc-7989-4fcb-a63a-d0dd4d6bcea7"
}
```

!!! note
    `ip` and `request_id` are injected automatically by `django_structlog.middlewares.RequestMiddleware`.

### Routing Logs to External Systems

If you are not using structlog, the logging middleware uses Python's standard `logging` module and can be routed to any backend via Django's `LOGGING` configuration:

```python
# settings.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "graphql_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "/var/log/app/graphql_queries.log",
        },
    },
    "loggers": {
        "graphene_django_observability.graphql_query_log": {
            "handlers": ["graphql_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
```

### Security Considerations

!!! warning
    Enabling `log_query_body` will log the full GraphQL query text, and `log_query_variables` will log query variables which may contain sensitive data (passwords, tokens, etc.). Only enable these in environments where log access is properly secured.
