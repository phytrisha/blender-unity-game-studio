> Gate definition. The spawning skill passes this file's path to the agent; the AGENT reads it — the parent session should not.

# AD-ASSET — Independent Asset Stage Review

Agent: `asset-critic` (runs this gate on the art-director's behalf, independent of the builder) | Model tier: session (inherit)

**Trigger**: At the end of every art stage of one asset (`/produce-asset`, `/art-stage`, `/paint-asset`), before the
stage's gate question; and on demand via `/art-review`.

**Context to pass** (paths, not summaries):
- `blender/assets/<Name>/asset.json` and `BRIEF.md` (the stage's definition of done)
- The reference crops (`blender/assets/<Name>/ref/`, `sources/reference/...`)
- The latest sheets for the stage (`renders/<Name>/*_sheet.png`, Unity captures `renders/unity/*.png`)
- The art bible sections the brief names (by heading)
- The stage name
- **Never** the building agent's report or self-assessment

**Prompt**:
> "Review the <stage> stage of <Name> against its reference, its brief and the art bible. Judge only what the images
> and the numbers show. Render any view you need that is missing. Report concrete, high-confidence problems with
> evidence and fixes, the qa_check SUMMARY line for the stage, and a verdict: APPROVE (meets the stage's definition
> of done), REVISE [the findings that must be fixed before the gate], or REJECT [the approach cannot reach the
> reference or the budget — change the brief, the route or the tool]. If an input this gate needs is missing or
> unreadable, or the stage's numeric check could not run, return NOT ASSESSED naming it."

**Verdicts**: APPROVE / REVISE / REJECT

`NOT ASSESSED` (any missing input, or a stage check that could not run — e.g. no reference, no sheets, `qa_check`
unavailable, Unity editor closed for the Unity stage) outranks APPROVE and is outranked by REVISE and REJECT: a
review that could not look has not established the stage is good, and a found problem is more actionable than an
unknown. The calling skill reports it by name and does not treat it as a pass.
