#!/usr/bin/env bash
# test-run.sh — run a Unity project's automated tests the way /smoke-check
# Phase 2 does, under a timeout, and read the result with that phase's
# exit-code ladder: the command, the timeout, the exit code, the zero-tests
# marker, the counts, and the ladder row that matched.
#
# Replaces the hand-run test command, `timeout`, exit-code reading and "looks
# like success and is not" cases.
#
# OBSERVATIONS, NOT A VERDICT (CLAUDE.md, "Helpers in .claude/scripts/"). The
# `rule` row says which row of the ladder the exit code and output fall on, in
# plain words; PASS, FAIL, NOT ASSESSED and "PASS WITH WARNINGS" stay with
# /smoke-check, which also decides what an unmatched exit code means.
#
# Usage: bash .claude/scripts/test-run.sh <engine> [options]
#   <engine>            unity (any case) — the only engine this studio supports
#   --cmd COMMAND       the test command to run, instead of project.yaml's
#                       commands.test or the default
#   --exe PATH          the editor executable (default: the one commands.test
#                       names, else engine.path, else Unity on PATH)
#   --platform P        editmode (default) or playmode
#   --timeout SECONDS   default 900
#   --tool T            force the timeout tool: timeout, gtimeout, perl or none (the
#                       tests use this to reach the perl and no-tool paths)
#   --log FILE          keep the runner's output here (default: a temp file)
#   --dry-run           print what would run; run nothing
#   --root DIR          the project; defaults to the repo this script is in
#   -h, --help          this text
#
# The timeout is `timeout`, else `gtimeout`, else perl (the command in its own
# process group, which gets TERM at the timeout and KILL five seconds on, as
# coreutils timeout does), whichever exists first; the `timeout` row names it,
# or `none` when no timeout tool exists and the run is unbounded. An exit of
# 124 (timeout, gtimeout) or 142 (perl) is a timeout.
#
# Before the test run it checks Packages/manifest.json names
# com.unity.test-framework and deletes the old results file. A check that fails
# runs nothing and prints why.
#
# Output: TSV, in this order (a row that cannot apply is left out).
#   engine      Unity
#   exe         <path|->  <commands.test|engine.path|path|--exe|->
#   command     <--cmd|commands.test|default>  <the command>
#   timeout     <seconds>  <timeout|gtimeout|perl|none>
#   precheck    <what>  <present|absent>
#   ran         <yes|no>  <why not, or ->
#   exit        <code of the test command>
#   timed_out   <yes|no>
#   results_file  <path>  <present|absent>
#   zero_tests  <yes|no|unknown>  <the marker line, or ->
#   tests       total=<n> passed=<n> failed=<n>             (the <test-run> element)
#   failed      <a line naming a failing test>  (up to 10, then `failed_more <n>`)
#   evidence    <a line that backs the rule>
#   rule        <id>  <what that row of the ladder says>     `-` when no row fits
#   log         <path>
# Rule ids: timeout, runner-unavailable, unity:no-test-framework, unity:0,
# unity:zero-tests, unity:no-count, unity:no-results, unity:2, unity:1, unity:3,
# unity:4, unity:other.
#
# Exit codes: 0 the helper finished (whatever the tests did: read the rows);
# 1 cannot read the root or write the log; 2 usage error; 3 an engine other
# than Unity. It runs the project's own test command and writes under the
# project (Unity's results file and caches); it never prompts and never edits
# project.yaml.
#
# bash 3.2 and BWK awk safe, no Python.

set -u
# Byte semantics for awk and sort.
LC_ALL=C
export LC_ALL

HERE="$(cd "$(dirname "$0")" && pwd)"
usage() { echo "test-run: $1 (try --help)" >&2; exit 2; }
ENGINE_ARG=""; CMD_ARG=""; EXE_ARG=""; PLATFORM="editmode"; TIMEOUT=""
LOG=""; DRY=0; ROOT_ARG=""; TOOL_ARG=""
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --dry-run) DRY=1; shift ;;
    --cmd|--exe|--platform|--timeout|--log|--root|--tool)
      [ $# -ge 2 ] || usage "$1 needs a value"
      case "$1" in
        --cmd) CMD_ARG="$2" ;; --exe) EXE_ARG="$2" ;; --platform) PLATFORM="$2" ;;
        --timeout) TIMEOUT="$2" ;;
        --log) LOG="$2" ;; --root) ROOT_ARG="$2" ;; --tool) TOOL_ARG="$2" ;;
      esac
      shift 2 ;;
    -?*) usage "unknown argument: $1" ;;
    *) [ -z "$ENGINE_ARG" ] || usage "one engine only"; ENGINE_ARG="$1"; shift ;;
  esac
