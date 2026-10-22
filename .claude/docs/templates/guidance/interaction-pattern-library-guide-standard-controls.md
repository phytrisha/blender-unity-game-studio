> Authoring guidance for interaction-pattern-library.md. Load only the part covering the section currently being authored — not the whole file at once.

> Covers: **Standard Control Patterns** — full reference specifications for Button (Primary/Secondary/Destructive), Toggle, Slider, Dropdown / Select, List Item, Grid Item, Modal Dialog, Confirmation Dialog, Toast / Notification, Tooltip, Progress Bar, Input Field, Tab Bar, Scroll Container.

## Standard Control Patterns

---

#### Button (Primary)

**Category**: Input
**Status**: Draft
**When to Use**: The single most important action on a screen. "Start Game,"
"Confirm," "Accept," "Buy." There should be at most one Primary button visible
at a time. It is the answer to "what does the player most likely want to do here?"
**When NOT to Use**: Alternative or secondary actions; destructive actions that
require confirmation before the consequence is irreversible; any action that is
not the primary intent of the screen.

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Default | Full-opacity fill, primary color from art-bible. Label centered. | — | — | — | — |
| Hovered (mouse) | Brightness +15%, subtle scale 1.03x, cursor changes to pointer | Mouse over element | Transition from Default | 80ms ease-out | [UI hover sound — see Sound Standards] |
| Focused (keyboard/gamepad) | Focus ring visible (2px, offset 3px, high contrast color). Same brightness as Hovered. | Tab / D-pad navigation | Transition from Default | 80ms ease-out | [UI focus sound — same as hover] |
| Pressed | Scale 0.97x, brightness -10% | Click / Enter / A (Xbox) / Cross (PS) | Action fires on press-up, not press-down. Scale on press-down. | 60ms ease-in for press; 80ms ease-out on release | [UI confirm sound] |
| Disabled | 40% opacity, no pointer cursor, no hover state | — | No response | — | — |
| Loading (post-press) | Replace label with spinner. Button remains at pressed scale, disabled state. | — | Prevents double-submission | Duration of async operation | — |

**Accessibility**:
- Keyboard: Tab to focus, Enter or Space to activate. Must be reachable from any other interactive element on screen via Tab sequence.
- Gamepad: D-pad or left stick to navigate focus to button. A (Xbox) / Cross (PS) to activate. Focus must be placed on Primary button by default when screen opens.
- Screen reader: Button must expose accessible name matching visible label. Role: "button." State: "dimmed" when disabled. Activation announcement: "[Label] button — [result of action, if known]."
- Colorblind: Do not rely on color alone to distinguish Primary from Secondary. Primary uses higher visual weight (fill vs. outline, or larger size) in addition to color differentiation.
- Minimum touch target: 44x44pt (iOS HIG) / 48x48dp (Android). Apply even on PC if touch support is possible.

**Implementation Notes**:
[Unity (uGUI): a `Button` with a custom transition (sprite swap or animation) for
the states, rather than changing shared styles mid-state. Keep it a `Selectable` in
the navigation graph so keyboard and gamepad can focus it. For the scale animation,
animate a parent `RectTransform` — scaling the Button itself can clip children. In
UI Toolkit, use USS `:hover`, `:active` and `:focus` pseudo-classes.]

---

#### Button (Secondary)

**Category**: Input
**Status**: Draft
**When to Use**: Alternative or cancel action. "Back," "Cancel," "Skip," "Maybe
Later." Lower visual weight than Primary — it should recede visually, not compete.
**When NOT to Use**: Destructive actions (use Button (Destructive)). The most
important action on the screen (use Button (Primary)).

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Default | Outlined style (border only, transparent fill), secondary color. Slightly smaller or lower weight than Primary. | — | — | — | — |
| Hovered | Background fill appears at 15% opacity. Border brightens. Scale 1.02x. | Mouse over | Transition from Default | 80ms ease-out | [UI hover sound — softer variant than Primary] |
| Focused | Focus ring, same specification as Primary. | Tab / D-pad | Transition from Default | 80ms ease-out | [UI focus sound] |
| Pressed | Scale 0.97x, fill opacity increases to 30% | Click / Enter / B (Xbox) / Circle (PS) on focused state | Action fires on press-up | 60ms ease-in | [UI cancel/back sound] |
| Disabled | 40% opacity | — | No response | — | — |

