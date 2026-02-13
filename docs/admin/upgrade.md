# Upgrading the App

Here you will find any steps necessary to upgrade the App in your Nautobot environment.

## Upgrade Guide

This app has no database models and therefore requires no database migrations. To upgrade:

1. Update the package:

    ```shell
    pip install --upgrade nautobot-app-prometheus-graphql
    ```

2. Run `nautobot-server post_upgrade` to clear caches and collect static files:

    ```shell
    nautobot-server post_upgrade
    ```

3. Restart Nautobot services:

    ```shell
    sudo systemctl restart nautobot nautobot-worker nautobot-scheduler
    ```

4. Review the [release notes](release_notes/index.md) for any new configuration options added in the new version.
