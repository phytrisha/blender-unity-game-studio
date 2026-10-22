---
paths:
  - "Assets/**/{Gameplay,gameplay}/**/*.cs"
---

# Gameplay Code Rules

- ALL gameplay values MUST come from external config/data files, NEVER hardcoded
- Use delta time for ALL time-dependent calculations (frame-rate independence)
- NO direct references to UI code — use events for cross-system communication
  (C# events, UnityEvents)
- Every gameplay system must implement a clear interface
- State machines must have explicit transition tables with documented states
- Write unit tests for all gameplay logic — separate logic from presentation
- Document which design doc each feature implements in code comments
- No static singletons for game state — use dependency injection

## Examples

**Correct** (data-driven; values from a ScriptableObject):

```csharp
float damage = combatConfig.BaseDamage;
float speed = stats.MovementSpeed * Time.deltaTime;
```

**Incorrect** (hardcoded):

```csharp
float damage = 25f;   // VIOLATION: hardcoded gameplay value
float speed = 5f;     // VIOLATION: not from config, not using deltaTime
```