**Accessibility**: Same requirements as Button (Primary). Accessible name must
match visible label. In a dialog with Primary and Secondary buttons, the Secondary
button typically maps to the platform "cancel" input (B / Circle / Escape) as well
as direct focus activation.

**Implementation Notes**: [Same as Button (Primary). Where a Primary and Secondary
appear together, ensure Secondary is always positioned consistently — right/bottom
of Primary on horizontal layouts, or below Primary on vertical layouts. Consistency
across screens is more important than per-screen aesthetic preference.]

---

#### Button (Destructive)

**Category**: Input
**Status**: Draft
**When to Use**: Any action that is irreversible and causes loss of player data or
significant progress: "Delete Save File," "Reset All Settings," "Leave Match,"
"Discard Changes." The visual treatment signals danger before the player presses.
**When NOT to Use**: Actions that can be undone, or actions that are merely
consequential but reversible.

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Default | Outlined or filled with destructive color (typically a desaturated red — confirm colorblind compatibility in accessibility-requirements). Label may include a warning icon. | — | — | — | — |
| Hovered / Focused | Same behavior as Button (Primary) hover/focus but with destructive color | — | — | 80ms | [UI hover sound] |
| Pressed (first press) | Does NOT execute the action. Instead, opens Confirmation Dialog pattern (see below). The button itself shows a brief pulse animation. | Click / Enter | Trigger Confirmation Dialog | 100ms pulse | [UI warning sound — distinct from standard confirm] |
| — | Confirmation Dialog handles the actual execution | — | — | — | — |
| Disabled | 40% opacity | — | No response | — | — |

> **Critical rule**: A Button (Destructive) NEVER executes its action directly.
> It always triggers a Confirmation Dialog. There are no exceptions. A player
> who presses it by accident must always have one more opportunity to back out.
> Games that skip confirmation on destructive actions generate the most visible
> negative community sentiment of any UX failure type. See: every "accidentally
> deleted save file" complaint on any game forum.

**Accessibility**: Screen reader must announce the destructive nature: "[Label] button — this action cannot be undone." In addition to accessible name, use the `description` property if available to add the warning text.

**Implementation Notes**: [Destructive button triggers a separate Confirmation Dialog scene. Pass the action callback to the dialog — the button itself does not hold the execution logic. This separation prevents accidental execution if the confirmation dialog has a bug.]

---

#### Toggle

**Category**: Input
**Status**: Draft
**When to Use**: Binary on/off settings where both states are equally valid and
the current state must be visible at a glance. "Subtitles: On/Off," "Aim Assist:
On/Off," "Notifications: On/Off."
**When NOT to Use**: Selections from more than two options (use Dropdown). Actions
that happen once rather than representing a persistent state (use Button). Cases
where the consequence of toggling is complex enough to need explanation (show
a description field alongside).

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Off / Default | Track: muted fill. Thumb: leftmost position. Label: "Off" or state label. | — | — | — | — |
| Hovered | Track brightens 10%. Cursor: pointer. | Mouse over | Transition | 60ms | [UI hover sound] |
| Focused | Focus ring around entire toggle element (track + thumb). | Tab / D-pad | — | 60ms | [UI focus sound] |
| Pressed / Activated | Thumb slides to right side. Track fill changes to active color. Label changes to "On" or active state label. State persists. | Click / Enter / A / Cross | Toggle state change. Fire onChange event. Persist value. | 150ms ease-in-out for slide | [Toggle ON sound] |
| Pressed / Deactivated | Thumb slides to left. Track reverts to muted fill. | Same inputs | Toggle state change | 150ms ease-in-out | [Toggle OFF sound — subtly different from ON] |
| Disabled | 40% opacity. No interaction. Current state still visible. | — | No response | — | — |

**Accessibility**:
- Keyboard/Gamepad: Space or Enter to toggle. Avoid requiring directional inputs (left/right) to toggle — some users cannot predict that behavior.
- Screen reader: Role: "switch." State: "on" or "off" — the accessible name should NOT include the state (the screen reader announces state separately). Correct: accessible name "Subtitles," state "on." Incorrect: accessible name "Subtitles On."
- The toggle label (not just the visual thumb position) must change to show current state for players who cannot reliably distinguish left from right positions.

**Implementation Notes**: [Unity: use a custom `Toggle` prefab. The built-in
`Toggle` provides the selection behaviour but a checkbox-style visual; a custom
slide-toggle animation may be needed for the target art style. Ensure the slide
animation is skipped when motion reduction mode is active — in that case, snap to
the final state instantly.]

---

