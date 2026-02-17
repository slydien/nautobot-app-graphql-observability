# Using the App

This document describes common use-cases and scenarios for this App.

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

The app includes a separate logging middleware that emits structured log entries for every GraphQL operation. This complements the Prometheus metrics by providing per-request detail that can be searched, filtered, and forwarded to log aggregation systems.

### Enabling Query Logging

Set `query_logging_enabled` to `True` in your `PLUGINS_CONFIG`:

```python
PLUGINS_CONFIG = {
    "nautobot_graphql_observability": {
        "query_logging_enabled": True,
        "log_query_body": True,
        "log_query_variables": False,
    }
}
```

### Log Output Format

Each query produces a structured log line:

```
14:32:05.123 INFO    nautobot_graphql_observability.graphql_query_log : operation_type=query operation_name=GetDevices user=admin duration_ms=42.3 status=success query=query GetDevices { devices { name } }
```

Failed queries are logged at WARNING level and include the error type:

```
14:32:06.456 WARNING nautobot_graphql_observability.graphql_query_log : operation_type=query operation_name=BadQuery user=admin duration_ms=5.1 status=error error_type=GraphQLError
```

### Routing Logs to External Systems

The logging middleware uses Python's standard `logging` module with the logger name `nautobot_graphql_observability.graphql_query_log`. You can route these logs to any backend via Django's `LOGGING` configuration:

```python
# nautobot_config.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "graphql_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "/var/log/nautobot/graphql_queries.log",
        },
    },
    "loggers": {
        "nautobot_graphql_observability.graphql_query_log": {
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
