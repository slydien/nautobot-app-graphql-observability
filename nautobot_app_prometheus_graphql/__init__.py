"""App declaration for nautobot_app_prometheus_graphql."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig

__version__ = metadata.version(__name__)


class NautobotAppPrometheusGraphqlConfig(NautobotAppConfig):
    """App configuration for the nautobot_app_prometheus_graphql app."""

    name = "nautobot_app_prometheus_graphql"
    verbose_name = "Nautobot App Prometheus Graphql"
    version = __version__
    author = "Lydien SANDANASAMY"
    description = "Nautobot App Prometheus Graphql."
    base_url = "nautobot-app-prometheus-graphql"
    required_settings = []
    default_settings = {
        "graphql_metrics_enabled": True,
        "track_query_depth": True,
        "track_query_complexity": True,
        "track_field_resolution": False,
        "track_per_user": True,
    }
    docs_view_name = "plugins:nautobot_app_prometheus_graphql:docs"
    searchable_models = []

    def ready(self):
        """Patch Nautobot's GraphQLDRFAPIView to load Graphene middleware from settings.

        Nautobot's GraphQLDRFAPIView.init_graphql() does not load middleware from
        GRAPHENE["MIDDLEWARE"] when self.middleware is None (the default). This patch
        ensures that middleware configured in Django settings is properly loaded.
        """
        super().ready()
        self._patch_graphql_view_middleware()

    @staticmethod
    def _patch_graphql_view_middleware():
        """Monkey-patch GraphQLDRFAPIView.init_graphql to load middleware from settings."""
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


config = NautobotAppPrometheusGraphqlConfig  # pylint:disable=invalid-name
