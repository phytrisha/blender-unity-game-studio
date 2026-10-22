#!/bin/bash
# Start a new game from this studio: a clean copy with its own git history.
#
#   tools/new_project.sh ~/Dev/my-game "My Game"
#
# Copies the studio (no git history, no Unity Library/Temp/Logs, no generated exports/renders, no local secrets),
# creates .env from .env.example, initialises git + Git LFS (.gitattributes routes .blend/.fbx/.png/... to LFS) and
# makes the first commit. Then:
#   1. open the new folder in Unity Hub (Add > the folder: it IS the Unity project) with Unity 6, let it import, then
#      Tools > Asset Pipeline > Setup Project (or: tools/unity_run.sh with `return ProjectSetup.Run();`)
#   2. start Claude Code in the folder and run /start (concept, /setup-engine, art bible, ...)
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
DST="${1:?usage: new_project.sh <target dir> [\"Game Name\"]}"
NAME="${2:-$(basename "$DST")}"
[ -e "$DST" ] && { echo "$DST exists"; exit 1; }
mkdir -p "$DST"
rsync -a \
  --exclude .git --exclude .env --exclude .claude/settings.local.json --exclude project.local.yaml \
  --exclude Library --exclude Temp --exclude Logs --exclude UserSettings --exclude obj --exclude Build --exclude Builds \
  --exclude '*.csproj' --exclude '*.sln*' --exclude 'blender/export' --exclude renders --exclude 'unity/reports' \
  --exclude '*.blend1' --exclude 'blender/.current_*' --exclude 'unity/.run_*' --exclude '__pycache__' --exclude '.DS_Store' \
  --exclude 'production/session-state/*.md' --exclude 'production/session-logs' --exclude 'weave-ledger.jsonl' \
  --exclude '.claude/scheduled_tasks.lock' \
  "$SRC/" "$DST/"
cp "$DST/.env.example" "$DST/.env"
cd "$DST"
git init -q -b main
if git lfs version >/dev/null 2>&1; then git lfs install --local >/dev/null; else echo "warning: git-lfs not installed (brew install git-lfs); large files would go into plain git"; fi
git add -A
git commit -q -m "Start $NAME from blender-unity-game-studio"
echo "created $DST ($NAME)"
echo "next: open the folder in Unity Hub (it is the Unity project), Tools > Asset Pipeline > Setup Project; then claude -> /start"