#### Slider

**Category**: Input
**Status**: Draft
**When to Use**: Selecting a value from a continuous range where approximate values
are acceptable and the range and relative position matter. Volume (0–100%), brightness,
text size. The visual representation of position is itself useful information.
**When NOT to Use**: Precise value entry (use Input Field). Selection from a short
discrete list (use Dropdown). Binary state (use Toggle).

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Default | Track (full width). Fill (left of thumb, shows current value). Thumb (draggable handle). Current value label (right of track or above thumb). | — | — | — | — |
| Hovered | Thumb enlarges slightly (1.2x). Track brightens. | Mouse over | — | 60ms | — |
| Focused | Focus ring on thumb. Track brightens. | Tab / D-pad | — | 60ms | [UI focus sound] |
| Dragging (mouse) | Thumb follows cursor. Fill updates in real time. Value label updates in real time. | Click + drag on thumb | Continuous value update. Fire onChange continuously. | Real time | [Slider adjust sound — subtle, loops while dragging] |
| Keyboard / D-pad adjust | Thumb moves one step (5% of range per press, or 1 discrete unit). | Left/Right arrows or Left/Right D-pad while focused | Step value change. Fire onChange per step. | Instant | [Slider step sound — one click per step] |
| Keyboard fast adjust | Larger step (25% of range). | Page Up / Page Down while focused | Large step value change | Instant | [Same step sound] |
| Released | Value locks. onChange fires final value. | Mouse release | — | — | — |
| Disabled | 40% opacity. No interaction. Value visible. | — | No response | — | — |

**Accessibility**:
- Keyboard: Left/Right arrows to adjust by small step. Page Up/Page Down for large step. Home/End to jump to min/max.
- Screen reader: Role: "slider." Accessible name: the label (e.g., "Music Volume"). Current value announced on every change: "Music Volume, 80 percent." Min/max values announced on first focus.
- All sliders must show a numeric value alongside the visual position. Relying only on track fill position excludes players who cannot perceive relative position.

**Implementation Notes**: [Unity `Slider`: set whole numbers or the step in code to the
appropriate increment. Add Page Up/Down support by handling those keys while the
slider is selected. Bind `onValueChanged` to update the displayed numeric label. When
motion reduction mode is enabled, ensure value label updates are the sole feedback —
do not suppress them. Rumble feedback on gamepad slider adjustment is a nice
enhancement for accessibility.]

---

#### Dropdown / Select

**Category**: Input
**Status**: Draft
**When to Use**: Selection from a discrete list of 3-15 options where only the
selected value needs to be visible at rest. Display resolution, language, window
mode, input preset. The closed state shows only the current selection.
**When NOT to Use**: Binary choices (use Toggle). More than ~15 options (use a
full List pattern or a scrollable Select). When comparing options matters as much
as selecting one (show options visibly, e.g., as a horizontal selector or list).

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Closed / Default | Label (left). Current value (right). Chevron-down icon (far right). | — | — | — | — |
| Hovered | Row background fills at 10% opacity | Mouse over | — | 60ms | — |
| Focused (closed) | Focus ring on entire row. | Tab / D-pad | — | 60ms | [UI focus sound] |
| Opening | Dropdown list appears below (or above if near screen bottom). List items visible. Previously selected item highlighted. Focus moves to selected item inside list. | Click / Enter / A / Cross | Open list | 100ms ease-out (expand) | [UI expand sound] |
| List item hovered/focused | List item highlights | Mouse / D-pad | — | 60ms | [UI hover sound] |
| List item selected | List closes. Closed state shows new value. onChange event fires. | Click / Enter / A / Cross on item | Select value, close list | 80ms ease-in (collapse) | [UI confirm sound] |
| Dismissed without selecting | List closes. Value unchanged. | Escape / B / Circle / click outside | Dismiss | 80ms | [UI cancel sound] |
| Disabled | 40% opacity. No interaction. | — | — | — | — |

**Accessibility**:
- Keyboard: Up/Down arrows navigate list items while open. Enter selects. Escape dismisses. First letter of an option jumps focus to first matching item.
- Screen reader: Role: "combobox." Accessible name: the field label. Expanded/collapsed state announced. Current value announced when focused. Each list item announces its value and position: "English, 1 of 12."
- The dropdown list must never obscure the current item or the control that opened it — this is a common failure on small screens.

