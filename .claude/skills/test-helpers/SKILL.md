---
name: test-helpers
description: "Generate engine-specific test helper libraries — assertion utilities, factory functions, mocks in the engine's test folder. Reduces boilerplate."
argument-hint: "[system-name | all | scaffold]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Bash(bash "*/.claude/skills/test-helpers/../../hooks/yaml-helper.sh" resolve_config *)
model: sonnet
---

!`bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys automation`

**Automation mode**: Resolve `modes.automation` (`project.local.yaml` →
`project.yaml` → default `collaborative`). Every `AskUserQuestion` call and
every file write follows `.claude/docs/automation-modes.md`
(collaborative asks always · guided major-only · autonomous logs and proceeds;
`automation_always_ask` categories always prompt).

# Test Helpers

Writing test cases is faster and more consistent when common setup, teardown,
and assertion patterns are abstracted into helpers. This skill generates a
helper library tailored to the project's Unity setup and systems — so every developer writes less boilerplate and more assertions.

**Output:** C# helper files in Unity's **helper root** — the only place its
test runner compiles them (`.claude/docs/directory-structure.md`):
`Assets/Tests/EditMode/Helpers/`, inside the `EditModeTests` assembly
`/test-setup` creates. If PlayMode tests need the same helpers, ask before
creating `Assets/Tests/Helpers/TestHelpers.asmdef` and referencing it from both
test assemblies.

"The helper root" below means that folder.

**When to run:**
- After `/test-setup` scaffolds the framework (first time)
- When multiple test files repeat the same setup boilerplate
- When starting to write tests for a new system

---

## Assertions: use the project's test framework, never bare `assert()`

**Generated helpers must assert through the configured test framework's assertion
API**, resolved from `testing.framework` — not through a bare C#
`System.Diagnostics.Debug.Assert()`.

Two things go wrong with a bare `assert()` in a helper, and both are silent:

1. **It aborts the run instead of failing the test.** A framework assertion
   records a failure and continues, so one broken expectation yields one red test.
   A bare `assert()` halts execution, so the first failure hides every result
   after it.
2. **It is stripped in release builds.** A helper library built on `assert()`
   stops asserting entirely in exactly the build you most want checked, and does
   so without any error — the tests still "pass".

**Look up the assertion form for the configured framework before generating
code.** Do not copy the forms in this file or in other skills' examples as
authoritative — they are illustrative and have drifted (`assert_eq`,
`assert_true` and `assert_that` all appear across the repo). If you cannot
confirm the correct API for the project's framework, say so and generate no
helper rather than guessing.

**Helpers must not be test fixtures.** A helper class in the helper root that
carries the framework's test-fixture markers is discovered by the runner as a
test suite containing zero tests. Helpers are plain (static) classes; only real
test files are fixtures.

---

## 1. Parse Arguments

**Modes:**
- `/test-helpers [system-name]` — generate helpers for a specific system
  (e.g., `/test-helpers combat`)
- `/test-helpers all` — generate helpers for all systems with test files
- `/test-helpers scaffold` — generate only the base helper library (no
  system-specific helpers); use this on first run
- No argument — run `scaffold` if no helpers exist, else `all`

---

## 2. Detect Engine and Language

Read from `project.yaml` first, falling back to `.claude/docs/technical-preferences.md` for any key that is absent or empty:
- `engine.name` (else the `Engine:` value)
- `engine.language` (else the `Language:` value)
- `testing.framework` (else `Framework:` from the Testing section)

If the engine is not configured in either source: "Engine not configured. Run `/setup-engine` first."
If it is configured as anything other than Unity: "Engine '[value]' is not
supported by this studio (Unity only)." Generate nothing.

---

## 3. Load Existing Test Patterns

Scan Unity's test root (`Assets/Tests/`) for patterns already in use:

```
Glob pattern="Assets/Tests/**/*Tests.cs"
```

For a representative sample (up to 5 files), read the test files and extract:
- Setup patterns (how `before_each` / `setUp` / fixtures are written)
- Common assertion patterns (what is being asserted most often)
- Object creation patterns (how game objects or scenes are instantiated in tests)
- Mock/stub patterns (how dependencies are replaced)

This ensures generated helpers match the project's existing style, not a
generic template.

Also read:
- `design/gdd/systems-index.md` — to know which systems exist
- In-scope GDD(s) — to understand what data types and values need testing. Read
  them by section: find the headings you need with the Grep tool (pattern `^#`,
  content mode) and Read those ranges with offset and limit.
- `docs/architecture/tr-registry.yaml` — to map requirements to tested systems

---

## 4. Generate Base Helpers

### Unity (NUnit / C#)

**Base helper** (`Assets/Tests/EditMode/Helpers/GameAssertions.cs`):

