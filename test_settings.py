"""Minimal Django settings for running the test suite standalone (no Nautobot required)."""

SECRET_KEY = "test-secret-key-not-for-production"  # noqa: S105

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "graphene_django_observability",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

GRAPHENE = {
    "MIDDLEWARE": [],
}

# Silence Django's system check for DEFAULT_AUTO_FIELD
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
