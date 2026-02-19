# Compatibility Matrix

| graphene-django-observability | Python | Django | graphene-django |
|-------------------------------|--------|--------|-----------------|
| 1.x                           | 3.10, 3.11, 3.12, 3.13 | 3.2+ | 3.0+ |

## Deprecation Policy

- Minor releases (`1.x`) may add new settings with backwards-compatible defaults.
- Major releases may remove deprecated settings or change metric label schemas.
- Dropped Python or Django versions are announced at least one minor release in advance.
