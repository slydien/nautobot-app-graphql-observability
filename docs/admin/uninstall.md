# Uninstalling

```shell
pip uninstall graphene-django-observability
```

Then remove the following from your `settings.py`:

- `"graphene_django_observability"` from `INSTALLED_APPS`
- `"graphene_django_observability.django_middleware.GraphQLObservabilityDjangoMiddleware"` from `MIDDLEWARE`
- The Graphene middlewares from `GRAPHENE["MIDDLEWARE"]`
- The `GRAPHENE_OBSERVABILITY` dict (if present)

And remove the URL pattern from `urls.py` (if you added it).

This library has no database migrations, so no data cleanup is required.