```csharp
using NUnit.Framework;
using UnityEngine;

/// <summary>
/// Game-specific assertion utilities for [Project Name] tests.
/// Extends NUnit's Assert with domain-specific helpers.
/// </summary>
public static class GameAssertions
{
    /// <summary>
    /// Assert a value is within an inclusive range [min, max].
    /// Use for any formula output defined in GDD Formulas sections.
    /// </summary>
    public static void AssertInRange(float value, float min, float max, string label = "value")
    {
        Assert.That(value, Is.InRange(min, max),
            $"{label} ({value:F2}) is outside expected range [{min:F2}, {max:F2}]");
    }

    /// <summary>Assert a UnityEvent or C# event was raised during an action.</summary>
    public static void AssertEventRaised(ref bool wasCalled, System.Action action, string eventName)
    {
        wasCalled = false;
        action();
        Assert.IsTrue(wasCalled, $"Expected event '{eventName}' to be raised, but it was not.");
    }

    /// <summary>Assert a component exists on a GameObject.</summary>
    public static void AssertHasComponent<T>(GameObject obj) where T : Component
    {
        var component = obj.GetComponent<T>();
        Assert.IsNotNull(component,
            $"Expected GameObject '{obj.name}' to have component {typeof(T).Name}.");
    }
}
```

**Factory helper** (`Assets/Tests/EditMode/Helpers/GameFactory.cs`):

```csharp
using UnityEngine;

/// <summary>
/// Factory methods for creating minimal test objects without loading scenes.
/// </summary>
public static class GameFactory
{
    /// <summary>Create a minimal GameObject with a named component for testing.</summary>
    public static GameObject MakeGameObject(string name = "TestObject")
    {
        var go = new GameObject(name);
        return go;
    }

    /// <summary>
    /// Create a ScriptableObject of type T for data-driven tests.
    /// Dispose with Object.DestroyImmediate after test.
    /// </summary>
    public static T MakeScriptableObject<T>() where T : ScriptableObject
    {
        return ScriptableObject.CreateInstance<T>();
    }
}
```

---

## 5. Generate System-Specific Helpers

For `[system-name]` or `all` modes, generate a helper per system:

Read only the GDD sections this needs — `Grep pattern="^## ([0-9]+\. )?(Formulas|Edge Cases|Detailed Rules|Detailed Design)" path="design/gdd/[system].md" output_mode="content" -A 30` (the optional number matches a reverse-documented GDD's `## 4. Formulas`) — rather than a full read (every peer skill section-greps GDDs; in `all` mode a full read multiplies across each system's 400+-line GDD). Extract:
- Data types (entity types, component names)
- Formula variables and their bounds
- Common test scenarios mentioned in Edge Cases

Generate `[helper root]/[System]TestFactory.cs` with factory functions
specific to that system's objects.

Example pattern for a `combat` system:

```csharp
using UnityEngine;

/// <summary>
/// Factory and assertion helpers for Combat system tests.
/// Generated by /test-helpers combat on [date]. Based on: design/gdd/combat.md
/// </summary>
public static class CombatTestFactory
{
    public const float DamageMin = 0f;
    public const float DamageMax = 999f;   // From GDD: damage formula upper bound

    /// <summary>Create a minimal attacker for damage formula tests.
    /// Replace the stand-in type with the real combat data class once it exists.</summary>
    public static CombatStats MakeAttacker(float attack = 10f, float critChance = 0f)
        => new CombatStats { Attack = attack, CritChance = critChance };

    /// <summary>Create a minimal target for damage receive tests.</summary>
    public static CombatStats MakeTarget(float defense = 0f, float health = 100f)
        => new CombatStats { Defense = defense, Health = health, MaxHealth = health };

    /// <summary>Assert damage output is within GDD-specified bounds.</summary>
    public static void AssertDamageInBounds(float damage)
        => GameAssertions.AssertInRange(damage, DamageMin, DamageMax, "damage");

    /// <summary>Stand-in data holder for the example; use the game's own type.</summary>
    public class CombatStats
    {
        public float Attack, CritChance, Defense, Health, MaxHealth;
    }
}
```

---

## 6. Write Output

Present a summary of what will be created:

```
## Test Helpers to Create

Base helpers (Unity, helper root: [helper root]):
- [helper root]/GameAssertions.cs
- [helper root]/GameFactory.cs

System helpers ([mode]):
- [helper root]/[System]TestFactory.cs  ← from [system] GDD
```

Ask: "May I write these helper files to `[helper root]`?"

**Never overwrite existing files.** If a file already exists, report:
"Skipping `[path]` — already exists. Remove the file manually if you want it
regenerated."

After writing: Verdict: **COMPLETE** — helper files created.

"Helper files created. To use them in a test: add a `using` directive, or
reference the test helper assembly from the test assembly."

---

## Collaborative Protocol

- **Never overwrite existing helpers** — they may contain hand-written
  customisations. Only generate new files that don't exist yet
- **Generated code is a starting point** — the generated factory functions use
  stand-in data types for simplicity; adapt to the actual class structure once
  the code exists
- **Helpers should reflect the GDD** — bounds and constants in helpers should
  trace to GDD Formulas sections, not invented values
- **Ask before writing** — always confirm before creating files in the helper root

## Next Steps

- Run `/test-setup` if the test framework has not been scaffolded yet.
- Use `/dev-story` to implement stories — helpers reduce boilerplate in new test files.
- Run `/skill-test` to validate other skills that may need helper coverage.
