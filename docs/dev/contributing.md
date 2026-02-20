# Contributing

Contributions are very welcome!  Please open an issue or pull request on [GitHub](https://github.com/slydien/nautobot-app-graphql-observability).

## Guidelines

- **One change per PR.** Keep PRs focused.
- **Tests required.** All new code must be covered by unit tests.
- **Changelog entry required.** Every PR must include a changelog fragment (see below).
- **Docs updated.** Update the documentation if you add or change user-visible behaviour.

## Changelog Fragments

This project uses [towncrier](https://towncrier.readthedocs.io/) for changelog management.

Create a fragment file in the `changes/` directory named `<issue-number>.<type>.md`:

```
changes/
  123.added.md     ← new feature
  124.fixed.md     ← bug fix
  125.changed.md   ← behaviour change
  126.removed.md   ← removal
  127.security.md  ← security fix
  128.dependencies.md ← dependency update
  129.documentation.md ← docs-only change
  130.housekeeping.md  ← internal/CI change
```

The content of the file is the plain-text description of the change, e.g.:

```
Added `graphql_paths` setting to control which URL paths are instrumented.
```

## Branching

- Branch off `main` for all changes.
- Name your branch `<your-handle>/<short-description>`, e.g. `slydien/add-mutation-label`.

## Running the Full Check Suite

```shell
# Format check
ruff format --check .

# Lint
ruff check .

# Tests
python -m django test graphene_django_observability --settings=test_settings

# Docs build
mkdocs build --strict
```
