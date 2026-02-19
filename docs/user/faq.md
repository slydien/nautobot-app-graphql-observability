# Frequently Asked Questions

## Why don't I see any metrics after installing the app?

Metrics are only recorded when GraphQL queries are executed against the `/api/graphql/` endpoint. Send a test query and then check the metrics at Nautobot's default `/metrics/` endpoint.

If metrics still don't appear, verify that:

1. The app is listed in `PLUGINS` in your `nautobot_config.py`.
2. Nautobot was restarted after installation.
3. The `graphql_metrics_enabled` setting is `True` (the default).

## How do I configure Prometheus to scrape this endpoint?

Add the following to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "nautobot-graphql"
    metrics_path: "/metrics/"
    static_configs:
      - targets: ["nautobot-host:8080"]
```

No authentication is required — Nautobot's `/metrics/` endpoint bypasses DRF.

## What is the performance impact of this app?

The basic metrics (request count, duration, errors) add negligible overhead since they only instrument the root resolver.

Enabling `track_query_depth` and `track_query_complexity` adds a small amount of overhead to parse the query AST after resolution. This is typically sub-millisecond.

Enabling `track_field_resolution` instruments **every** field resolver in every query. This can add measurable overhead for complex queries with hundreds of fields. It is recommended to leave this disabled in production and only enable it for short-term debugging.

## How does this work with multiple Nautobot worker processes?

Set the `PROMETHEUS_MULTIPROC_DIR` environment variable to a writable directory before starting Nautobot:

```shell
export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
```

The `prometheus_client` library will use shared files in this directory to aggregate metrics across all worker processes. Nautobot's `/metrics/` endpoint automatically handles multiprocess aggregation.

## Why does the app monkey-patch GraphQLDRFAPIView?

Nautobot 3.x's `GraphQLDRFAPIView.init_graphql()` has a bug: when `self.middleware` is `None` (the default), it does not load middleware from the `GRAPHENE["MIDDLEWARE"]` Django setting. The app patches this method during `AppConfig.ready()` to ensure configured Graphene middleware is properly loaded.

## How do I enable GraphQL query logging?

Set `query_logging_enabled` to `True` in your `PLUGINS_CONFIG`:

```python
PLUGINS_CONFIG = {
    "nautobot_graphql_observability": {
        "query_logging_enabled": True,
    }
}
```

Optionally enable `log_query_body` and `log_query_variables` to include the query text and variables in each log entry. See [Query Logging](app_use_cases.md#query-logging) for details on routing logs to external systems.

## Why aren't my query logs appearing?

The logging middleware uses a dedicated logger (`nautobot_graphql_observability.graphql_query_log`) that writes to stderr by default. If you have a custom Django `LOGGING` configuration that suppresses loggers not explicitly listed, you may need to add an entry for this logger. See [Routing Logs to External Systems](app_use_cases.md#routing-logs-to-external-systems).

## Can I use metrics and logging independently?

Yes. The two middlewares are independent:

- Set `graphql_metrics_enabled: True` and `query_logging_enabled: False` for metrics only.
- Set `graphql_metrics_enabled: False` and `query_logging_enabled: True` for logging only.
- Enable both for full observability.

## Do Celery workers emit structured JSON logs?

Not by default. Even though Celery workers load the same `nautobot_config.py` as the web process, Celery overrides the Python logging configuration after Django's setup runs — both in the main worker process and in each prefork child process. As a result, all Celery log output uses Celery's own plain-text format (`[timestamp: LEVEL/ProcessName] message`) regardless of what structlog configured.

This does **not** affect the GraphQL metrics or query logging features of this app, which only run in the web process during HTTP request handling.

If you want Celery workers to also emit structlog JSON (e.g. for log aggregation pipelines), see [Celery Workers and Structured JSON Logging](../admin/install.md#celery-workers-and-structured-json-logging) in the installation guide.

## Can I use this app without Nautobot?

The `PrometheusMiddleware` and `GraphQLQueryLoggingMiddleware` classes are standard Graphene middlewares. While this Nautobot app handles the automatic setup and configuration, the middlewares themselves could be used in any Graphene-based project by manually adding them to your `GRAPHENE["MIDDLEWARE"]` setting.
