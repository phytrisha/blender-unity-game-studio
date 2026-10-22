#!/usr/bin/env python3
"""Figma Weave spend guard + ledger (the art department's paid image/3D generation).

PreToolUse  (mcp__*weave_run_model|weave_run_tool): a call that carries `acknowledgedCost` spends credits. Deny it
            when the ledger total + this run would exceed the cap in production/art/weave-budget.json
            ({"cap": 300}). No budget file = no cap, and the report says so. Quotes (no acknowledgedCost) pass.
PostToolUse (same tools): append every paid run to production/art/weave-ledger.jsonl: model/tool id, inputs
            (prompt, params, asset ids), cost, runs, returned ids. It is the spend record and the recipe to
            reproduce a texture. Tripo logs to sources/tripo/LOG.tsv, AI Hub to textures/<Set>/gen.sh.
Approval itself is not checked here (a hook cannot see the conversation): skills ask per run, always, in every
automation mode, because paid external generation is irreversible (.claude/docs/art-pipeline/texturing.md).
Usage: weave-guard.py pre|post
"""
import json, os, sys, time

mode = sys.argv[1] if len(sys.argv) > 1 else "pre"
root = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
art = os.path.join(root, "production", "art")
ledger, budget = os.path.join(art, "weave-ledger.jsonl"), os.path.join(art, "weave-budget.json")
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = data.get("tool_input", {}) or {}
cost = ti.get("acknowledgedCost")
if cost is None:
    sys.exit(0)                      # a quote: spends nothing


def spent():
    total = 0.0
    if os.path.exists(ledger):
        for line in open(ledger):
            try:
                e = json.loads(line)
                total += max(float(e.get("cost") or 0), 0) * int(e.get("runs") or 1)
            except Exception:
                pass
    return total


if mode == "pre":
    runs = int(ti.get("numberOfRuns", 1) or 1)
    want = max(float(cost), 0) * runs   # dynamic-cost tools pass -1: counted as 0, the post hook logs the real call
    if os.path.exists(budget):
        try:
            cap = float(json.load(open(budget)).get("cap", 0) or 0)
        except Exception as e:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                  "permissionDecisionReason": f"production/art/weave-budget.json is unreadable ({e}); fix it before spending."}}))
            sys.exit(0)
        now = spent()
        if cap and now + want > cap:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse", "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Weave budget: {now:.1f} of {cap:.0f} credits used, this run needs {want:.1f}. "
                    "Ask the user to raise the cap in production/art/weave-budget.json or skip this run.")}}))
    sys.exit(0)

resp = data.get("tool_response")
entry = {
    "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "tool": data.get("tool_name", "").rsplit("__", 1)[-1],
    "id": ti.get("id") or ti.get("recipeId"),
    "version": ti.get("version"),
    "cost": cost, "runs": ti.get("numberOfRuns", 1),
    "input": ti.get("input") or ti.get("inputs"),
    "response": resp if isinstance(resp, (dict, list)) and len(json.dumps(resp)) < 4000 else str(resp)[:4000],
}
os.makedirs(art, exist_ok=True)
with open(ledger, "a") as f:
    f.write(json.dumps(entry) + "\n")
sys.exit(0)