**Implementation Notes**: [Unity: the TextMeshPro `TMP_Dropdown` covers the common
case; for custom visuals, a `Button` (the closed state) that reveals a list panel by
animation. Ensure the list positions itself above the control if it would be clipped
by the screen bottom. Close it on a click outside its rect.]

---

#### List Item

**Category**: Layout / Input
**Status**: Draft
**When to Use**: A single selectable row in a vertically scrollable list. Achievements,
quest log entries, settings categories, save file slots. The list is the container;
this is the row within it.
**When NOT to Use**: Grid layouts where items exist in two dimensions (use Grid Item).
Non-selectable content rows (remove hover/focus states and the pressed state).

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Default | Full-width row. Icon (optional, left). Primary label. Secondary label / metadata (right or below primary). Chevron (right, if navigates deeper). | — | — | — | — |
| Hovered | Row background at 12% opacity highlight. | Mouse over | — | 60ms | — |
| Focused | Focus ring on row OR row background at 20% opacity (consistent with platform convention). | D-pad / Tab | — | 60ms | [UI focus sound] |
| Selected (persistent) | Row background at 25% opacity. May show a selection indicator (left border, checkmark). Distinct from focused state — a row can be selected but not focused. | — | Rendered state | — | — |
| Pressed / Activated | Brief brightness flash, then navigates or performs action | Click / Enter / A / Cross | Navigation or action | 80ms flash | [UI confirm sound] |
| Disabled | 40% opacity. No interaction. | — | — | — | — |

**Accessibility**:
- Keyboard/Gamepad: Up/Down arrows or D-pad to move between list items. The list must handle focus cycling — reaching the bottom should stop (not wrap) unless wrapping is explicitly designed.
- Screen reader: Role: "listitem." Parent list role: "list." Accessible name: primary label content. Metadata (secondary label) is optionally included in the description. Position announced: "Quest Log, 3 of 12."
- Minimum row height: 44pt / 48dp for touch. For controller-primary platforms, 56px rows are more comfortable.

**Implementation Notes**: [Unity: a `ScrollRect` with a vertical layout group as its
content. Each row is a prefab with its own `Selectable`. Keyboard and gamepad
navigation moves selection between rows, but the `ScrollRect` does not scroll to
keep the selected row in view on its own — scroll it when selection changes.]

---

#### Grid Item

**Category**: Layout / Input
**Status**: Draft
**When to Use**: A selectable cell in a two-dimensional grid. Inventory slots,
ability select, crafting ingredient selection, character portrait selection. The
grid is the container; this is the cell.
**When NOT to Use**: Single-column content (use List Item). Non-selectable display
cells (remove interactive states).

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Empty | Empty slot visual (subtle border or dashed outline). Different from disabled. | — | — | — | — |
| Populated | Item icon fills cell. Stack count (bottom right, if applicable). Quality indicator (border color or icon overlay). | — | — | — | — |
| Hovered | Brightness +15%. Tooltip appears after 400ms delay. | Mouse over | — | 60ms | — |
| Focused | Focus ring (2px, offset 2px). Same brightness as hovered. Tooltip appears after 400ms delay or immediately on gamepad. | D-pad navigation | — | 60ms | [UI focus sound] |
| Selected (persistent) | Distinct border (thicker, contrasting color). May show selection checkmark. | Click / Enter / A / Cross | Select item. Can coexist with focused state on a different cell. | Instant | [UI select sound] |
| Pressed | Brief scale 0.95x, then executes action | Double-click / Enter / A / Cross | Action (equip, use, inspect — defined by context) | 80ms | [UI confirm sound] |
| Locked | Padlock overlay icon on populated content. No hover/focus states. | — | No interaction | — | — |
| Drag source | Cell dims (50% opacity), drag preview appears at cursor. | Click + drag (mouse only) | Begin drag operation | Instant | [UI grab sound] |
| Drop target (valid) | Cell brightens, accepting color indicator | Item dragged over | — | 60ms | — |
| Drop target (invalid) | Red tint or shake animation | Item dragged over invalid slot | — | 60ms | [UI error sound] |

**Accessibility**:
- Keyboard/Gamepad: D-pad or arrow keys navigate cells. The grid must communicate its dimensions to screen readers. Row/column position announced.
- Screen reader: Role: "gridcell." Parent role: "grid." Accessible name: item name (or "empty slot" for empty cells). State: "selected" when selected, "dimmed" when locked. Position: "row 2, column 3."
- Tooltips must be reachable by keyboard — they must appear when the cell is focused, not only when hovered.

