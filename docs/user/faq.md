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

## Can I use this app without Nautobot?

The `PrometheusMiddleware` class is a standard Graphene middleware. While this Nautobot app handles the automatic setup and configuration, the middleware itself could be used in any Graphene-based project by manually adding it to your `GRAPHENE["MIDDLEWARE"]` setting.
