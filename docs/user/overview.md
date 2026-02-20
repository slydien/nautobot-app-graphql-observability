# Overview

`graphene-django-observability` provides comprehensive observability for any [graphene-django](https://docs.graphene-python.org/projects/django/) GraphQL API.
It ships two independent [Graphene middlewares](https://docs.graphene-python.org/en/latest/execution/middleware/) that can be used together or separately.

## Prometheus Metrics

The `PrometheusMiddleware` instruments every GraphQL operation with Prometheus metrics.

### Basic Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `graphql_requests_total` | Counter | `operation_type`, `operation_name`, `status` | Total number of GraphQL requests (success/error). |
| `graphql_request_duration_seconds` | Histogram | `operation_type`, `operation_name` | Duration of GraphQL request execution in seconds. |
| `graphql_errors_total` | Counter | `operation_type`, `operation_name`, `error_type` | Total number of GraphQL errors by exception type. |

### Advanced Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `graphql_query_depth` | Histogram | `operation_name` | Depth (nesting level) of GraphQL queries. |
| `graphql_query_complexity` | Histogram | `operation_name` | Complexity measured by total field count. |
| `graphql_field_resolution_duration_seconds` | Histogram | `type_name`, `field_name` | Duration of individual field resolution (opt-in). |
| `graphql_requests_by_user_total` | Counter | `user`, `operation_type`, `operation_name` | Total requests per authenticated user. |

## Query Logging

The `GraphQLQueryLoggingMiddleware` emits structured log entries for every GraphQL operation using Python's `logging` module.

Each log entry includes:

- **Operation type** (`query` / `mutation`)
- **Operation name** (or root field names for anonymous queries)
- **Authenticated user**
- **Duration** in milliseconds
- **Status** (`success` / `error`)
- **Error type** (on failure)
- **Query body** (optional — requires `log_query_body: True`)
- **Query variables** (optional — requires `log_query_variables: True`)

Logs are emitted to the `graphene_django_observability.graphql_query_log` logger and can be routed to any backend (file, syslog, ELK, Loki, etc.) via Django's `LOGGING` configuration.

## Architecture

The library uses **two middleware layers** that work together:

```
HTTP request
    │
    ▼
GraphQLObservabilityDjangoMiddleware    ← Django MIDDLEWARE
    │  starts wall-clock timer
    │
    ▼
graphene-django view
    │
    ▼
PrometheusMiddleware / LoggingMiddleware  ← GRAPHENE["MIDDLEWARE"]
    │  records counters + stashes labels on request
    │
    ▼
GraphQL resolvers
    │
    ▼
GraphQLObservabilityDjangoMiddleware    ← response path
    │  reads stashed labels, records duration histogram, emits log
    ▼
HTTP response
```

The split is deliberate: Graphene middleware runs once per root field (best for counters), while the Django middleware wraps the full HTTP lifecycle (accurate wall-clock timing).

## Authors

- Lydien SANDANASAMY ([@slydien](https://github.com/slydien))