**Implementation Notes**: [Unity: a `GridLayoutGroup` with a fixed column count.
Each cell is a `Selectable` prefab. Set explicit navigation (left/right/up/down)
from each cell's index and the column count when the automatic navigation picks the
wrong neighbour.]

---

#### Modal Dialog

**Category**: Feedback / Layout
**Status**: Draft
**When to Use**: A decision or acknowledgment that must be resolved before the
player can continue. The dialog is blocking — background content is dimmed and
non-interactive. "Are you sure?", "Your progress will be saved.", error states.
**When NOT to Use**: Non-blocking notifications (use Toast / Notification). Information
that can wait until the player is ready (add it to a persistent help system instead).
Dialogs that should allow the player to continue playing behind them.

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Opening | Background overlay animates from 0 to 60% opacity. Dialog panel scales from 0.9 to 1.0. Dialog enters from center (not from an edge). | Triggered by code | Focus moves to first interactive element in dialog (or the Primary button) | 200ms ease-out | [UI modal open sound] |
| Active | Background non-interactive. Dialog has all input focus. Player cannot interact with background. | Keyboard / gamepad navigates within dialog only | — | — | — |
| Dismissing (confirmed) | Dialog panel scales to 1.1 then fades. Overlay fades to 0%. | Primary button pressed | Execute action, return focus to trigger element | 180ms | [UI confirm sound] |
| Dismissing (cancelled) | Dialog panel scales to 0.9 then fades. Overlay fades to 0%. | Secondary button / Escape / B / Circle | No action, return focus to trigger element | 150ms | [UI cancel sound] |
| Cannot dismiss | If the dialog represents a blocking error, do not provide a cancel path. Provide only resolution options. | — | — | — | — |

> **Focus trap rule**: While a modal dialog is open, Tab and D-pad navigation
> must cycle within the dialog's interactive elements only. It must not be possible
> to navigate focus outside the dialog to the background content. This is both
> an accessibility requirement (WCAG 2.1 SC 2.1.2) and a UX integrity requirement.
> When the dialog closes, focus must return to the element that triggered it,
> not to the top of the page.

**Accessibility**:
- Screen reader: Dialog container role: "dialog." Accessible name: dialog title (required — every dialog must have a title, even if visually hidden). On open, screen reader announces dialog title and first focusable element. Focus trap active.
- Keyboard: Escape key always maps to the cancel/dismiss action (same as Secondary button or close button). Enter always maps to the primary/confirm action.
- Motion reduction: Scale animation replaced with instant appear/disappear. Overlay fade retained at 100ms (faster).

