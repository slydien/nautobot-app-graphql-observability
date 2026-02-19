# Architecture Decision Records

## ADR-1: Graphene Middleware vs Django Middleware

**Decision**: Use a Graphene middleware (not a Django HTTP middleware) for metrics instrumentation.

**Context**: Django middleware operates at the HTTP request/response level and cannot inspect GraphQL-specific details like operation names, types, query depth, or individual field resolution. Graphene middleware is invoked for each field resolution and has access to the `GraphQLResolveInfo` object with full query metadata.

**Consequence**: The middleware can label metrics with `operation_type`, `operation_name`, `type_name`, and `field_name` labels that would be unavailable at the HTTP layer.

## ADR-2: time.monotonic() for Duration Measurement

**Decision**: Use `time.monotonic()` instead of `time.time()` for duration measurements.

**Context**: `time.monotonic()` is immune to system clock adjustments (NTP corrections, manual changes) and provides consistent interval measurement. `time.time()` can produce negative durations if the clock is adjusted backward.

**Consequence**: Duration metrics are always non-negative and accurate regardless of clock adjustments.

## ADR-3: Metric Label Design

**Decision**: Use a fixed set of low-cardinality labels. Operation names are included as labels but field-level tracking is opt-in.

**Context**: Prometheus best practices recommend keeping label cardinality low. Operation names can have moderate cardinality (typically tens to low hundreds of unique names in a typical deployment). Field-level labels (`type_name`, `field_name`) can have higher cardinality and are gated behind the `track_field_resolution` setting (disabled by default).

**Consequence**: Basic metrics are safe for production use. Per-field metrics should only be enabled for short-term debugging to avoid cardinality explosion in Prometheus.

## ADR-4: Root-Only Instrumentation for Basic Metrics

**Decision**: Only record basic metrics (request count, duration, errors) at the root resolver level (`root is None`).

**Context**: Graphene middleware is called for every field resolution in a query. Recording metrics at every level would multiply the overhead by the number of fields and produce misleading counts (one query would generate hundreds of metric increments).

**Consequence**: Basic metrics accurately represent one increment per GraphQL operation. Per-field instrumentation is a separate opt-in feature.
