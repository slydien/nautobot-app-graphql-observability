# External Interactions

This document describes external dependencies and prerequisites for this App to operate.

## External System Integrations

### From Other Systems to the App

#### Prometheus Scraping

The app registers its metrics in the default `prometheus_client` registry. They are served by the built-in `/metrics/` endpoint (provided by `graphene_django_observability.urls`).

- **URL**: `/metrics/`
- **Format**: Standard Prometheus text exposition format
- **Authentication**: None required by default

Add this to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: "django-graphql"
    metrics_path: "/metrics/"
    scrape_interval: 15s
    static_configs:
      - targets: ["your-django-app:8080"]
```

### Grafana Dashboards

The repository includes pre-built Grafana dashboard templates in the `docs/grafana/dashboards/` directory:

| Dashboard | File | Description |
| --------- | ---- | ----------- |
| GraphQL Performance | `graphql-performance.json` | Query duration percentiles, request rates, error rates, depth and complexity distributions. |
| System Health | `system-health.json` | Process-level metrics (CPU, memory, open file descriptors). |
| Database and Cache | `database-and-cache.json` | Database connection pool and cache hit/miss metrics. |

To import a dashboard:

1. Open Grafana and navigate to **Dashboards > Import**.
2. Upload the JSON file or paste its contents.
3. Select your Prometheus data source.
4. Save the dashboard.

### Alerting Rules

An example Alertmanager rule file is provided at `docs/grafana/alerts/graphql-alert-rules.yaml`. It includes rules for:

- High GraphQL error rates
- Slow query duration thresholds
- High query depth/complexity

Import these rules into your Prometheus or Grafana alerting configuration.

### Query Log Integration

The logging middleware emits structured log entries to the `graphene_django_observability.graphql_query_log` Python logger. These logs can be forwarded to external systems via Django's `LOGGING` configuration:

| Target | Handler Class | Notes |
| ------ | ------------- | ----- |
| File | `logging.FileHandler` | Write to a dedicated log file for rotation and archival. |
| Syslog | `logging.handlers.SysLogHandler` | Forward to a centralized syslog server. |
| HTTP | `logging.handlers.HTTPHandler` | Send log entries to an HTTP endpoint (e.g., Logstash, Splunk HEC). |
| Console | `logging.StreamHandler` | Default behavior — writes to stderr. |

See [Query Logging](app_use_cases.md#query-logging) for configuration examples.

## REST API Endpoints

This app does not add any REST API endpoints. All metrics are available at the `/metrics/` endpoint configured in your URL configuration.
