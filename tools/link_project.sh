#!/bin/bash
# Start a game that USES this studio instead of copying it, or refresh an existing game's links.
#
#   tools/link_project.sh ~/Dev/my-game "My Game"     new game: own files + links into this studio, git + LFS, first commit
#   tools/link_project.sh --relink ~/Dev/my-game      refresh links (new studio files, studio moved, links broken)
#
# The game owns (real files, copied once): CLAUDE.md, README.md, project.yaml, design/, production/, docs/ (engine pin,
#   architecture, registries, perf, art lessons/checklists), .claude/settings.json, .claude/docs/technical-preferences.md
#   (written by /setup-engine), Assets/, Packages/manifest.json, blender/assets/, sources/, textures/, unity/args/,
#   .gitignore, .gitattributes, .env, and .claude/settings.local.json (per machine, gitignored) which adds the studio
#   to permissions.additionalDirectories: without it Claude Code may not read files through the links.
# The studio provides (relative symlinks, so a fix here reaches every linked game):
#   .claude/{agents,skills,hooks,scripts,rules,statusline.sh}, every .claude/docs entry except technical-preferences.md,
#   docs/{WORKFLOW-GUIDE.md,COLLABORATIVE-DESIGN-PRINCIPLE.md,skill-flow-diagrams.md,CLAUDE.md}, tools/, blender/lib,
#   blender/scripts, blender/bases, unity/*.cs, and the Unity package com.phytrisha.studio-pipeline (a relative file:
#   dependency in Packages/manifest.json).
# Links are relative, so the game also works on another machine with the same layout (game and studio side by side,
# e.g. ~/Dev/my-game and ~/Dev/blender-unity-game-studio). .studio records the studio path and commit at link time.
# A studio change reaches every linked game at once: pin a studio tag/commit when a game needs stability.
set -euo pipefail
STUDIO="$(cd "$(dirname "$0")/.." && pwd -P)"
MODE=new; [ "${1:-}" = "--relink" ] && { MODE=relink; shift; }
DST="${1:?usage: link_project.sh <target dir> [\"Game Name\"] | --relink <target dir>}"
NAME="${2:-$(basename "$DST")}"
if [ $MODE = new ]; then
  [ -e "$DST" ] && { echo "$DST exists (use --relink to refresh an existing game)"; exit 1; }
  mkdir -p "$DST"
else
  [ -d "$DST" ] || { echo "no such game: $DST"; exit 1; }
fi
DST="$(cd "$DST" && pwd -P)"
case "$DST/" in "$STUDIO/"*) echo "the game must live outside the studio"; exit 1 ;; esac

python3 - "$STUDIO" "$DST" "$MODE" "$NAME" <<'EOF'
import json, os, shutil, subprocess, sys
studio, dst, mode, name = sys.argv[1:5]
made, kept = [], []

