# Project: Graphene Middleware for Prometheus Metrics on Nautobot

## Project Context

### Objective

Create a Graphene middleware to export Prometheus metrics from Nautobot's GraphQL endpoint, without forking the Nautobot project, using the existing Django application system.

### Nautobot Architecture

Nautobot is a "Network Source of Truth" platform built on Django with a GraphQL implementation via `graphene-django` and `graphene-django-optimizer`.

## Analysis of GraphQL Implementation in Nautobot

### 1. GraphQL Technical Stack

**Libraries used:**

- `graphene-django`: GraphQL integration for Django
- `graphene-django-optimizer`: Query optimization (automatic prefetch_related/select_related)
- Standard GraphQL backend

**Endpoints:**

- `/graphql/` - GraphiQL interface for human exploration
- `/api/graphql/` - API endpoint for programmatic queries

### 2. GraphQL Code Structure

**GraphQL code location in Nautobot:**

```
nautobot/
├── core/
│   └── graphql/
│       ├── __init__.py          # Utility functions (execute_query, execute_saved_query)
│       ├── schema.py            # Dynamic GraphQL schema generation
│       ├── types.py             # Base types (OptimizedNautobotObjectType)
│       └── utils.py             # Utilities for resolver construction
├── circuits/
│   └── graphql/
│       └── types.py             # GraphQL types for circuits
├── dcim/
│   └── graphql/
│       ├── types.py             # GraphQL types for DCIM
│       └── mixins.py            # Mixins for GraphQL types
└── extras/
    └── api/
        └── views.py             # GraphQLView for REST API
```

**Key points identified:**

1. **GraphQL View**: Nautobot uses `graphene_django.views.GraphQLView` (visible in `nautobot/extras/api/views.py`)

2. **Custom types**: Types inherit from `OptimizedNautobotObjectType` which inherits from `graphene_django_optimizer.OptimizedDjangoObjectType`

3. **Dynamic schema**: The schema is dynamically generated via `nautobot.core.graphql.schema.generate_query_mixin()`

4. **Configuration**: The schema is defined in Django settings under `GRAPHENE['SCHEMA']`

### 3. Nautobot Plugin/App System

**App architecture:**

