---
paths:
  - "Assets/**/{Core,core}/**/*.cs"
---

# Engine Code Rules

- ZERO allocations in hot paths (update loops, rendering, physics) — pre-allocate, pool, reuse
- All engine APIs must be thread-safe OR explicitly documented as single-thread-only
- Profile before AND after every optimization — document the measured numbers
- Engine code must NEVER depend on gameplay code (strict dependency direction: engine <- gameplay)
- Every public API must have usage examples in its doc comment
- Changes to public interfaces require a deprecation period and migration guide
- Use RAII / deterministic cleanup for all resources
- All engine systems must support graceful degradation
- Before writing engine API code, consult `docs/engine-reference/` for the current engine version and verify APIs against the reference docs

## Examples

**Correct** (zero-alloc hot path):

```csharp
private readonly Collider[] _nearbyCache = new Collider[64];  // allocated once

void FixedUpdate()
{
    int count = Physics.OverlapSphereNonAlloc(transform.position, radius, _nearbyCache);
}
```

**Incorrect** (allocating in hot path):

```csharp
void FixedUpdate()
{
    var nearby = Physics.OverlapSphere(transform.position, radius);  // VIOLATION: allocates a new array every frame
}
```
