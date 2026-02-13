# Installing the App in Nautobot

Here you will find detailed instructions on how to **install** and **configure** the App within your Nautobot environment.

## Prerequisites

- The app is compatible with Nautobot 3.0.0 and higher.
- Databases supported: PostgreSQL, MySQL

!!! note
    Please check the [dedicated page](compatibility_matrix.md) for a full compatibility matrix and the deprecation policy.

## Install Guide

!!! note
    Apps can be installed from the [Python Package Index](https://pypi.org/) or locally. See the [Nautobot documentation](https://docs.nautobot.com/projects/core/en/stable/user-guide/administration/installation/app-install/) for more details. The pip package name for this app is [`nautobot-app-graphql-observability`](https://pypi.org/project/nautobot-app-graphql-observability/).

The app is available as a Python package via PyPI and can be installed with `pip`:

```shell
pip install nautobot-app-graphql-observability
```

To ensure the app is automatically re-installed during future upgrades, create a file named `local_requirements.txt` (if not already existing) in the Nautobot root directory (alongside `requirements.txt`) and list the `nautobot-app-graphql-observability` package:

```shell
echo nautobot-app-graphql-observability >> local_requirements.txt
```

Once installed, the app needs to be enabled in your Nautobot configuration. The following block of code below shows the additional configuration required to be added to your `nautobot_config.py` file:

- Append `"nautobot_app_graphql_observability"` to the `PLUGINS` list.
- Optionally append the `"nautobot_app_graphql_observability"` dictionary to the `PLUGINS_CONFIG` dictionary to override any defaults.

```python
# In your nautobot_config.py
PLUGINS = ["nautobot_app_graphql_observability"]

PLUGINS_CONFIG = {
    "nautobot_app_graphql_observability": {
        # Prometheus metrics settings
        "graphql_metrics_enabled": True,
        "track_query_depth": True,
        "track_query_complexity": True,
        "track_field_resolution": False,
        "track_per_user": True,
        # Query logging settings
        "query_logging_enabled": False,
        "log_query_body": False,
        "log_query_variables": False,
    }
}
```

!!! info "No GRAPHENE middleware configuration needed"
    Unlike typical Graphene middleware, you do **not** need to manually configure `GRAPHENE["MIDDLEWARE"]` in your settings. The app's `ready()` method automatically monkey-patches Nautobot's `GraphQLDRFAPIView.init_graphql()` to load middleware from `GRAPHENE["MIDDLEWARE"]`. This works around a bug in Nautobot 3.x where the view does not load middleware when `self.middleware` is `None`.

Once the Nautobot configuration is updated, run the Post Upgrade command (`nautobot-server post_upgrade`) to run migrations and clear any cache:

```shell
nautobot-server post_upgrade
```

Then restart (if necessary) the Nautobot services which may include:

- Nautobot
- Nautobot Workers
- Nautobot Scheduler

```shell
sudo systemctl restart nautobot nautobot-worker nautobot-scheduler
```

## App Configuration

The app behavior can be controlled with the following list of settings:

### Prometheus Metrics Settings

| Key | Type | Default | Description |
| --- | ---- | ------- | ----------- |
| `graphql_metrics_enabled` | `bool` | `True` | Enable or disable all metrics collection. When `False`, the Prometheus middleware is a no-op. |
| `track_query_depth` | `bool` | `True` | Record a histogram of GraphQL query nesting depth. |
| `track_query_complexity` | `bool` | `True` | Record a histogram of GraphQL query complexity (total field count). |
| `track_field_resolution` | `bool` | `False` | Record per-field resolver duration. **Warning:** enabling this adds significant overhead for queries with many fields. |
| `track_per_user` | `bool` | `True` | Record a per-user request counter using the authenticated username. |

### Query Logging Settings

| Key | Type | Default | Description |
| --- | ---- | ------- | ----------- |
| `query_logging_enabled` | `bool` | `False` | Enable or disable GraphQL query logging. When `False`, the logging middleware is a no-op. |
| `log_query_body` | `bool` | `False` | Include the full GraphQL query text in log entries. |
| `log_query_variables` | `bool` | `False` | Include the GraphQL query variables in log entries. **Warning:** may log sensitive data. |

## Multi-Process Deployments

If you run Nautobot with multiple worker processes (e.g. via Gunicorn), you must set the `PROMETHEUS_MULTIPROC_DIR` environment variable to a writable directory so that `prometheus_client` can aggregate metrics across processes:

```shell
export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
```

Nautobot's default `/metrics/` endpoint will automatically aggregate metrics from all worker processes when this variable is set.
