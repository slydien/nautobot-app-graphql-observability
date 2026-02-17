"""App declaration for nautobot_graphql_observability."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig

__version__ = metadata.version(__name__)


class NautobotAppGraphqlObservabilityConfig(NautobotAppConfig):
    """App configuration for the nautobot_graphql_observability app."""

    name = "nautobot_graphql_observability"
    verbose_name = "Nautobot App GraphQL Observability"
    version = __version__
    author = "Lydien SANDANASAMY"
    description = "Nautobot App GraphQL Observability."
    base_url = "nautobot-graphql-observability"
    required_settings = []
    default_settings = {
        "graphql_metrics_enabled": True,
        "track_query_depth": True,
        "track_query_complexity": True,
        "track_field_resolution": False,
        "track_per_user": True,
        "query_logging_enabled": False,
        "log_query_body": False,
        "log_query_variables": False,
    }
    middleware = [
        "nautobot_graphql_observability.django_middleware.GraphQLObservabilityDjangoMiddleware",
    ]
    docs_view_name = "plugins:nautobot_graphql_observability:docs"
    searchable_models = []

    def ready(self):
        """Patch Nautobot's GraphQLDRFAPIView to load Graphene middleware from settings.

        Nautobot's ``GraphQLDRFAPIView.init_graphql()`` does not load middleware
        from ``GRAPHENE["MIDDLEWARE"]`` when ``self.middleware`` is ``None`` (the
        default).  This is a known limitation of the DRF-based GraphQL view —
        the standard ``graphene_django.views.GraphQLView`` (used by the GraphiQL
        UI at ``/graphql/``) loads middleware correctly.

        No official extension point (``override_views``, etc.) can replace this
        patch because the ``graphql-api`` URL is registered without a namespace.
        Request duration and query logging are handled by
        :class:`~nautobot_graphql_observability.django_middleware.GraphQLObservabilityDjangoMiddleware`,
        which is registered via :attr:`middleware` (the official Nautobot mechanism).
        """
        super().ready()
        self._patch_init_graphql()

    @staticmethod
    def _patch_init_graphql():
        """Patch ``GraphQLDRFAPIView.init_graphql`` to load ``GRAPHENE["MIDDLEWARE"]``."""
        from nautobot.core.api.views import GraphQLDRFAPIView  # pylint: disable=import-outside-toplevel

        original_init_graphql = GraphQLDRFAPIView.init_graphql

        def patched_init_graphql(view_self):
            original_init_graphql(view_self)
            if view_self.middleware is None:
                from graphene_django.settings import graphene_settings  # pylint: disable=import-outside-toplevel
                from graphene_django.views import instantiate_middleware  # pylint: disable=import-outside-toplevel

                if graphene_settings.MIDDLEWARE:
                    view_self.middleware = list(instantiate_middleware(graphene_settings.MIDDLEWARE))

        GraphQLDRFAPIView.init_graphql = patched_init_graphql


config = NautobotAppGraphqlObservabilityConfig  # pylint:disable=invalid-name