- Nautobot apps are standard Django applications with specific conventions
- Configuration via `NautobotAppConfig` (inherits from Django's `AppConfig`)
- Apps can define custom GraphQL types in `graphql/types.py`
- Apps are loaded at startup and integrated into the global GraphQL schema

**Key files in an app:**

```
nautobot_app_example/
├── __init__.py
├── graphql/
│   └── types.py              # Custom GraphQL types
├── middleware.py             # Custom Django middleware (NEW)
└── __init__.py               # NautobotAppConfig
```

## Possible Approaches for Prometheus Middleware

### Option 1: Generic Graphene Middleware (RECOMMENDED)

**Advantages:**

- Reusable on any Django project with Graphene
- Better maintainability
- Can be published as an independent Python package
- Easier to test in isolation

**Structure:**

```python
# graphene_prometheus_middleware.py
from prometheus_client import Counter, Histogram, Gauge
import time

class PrometheusMiddleware:
    """Graphene middleware for Prometheus metrics"""

    # Prometheus metrics
    graphql_requests_total = Counter(
        'graphql_requests_total',
        'Total GraphQL requests',
        ['operation_type', 'operation_name']
    )

    graphql_request_duration_seconds = Histogram(
        'graphql_request_duration_seconds',
        'GraphQL request duration',
        ['operation_type', 'operation_name']
    )

    graphql_errors_total = Counter(
        'graphql_errors_total',
        'Total GraphQL errors',
        ['operation_type', 'operation_name', 'error_type']
    )

    def resolve(self, next, root, info, **kwargs):
        """Graphene resolution hook"""
        # Extract query metadata
        operation_type = info.operation.operation
        operation_name = info.operation.name.value if info.operation.name else 'anonymous'

        # Start timer
        start_time = time.time()

        try:
            # Execute resolution
            result = next(root, info, **kwargs)

            # Increment success counter
            self.graphql_requests_total.labels(
                operation_type=operation_type,
                operation_name=operation_name
            ).inc()

            return result

        except Exception as e:
            # Increment error counter
            self.graphql_errors_total.labels(
                operation_type=operation_type,
                operation_name=operation_name,
                error_type=type(e).__name__
            ).inc()
            raise

        finally:
            # Record duration
            duration = time.time() - start_time
            self.graphql_request_duration_seconds.labels(
                operation_type=operation_type,
                operation_name=operation_name
            ).observe(duration)
```

**Installation in Nautobot:**

```python
# nautobot_config.py or settings.py
GRAPHENE = {
    'SCHEMA': 'nautobot.core.graphql.schema.schema',
    'MIDDLEWARE': [
        'nautobot_app_prometheus.middleware.PrometheusMiddleware',
    ]
}
```

### Option 2: Nautobot-Specific Middleware

**Advantages:**

- Direct access to Nautobot metadata
- Can include network-specific metrics
- Integration with Nautobot authentication systems

**Disadvantages:**

- Strong coupling with Nautobot
- Less reusable

### Option 3: GraphQLView Decorator (Alternative)

**Approach:**
Create a wrapper around `GraphQLView` to instrument at the Django view level rather than at the Graphene level.

**Advantages:**

- Captures HTTP metrics in addition to GraphQL metrics
- Easier to debug

**Disadvantages:**

- Less granularity on individual GraphQL operations
- Requires overriding the view in URLs

## Recommended Development Plan

### Phase 1: Basic Generic Graphene Middleware

**Step 1.1: Project structure**

```
nautobot-app-graphql-observability/
├── pyproject.toml
├── README.md
├── nautobot_graphql_prometheus/
│   ├── __init__.py
│   ├── middleware.py          # Graphene middleware
│   ├── metrics.py             # Prometheus metrics definitions
│   └── config.py              # Middleware configuration
└── tests/
    ├── __init__.py
    └── test_middleware.py
```

**Step 1.2: Metrics to implement**

**Basic metrics:**

1. `graphql_requests_total` - Total request counter

    - Labels: `operation_type` (query/mutation), `operation_name`, `status` (success/error)

2. `graphql_request_duration_seconds` - Duration histogram

    - Labels: `operation_type`, `operation_name`
    - Buckets: [0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]

3. `graphql_errors_total` - Error counter
    - Labels: `operation_type`, `operation_name`, `error_type`

**Advanced metrics (Phase 2):** 4. `graphql_field_resolution_duration_seconds` - Duration per field

- Labels: `type_name`, `field_name`

5. `graphql_query_depth` - Query depth

    - Labels: `operation_name`

6. `graphql_query_complexity` - Query complexity
    - Labels: `operation_name`

**Step 1.3: Middleware implementation**

```python
# nautobot_graphql_prometheus/middleware.py
from typing import Any, Optional
import time
from graphql import GraphQLResolveInfo
from prometheus_client import Counter, Histogram

from .metrics import (
    graphql_requests_total,
    graphql_request_duration_seconds,
    graphql_errors_total
)

class PrometheusMiddleware:
    """
    Graphene middleware to export Prometheus metrics.

    Compatible with Graphene 2.x and 3.x.

    Usage in Django settings:
        GRAPHENE = {
            'MIDDLEWARE': [
                'nautobot_graphql_prometheus.middleware.PrometheusMiddleware',
            ]
        }
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.track_field_resolution = self.config.get('track_field_resolution', False)
        self.track_query_complexity = self.config.get('track_query_complexity', False)

    def resolve(self, next, root, info: GraphQLResolveInfo, **kwargs):
        """
        Hook called for each field resolution.

        Args:
            next: Callable to continue the resolution chain
            root: Parent value
            info: Information about the GraphQL query
            **kwargs: Field arguments

        Returns:
            Resolution result
        """
        # Identify operation type
        operation = info.operation.operation  # 'query' or 'mutation'
        operation_name = self._get_operation_name(info)

        # For root field only (query start)
        if root is None:
            return self._resolve_with_metrics(next, root, info, operation, operation_name, **kwargs)

        # For nested fields
        return next(root, info, **kwargs)

    def _resolve_with_metrics(self, next, root, info, operation, operation_name, **kwargs):
        """Resolution with metrics capture."""
        start_time = time.time()
        status = 'success'
        error_type = None

        try:
            result = next(root, info, **kwargs)
            return result

        except Exception as error:
            status = 'error'
            error_type = type(error).__name__

            # Increment error counter
            graphql_errors_total.labels(
                operation_type=operation,
                operation_name=operation_name,
                error_type=error_type
            ).inc()

            raise

        finally:
            # Record duration
            duration = time.time() - start_time

            # Increment request counter
            graphql_requests_total.labels(
                operation_type=operation,
                operation_name=operation_name,
                status=status
            ).inc()

            # Record duration
            graphql_request_duration_seconds.labels(
                operation_type=operation,
                operation_name=operation_name
            ).observe(duration)

    @staticmethod
    def _get_operation_name(info: GraphQLResolveInfo) -> str:
        """Extract operation name."""
        if info.operation.name:
            return info.operation.name.value
        return 'anonymous'
```

**Step 1.4: Metrics definitions**

```python
# nautobot_graphql_prometheus/metrics.py
from prometheus_client import Counter, Histogram

# Prometheus metrics
graphql_requests_total = Counter(
    'graphql_requests_total',
    'Total number of GraphQL requests',
    ['operation_type', 'operation_name', 'status']
)

graphql_request_duration_seconds = Histogram(
    'graphql_request_duration_seconds',
    'Duration of GraphQL request execution in seconds',
    ['operation_type', 'operation_name'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

graphql_errors_total = Counter(
    'graphql_errors_total',
    'Total number of GraphQL errors',
    ['operation_type', 'operation_name', 'error_type']
)
```

### Phase 2: Integration with Nautobot App

**Step 2.1: Nautobot application structure**

```
nautobot-app-graphql-observability/
├── pyproject.toml
├── README.md
├── nautobot_app_graphql_observability/
│   ├── __init__.py              # NautobotAppConfig
│   ├── urls.py                  # /metrics endpoint
│   ├── middleware.py            # Import of Graphene middleware
│   └── views.py                 # View for Prometheus endpoint
```

**Step 2.2: Nautobot App configuration**

```python
# nautobot_app_graphql_observability/__init__.py
from nautobot.apps import NautobotAppConfig

class PrometheusGraphQLConfig(NautobotAppConfig):
    name = 'nautobot_app_graphql_observability'
    verbose_name = 'Prometheus GraphQL Metrics'
    version = '1.0.0'
    author = 'Your Name'
    description = 'Export Prometheus metrics for GraphQL queries'
    base_url = 'graphql-observability'
    required_settings = []
    default_settings = {
        'graphql_metrics_enabled': True,
        'track_field_resolution': False,
        'track_query_complexity': False,
    }

config = PrometheusGraphQLConfig
```

**Step 2.3: Prometheus endpoint**

```python
# nautobot_app_graphql_observability/views.py
from django.http import HttpResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

def metrics_view(request):
    """Endpoint to expose Prometheus metrics."""
    metrics = generate_latest()
    return HttpResponse(metrics, content_type=CONTENT_TYPE_LATEST)
```

```python
# nautobot_app_graphql_observability/urls.py
from django.urls import path
from .views import metrics_view

urlpatterns = [
    path('metrics/', metrics_view, name='prometheus_metrics'),
]
```

**Step 2.4: Configuration in Nautobot**

```python
# nautobot_config.py

# 1. Add app to PLUGINS (or INSTALLED_APPS for recent versions)
PLUGINS = [
    'nautobot_app_graphql_observability',
]

# 2. Configure Graphene middleware
GRAPHENE = {
    'SCHEMA': 'nautobot.core.graphql.schema.schema',
    'MIDDLEWARE': [
        'nautobot_app_graphql_observability.middleware.PrometheusMiddleware',
    ]
}

# 3. Optional app configuration
PLUGINS_CONFIG = {
    'nautobot_app_graphql_observability': {
        'graphql_metrics_enabled': True,
        'track_field_resolution': False,
        'track_query_complexity': False,
    }
}
```

### Phase 3: Advanced Features

**3.1 Per-user metrics**

```python
# Add a 'user' label to metrics
graphql_requests_total.labels(
    operation_type=operation,
    operation_name=operation_name,
    status=status,
    user=info.context.user.username if info.context.user.is_authenticated else 'anonymous'
).inc()
```

**3.2 Query complexity metrics**

- Calculate query depth
- Count number of requested fields
- Estimate complexity based on joins

**3.3 Grafana dashboard**

- Create pre-configured Grafana dashboard
- Include alerts for slow queries
- Key metrics visualizations

## Outstanding Questions

1. **Specific metrics**: What Prometheus metrics are priority for your use case?
2. **Granularity**: Do you want metrics per GraphQL query type (devices, sites, interfaces, etc.)?

3. **Performance**: What is the expected volume of GraphQL queries? (to optimize the middleware)

4. **Authentication**: Do you want to track metrics per user?

5. **Compatibility**: What version of Nautobot are you using? (important for app compatibility)

## Next Steps

1. **Clarify requirements** with answers to the above questions
2. **Create base project** with recommended structure
3. **Implement Graphene middleware** with basic metrics
4. **Create Nautobot app** for integration
5. **Test on Nautobot development environment**
6. **Document installation and configuration**
7. **Publish to PyPI** (optional)

## Resources

### Official Documentation

- [Nautobot Apps Development](https://docs.nautobot.com/projects/core/en/stable/development/apps/)
- [Graphene-Django Documentation](https://docs.graphene-python.org/projects/django/)
- [Graphene Middleware](https://docs.graphene-python.org/en/latest/execution/middleware/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)

### Code Examples

- [Nautobot Golden Config App](https://github.com/nautobot/nautobot-app-golden-config) - Example of GraphQL usage
- [Nautobot Core GraphQL Implementation](https://github.com/nautobot/nautobot/tree/develop/nautobot/core/graphql)

### Graphene Middleware

- Graphene middleware is called for each field resolution
- It receives an `info` object containing the request context
- Middleware can modify resolution behavior or capture metrics

### Important Note: Graphene vs Django Middleware

It's important to distinguish:

- **Graphene Middleware**: Executes at GraphQL resolution level (in Graphene engine)
- **Django Middleware**: Executes at HTTP level (before request reaches view)

To capture specific GraphQL metrics (operations, fields, etc.), you must use **Graphene Middleware**.

## Setting Up Nautobot Development Environment

To develop and test this middleware with Nautobot, you'll need to set up a Nautobot development environment. Nautobot provides two primary development workflows.

### Prerequisites

- Git
- Python 3.10, 3.11, or 3.12
- Docker and Docker Compose (for Docker workflow)
- PostgreSQL or MySQL (for virtual environment workflow)
- Redis (for virtual environment workflow)

### Quick Start with Docker Compose (Recommended)

The Docker Compose workflow is the easiest way to get started with Nautobot development.

#### 1. Fork and Clone Nautobot

```bash
# Fork the repository on GitHub first, then:
git clone git@github.com:yourusername/nautobot.git
cd nautobot
git remote add upstream git@github.com:nautobot/nautobot.git
```

#### 2. Install Invoke

Invoke is used to execute common development tasks:

```bash
pip3 install invoke
```

#### 3. List Available Invoke Tasks

```bash
invoke --list
```

This will show all available development commands including:

- `invoke build` - Build Nautobot Docker images
- `invoke start` - Start Nautobot and dependencies in background
- `invoke debug` - Start Nautobot in debug mode with output
- `invoke migrate` - Run database migrations
- `invoke createsuperuser` - Create admin user
- `invoke nbshell` - Launch interactive Nautobot shell
- `invoke cli` - Launch bash shell in container
- `invoke tests` - Run test suite
- `invoke stop` - Stop all containers

#### 4. Start Development Environment

```bash
# Build the Docker images
invoke build

# Run database migrations
invoke migrate

# Start Nautobot in debug mode (output to terminal)
invoke debug

# Or start in background:
invoke start

# Create a superuser (if needed)
invoke createsuperuser
```

#### 5. Access Nautobot

- Web UI: `http://localhost:8080`
- Username/Password: `admin/admin` (created automatically)

### Alternative: Python Virtual Environment Workflow

If you prefer not to use Docker, you can set up a local Python development environment.

#### 1. Install System Dependencies

Install PostgreSQL/MySQL and Redis according to the [Nautobot installation docs](https://docs.nautobot.com/projects/core/en/stable/user-guide/administration/installation/install_system/).

#### 2. Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Important**: Never install Poetry with `pip` into your Nautobot virtual environment.

#### 3. Create Virtual Environment

```bash
cd nautobot
poetry install
poetry shell
```

#### 4. Configure Nautobot

```bash
# Initialize configuration
nautobot-server init

# Or use the development config
cp development/nautobot_config.py ~/.nautobot/nautobot_config.py
```

#### 5. Run Migrations and Create Superuser

```bash
nautobot-server migrate
nautobot-server createsuperuser
```

#### 6. Start Development Server

```bash
nautobot-server runserver
```

### Working with the Development Environment

#### Creating a Branch

Always create a new branch for your changes:

```bash
# For bug fixes and minor features (off develop)
invoke branch --create --branch u/yourusername-1234-feature-name --parent develop

# For major features (off next)
invoke branch --create --branch u/yourusername-1235-major-feature --parent next
```

#### Running Tests

```bash
# Run all unit tests
invoke tests

# Run specific test
invoke tests --label nautobot.core.tests.test_something

# Run integration tests
invoke tests --tag integration

# With more options
invoke tests --failfast --verbose --keepdb
```

#### Interactive Shell

```bash
# Docker workflow
invoke nbshell

# Virtual environment workflow
nautobot-server nbshell
```

#### Accessing Logs

```bash
# Docker workflow - view all logs
invoke logs

# View specific service logs
invoke logs -s nautobot
invoke logs -s celery
```

### Testing Your Middleware

Once you have Nautobot running, you can test your middleware by:

1. **Installing your app in development mode**:

   ```bash
   # In your middleware project directory
   poetry install

   # Link to Nautobot's environment
   # Docker: Copy files into container or mount volume
   # Virtual env: pip install -e /path/to/your/middleware
   ```

2. **Configuring Nautobot to use your middleware**:
   Edit `nautobot_config.py`:

   ```python
   PLUGINS = ['nautobot_app_graphql_observability']

   GRAPHENE = {
       'SCHEMA': 'nautobot.core.graphql.schema.schema',
       'MIDDLEWARE': [
           'nautobot_app_graphql_observability.middleware.PrometheusMiddleware',
       ]
   }
   ```

3. **Restart Nautobot**:

   ```bash
   # Docker workflow
   invoke restart

   # Virtual environment workflow
   # Stop server (Ctrl+C) and restart
   nautobot-server runserver
   ```

4. **Test GraphQL queries**:
    - Navigate to `http://localhost:8080/graphql/`
    - Run test queries
    - Check your metrics endpoint

### Troubleshooting

#### Too Many Database Connections

If you see "FATAL: sorry, too many clients already":

```bash
nautobot-server runserver --nothreading
```

#### Docker Issues

```bash
# Rebuild containers if things seem broken
invoke destroy
invoke build
invoke start

# View container logs
invoke logs -s nautobot
```

#### Database Issues

```bash
# Reset database (Docker)
invoke destroy
invoke start

# Reset database (Virtual env)
nautobot-server migrate --fake-initial
```

### Additional Resources

- [Nautobot Development Guide](https://docs.nautobot.com/projects/core/en/stable/development/core/getting-started/)
- [Docker Compose Advanced Usage](https://docs.nautobot.com/projects/core/en/stable/development/core/docker-compose-advanced-use-cases/)
- [Testing Guide](https://docs.nautobot.com/projects/core/en/stable/development/core/testing/)

## Final Recommendation

### ✅ OPTIMAL SOLUTION: Nautobot App with Generic Graphene Middleware

**Target Nautobot version**: 2.4.x (stable) and 3.0.x (latest version)

- Compatible with Python 3.10, 3.11, 3.12
- Django 4.2.x
- Integrated Graphene-Django

**Recommended architecture:**

```
nautobot-app-graphql-prometheus/
├── pyproject.toml
├── README.md
├── docs/
│   ├── installation.md
│   └── grafana-dashboard.json
├── nautobot_graphql_prometheus/
│   ├── __init__.py              # NautobotAppConfig
│   ├── middleware.py            # Graphene middleware with complete metrics
│   ├── metrics.py               # Prometheus definitions (counters, histograms)
│   ├── config.py                # Middleware configuration
│   ├── urls.py                  # /metrics endpoint
│   ├── views.py                 # Prometheus view
│   └── utils.py                 # Utilities (metadata extraction, complexity calculation)
└── tests/
    ├── __init__.py
    ├── test_middleware.py
    ├── test_metrics.py
    └── fixtures/
        └── test_queries.graphql
```

**Implemented features:**

✅ **Basic metrics:**

- Request counter by operation type and name
- Request duration histogram
- Error counter by type

✅ **Advanced metrics:**

- Per-user metrics (with authentication tracking)
- Query depth
- Query complexity (number of fields)
- Metrics per GraphQL model type (Device, Site, Interface, etc.)
- Per-field resolution (optional, for debugging)

✅ **Prometheus endpoint:**

- `/api/plugins/graphql-prometheus/metrics/` for Prometheus scraping
- Configurable optional authentication
- Standard Prometheus format

✅ **Nautobot integration:**

- No Nautobot core modifications
- Installation via `pip install nautobot-graphql-prometheus`
- Simple configuration in `nautobot_config.py`

**Next action**: Complete implementation ready for development.
