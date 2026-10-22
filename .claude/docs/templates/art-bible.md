# Art Bible: [Game Title]

> **Status**: [Draft / Under Review / Approved]
> **Owned By**: art-director
> **Last Updated**: [Date]
> **Art Director Sign-Off (AD-ART-BIBLE)**: [Not yet reviewed]

`/art-bible` writes these nine sections in this order and replaces each
section's `[To be designed]` line as that section is approved. A section still
holding its placeholder is incomplete; a later run fills only those.

## 1. Visual Identity Statement

[To be designed] — a one-line visual rule that resolves any visual ambiguity,
plus 2–3 supporting principles, each with a design test ("when X is ambiguous,
choose Y") and the pillar it serves.

## 2. Mood & Atmosphere

[To be designed] — for each major game state (exploration, combat, victory,
defeat, menus — whichever this game has): the emotional target, lighting
character (time of day, colour temperature, contrast), 3–5 atmospheric
descriptors, and energy level. Each state must look distinct from the others.

## 3. Shape Language

[To be designed] — character silhouette philosophy (readable at thumbnail
size, one distinguishing trait per archetype), environment geometry, UI shape
grammar, and hero versus supporting shapes.

## 4. Color System

[To be designed] — a primary palette of 5–7 colours with their meaning in this
world, semantic colour usage, per-area colour temperature rules, the UI palette
and where it diverges, and colourblind safety: which semantic colours need a
shape, icon or sound backup.

## 5. Character Design Direction

[To be designed] — the player character's visual archetype, how players tell
enemies, NPCs and allies apart at a glance, expression and pose style, and how
much detail survives at game camera distance (LOD philosophy).

## 6. Environment Design Language

[To be designed] — architectural style and its tie to the world's culture,
texture philosophy (painted, PBR or stylised, and why), prop density rules per
area type, and environmental storytelling guidelines.

## 7. UI/HUD Visual Direction

[To be designed] — diegetic versus screen-space HUD, typography (personality,
weight, size hierarchy, minimum readable size), iconography style, UI animation
feel, and any art-direction versus readability conflict and how it was decided.

## 8. Asset Standards

[To be designed] — file formats, naming convention, texture resolution tiers,
LOD levels, export settings, and the engine's hard limits (poly budgets per
asset category, texture memory, material slots). Where an art preference and a
technical limit disagree, record both and the trade-off chosen.

The 3D pipeline (Blender → Unity) reads this section when it writes each asset's
`asset.json`; a missing value falls back to the pipeline default and the brief
says so. Use these sub-headings so `/produce-asset` can read them by section:

### 8.1 Budgets per asset class
[To be designed] — LOD0 tris, materials, texel density (px/m), texture size,
LOD ratios per class (small/medium/large prop, building, character, creature,
plant), bones and influences for rigged classes. Defaults:
`.claude/docs/art-pipeline/pipeline.md` "Default budgets".

### 8.2 Naming and materials
[To be designed] — the naming contract (defaults: pipeline.md "Naming
contract": `SM_ SK_ PF_ MI_ M_ T_<Stem>_{BC,N,MS,AO,E} AC_ UCX_`), the shared
material library (`MI_*`: name, use, tiling size, texture set), when an asset
gets its own `M_` material instead.

### 8.3 Texturing route and prompt style
[To be designed] — which assets use library tiling materials, which are painted
(`/paint-asset`), which are baked; the **prompt style block** appended to every
Weave / AI Hub texture prompt and the Tripo prompt suffix; colour-space and
lighting rules for albedo (no baked light unless the style is painted).

### 8.4 Rigs and animation
[To be designed] — Humanoid vs Generic per character class, frame rate, clip
naming, root motion or in place, events.

## 9. Reference Direction

[To be designed] — 3–5 references (games, films, art styles or artists). For
each: the specific element to take from it, and what to avoid so the result
does not read as a copy.
