> Authoring guidance for interaction-pattern-library.md. Load only the part covering the section currently being authored — not the whole file at once.

> Covers: **Game-Specific UI Patterns** — full reference specifications for Inventory Slot, Ability / Skill Icon, Health / Resource Bar, Dialogue Box, Context Action Prompt, Damage Number.

## Game-Specific UI Patterns

---

#### Inventory Slot

**Category**: Game-Specific
**Status**: Draft
**When to Use**: Every item container in the inventory grid. Empty slots, populated
slots, equipped slots, locked slots. The slot is the frame; the item icon is the
content.

**States**:

| State | Visual | Notes |
|-------|--------|-------|
| Empty | Subtle slot border, no content. Not the same as disabled. Empty slots are interactable (receive items). | Avoid fully invisible empty slots — players lose track of grid dimensions |
| Populated | Item icon fills 80% of slot area. Stack count bottom-right (if applicable). Quality border (colorblind-safe — icon + color). Equipped badge (top-right, if equipped). | |
| Focused | Focus ring. Tooltip appears after 300ms. | |
| Selected | Thicker or contrasting border. Used when multi-select is supported. | |
| Drag source | Slot dims, drag ghost follows pointer. | See Grid Item for full drag spec |
| Locked | Padlock icon overlay. No interaction. May show item at 50% opacity behind lock. | Used for locked loadout slots, DLC content, etc. |
| Highlighted | Animated border glow (pulsing). Used for quest-relevant items or newly acquired items. | Respect motion reduction — replace pulse with a static badge |
| Cooldown overlay | Radial fill overlay from 12 o'clock, clockwise, depleting as cooldown expires. | Only applicable if slots represent active items with cooldowns |

**Accessibility**: Stack counts and quality tiers must have text or icon alternatives to color coding. Tooltip is the primary accessibility mechanism — ensure it is reachable by keyboard and screen reader. Locked slots must announce "locked" to screen readers.

