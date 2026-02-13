"""Graphene middleware for exporting Prometheus metrics from GraphQL queries."""

import time

from graphql import GraphQLResolveInfo
from graphql.language.ast import FieldNode

from nautobot_app_prometheus_graphql.metrics import (
    graphql_errors_total,
    graphql_field_resolution_duration_seconds,
    graphql_query_complexity,
    graphql_query_depth,
    graphql_request_duration_seconds,
    graphql_requests_by_user_total,
    graphql_requests_total,
)
from nautobot_app_prometheus_graphql.utils import (
    calculate_query_complexity,
    calculate_query_depth,
)


def _get_app_settings():
    """Load the app's plugin settings from Django config.

    Returns:
        dict: The plugin settings, or an empty dict if not found.
    """
    from django.conf import settings  # pylint: disable=import-outside-toplevel

    return getattr(settings, "PLUGINS_CONFIG", {}).get("nautobot_app_prometheus_graphql", {})


class PrometheusMiddleware:  # pylint: disable=too-few-public-methods
    """Graphene middleware that instruments GraphQL resolvers with Prometheus metrics.

    Records basic metrics (request count, duration, errors) for all queries at
    the root resolver level. Optionally records advanced metrics based on app
    configuration:

    - ``track_query_depth``: Record query nesting depth histogram.
    - ``track_query_complexity``: Record query field count histogram.
    - ``track_field_resolution``: Record per-field resolver duration histogram.
    - ``track_per_user``: Record per-user request counter.

    Usage in Django settings::

        GRAPHENE = {
            "MIDDLEWARE": [
                "nautobot_app_prometheus_graphql.middleware.PrometheusMiddleware",
            ]
        }
    """

    def resolve(self, next, root, info: GraphQLResolveInfo, **kwargs):  # pylint: disable=redefined-builtin
        """Intercept each field resolution and record metrics.

        Root-level resolutions (root is None) record basic and advanced metrics.
        Nested resolutions optionally record per-field duration when enabled.

        Args:
            next: Callable to continue the resolution chain.
            root: Parent resolved value. None for top-level fields.
            info: GraphQL resolve info containing operation metadata.
            **kwargs: Field arguments.

        Returns:
            The result of the resolver.
        """
        config = _get_app_settings()

        if root is not None:
            if config.get("track_field_resolution", False):
                return self._resolve_field_with_metrics(next, root, info, **kwargs)
            return next(root, info, **kwargs)

        operation_type = info.operation.operation.value
        operation_name = self._get_operation_name(info)
        start_time = time.monotonic()
        status = "success"

        try:
            result = next(root, info, **kwargs)
            return result
        except Exception as error:
            status = "error"
            graphql_errors_total.labels(
                operation_type=operation_type,
                operation_name=operation_name,
                error_type=type(error).__name__,
            ).inc()
            raise
        finally:
            duration = time.monotonic() - start_time

            graphql_requests_total.labels(
                operation_type=operation_type,
                operation_name=operation_name,
                status=status,
            ).inc()

            graphql_request_duration_seconds.labels(
                operation_type=operation_type,
                operation_name=operation_name,
            ).observe(duration)

            self._record_advanced_metrics(info, operation_name, config)

    @staticmethod
    def _resolve_field_with_metrics(next, root, info, **kwargs):  # pylint: disable=redefined-builtin
        """Resolve a nested field while recording per-field duration."""
        type_name = info.parent_type.name if info.parent_type else "Unknown"
        field_name = info.field_name

        start_time = time.monotonic()
        try:
            return next(root, info, **kwargs)
        finally:
            duration = time.monotonic() - start_time
            graphql_field_resolution_duration_seconds.labels(
                type_name=type_name,
                field_name=field_name,
            ).observe(duration)

    @staticmethod
    def _record_advanced_metrics(info, operation_name, config):
        """Record query depth, complexity, and per-user metrics if enabled."""
        if config.get("track_query_depth", True):
            depth = calculate_query_depth(info.operation.selection_set, info.fragments)
            graphql_query_depth.labels(operation_name=operation_name).observe(depth)

        if config.get("track_query_complexity", True):
            complexity = calculate_query_complexity(info.operation.selection_set, info.fragments)
            graphql_query_complexity.labels(operation_name=operation_name).observe(complexity)

        if config.get("track_per_user", True):
            user = "anonymous"
            request = info.context
            if hasattr(request, "user") and hasattr(request.user, "is_authenticated"):
                if request.user.is_authenticated:
                    user = request.user.username
            graphql_requests_by_user_total.labels(
                user=user,
                operation_type=info.operation.operation.value,
                operation_name=operation_name,
            ).inc()

    @staticmethod
    def _get_operation_name(info: GraphQLResolveInfo) -> str:
        """Extract the operation name from the GraphQL query.

        Uses the explicit operation name if provided, otherwise falls back
        to the sorted, comma-joined root field names (e.g. "devices,locations").
        """
        if info.operation.name:
            return info.operation.name.value
        root_fields = []
        if info.operation.selection_set:
            for selection in info.operation.selection_set.selections:
                if isinstance(selection, FieldNode):
                    root_fields.append(selection.name.value)
        return ",".join(sorted(root_fields)) if root_fields else "anonymous"
