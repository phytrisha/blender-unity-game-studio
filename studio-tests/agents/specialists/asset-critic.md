# Agent Test Spec: asset-critic

## Agent Summary
Domain: independent visual review of one asset stage — renders and Unity captures vs reference, brief and art bible; runs the AD-ASSET gate.
Does NOT own: fixing anything (read-only except extra renders under `renders/<Name>/`), the brief or the art bible.
Gate IDs handled: AD-ASSET (verdicts APPROVE / REVISE / REJECT, or NOT ASSESSED).

---

## Static Assertions (Structural)

- [ ] `description:` says independent and that it never sees the builder's summary
- [ ] `tools:` has Read, Glob, Grep, Bash and no Write/Edit
- [ ] Model tier is `inherit`
- [ ] Definition requires reading `.claude/docs/director-gates/ad-asset.md` first and starting with `AD-ASSET: <verdict>`

---

## Test Cases

### Case 1: Clean stage
**Scenario:** model stage sheets match the reference crops; QA no FAIL.
**Assertions:**
- [ ] First line `AD-ASSET: APPROVE`; includes the qa_check SUMMARY line

### Case 2: Problems found
**Scenario:** the lid is 20 % too tall vs the reference; a bracket floats 3 cm.
**Assertions:**
- [ ] First line `AD-ASSET: REVISE`; each finding has view, evidence (sheet path + where) vs reference crop, fix, confidence ≥ 80
- [ ] At most ~8 findings, most important first; no praise padding

### Case 3: Missing input
**Scenario:** no reference crops given.
**Assertions:**
- [ ] `AD-ASSET: NOT ASSESSED`, naming the missing reference

### Case 4: Builder's claim in the prompt
**Scenario:** the prompt (wrongly) includes "the 3d-artist says it matches".
**Assertions:**
- [ ] Treats it as no evidence; judges only images and numbers

### Case 5: Approach can't work
**Scenario:** budget 800 tris but the reference shows a dense wicker basket modelled per strand.
**Assertions:**
- [ ] `AD-ASSET: REJECT` with the reason (route/tool/brief must change)

### Case 6: Missing view
**Scenario:** no back view rendered.
**Assertions:**
- [ ] Renders it with `render_views.py --tag critic` before judging; writes nothing else

---

## Protocol Compliance
- [ ] Verdict vocabulary exactly from the gate; NOT ASSESSED outranks APPROVE and is outranked by REVISE/REJECT
- [ ] Never edits asset files, scripts, brief or bible
