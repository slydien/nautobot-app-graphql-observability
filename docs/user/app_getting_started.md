# Getting Started with the App

This document provides a step-by-step tutorial on how to get the App going and how to use it.

## Install the App

To install the App, please follow the instructions detailed in the [Installation Guide](../admin/install.md).

## First Steps with the App

Once the app is installed and Nautobot has been restarted, metrics collection begins automatically. Here is how to verify it is working:

### 1. Send a GraphQL Query

Use the Nautobot GraphQL API to run a query. You can use the GraphiQL interface at `/graphql/` or send a request via `curl`:

```shell
curl -X POST http://localhost:8080/api/graphql/ \
  -H "Authorization: Token $NAUTOBOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "query GetDevices { devices { name } }"}'
```

### 2. Check the Metrics Endpoint

Browse to or query Nautobot's default Prometheus metrics endpoint:

```shell
curl http://localhost:8080/metrics/
```

You should see output similar to:

```
# HELP graphql_requests_total Total number of GraphQL requests
# TYPE graphql_requests_total counter
graphql_requests_total{operation_name="GetDevices",operation_type="query",status="success"} 1.0

# HELP graphql_request_duration_seconds Duration of GraphQL request execution in seconds
# TYPE graphql_request_duration_seconds histogram
graphql_request_duration_seconds_bucket{le="0.01",operation_name="GetDevices",operation_type="query"} 0.0
...

# HELP graphql_query_depth Depth of GraphQL queries
# TYPE graphql_query_depth histogram
graphql_query_depth_bucket{le="1.0",operation_name="GetDevices"} 1.0
...
```

### 3. Configure Prometheus Scraping

Add a scrape target in your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "nautobot-graphql"
    metrics_path: "/metrics/"
    static_configs:
      - targets: ["nautobot:8080"]
```

### 4. Enable Query Logging (Optional)

To also log every GraphQL query, enable logging in your `nautobot_config.py`:

```python
PLUGINS_CONFIG = {
    "nautobot_graphql_observability": {
        "query_logging_enabled": True,
        "log_query_body": True,
    }
}
```

After restarting Nautobot, send a GraphQL query and check the Nautobot logs. With [structlog JSON logging](app_use_cases.md#structured-json-logging-with-structlog) configured, each entry looks like:

```json
{
  "event": "graphql_query",
  "level": "info",
  "logger": "nautobot_graphql_observability.graphql_query_log",
  "timestamp": "2026-02-19T14:32:05.123456Z",
  "operation_type": "query",
  "operation_name": "GetDevices",
  "user": "admin",
  "duration_ms": 42.3,
  "status": "success",
  "query": "query GetDevices { devices { name } }"
}
```

## What are the next steps?

- Review the [App Configuration](../admin/install.md#app-configuration) to tune which metrics and logging options are enabled.
- Set up Grafana dashboards using the provided [templates](external_interactions.md#grafana-dashboards).
- Route query logs to external systems — see [Query Logging](app_use_cases.md#query-logging).
- Check out the [Use Cases](app_use_cases.md) section for more examples.
