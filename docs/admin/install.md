# Installing the App in Nautobot

Here you will find detailed instructions on how to **install** and **configure** the App within your Nautobot environment.

## Prerequisites

- The app is compatible with Nautobot 3.0.0 and higher.
- Databases supported: PostgreSQL, MySQL

!!! note
    Please check the [dedicated page](compatibility_matrix.md) for a full compatibility matrix and the deprecation policy.

## Install Guide

!!! note
    Apps can be installed from the [Python Package Index](https://pypi.org/) or locally. See the [Nautobot documentation](https://docs.nautobot.com/projects/core/en/stable/user-guide/administration/installation/app-install/) for more details. The pip package name for this app is [`nautobot-graphql-observability`](https://pypi.org/project/nautobot-graphql-observability/).

The app is available as a Python package via PyPI and can be installed with `pip`:

```shell
pip install nautobot-graphql-observability
```

To ensure the app is automatically re-installed during future upgrades, create a file named `local_requirements.txt` (if not already existing) in the Nautobot root directory (alongside `requirements.txt`) and list the `nautobot-graphql-observability` package:

```shell
echo nautobot-graphql-observability >> local_requirements.txt
```

Once installed, the app needs to be enabled in your Nautobot configuration. The following block of code below shows the additional configuration required to be added to your `nautobot_config.py` file:

- Append `"nautobot_graphql_observability"` to the `PLUGINS` list.
- Optionally append the `"nautobot_graphql_observability"` dictionary to the `PLUGINS_CONFIG` dictionary to override any defaults.

```python
# In your nautobot_config.py
PLUGINS = ["nautobot_graphql_observability"]

PLUGINS_CONFIG = {
    "nautobot_graphql_observability": {
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

## Celery Workers and Structured JSON Logging

!!! note
    This section is only relevant if you use Nautobot's structlog JSON logging (configured via `setup_structlog_logging()`) **and** you want Celery worker logs to also emit JSON — for example to feed them into a log aggregation pipeline (ELK, Loki, etc.).

### Why Celery workers do not use structlog by default

Although Celery workers load the same `nautobot_config.py` as the web process — and therefore run `setup_structlog_logging()` — Celery **overrides the Python logging configuration** after Django's setup runs. This happens in two places:

1. **Main worker process** — Celery calls its own `setup_logging` routine, which replaces the root logger's handler and formatter with Celery's `[timestamp: LEVEL/ProcessName]` format.
2. **Prefork child processes** — Each forked task-runner process re-initialises the `celery.task` logger with its own handler (`propagate=False`), bypassing the root logger entirely.

The result is that all Celery log output — including Django application-level messages emitted inside tasks — uses Celery's plain-text format regardless of what structlog configured.

### Enabling JSON logging for Celery workers

To make Celery workers emit structlog JSON, add the following three additions to your `nautobot_config.py`.  They work together: the first stops the main-process hijack, the second takes ownership of the `setup_logging` event so Celery never applies its own format, and the third re-applies structlog in each forked child and clears the task logger's private handler.

```python
# nautobot_config.py

# 1. Prevent Celery from hijacking the root logger in the main worker process.
CELERY_WORKER_HIJACK_ROOT_LOGGER = False

# 2 & 3. Re-apply structlog in both the main process and each prefork child.
from celery.signals import setup_logging, worker_process_init


def _apply_structlog():
    setup_structlog_logging(
        LOGGING,
        INSTALLED_APPS,
        MIDDLEWARE,
        log_level=LOG_LEVEL,
        plain_format=DEBUG,
    )


@setup_logging.connect
def _setup_logging_main_process(**kwargs):
    _apply_structlog()


@worker_process_init.connect
def _setup_structlog_in_worker(**kwargs):
    import logging

    _apply_structlog()
    # Celery registers its own handler on celery.task (propagate=False) after
    # the fork. Clear it so task log records reach the root logger and get
    # formatted by structlog.
    celery_task_log = logging.getLogger("celery.task")
    celery_task_log.handlers.clear()
    celery_task_log.propagate = True
```

With these additions, a Celery job execution produces output like:

```json
{"event": "Task nautobot.extras.jobs.run_job[...] received", "level": "info", "logger": "celery.worker.strategy", "timestamp": "2026-02-19T09:46:05.850656Z"}
{"event": "Running job", "level": "info", "logger": "nautobot.core.jobs.groups", "timestamp": "2026-02-19T09:46:05.862450Z"}
{"event": "Job completed", "level": "success", "logger": "nautobot.core.jobs.groups", "timestamp": "2026-02-19T09:46:05.865676Z"}
```

!!! warning
    These changes have no effect on the GraphQL metrics or query logging features of this app. The Graphene middlewares only run during HTTP request handling (in the web process); Celery workers do not handle GraphQL requests.
