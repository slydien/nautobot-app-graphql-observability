# Architecture Decision Records

## ADR-1: Graphene Middleware vs Django Middleware

**Decision**: Use a Graphene middleware (not a Django HTTP middleware) for metrics instrumentation.

**Context**: Django middleware operates at the HTTP request/response level and cannot inspect GraphQL-specific details like operation names, types, query depth, or individual field resolution. Graphene middleware is invoked for each field resolution and has access to the `GraphQLResolveInfo` object with full query metadata.

**Consequence**: The middleware can label metrics with `operation_type`, `operation_name`, `type_name`, and `field_name` labels that would be unavailable at the HTTP layer.

## ADR-2: Monkey-Patching GraphQLDRFAPIView.init_graphql

**Decision**: Monkey-patch `GraphQLDRFAPIView.init_graphql()` in the app's `AppConfig.ready()` method.

**Context**: Nautobot 3.x's `GraphQLDRFAPIView.init_graphql()` does not load middleware from the `GRAPHENE["MIDDLEWARE"]` setting when `self.middleware` is `None`. This is a bug in Nautobot's implementation. Without patching, configured Graphene middleware is silently ignored.

**Alternatives considered**:

- Forking Nautobot: Too heavy and maintenance-intensive.
- Overriding the URL route: Would require duplicating the view class and URL configuration.
- Subclassing the view: `GraphQLDRFAPIView` is referenced directly in Nautobot's URL configuration, so a subclass would not be used.

**Consequence**: The patch is minimal (wraps the original method, only acts when `self.middleware is None`) and is applied once at startup. It introduces a coupling to Nautobot's internal API that may need updating if Nautobot fixes the bug upstream.

## ADR-3: time.monotonic() for Duration Measurement

**Decision**: Use `time.monotonic()` instead of `time.time()` for duration measurements.

**Context**: `time.monotonic()` is immune to system clock adjustments (NTP corrections, manual changes) and provides consistent interval measurement. `time.time()` can produce negative durations if the clock is adjusted backward.

**Consequence**: Duration metrics are always non-negative and accurate regardless of clock adjustments.

## ADR-4: Metric Label Design

**Decision**: Use a fixed set of low-cardinality labels. Operation names are included as labels but field-level tracking is opt-in.

**Context**: Prometheus best practices recommend keeping label cardinality low. Operation names can have moderate cardinality (typically tens to low hundreds of unique names in a Nautobot deployment). Field-level labels (`type_name`, `field_name`) can have higher cardinality and are gated behind the `track_field_resolution` setting (disabled by default).

**Consequence**: Basic metrics are safe for production use. Per-field metrics should only be enabled for short-term debugging to avoid cardinality explosion in Prometheus.

## ADR-5: Root-Only Instrumentation for Basic Metrics

**Decision**: Only record basic metrics (request count, duration, errors) at the root resolver level (`root is None`).

**Context**: Graphene middleware is called for every field resolution in a query. Recording metrics at every level would multiply the overhead by the number of fields and produce misleading counts (one query would generate hundreds of metric increments).

**Consequence**: Basic metrics accurately represent one increment per GraphQL operation. Per-field instrumentation is a separate opt-in feature.