done
[ -n "$ENGINE_ARG" ] || usage "no engine given"
case "$(printf '%s' "$ENGINE_ARG" | tr 'A-Z' 'a-z')" in
  unity) ENGINE=unity; ENAME=Unity ;;
  *) echo "test-run: '$ENGINE_ARG' is not supported: this studio runs Unity tests only" >&2; exit 3 ;;
esac
case "$PLATFORM" in editmode|playmode) ;; *) usage "--platform is editmode or playmode" ;; esac
# /smoke-check Phase 2's limit: `timeout 900` for a test run.
[ -n "$TIMEOUT" ] || TIMEOUT=900
case "$TIMEOUT" in ''|*[!0-9]*) usage "--timeout is whole seconds" ;; esac
[ "$TIMEOUT" -gt 0 ] || usage "--timeout must be above 0"

if [ -n "$ROOT_ARG" ]; then
  cd "$ROOT_ARG" 2>/dev/null || { echo "test-run: cannot read root $ROOT_ARG" >&2; exit 1; }
else
  cd "$HERE/../.." 2>/dev/null || { echo "test-run: cannot reach the repo root" >&2; exit 1; }
fi
[ -f "$HERE/yaml-get.awk" ] || { echo "test-run: $HERE/yaml-get.awk is missing" >&2; exit 1; }
yget() { [ -f project.yaml ] && YG_PATH="$1" awk -f "$HERE/yaml-get.awk" project.yaml; }

printf 'engine\t%s\n' "$ENAME"

# --- the editor executable ----------------------------------------------------
CFG_TEST=$(yget commands.test); ENGINE_PATH=$(yget engine.path)
# exe_ok P — an existing file, or a command found on PATH.
exe_ok() { [ -n "$1" ] && { [ -f "$1" ] || command -v "$1" >/dev/null 2>&1; }; }
EXE=""; EXE_SRC="-"
if [ -n "$EXE_ARG" ]; then
  EXE="$EXE_ARG"; EXE_SRC="--exe"
else
  # The executable commands.test names: its quoted path, else its first word.
  first=""
  if [ -n "$CFG_TEST" ]; then
    case "$CFG_TEST" in
      \"*) first=${CFG_TEST#\"}; first=${first%%\"*} ;;
      \'*) first=${CFG_TEST#\'}; first=${first%%\'*} ;;
      *) first=${CFG_TEST%% *} ;;
    esac
  fi
  if exe_ok "$first"; then EXE="$first"; EXE_SRC="commands.test"
  elif [ -n "$ENGINE_PATH" ] && exe_ok "$ENGINE_PATH"; then EXE="$ENGINE_PATH"; EXE_SRC="engine.path"
  elif exe_ok Unity; then EXE="Unity"; EXE_SRC="path"
  fi
fi
printf 'exe\t%s\t%s\n' "${EXE:--}" "$EXE_SRC"

# --- timeout tool -------------------------------------------------------------
if [ -n "$TOOL_ARG" ]; then
  case "$TOOL_ARG" in timeout|gtimeout|perl|none) TOOL="$TOOL_ARG" ;; *) usage "--tool is timeout, gtimeout, perl or none" ;; esac
