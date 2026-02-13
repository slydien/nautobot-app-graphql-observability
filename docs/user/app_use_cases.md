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