**Implementation Notes**: [Unity (uGUI): a slot prefab with a frame `Image` whose sprite is swapped by rarity — avoid tinting the icon `Image` for quality, as it changes the icon's colour. Drag and drop via the EventSystem drag interfaces (`IBeginDragHandler`, `IDragHandler`, `IEndDragHandler`, `IDropHandler`). In UI Toolkit, a custom `VisualElement` with a USS class per rarity.]

---

#### Ability / Skill Icon

**Category**: Game-Specific
**Status**: Draft
**When to Use**: Ability buttons in the HUD ability bar, skill tree nodes, and
any context where an ability must show availability state.

**States**:

| State | Visual | Notes |
|-------|--------|-------|
| Available | Full opacity icon. Keybinding label below. | |
| On cooldown | Radial overlay depleting clockwise from 12 o'clock. Remaining time shown as a number in the center when > 2 seconds remain. | |
| Charges remaining | Charge pip indicators below icon (e.g., 3 filled circles = 3 charges). Number alternative for screen readers. | |
| Out of resource | Icon desaturates to ~20%. Border dims. Keybinding label dims. Distinct from cooldown — resource-gated, not time-gated. | |
| Locked / not unlocked | Icon silhouette only (no full art visible). Padlock badge. May show unlock condition in tooltip. | |
| Active / channeling | Pulsing border. Radial fill shows channel duration remaining. | |
| Just activated | Brief scale 0.9x then spring to 1.0x (overshoot to 1.05x). | Example: Guild Wars 2 and Path of Exile both use press-depress animations on ability use to confirm activation. Respect motion reduction. |

**Accessibility**: All cooldown/charge information must have a numeric value (screen reader cannot parse radial overlays). The cooldown timer number satisfies this. Ability names and descriptions must be exposed to screen readers via tooltip.

**Implementation Notes**: [Unity (uGUI): a `Button` prefab with overlay `Image`
children for the cooldown radial and charge pips. The cooldown radial is an `Image`
set to Filled / Radial 360 with `fillAmount` driven by the remaining time, or a
custom shader on a mask. Verify against docs/engine-reference/unity/ for the
pinned version before relying on a specific UI API.]

---

#### Health / Resource Bar

**Category**: Game-Specific
**Status**: Draft
**When to Use**: Any continuously varying value in the HUD that represents a
critical player resource. Health, mana, stamina, shield, fuel.

**States and behaviors**:

| Event | Visual | Audio | Duration |
|-------|--------|-------|---------|
| Value decrease (damage) | Fill shrinks. Brief "damage flash" on the fill (white or red flash). Ghost bar lingers at previous value and drains to new value over 0.5s ("damage indicator"). | [Damage taken sound — varies by amount] | Instant decrease, 500ms ghost bar drain |
| Value increase (heal) | Fill grows. Brief heal color flash (green — ensure colorblind safe with icon/glow backup). | [Heal sound] | 300ms ease-in |
| Below 25% threshold | Fill changes color to warning state. Border pulses (or static badge in motion reduction mode). Optional: heartbeat audio cue (paired with visual if audio is sole signal). | [Low health sound — loops until above threshold] | Continuous |
| At zero | Bar empty. Optional: bar shakes briefly. Death/depletion event fires. | [Death/depletion sound] | 200ms shake |
| Maximum | Fill at 100%, brief glow. | — | 200ms |
| Overflow (shield) | A separate bar segment appears beyond the natural fill area, in shield color. | [Shield gain sound] | 200ms |

**Accessibility**: The current value must be accessible as a number (tooltip or persistent display, or both). Color-coded threshold states must have non-color backups (icon, flashing, or audio visual warning). Warning state at 25% must have a visual signal independent of the color change.

**Implementation Notes**: [Unity (uGUI): two overlapping filled `Image` bars for the
ghost effect — the back bar holds the previous value (drains over time), the front
bar holds the current value (updates instantly). Threshold states swap the front
bar's sprite or colour. The ghost drain duration is a designer-tunable parameter.]

---

#### Dialogue Box

**Category**: Game-Specific
**Status**: Draft
**When to Use**: NPC conversation, voiced narrative dialogue, tutorial text
delivered through a character. All dialogue that has a speaker.

**Structure**: Speaker portrait or name tag (top of box or left side). Dialogue text body. Continue/advance prompt (bottom right). Optional: skip-all button, voice acting indicator, subtitle indicator.

**States and behaviors**:

| State | Visual | Input | Response | Duration |
|-------|--------|-------|----------|---------|
| Line entering | Text reveals character-by-character (typewriter effect). Or: text fades in at full speed if accessibility option set. | — | — | Speed: configurable in accessibility settings |
| Revealing | Text animating in. Continue prompt hidden or pulsing at slow opacity. | [Any advance input] | Skip to end of current line instantly (show full line, stop typewriter) | Immediate |
| Line complete | Full line shown. Continue prompt visible and animated. | — | — | — |
| Advancing to next line | Continue prompt hides. Text fades out or wipes. New line begins. | [Any advance input] — Enter / A / Cross / Space / mouse click | Advance | 100ms transition |
| Choices appearing | Choice buttons appear below dialogue text. Continue prompt hidden. Navigation focus moves to first choice. | D-pad / keyboard to select, Enter / A / Cross to confirm | Select choice | 150ms enter animation |
| Closing | Box fades out | Final line advanced | Return control to player | 200ms |
| Skipping all (if supported) | Brief confirmation prompt: "Skip dialogue?" | Dedicated skip button | Skip to post-dialogue state | — |

**Accessibility**: Subtitles are always enabled by default for all voiced dialogue. Typewriter animation speed is a user setting (see accessibility-requirements.md). The dialogue box must not auto-advance — players must control pacing. Speaker name is always shown. All choice buttons must be navigable by keyboard and gamepad. Choices must be accessible to screen readers with position announced.

**Implementation Notes**: [Unity: a TextMeshPro text component with rich-text tags
for formatting. Typewriter effect by stepping `maxVisibleCharacters` from a
coroutine. Bind the advance input to a function that either skips the typewriter
(shows every character) or advances the dialogue state. Speaker name in a separate
text element above or beside the box. Dialogue data loaded from JSON, a
ScriptableObject, or a dedicated dialogue tool (e.g. Ink, Yarn Spinner for Unity).]

---

#### Context Action Prompt

**Category**: Game-Specific
**Status**: Draft
**When to Use**: A prompt that appears near an interactable game object indicating
what the player can do. "Press [A] to open chest." "Hold [E] to pick up." Appears
when the player enters the interaction zone, disappears when they leave.

**States**:

| State | Visual | Notes |
|-------|--------|-------|
| Appearing | Fades in and rises 8px from object anchor point. | Respect motion reduction — fade only, no rise |
| Idle | Platform-correct button icon + action label. Icon matches current input method (updates if player switches). | Always show platform-correct icon — do not hardcode "Press A" for all platforms |
| Holding (for hold inputs) | Radial fill on the button icon shows hold progress. Label changes to active verb ("Opening..."). | |
| Cannot interact (blocked) | Icon dims. Label shows reason if known ("Too heavy", "Need key"). | Optional — only show blocked state if the reason is meaningful to the player |
| Disappearing | Fades out. | Triggered when player exits interaction zone |

**Accessibility**: The button icon must be accompanied by a text label — do not rely on icon alone (some players use custom button labels or adaptive controllers with non-standard icons). The prompt must be positioned to not overlap character health or critical HUD information.

**Implementation Notes**: [Unity: a world-space `Canvas` (or a sprite) as a child of the interactable object, turned to face the camera each frame (billboard). Swap the button icon by the active control scheme (keyboard and mouse vs gamepad) as the Input System reports it. Hold progress as a filled radial `Image` driven by the hold time, or an animation on a radial mask shader.]

---

#### Damage Number

**Category**: Game-Specific
**Status**: Draft
**When to Use**: Floating feedback numbers above combat participants. Normal
damage, critical damage, healing, miss.

**Variants**:

| Variant | Visual | Notes |
|---------|--------|-------|
| Normal damage | White number, normal weight, medium size. | |
| Critical hit | Larger size (1.5x), bold weight, orange or yellow — verify colorblind safe. Brief scale impact (1.3x → 1.0x on appear). | Example: Path of Exile and Diablo IV both use scale-pop for crits to make them immediately recognizable by size alone, independent of color. |
| Healing | Green (verify colorblind safe — use + prefix and upward trajectory as non-color backups). | |
| Miss / Evade | "MISS" text, grey, italic. Floats at smaller size. | |
| Status damage (DoT) | Smaller size, distinct color matching the status effect. | |

**Behavior**: Numbers float upward from the hit location over 1.0 second. Numbers fade from 100% to 0% during the last 0.4 seconds. Multiple numbers from rapid hits stagger horizontally to avoid overlap. Maximum simultaneous damage numbers on screen: [define per game — typically 8-12 per character].

**Accessibility**: Damage numbers are purely supplementary feedback — they must never be the only way to understand combat state. Health bars are the authoritative source. Provide an option to disable damage numbers entirely (some players find them visually overwhelming). When disabled, the game must remain fully playable.

**Implementation Notes**: [Unity: a pool of TextMeshPro text instances (world-space
for 3D games, screen-space for 2D) recycled via an object pool. Each instance gets a
random small horizontal offset on spawn (±20px) to reduce overlap. Float animation
on its local position and a `CanvasGroup` alpha. Critical hit scale-pop: ease-out on
scale, then a linear settle.]

---