elif command -v timeout >/dev/null 2>&1; then TOOL=timeout
elif command -v gtimeout >/dev/null 2>&1; then TOOL=gtimeout
elif command -v perl >/dev/null 2>&1; then TOOL=perl
else TOOL=none; fi
# The perl fallback does what coreutils timeout does: the command runs in a
# process group of its own, and at the timeout the whole group gets TERM, then
# KILL five seconds on, so an editor that a compound command started (cd x &&
# Unity ...) ends with it. It exits 142 (128 + SIGALRM's 14) on a timeout,
# else with the command's own code.
PERL_TIMEOUT='
  my $t = shift @ARGV;
  my $pid = fork;
  defined $pid or die "test-run: fork failed: $!\n";
  if ($pid == 0) { setpgrp(0, 0); exec @ARGV or exit 127; }
  setpgrp($pid, $pid);
  my $timed = 0;
  $SIG{ALRM} = sub { if ($timed++) { kill "KILL", -$pid } else { kill "TERM", -$pid; alarm 5 } };
  for my $s (qw(INT TERM HUP)) { $SIG{$s} = sub { kill $_[0], -$pid } }
  alarm $t;
  my $st = 0;
  while (1) {
    my $w = waitpid($pid, 0);
    if ($w == $pid) { $st = $?; last }
    last if $w == -1;
  }
  alarm 0;
  if ($timed) {
    for (1 .. 50) { last unless kill 0, -$pid; select(undef, undef, undef, 0.1) }
    kill "KILL", -$pid if kill 0, -$pid;
    exit 142;
  }
  exit(($st & 127) ? 128 + ($st & 127) : $st >> 8);
'
# run_timed SECONDS COMMAND — COMMAND under the timeout tool, output on stdout and stderr.
run_timed() {
  case "$TOOL" in
    timeout|gtimeout) "$TOOL" "$1" bash -c "$2" ;;
    perl) perl -e "$PERL_TIMEOUT" "$1" bash -c "$2" ;;
    *) bash -c "$2" ;;
  esac
}
# is_timeout CODE — whether CODE is the tool's timeout exit: 124 from timeout and
# gtimeout, 142 (128 + SIGALRM's 14) from the perl alarm.
is_timeout() {
  case "$TOOL" in
    timeout|gtimeout) [ "$1" = 124 ] ;;
    perl) [ "$1" = 142 ] ;;
    *) return 1 ;;
  esac
}

