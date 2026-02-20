# v1.0

## Release Date

2026-02-19

## Overview

Initial release of `graphene-django-observability` as a **generic, Nautobot-free** library.

This package was previously released as `nautobot-graphql-observability` (versions 1.x–2.x), a Nautobot-specific app.  Starting from v1.0 of this package it has been refactored into a standalone Django library with no dependency on Nautobot.

## What's Included

### Prometheus Metrics (`PrometheusMiddleware`)

- `graphql_requests_total` — request counter with `operation_type`, `operation_name`, `status` labels.
- `graphql_request_duration_seconds` — full-request duration histogram.
- `graphql_errors_total` — error counter with `error_type` label.
- `graphql_query_depth` — query nesting depth histogram (opt-in).
- `graphql_query_complexity` — total field count histogram (opt-in).
- `graphql_field_resolution_duration_seconds` — per-field resolver duration (opt-in, high overhead).
- `graphql_requests_by_user_total` — per-user request counter (opt-in).

### Query Logging (`GraphQLQueryLoggingMiddleware`)

- Structured log entries via Python's `logging` module.
- Optional query body and variables in log entries.
- Logger name: `graphene_django_observability.graphql_query_log`.

### Django Integration

- `GraphQLObservabilityDjangoMiddleware` — HTTP middleware for accurate wall-clock timing.
- `GRAPHENE_OBSERVABILITY` settings key for configuration.
- Configurable `graphql_paths` to instrument any URL path.
- Built-in `/metrics/` endpoint via `graphene_django_observability.urls`.

## Migrating from `nautobot-graphql-observability`

1. Uninstall the old package: `pip uninstall nautobot-graphql-observability`
2. Install the new package: `pip install graphene-django-observability`
3. Replace `PLUGINS = ["nautobot_graphql_observability"]` with `INSTALLED_APPS = [..., "graphene_django_observability"]`.
4. Add `GraphQLObservabilityDjangoMiddleware` to `MIDDLEWARE` manually.
5. Move settings from `PLUGINS_CONFIG["nautobot_graphql_observability"]` to `GRAPHENE_OBSERVABILITY`.
