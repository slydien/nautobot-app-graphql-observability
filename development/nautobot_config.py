"""Nautobot development configuration file."""

import os
import sys

import structlog
from nautobot.core.settings import *  # noqa: F403  # pylint: disable=wildcard-import,unused-wildcard-import
from nautobot.core.settings_funcs import is_truthy, setup_structlog_logging

#
# Debug
#

DEBUG = is_truthy(os.getenv("NAUTOBOT_DEBUG", "false"))
_TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

if DEBUG and not _TESTING:
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda _request: True}

    if "debug_toolbar" not in INSTALLED_APPS:  # noqa: F405
        INSTALLED_APPS.append("debug_toolbar")  # noqa: F405
    if "debug_toolbar.middleware.DebugToolbarMiddleware" not in MIDDLEWARE:  # noqa: F405
        MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

#
# Prometheus scrape fix
#
# Nautobot's NautobotMetricsView uses AcceptHeaderVersioning which rejects
# Prometheus's "Accept: text/plain;version=0.0.4" header with HTTP 406.
# This middleware rewrites the Accept header on /metrics/ to plain "text/plain".
#


class FixPrometheusAcceptMiddleware:
    """Rewrite Accept header on /metrics/ so Prometheus can scrape."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/metrics/":
            request.META["HTTP_ACCEPT"] = "text/plain"
        return self.get_response(request)


MIDDLEWARE.insert(0, f"{__name__}.FixPrometheusAcceptMiddleware")  # noqa: F405

#
# Misc. settings
#

ALLOWED_HOSTS = os.getenv("NAUTOBOT_ALLOWED_HOSTS", "").split(" ")
SECRET_KEY = os.getenv("NAUTOBOT_SECRET_KEY", "")

#
# Database
#

nautobot_db_engine = os.getenv("NAUTOBOT_DB_ENGINE", "django.db.backends.postgresql")
default_db_settings = {
    "django.db.backends.postgresql": {
        "NAUTOBOT_DB_PORT": "5432",
    },
    "django.db.backends.mysql": {
        "NAUTOBOT_DB_PORT": "3306",
    },
}
DATABASES = {
    "default": {
        "NAME": os.getenv("NAUTOBOT_DB_NAME", "nautobot"),  # Database name
        "USER": os.getenv("NAUTOBOT_DB_USER", ""),  # Database username
        "PASSWORD": os.getenv("NAUTOBOT_DB_PASSWORD", ""),  # Database password
        "HOST": os.getenv("NAUTOBOT_DB_HOST", "localhost"),  # Database server
        "PORT": os.getenv(
            "NAUTOBOT_DB_PORT", default_db_settings[nautobot_db_engine]["NAUTOBOT_DB_PORT"]
        ),  # Database port, default to postgres
        "CONN_MAX_AGE": int(os.getenv("NAUTOBOT_DB_TIMEOUT", "300")),  # Database timeout
        "ENGINE": nautobot_db_engine,
    }
}

# Ensure proper Unicode handling for MySQL
if DATABASES["default"]["ENGINE"] == "django.db.backends.mysql":
    DATABASES["default"]["OPTIONS"] = {"charset": "utf8mb4"}

#
# Redis
#

# The django-redis cache is used to establish concurrent locks using Redis.
# Inherited from nautobot.core.settings
# CACHES = {....}

#
# Celery settings are not defined here because they can be overloaded with
# environment variables. By default they use `CACHES["default"]["LOCATION"]`.
#

# Prevent Celery from hijacking the root logger so that structlog's JSON
# formatter (configured below) stays in effect for all log records emitted
# by Celery workers.
CELERY_WORKER_HIJACK_ROOT_LOGGER = False

# Take full ownership of logging in Celery workers so that structlog's JSON
# formatter is used everywhere — both in the main process and in each prefork
# child process.
#
# • setup_logging  – fires in the main worker process; returning without error
#   tells Celery we handled it, so it skips its own root-logger configuration.
# • worker_process_init – fires in each forked child; we re-apply structlog
#   and then clear the celery.task logger's own handler (which Celery adds
#   after the fork and which has propagate=False, bypassing the root logger).
from celery.signals import setup_logging, worker_process_init  # noqa: E402


def _apply_structlog():
    """(Re-)configure structlog logging — safe to call multiple times."""
    setup_structlog_logging(
        LOGGING,
        INSTALLED_APPS,  # noqa: F405
        MIDDLEWARE,  # noqa: F405
        log_level=LOG_LEVEL,
        plain_format=DEBUG,
    )
    if "formatters" in LOGGING:
        _fmt = LOGGING["formatters"]["default_formatter"]
        if structlog.stdlib.ExtraAdder not in [type(p) for p in _fmt.get("foreign_pre_chain", ())]:
            _fmt["foreign_pre_chain"] = (*_fmt["foreign_pre_chain"], structlog.stdlib.ExtraAdder())


@setup_logging.connect
def _setup_logging_main_process(**kwargs):
    _apply_structlog()


@worker_process_init.connect
def _setup_structlog_in_worker(**kwargs):
    import logging  # noqa: PLC0415

    _apply_structlog()
    # Celery registers its own handler on celery.task (with propagate=False)
    # after the fork.  Clear it so task log records flow through the root
    # logger and get formatted by structlog.
    celery_task_log = logging.getLogger("celery.task")
    celery_task_log.handlers.clear()
    celery_task_log.propagate = True

#
# Logging
#

LOG_LEVEL = "DEBUG" if DEBUG else "INFO"

# All three loggers use the single default_handler wired by setup_structlog_logging.
# nautobot_graphql_observability.graphql_query_log must be listed here explicitly:
# _get_logger() in logging_middleware.py unconditionally sets propagate=False, so
# the record never reaches the root logger — a direct handler is required.
LOGGING = {
    "loggers": {
        # django and nautobot are already defined in nautobot.core.settings and
        # will be picked up automatically by setup_structlog_logging.
        #
        # django.request is NOT in the base settings; list it here so it is not
        # silenced by disable_existing_loggers=True if Django created the logger
        # before dictConfig runs.
        "django.request": {"level": "INFO"},
        # Must be listed directly: _get_logger() in logging_middleware.py sets
        # propagate=False unconditionally, so the record never reaches the root
        # logger and needs a handler attached to this exact logger name.
        "nautobot_graphql_observability.graphql_query_log": {"level": "INFO"},
    },
}

# Configures structlog + overwrites LOGGING formatters/handlers/root in-place.
# plain_format=True → ConsoleRenderer (human-readable) in DEBUG mode.
# plain_format=False → JSONRenderer in production mode.
# Test mode (sys.argv contains "test") is handled internally: all loggers → NullHandler.
setup_structlog_logging(
    LOGGING,
    INSTALLED_APPS,  # noqa: F405
    MIDDLEWARE,  # noqa: F405
    log_level=LOG_LEVEL,
    plain_format=DEBUG,
)

# setup_structlog_logging overwrites formatters; append ExtraAdder here so that
# fields passed via logging.extra() (operation_type, operation_name, user, …)
# are promoted to top-level JSON keys instead of being buried in the event string.
# In test mode setup_structlog_logging returns before creating formatters, so guard.
if "formatters" in LOGGING:
    _fmt = LOGGING["formatters"]["default_formatter"]
    _fmt["foreign_pre_chain"] = (*_fmt["foreign_pre_chain"], structlog.stdlib.ExtraAdder())

#
# Apps
#

# Enable installed Apps. Add the name of each App to the list.
PLUGINS = ["nautobot_graphql_observability"]

# Apps configuration settings. These settings are used by various Apps that the user may have installed.
# Each key in the dictionary is the name of an installed App and its value is a dictionary of settings.
PLUGINS_CONFIG = {
    "nautobot_graphql_observability": {
        "graphql_metrics_enabled": True,
        "track_query_depth": True,
        "track_query_complexity": True,
        "track_field_resolution": False,
        "track_per_user": True,
        "query_logging_enabled": True,
        "log_query_body": True,
        "log_query_variables": False,
    },
}

# Graphene middleware for GraphQL query logging and Prometheus metrics
GRAPHENE["MIDDLEWARE"] = [  # noqa: F405
    "nautobot_graphql_observability.logging_middleware.GraphQLQueryLoggingMiddleware",
    "nautobot_graphql_observability.middleware.PrometheusMiddleware",
]