# --- the commands -------------------------------------------------------------
RESULTS=""; CMD=""; CMD_SRC="default"
if [ "$PLATFORM" = playmode ]; then P=PlayMode; RESULTS=test-results/playmode.xml; else P=EditMode; RESULTS=test-results/editmode.xml; fi
CMD="\"${EXE:-Unity}\" -batchmode -runTests -projectPath . -testPlatform $P -testResults $RESULTS"
# commands.test and --cmd win over the default.
if [ -n "$CMD_ARG" ]; then CMD="$CMD_ARG"; CMD_SRC="--cmd"
elif [ -n "$CFG_TEST" ]; then CMD="$CFG_TEST"; CMD_SRC="commands.test"; fi
# A Unity results file named in the command is the one to read and to delete first.
if [ "$CMD_SRC" != default ]; then
  # -E: BSD sed has no \| in a basic regex.
  named=$(printf '%s\n' "$CMD" | sed -n -E 's/.*-testResults[ =]*("[^"]*"|[^ ]*).*/\1/p' | head -1)
  named=${named#\"}; named=${named%\"}
  [ -n "$named" ] && RESULTS="$named"
fi
[ -n "$CMD" ] && printf 'command\t%s\t%s\n' "$CMD_SRC" "$CMD"
printf 'timeout\t%s\t%s\n' "$TIMEOUT" "$TOOL"

# --- prechecks ----------------------------------------------------------------
ran_no() { printf 'ran\tno\t%s\n' "$2"; printf 'rule\t%s\t%s\n' "$1" "$3"; exit 0; }
if [ -f Packages/manifest.json ] && grep -q 'com.unity.test-framework' Packages/manifest.json; then printf 'precheck\tcom.unity.test-framework\tpresent\n'
else
  printf 'precheck\tcom.unity.test-framework\tabsent\n'
  ran_no unity:no-test-framework "Unity Test Framework is not in Packages/manifest.json" "the Unity Test Framework is not installed; the editor would hang, so it was not started"
fi
if [ -z "$EXE" ] && [ "$CMD_SRC" = default ]; then
  ran_no runner-unavailable "no editor executable (commands.test, engine.path, PATH)" "the engine executable was not found, so the tests could not be run here"
fi
if [ "$DRY" = 1 ]; then printf 'ran\tno\tdry run\n'; exit 0; fi

# --- run ----------------------------------------------------------------------
if [ -z "$LOG" ]; then
  LOG=$(mktemp "${TMPDIR:-/tmp}/test-run-XXXXXX" 2>/dev/null) || { echo "test-run: cannot create a log file" >&2; exit 1; }
fi
: > "$LOG" 2>/dev/null || { echo "test-run: cannot write the log $LOG" >&2; exit 1; }
[ -n "$RESULTS" ] && rm -f "$RESULTS"
run_timed "$TIMEOUT" "$CMD" > "$LOG" 2>&1
CODE=$?
printf 'ran\tyes\t-\n'
printf 'exit\t%s\n' "$CODE"
TIMED=no
is_timeout "$CODE" && TIMED=yes
printf 'timed_out\t%s\n' "$TIMED"

# --- read ---------------------------------------------------------------------
# first_line PATTERN — the first output line matching the extended regex, or empty.
first_line() { grep -E -m 1 "$1" "$LOG" 2>/dev/null | head -1 | tr -d '\r'; }
# list_failed PATTERN FILE — up to 10 matching lines as `failed` rows, then the
# overflow (Phase 2: "names of any failing tests (up to 10; if more, note the count)").
list_failed() {
  n=$(grep -E -c "$1" "$2" 2>/dev/null); n=${n:-0}
  grep -E "$1" "$2" 2>/dev/null | head -10 | tr -d '\r' | while IFS= read -r l; do printf 'failed\t%s\n' "$(printf '%s' "$l" | sed 's/^[[:blank:]]*//')"; done
  [ "$n" -gt 10 ] && printf 'failed_more\t%s\n' "$((n - 10))"
  return 0
}
RULE_ID="-"; RULE_TXT="no row of the ladder fits"
set_rule() { RULE_ID="$1"; RULE_TXT="$2"; }
if [ -f "$RESULTS" ]; then
  printf 'results_file\t%s\tpresent\n' "$RESULTS"
  run_el=$(grep -E -m 1 '<test-run' "$RESULTS" | tr -d '\r')
  attr() { printf '%s\n' "$run_el" | sed -n "s/.*[ <]$1=\"\\([0-9]*\\)\".*/\\1/p" | head -1; }
  total=$(attr testcasecount); passed=$(attr passed); failed=$(attr failed)
  printf 'tests\ttotal=%s passed=%s failed=%s\n' "${total:--}" "${passed:--}" "${failed:--}"
  if [ -z "$total" ]; then printf 'zero_tests\tunknown\tno testcasecount on a <test-run> element\n'
  elif [ "$total" = 0 ]; then printf 'zero_tests\tyes\ttestcasecount="0"\n'; else printf 'zero_tests\tno\t-\n'; fi
  list_failed '<test-case[^>]*result="Failed"' "$RESULTS"
else
  printf 'results_file\t%s\tabsent\n' "$RESULTS"; total=""
fi
case "$CODE" in
  0) if [ ! -f "$RESULTS" ]; then set_rule unity:no-results "exit 0 but no results file was written"
     elif [ -z "$total" ]; then set_rule unity:no-count "exit 0, but the results file has no <test-run> testcasecount, so no test was counted"
     elif [ "$total" = 0 ]; then set_rule unity:zero-tests "testcasecount is 0: no test was compiled or run"
     else set_rule unity:0 "exit 0: every test passed"; fi ;;
  2) set_rule unity:2 "a test failed" ;;
  1) set_rule unity:1 "the project did not compile (see the editor log for error CS lines)" ;;
  3) set_rule unity:3 "the run itself failed" ;;
  4) set_rule unity:4 "an unknown -testPlatform" ;;
  126|127) set_rule runner-unavailable "the editor did not start (command not found or not executable)" ;;
  *) set_rule unity:other "any other non-zero exit" ;;
esac
if [ "$TIMED" = yes ]; then set_rule timeout "the run did not complete: timed out after ${TIMEOUT}s, so nothing was verified"; fi
printf 'rule\t%s\t%s\n' "$RULE_ID" "$RULE_TXT"
printf 'log\t%s\n' "$LOG"
exit 0
