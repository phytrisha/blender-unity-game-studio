#!/usr/bin/env python3
"""PreToolUse (Write|Edit|NotebookEdit|Bash): sources/ is append-only.

sources/ holds the art department's inputs: reference images and concept sheets (sources/reference/), paid
generations (sources/tripo/<Name>/, sources/weave/<Asset>/) and their logs. They are evidence of what was paid
for and what an asset was built from, so they are never edited, moved or deleted. New files arrive through the
tools (tools/tripo_make.sh, `curl -o sources/weave/...`), which this hook does not block. Derived work goes to
blender/assets/<Name>/ (textures/, ref/ crops) or textures/<Set>/.

Denies: Write/Edit of an existing file under sources/; shell rm/mv/truncate/shred on a sources/ path; shell
redirection (>, >>) or cp/rsync/sips/tee onto an existing sources/ file. Deny = JSON on stdout, exit 0.
"""
import json, os, re, sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
tool, ti = data.get("tool_name", ""), data.get("tool_input", {}) or {}
root = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


def rel(p):
    p = os.path.abspath(os.path.join(root, p)) if not os.path.isabs(p) else os.path.abspath(p)
    r = os.path.relpath(p, root)
    return None if r.startswith("..") else r.replace(os.sep, "/")


SRC = re.compile(r"(^|[\s'\"=(])(\./)?sources/")
if tool in ("Write", "Edit", "NotebookEdit"):
    r = rel(ti.get("file_path") or ti.get("notebook_path") or "")
    if r and r.startswith("sources/") and (tool != "Write" or os.path.exists(os.path.join(root, r))):
        deny(f"{r} is an art source (sources/ is append-only: references and paid generations are never edited). "
             "Write derived work to blender/assets/<Name>/ or textures/<Set>/ instead.")
elif tool == "Bash":
    for seg in re.split(r"&&|\|\||;|\n|\|", ti.get("command", "")):
        s = seg.strip()
        if re.match(r"(sudo\s+)?(rm|mv|truncate|shred|unlink)\b", s) and SRC.search(s):
            deny("This command would delete or move something in sources/ (append-only: paid generations and "
                 "references are kept as evidence). Leave it; derived files go to blender/assets/<Name>/.")
        m = re.search(r">>?\s*(\S*sources/\S+)", s)
        if m and os.path.exists(os.path.join(root, m.group(1).lstrip("./"))):
            deny(f"This command overwrites {m.group(1)} in sources/ (append-only). Write to a new file name instead.")
        m = re.match(r"(cp|rsync|sips|tee)\b.*\s(\S*sources/\S+)\s*$", s)
        if m and os.path.isfile(os.path.join(root, m.group(2).lstrip("./"))):
            deny(f"This command overwrites {m.group(2)} in sources/ (append-only). Write to a new file name instead.")
sys.exit(0)
