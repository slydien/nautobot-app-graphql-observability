# App Overview

This document provides an overview of the App including critical information and important considerations when applying it to your Nautobot environment.

!!! note
    Throughout this documentation, the terms "app" and "plugin" will be used interchangeably.

## Description

The Nautobot App GraphQL Observability provides comprehensive observability for Nautobot's GraphQL API. It includes two Graphene middlewares that work together to provide both real-time metrics and structured query logging — without modifying Nautobot's core code.

### Prometheus Metrics

The `PrometheusMiddleware` instruments every GraphQL query with Prometheus metrics, exposed at Nautobot's default `/metrics/` endpoint.

#### Basic Metrics

| Metric | Type | Labels | Description |
| ------ | ---- | ------ | ----------- |
| `graphql_requests_total` | Counter | `operation_type`, `operation_name`, `status` | Total number of GraphQL requests (success/error). |
| `graphql_request_duration_seconds` | Histogram | `operation_type`, `operation_name` | Duration of GraphQL request execution in seconds. |
| `graphql_errors_total` | Counter | `operation_type`, `operation_name`, `error_type` | Total number of GraphQL errors by exception type. |

#### Advanced Metrics

| Metric | Type | Labels | Description |
| ------ | ---- | ------ | ----------- |
| `graphql_query_depth` | Histogram | `operation_name` | Depth (nesting level) of GraphQL queries. |
| `graphql_query_complexity` | Histogram | `operation_name` | Complexity of GraphQL queries measured by total field count. |
| `graphql_field_resolution_duration_seconds` | Histogram | `type_name`, `field_name` | Duration of individual field resolution in seconds. |
| `graphql_requests_by_user_total` | Counter | `user`, `operation_type`, `operation_name` | Total number of GraphQL requests per authenticated user. |

### Query Logging

The `GraphQLQueryLoggingMiddleware` emits structured log entries for every GraphQL query using Python's `logging` module. Each log entry includes:

- **Operation type** (query/mutation)
- **Operation name**
- **Authenticated user**
- **Duration** in milliseconds
- **Status** (success/error)
- **Error type** (on failure)
- **Query body** (optional)
- **Query variables** (optional)

Logs are emitted to the `nautobot_graphql_observability.graphql_query_log` logger and can be routed to any backend (file, syslog, ELK, etc.) via Django's `LOGGING` configuration.

## Audience (User Personas) - Who should use this App?

- **Nautobot Operators** who need visibility into GraphQL API performance and usage patterns.
- **SREs / Platform Engineers** building observability stacks around Nautobot with Prometheus and Grafana.
- **Network Automation Teams** who want to monitor which GraphQL queries are slow, complex, or error-prone.
- **Security Teams** who want to track per-user API activity for auditing and forensics.

## Authors and Maintainers

- Lydien SANDANASAMY ([@slydien](https://github.com/slydien))

## Nautobot Features Used

This app does not add models, views, or navigation items to Nautobot. It operates entirely at the Graphene middleware layer and provides:

- A **Prometheus metrics middleware** (`PrometheusMiddleware`) that instruments GraphQL resolvers with counters and histograms.
- A **query logging middleware** (`GraphQLQueryLoggingMiddleware`) that emits structured log entries for every GraphQL operation.
- An automatic **monkey-patch** of Nautobot's `GraphQLDRFAPIView` to load Graphene middleware from Django settings.
- Metrics are registered in the default Prometheus registry and automatically appear at Nautobot's default `/metrics/` endpoint.
