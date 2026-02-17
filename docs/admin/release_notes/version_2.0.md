# v2.0 Release Notes

This document describes all new features and changes in the release `2.0`. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Package renamed from `nautobot-app-graphql-observability` to `nautobot-graphql-observability`.
- Refactored to use official Nautobot extension points instead of monkey patches where possible.
- Added Django HTTP middleware for accurate request timing on both GraphQL endpoints.

## [v2.0.0] - 2026

### Breaking Changes

- **Package renamed**: distribution name changed from `nautobot-app-graphql-observability` to `nautobot-graphql-observability`.
- **Module renamed**: Python module changed from `nautobot_app_graphql_observability` to `nautobot_graphql_observability`.
- Update all references in `nautobot_config.py` (`PLUGINS`, `PLUGINS_CONFIG`, `GRAPHENE["MIDDLEWARE"]`).

### Added

- `GraphQLObservabilityDjangoMiddleware` — Django HTTP middleware registered via official `NautobotAppConfig.middleware` mechanism.
- Handles request timing and query logging for both `/api/graphql/` and `/graphql/` endpoints.
- `stash_meta_on_request` shared utility for DRF/WSGI request metadata stashing.

### Changed

- Replaced monkey patches on `GraphQLDRFAPIView.post()` and `CustomGraphQLView.dispatch()` with official Django middleware.
- Only one monkey patch remains: `_patch_init_graphql()` to work around Nautobot's middleware loading limitation (no official extension point available).

### Migration Guide

```python
# Before (nautobot_config.py)
PLUGINS = ["nautobot_app_graphql_observability"]
PLUGINS_CONFIG = {"nautobot_app_graphql_observability": { ... }}

# After
PLUGINS = ["nautobot_graphql_observability"]
PLUGINS_CONFIG = {"nautobot_graphql_observability": { ... }}
```

```bash
pip uninstall nautobot-app-graphql-observability
pip install nautobot-graphql-observability
```