**Implementation Notes**: [Unity: a dedicated `Canvas` with a high sorting order
(100+) so it renders above all game content. The background overlay is a full-screen
`Image` at 60% black opacity. Select the dialog's primary button
(`EventSystem.SetSelectedGameObject`) after the open animation completes. Implement
the focus trap by keeping navigation inside the dialog's selectables while it is open.]

---

#### Confirmation Dialog

**Category**: Feedback / Layout
**Status**: Draft
**When to Use**: The specific case of confirming a destructive action. Always
triggered by Button (Destructive). Always has exactly two options: confirm (labeled
with the specific action, not "OK") and cancel.
**When NOT to Use**: Non-destructive confirmations. Errors or notifications that
do not require a decision. Any dialog with more than two actions.

> **Label rule**: The confirm button must be labeled with the specific action,
> not a generic "OK" or "Yes." "Delete Save File" not "OK." "Leave Match" not
> "Yes." This reduces mistakes for players who have difficulty reading the dialog
> content quickly. The pattern comes from Apple HIG and is validated by decades
> of usability research.

**Structure**:
- Title: Brief, action-describing. "Delete save file?" not "Are you sure?"
- Body: One sentence stating the consequence. "This cannot be undone."
- Confirm button: Button (Primary) — labeled with the specific action. "Delete Save File."
- Cancel button: Button (Secondary) — "Cancel."
- Default focus: Cancel (safer default — reduces accidental destructive actions).

**Accessibility**: Inherits all Modal Dialog accessibility. Additionally: screen
reader announces "Alert dialog, [title]" to signal destructive context. Default
focus on Cancel is a requirement, not a preference.

**Implementation Notes**: [Confirmation Dialog is a specific instance of Modal
Dialog — implement it as a subclass or as a parameterized scene. The default
focus on Cancel is critical: set `grab_focus()` on the Cancel button, not the
Confirm button, after open animation completes.]

---

#### Toast / Notification

**Category**: Feedback
**Status**: Draft
**When to Use**: Brief, non-blocking information that does not require a player
decision. "Game saved." "Achievement unlocked." "Your inventory is full." The player
can continue playing; the notification disappears on its own.
**When NOT to Use**: Information that requires a decision (use Modal Dialog).
Errors that require the player to take action. Critical information that the player
must not miss.

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Entering | Slides in from screen edge (typically bottom-right, away from primary action areas). Fades from 0 to 100% opacity. | Triggered by code | — | 200ms ease-out | [Sound matching notification type — see Sound Standards] |
| Displayed | Full opacity. Optional: icon (left), title, body text (optional), dismiss button (X, optional). | Pointer hover pauses auto-dismiss timer | Pause auto-dismiss | — | — |
| Auto-dismiss | Fades from 100 to 0% opacity, slides out | Timer expires (5 seconds default for one-line; 8 seconds for two-line) | Remove from queue | 200ms ease-in | — |
| Manual dismiss | Fades and slides out immediately | Click/tap X button or swipe on touch | Remove | 150ms | [UI cancel sound, quiet] |
| Queue overflow | New notification pushes oldest out early | New notification triggered while previous is displayed | FIFO queue, max 3 simultaneous | — | — |

**Accessibility**:
- Screen reader: Toasts must be read aloud without requiring focus. In HTML, this uses `role="status"` or `role="alert"`. In game UI, this requires the engine's accessibility notification system. Verify engine support in engine-reference docs.
- Motion reduction: Slide animation replaced with fade only.
- Toasts must never be the sole communication channel for information the player needs to act on. If the information requires action, use a persistent UI element in addition to the toast.
- Auto-dismiss timer: 5 seconds is the minimum. Players with cognitive processing differences may need more time. Consider a setting to extend to 10 or 15 seconds.

**Implementation Notes**: [Unity: manage a queue of toast prefabs in a vertical layout
group anchored to a screen corner. Each toast is instantiated, added to the
container, then auto-removed after a timer. The container's `Canvas` sorts high
(50+) but below modal dialogs (100+). Animate a `CanvasGroup` alpha and the x
position; when motion reduction is active, skip the position animation.]

---

#### Tooltip

**Category**: Feedback
**Status**: Draft
**When to Use**: Contextual information that supplements a visible label. Item
descriptions in inventory. Stat explanations on a character sheet. Setting
descriptions in accessibility options. The player must be able to access this
information or proceed without it.
**When NOT to Use**: Information the player MUST read to complete an action — put
that in the label or body text, not a tooltip. Tooltips are not discoverable
on mobile touch without a hover state. On touch-only platforms, use an info button
that opens a description modal instead.

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Hidden | — | — | — | — | — |
| Hover trigger | — | Mouse enters element | Begin 400ms delay timer | — | — |
| Gamepad/keyboard trigger | — | Element receives focus | Begin 300ms delay timer (shorter because navigation is intentional) | — | — |
| Appearing | Tooltip panel fades in and scales from 0.95 to 1.0. Positioned near element (prefer above, adjust if near screen edge). | Timer expires | Show tooltip | 120ms ease-out | — |
| Displayed | Tooltip visible. Title (optional). Body text. Max width: 300px. Multiple lines allowed. | — | — | — | — |
| Hiding | Tooltip fades out | Mouse leaves element / focus moves away | Hide tooltip | 80ms ease-in | — |

**Accessibility**:
- Screen reader: Tooltip content must be accessible without hover. The accessible name of the parent element should include the most critical tooltip information. The full tooltip text is optionally in the `description` property. Screen reader reads tooltip content when element is focused.
- The delay (300-400ms) prevents accidental tooltip display and is required — instant tooltips are disruptive in gamepad navigation.
- Tooltip text must meet the same contrast requirements as body text (4.5:1 minimum).

**Implementation Notes**: [Unity: a tooltip prefab shown and hidden after a delay
(coroutine or timer). Place it on a high-sorting `Canvas` so it appears above all
other UI. For screen edges, check whether its rect extends beyond the screen and flip
it to the opposite side.]

---

#### Progress Bar

**Category**: Feedback / Layout
**Status**: Draft
**When to Use**: Linear progress toward a defined endpoint. Loading screens (time
to completion), XP fill toward next level, quest objectives with countable progress
("3 of 10 enemies defeated"), download progress.
**When NOT to Use**: Circular or radial progress (use a separate Radial Progress
pattern if needed). Values that fluctuate up and down rapidly (use Health/Resource
Bar pattern). Values with no defined endpoint.

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Default | Track (full width, background color). Fill (left to right, value color). Value label (percentage or N/M, outside or inside fill). | — | — | — | — |
| Value increasing | Fill width animates to new value | Value changes | Smooth fill animation | 300ms ease-out | [Context-dependent — XP gain has a sound; loading has none] |
| Value at maximum | Fill reaches full width. Optional: completion animation (pulse, glow). | Value reaches 100% | Completion event fires | 200ms | [Completion sound if appropriate] |
| Value at zero | Fill hidden (zero width). Track still visible. | — | — | — | — |
| Indeterminate (unknown duration) | Animated loop (fill segment moves left-to-right, repeat). Used for loading of unknown duration. | — | — | Infinite loop | — |

**Accessibility**:
- Screen reader: Role: "progressbar." Accessible name: what is progressing (e.g., "Experience Points," "Loading"). Value: current numeric value AND percentage AND maximum. "Experience Points, 450 of 1000, 45 percent." Update on significant changes (not every pixel).
- Do not rely only on fill color to communicate value. Include a numeric label.
- Indeterminate progress bars: announce "Loading, in progress" — do not announce changes since the value is unknown.
- Motion reduction: Indeterminate animation is replaced with a static "loading" indicator. Smooth fill animation is replaced with instant jump to new value.

**Implementation Notes**: [Unity: a filled `Image` (or a `Slider` without
interaction) with custom styling. For indeterminate mode there is no built-in
state — animate a looping fill element's position. Ensure the loop is paused when
motion reduction mode is active and a static indicator is shown instead.]

---

#### Input Field

**Category**: Input
**Status**: Draft
**When to Use**: Text entry. Player name on a new save, search within a list,
remapping a key binding (special case — shows the key press, not typed text),
entering a numeric value precisely.
**When NOT to Use**: Selecting from known options (use Dropdown or List). On
console-primary platforms, minimize text entry — it requires a virtual keyboard,
which is high friction.

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Default | Field border, placeholder text (label-style, muted color), empty input area. | — | — | — | — |
| Hovered | Border brightens slightly | Mouse over | — | 60ms | — |
| Focused | Border brightens fully. Cursor (blinking, 530ms on/530ms off). Placeholder text hidden. | Tab / click | Open virtual keyboard on console/mobile | Instant | [UI focus sound] |
| Typing | Characters appear. Cursor advances. | Keyboard input | Update field value | Immediate | [Subtle keystroke sound, optional] |
| Value present | Field shows typed value. Placeholder hidden. Clear button appears (X, right of field) if value is non-empty. | — | — | — | — |
| Character limit reached | No further input accepted. Optional: brief shake animation and limit indicator changes color. | Input at limit | Reject further characters | 200ms shake | [UI error sound, subtle] |
| Clear | Field empties. Cursor returns. Clear button disappears. | Click X / gamepad clear input | Clear value | Instant | [UI cancel sound, subtle] |
| Validation error | Border turns error color (red — ensure colorblind safe). Error message appears below field. | On submit or on blur | Show error | Instant | [UI error sound] |
| Validated / correct | Border turns success color (green — ensure colorblind safe). Success icon optional. | On validation pass | — | Instant | — |
| Disabled | 40% opacity, no interaction. Value still visible. | — | — | — | — |

**Accessibility**:
- Keyboard: All standard text editing shortcuts (Home, End, Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+Z).
- Screen reader: Role: "textbox." Accessible name: field label (not placeholder text). Current value announced. Character limit announced when reached. Validation errors announced immediately on occurrence.
- Placeholder text must not be used as the only label — a visible label above or beside the field is required. Placeholder text disappears when the player types, causing confusion for players with cognitive or memory impairments.

**Implementation Notes**: [Unity `TMP_InputField`: set the placeholder for the hint
but always include a visible label as the field's accessible name. Bind
`onValueChanged` for real-time validation and `onSubmit` for form submission on
Enter. On console, use the platform's virtual keyboard — verify against
docs/engine-reference/unity/ for the pinned version's API specifics.]

---

#### Tab Bar

**Category**: Navigation
**Status**: Draft
**When to Use**: Dividing a single screen's content into discrete sections where
only one section is visible at a time. Character sheet tabs (Stats / Equipment /
Skills), settings tabs (Gameplay / Graphics / Audio / Accessibility). Maximum
5-6 tabs before the pattern breaks down and a sidebar navigation should be
considered instead.
**When NOT to Use**: More than 6 tabs. Content that benefits from simultaneous
visibility (use a layout pattern instead). Navigation between different screens
(use Screen Push).

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Default (inactive tab) | Tab label. No active indicator. | — | — | — | — |
| Active tab | Tab label. Active indicator (underline, fill, or contrasting background). Content area shows this tab's content. | — | — | — | — |
| Hovered (inactive) | Tab background fills slightly | Mouse over | — | 60ms | — |
| Focused (keyboard/gamepad) | Focus ring on tab label. | Tab key (within tab bar) or D-pad left/right on tab row | — | 60ms | [UI focus sound] |
| Activated | Active indicator transitions to this tab. Content area transitions (fade or slide). | Click / Enter / A / Cross | Switch active tab. Content update. | 150ms ease | [UI tab switch sound] |
| Gamepad shoulder button | — | L1/R1 (PS) or LB/RB (Xbox) | Switch to previous/next tab (standard platform convention) | 150ms | [UI tab switch sound] |

**Accessibility**:
- Keyboard: Arrow keys navigate between tabs within the tab bar (left/right). Tab key moves focus into the content area below. This follows the ARIA tab panel pattern.
- Screen reader: Role: "tab" for individual tabs. Role: "tablist" for the container. Role: "tabpanel" for the content area. Active tab state: "selected." Accessible name: tab label. Tabpanel is labeled by its corresponding tab.
- The active tab must be visually distinguishable by more than color alone (underline, fill pattern, or weight change in addition to color).

**Implementation Notes**: [Unity: implement manually with a horizontal layout group
of tab buttons and a content panel per tab. The shoulder button shortcut (LB/RB) is
an Input System action handled by the screen — there is no built-in tab control
for it. Check platform conventions: Xbox uses LB/RB; PlayStation uses L1/R1;
both are the same physical button, so a single binding works.]

---

#### Scroll Container

**Category**: Layout
**Status**: Draft
**When to Use**: Content that exceeds the visible area of its container. Inventory
lists, lore entry text, credits, long settings lists. The scroll indicator shows
the player that more content exists.
**When NOT to Use**: Content that can be paginated instead (pagination may be
clearer for dense list navigation). Infinite scroll (always provide a loading
state and an end state).

**Interaction Specification**:

| State | Visual | Input | Response | Duration | Audio |
|-------|--------|-------|----------|----------|-------|
| Content fits | No scrollbar visible (or always-visible scrollbar at full height, depending on art direction). | — | — | — | — |
| Scrollable | Scrollbar appears (right edge). Scrollbar thumb size represents viewport vs. content ratio. | — | — | — | — |
| Scrolling (mouse) | Content moves. Scrollbar thumb moves proportionally. | Mouse wheel | Scroll by 3 lines per wheel tick (configurable in OS) | Smooth | — |
| Scrollbar drag | Content moves. Thumb follows pointer. | Click + drag scrollbar thumb | Scroll proportionally | Real time | — |
| Keyboard scroll | Content moves one item height per keypress. | Up/Down arrows when container is focused and no child is focused | Scroll by one unit | Immediate | — |
| Gamepad scroll | Content moves to keep focused item in view. | D-pad navigation to items beyond visible area | Auto-scroll to keep focused item visible | Smooth 150ms | — |
| Scroll top / bottom | Content stops. Scrollbar thumb at end. | Content boundary reached | Stop scrolling | — | — |
| Focus follows scroll | When a child element receives focus, scroll container ensures it is fully visible. | Any child receives focus | Scroll to reveal focused element | 200ms ease | — |

**Accessibility**:
- Keyboard/Gamepad: The scroll container itself should not require explicit scrollbar interaction — navigating list items inside it should auto-scroll to keep focused items in view.
- Screen reader: The scroll container announces "scrollable" and the scroll position ("showing items 5 through 15 of 30"). This requires engine accessibility support — verify in docs/engine-reference/unity/.
- Fade edges (content fading at scroll boundaries to indicate more content exists) are a helpful visual affordance but must not be the only indicator that content exists beyond the visible area. Include a scrollbar.

**Implementation Notes**: [Unity `ScrollRect`: when selection changes to a child
inside it, scroll so the selected child is fully visible. For smooth scroll
animation, interpolate `normalizedPosition` rather than setting it directly. In UI
Toolkit, `ScrollView.ScrollTo` brings an element into view.]

---
