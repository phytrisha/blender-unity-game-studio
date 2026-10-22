# /setup-engine — Section 3: Look Up Current Version

> Part of `/setup-engine`. `SKILL.md` names when to read this file; the settings it
> resolved and the rules under its later headings still apply here.

## 3. Look Up Current Version

The engine is Unity (the only engine this studio supports):

- If version was provided, use it
- If no version provided, use WebSearch to find the latest stable release:
  - Search: `"Unity 6 latest LTS version [current year]"`
  - Confirm with the user: "The latest stable Unity is [version]. Use this?"

### Check the chosen version against what is actually installed

A version found by web search is what exists, not what the developer has. Pinning
one they cannot run means every later instruction — build, test, smoke, the
engine reference docs — targets an engine that is not on the machine.

Probe for the binary (Bash), and treat failure as unknown, never as absent:

| Engine | Probe |
|--------|-------|
| Unity | The Hub's editor directory, then that editor's `-version` — `C:/Program Files/Unity/Hub/Editor/<version>/Editor/Unity.exe` on Windows, `/Applications/Unity/Hub/Editor/<version>/Unity.app/Contents/MacOS/Unity` on macOS, `/home/<user>/Unity/Hub/Editor/<version>/Editor/Unity` on Linux. Not bare `Unity`: on `PATH` it may be Unity's separate CLI, which rejects `-version` |

Keep the editor executable the probe found: Section 5.5.1 writes it into
`commands.*` and `engine.path`.

Then:
- **Match** — say so in one line and continue.
- **Mismatch** — state both versions and ask, offering three options: pin the
  installed version, pin the newer one and upgrade later, or pin the newer one
  deliberately. Record the answer; do not pick silently.
- **Not found / probe failed** — report `installed version NOT DETERMINED` and
  continue with the chosen version. Do **not** report this as "no engine
  installed": a probe that could not run has not established absence.

Whatever the outcome, write it into Section 7's `VERSION.md` as an
`Installed at pin time` row, so a later reader can tell a deliberate
version-ahead pin from an accident.

---