def link(rel, target_rel=None):
    """Relative symlink dst/rel -> studio/target_rel (replaces an older link; never a real file the game owns)."""
    src = os.path.join(studio, target_rel or rel)
    if not os.path.exists(src):
        return
    p = os.path.join(dst, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.islink(p):
        os.unlink(p)
    elif os.path.exists(p):
        kept.append(rel); return            # the game made it its own: leave it
    os.symlink(os.path.relpath(src, os.path.dirname(p)), p)
    made.append(rel)

def copy(rel, target=None):
    """Copy once (new games); never overwrite what the game already has."""
    src = os.path.join(studio, rel); p = os.path.join(dst, target or rel)
    if not os.path.exists(src) or os.path.lexists(p):
        return
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.isdir(src):
        shutil.copytree(src, p, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", "*.blend1"))
    else:
        shutil.copy2(src, p)

# ---- owned by the game (copied once)
if mode == "new":
    for rel in ["CLAUDE.md", "project.yaml", "design", ".gitignore", ".gitattributes", ".worktreeinclude",
                ".env.example", ".tripo", "sources", "textures/README.md", "blender/assets/Crate",
                "unity/args", "Assets", "Packages/manifest.json", ".claude/settings.json",
                ".claude/settings.local.json.example", ".claude/docs/technical-preferences.md",
                "production/art/weave-budget.json", "docs/engine-reference", "docs/architecture", "docs/registry",
                "docs/perf.md", "docs/art-pipeline/LESSONS.md", "docs/art-pipeline/CHECKLISTS.md"]:
        copy(rel)
    copy(".env.example", ".env")
    for d in ["production/session-state", "blender/assets", "sources/weave", "renders"]:
        os.makedirs(os.path.join(dst, d), exist_ok=True)
    with open(os.path.join(dst, "README.md"), "w") as f:
        f.write(f"# {name}\n\nA Unity 6 (URP) game built with the Blender + Unity game studio, linked from\n"
                f"`{os.path.relpath(studio, dst)}` (see `.studio`). Start Claude Code here and run `/start`.\n\n"
                "Linked from the studio (don't edit here, edit the studio): `.claude/` skills, agents, hooks, scripts,\n"
                "rules and docs, `tools/`, `blender/lib`, `blender/scripts`, `blender/bases`, `unity/*.cs`, and the\n"
                "Unity package `com.phytrisha.studio-pipeline`. Everything else belongs to this game.\n"
                "Refresh links after studio updates: `<studio>/tools/link_project.sh --relink .`\n")

# ---- provided by the studio (relative symlinks)
for rel in ["agents", "skills", "hooks", "scripts", "rules", "statusline.sh"]:
    link(".claude/" + rel)
for entry in sorted(os.listdir(os.path.join(studio, ".claude", "docs"))):
    if entry != "technical-preferences.md":
        link(".claude/docs/" + entry)
for rel in ["docs/WORKFLOW-GUIDE.md", "docs/COLLABORATIVE-DESIGN-PRINCIPLE.md", "docs/skill-flow-diagrams.md",
            "docs/CLAUDE.md", "docs/art-pipeline/README.md", "tools", "blender/lib", "blender/scripts", "blender/bases"]:
    link(rel)
for f in sorted(os.listdir(os.path.join(studio, "unity"))):
    if f.endswith(".cs"):
        link("unity/" + f)

# ---- the Unity package, as a relative file: dependency
man_p = os.path.join(dst, "Packages", "manifest.json")
os.makedirs(os.path.dirname(man_p), exist_ok=True)
man = json.load(open(man_p)) if os.path.exists(man_p) else {"dependencies": {}}
pkg = os.path.join(studio, "Packages", "com.phytrisha.studio-pipeline")
man["dependencies"]["com.phytrisha.studio-pipeline"] = "file:" + os.path.relpath(pkg, os.path.dirname(man_p))
json.dump(man, open(man_p, "w"), indent=2); open(man_p, "a").write("\n")

# ---- Claude Code must be allowed to read through the links: the linked files resolve into the studio, outside the
# game's folder. Per machine (absolute path), so it goes into the gitignored settings.local.json, merged.
loc_p = os.path.join(dst, ".claude", "settings.local.json")
loc = {}
if os.path.exists(loc_p):
    try:
        loc = json.load(open(loc_p))
    except Exception:
        print(f"warning: {loc_p} is not valid JSON; add {studio} to permissions.additionalDirectories by hand")
        loc = None
if loc is not None:
    dirs = loc.setdefault("permissions", {}).setdefault("additionalDirectories", [])
    if studio not in dirs:
        dirs.append(studio)
    json.dump(loc, open(loc_p, "w"), indent=2); open(loc_p, "a").write("\n")

# ---- record where the studio is and which version was linked
try:
    sha = subprocess.run(["git", "-C", studio, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", studio, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
except Exception:
    sha, dirty = "unknown", ""
with open(os.path.join(dst, ".studio"), "w") as f:
    f.write(f"STUDIO_PATH={os.path.relpath(studio, dst)}\nSTUDIO_COMMIT={sha}{'-dirty' if dirty else ''}\n")
print(f"linked {len(made)} paths" + (f"; kept {len(kept)} the game owns: {', '.join(kept)}" if kept else ""))
EOF

cd "$DST"
if [ $MODE = new ]; then
  git init -q -b main
  if git lfs version >/dev/null 2>&1; then git lfs install --local >/dev/null; else echo "warning: git-lfs not installed (brew install git-lfs)"; fi
  git add -A
  git commit -q -m "Start $NAME, linked to blender-unity-game-studio $(sed -n 's/^STUDIO_COMMIT=//p' .studio)"
  echo "created $DST ($NAME), linked to $STUDIO"
  echo "next: open the folder in Unity Hub (it is the Unity project), Tools > Asset Pipeline > Setup Project;"
  echo "      then run claude here once interactively and accept the trust prompt (needed for settings.local.json,"
  echo "      which lets Claude read the linked studio files), then /start"
else
  echo "relinked $DST to $STUDIO ($(sed -n 's/^STUDIO_COMMIT=//p' .studio)); review and commit the changes"
fi
