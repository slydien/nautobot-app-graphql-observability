# Uninstall the App from Nautobot

Here you will find any steps necessary to cleanly remove the App from your Nautobot environment.

## Remove App Configuration

This app has no database models, so there are no migrations to roll back. Simply remove the configuration from `nautobot_config.py`:

1. Remove `"nautobot_app_graphql_observability"` from the `PLUGINS` list.
2. Remove the `"nautobot_app_graphql_observability"` entry from `PLUGINS_CONFIG` (if present).

## Uninstall the Package

```bash
pip uninstall nautobot-app-graphql-observability
```

## Restart Services

Restart Nautobot services to apply the changes:

```shell
sudo systemctl restart nautobot nautobot-worker nautobot-scheduler
```
