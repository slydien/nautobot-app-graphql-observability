# v1.0 Release Notes

This document describes all new features and changes in the release `1.0`. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Initial release of the Prometheus GraphQL Metrics middleware for Nautobot.
- Provides 7 Prometheus metrics covering request counts, durations, errors, query depth, query complexity, per-field resolution, and per-user tracking.
- Automatic monkey-patching of Nautobot's `GraphQLDRFAPIView` to load Graphene middleware from settings.
- Metrics are automatically available at Nautobot's default `/metrics/` endpoint.

## [v1.0.0] - 2025

### Added

- Graphene middleware (`PrometheusMiddleware`) that instruments GraphQL queries with Prometheus metrics.
- Basic metrics: `graphql_requests_total`, `graphql_request_duration_seconds`, `graphql_errors_total`.
- Advanced metrics: `graphql_query_depth`, `graphql_query_complexity`, `graphql_field_resolution_duration_seconds`, `graphql_requests_by_user_total`.
- Configurable settings to enable/disable individual metric categories.
- Metrics registered in the default Prometheus registry and available at Nautobot's `/metrics/` endpoint.
- Automatic patching of `GraphQLDRFAPIView.init_graphql()` to work around Nautobot 3.x middleware loading bug.
- Multi-process support via `PROMETHEUS_MULTIPROC_DIR`.
- Grafana dashboard templates for GraphQL performance monitoring.
