"""Django urlpatterns declaration for nautobot_app_prometheus_graphql app."""

from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView
from nautobot.apps.urls import NautobotUIViewSetRouter

app_name = "nautobot_app_prometheus_graphql"
router = NautobotUIViewSetRouter()

urlpatterns = [
    path("docs/", RedirectView.as_view(url=static("nautobot_app_prometheus_graphql/docs/index.html")), name="docs"),
]

urlpatterns += router.urls
