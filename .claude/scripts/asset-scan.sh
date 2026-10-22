#!/usr/bin/env bash
# asset-scan.sh — the measurements /asset-audit takes by hand on a Unity
# project's Assets/: asset names against the naming rule you pass, PNG
# power-of-two dimensions, file sizes against the budgets you pass, and audio
# sample rates where `file` reports one, each with the check that ran or the
# reason it did not.
#
# Replaces the hand-run asset scan: the file listing, `wc -c`, the PNG header
# read with `od` and the sample rate read with `file`.
#
# EMITS OBSERVATIONS, NOT A VERDICT (CLAUDE.md, "Helpers in .claude/scripts/").
# A row is a rule that matched a file; the counts under "hits" are rows, not
# violations, and the words the skill ranks its report by (COMPLIANT,
# WARNINGS, NON-COMPLIANT, NOT ASSESSED) stay in the skill. A check that did
# not run says so in a `check` row and its hits are `-`, never 0: a scan that
# measured nothing is not a scan that found nothing.
#
# Usage: bash .claude/scripts/asset-scan.sh [--root DIR] [--engine E] [--category C]
#          [--budget KEY=SIZE ...] [--max-dim N] [--sample-rates LIST]
#          [--name-regex ERE] [--files]
#   --root DIR          the project; defaults to the repo this script is in
#   --engine E          unity, the only engine this studio supports (default:
#                       engine.name from project.local.yaml, then project.yaml,
#                       as content-count.sh)
#   --category C        keep one category: the first folder under Assets/ (any case)
#   --budget KEY=SIZE   a size budget in bytes, or with a K (1024) or M
#                       (1048576) suffix. Budgets are prose in the art bible,
#                       so they are flags and never read from it. KEY is `all`,
#                       a type (texture, audio, data, other) or a file
#                       extension (png, ogg, ...); the most specific one that
#                       applies wins: extension, then type, then all. A key
#                       given twice is an error. A file of exactly SIZE bytes
#                       is inside its budget.
#   --max-dim N         a texture whose width or height is above N pixels
#   --sample-rates L    comma-separated Hz values audio may have (44100,48000)
#   --name-regex ERE    the art bible's naming rule, the only naming rule: without
#                       it the naming check does not run; matched against the
#                       file name with its extension
#   --files             one FILE row per scanned file
#   -h, --help          this text
#
# What is scanned (the skill's Phase 2): Assets/, leaving out scripts (.cs,
# .asmdef), .meta files and .gitkeep placeholders. Each left-out kind is counted
# in an `excluded` row.
#
# Naming (the skill's Phase 3): only the art bible's rule, passed as
# --name-regex; a NAMING row names each file it does not match. Unity names
# assets in PascalCase with type prefixes, so there is no built-in rule.
#
# Textures: PNG width and height are read from the IHDR header (24 bytes: 8 of
# signature, 4 of chunk length, 4 of chunk name, 4 of width, 4 of height, all
# big-endian) with `od`. A dimension is a power of two when halving it reaches
# 1 without an odd step (awk here has no bitwise operators); 0 is not one. A
# texture in another format, or a PNG with no readable header, is a NOTREAD
# row. Compression for 3D and PNG for UI are not checked: the skill does not
# say how to tell a UI texture from a 3D one.
#
# Audio: the sample rate is the `N Hz` (or `N.N kHz`) that `file -b` prints; a
# file `file` reports no rate for is a NOTREAD row. Duration is not measurable
# here. File size is `wc -c`, never `stat`, which differs between GNU and BSD;
# for the same reason the last-modified time the skill lists with its orphans
# is not read.
#
# Orphans and missing are not run: on Unity references live in scenes, prefabs
# and other assets (by GUID), and no reference syntax for them is defined here.
# Their check rows say so, and their hits are `-`.
#
# Output: TSV, in this order.
#   engine <name> <source: flag, project.yaml, ...>, root <dir> present|absent,
#   category_filter <name> (with --category), scanned <n>, excluded <kind> <n>
#   per kind, category <name> <n> per category (by name, `-` for files directly
#   in Assets/), check <name> <ran | not_run> <detail> for naming, pot, size,
#   dim, rate, orphans, missing, data, format and last_modified, then
#   hits <kind> <n | -> for
#   naming, pot, size, dim, rate, notread, orphan and missing, then the rows:
#   NAMING <path> <rule> <what broke it>
#   POT <path> <WxH> <width | height | both>
#   SIZE <path> <bytes> <budget> <overage> <key: all | type:T | ext:E>
#   DIM <path> <WxH> <max>
#   RATE <path> <hz> <allowed>
#   NOTREAD <path> <dims | rate> <reason>
#   FILE <path> <category> <type> <bytes> <WxH | -> <hz | ->   (with --files)
#   Rows of one kind are in path order (bytewise).
#
# Exit codes: 0 scanned (whatever it found, none included); 1 the root cannot
# be read, or a script it needs is missing; 2 usage error; 3 no engine set, or
# an engine other than Unity (prints its engine row); 4 the asset root is absent
# (its root row says absent), so nothing was scanned. Reads only; never
# writes, never prompts.
#
# bash 3.2 and BWK awk safe, no Python. BWK awk's split() with
# a one-character separator also splits on newlines, so split() is used here
# only on a single line (a path, a row) or on a list whose separator is the
# newline itself. Listings reach awk on stdin with "./" in front of every
# file name (never as arguments), so a file called x=1.png is not an assignment.

set -u
# Byte semantics for awk, sort and tolower.
LC_ALL=C
export LC_ALL

HERE="$(cd "$(dirname "$0")" && pwd)"
usage() { echo "asset-scan: $1 (try --help)" >&2; exit 2; }
TAB=$(printf '\t')

ROOT_ARG=""; ENGINE_ARG=""; CATF=""; BUDGETS=""; BUDGET_FLAGS=""; MAXDIM=""
RATES=""; NAMERE=""; SHOWFILES=0; BSPEC=""; BGOT=0
while [ $# -gt 0 ]; do
  case "$1" in
    --root) [ $# -ge 2 ] || usage "--root needs a value"; ROOT_ARG="$2"; shift 2 ;;
    --root=*) ROOT_ARG="${1#--root=}"; shift ;;
    --engine) [ $# -ge 2 ] || usage "--engine needs a name"; ENGINE_ARG="$2"; shift 2 ;;
    --engine=*) ENGINE_ARG="${1#--engine=}"; shift ;;
    --category) [ $# -ge 2 ] || usage "--category needs a name"; CATF="$2"; shift 2 ;;
    --category=*) CATF="${1#--category=}"; shift ;;
    --budget) [ $# -ge 2 ] || usage "--budget needs KEY=SIZE"; BSPEC="$2"; BGOT=1; shift 2 ;;
    --budget=*) BSPEC="${1#--budget=}"; BGOT=1; shift ;;
    --max-dim) [ $# -ge 2 ] || usage "--max-dim needs a number"; MAXDIM="$2"; shift 2 ;;
    --max-dim=*) MAXDIM="${1#--max-dim=}"; shift ;;
    --sample-rates) [ $# -ge 2 ] || usage "--sample-rates needs a list"; RATES="$2"; shift 2 ;;
    --sample-rates=*) RATES="${1#--sample-rates=}"; shift ;;
    --name-regex) [ $# -ge 2 ] || usage "--name-regex needs a pattern"; NAMERE="$2"; shift 2 ;;
    --name-regex=*) NAMERE="${1#--name-regex=}"; shift ;;
    --files) SHOWFILES=1; shift ;;
    -h|--help) sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -?*) usage "unknown argument: $1" ;;
    *) usage "unexpected argument: $1" ;;
  esac
  # A --budget was just read: check it and add it. (Done after the case so
  # that both spellings share the checks.)
  if [ "$BGOT" = 1 ]; then
    case "$BSPEC" in *=*) ;; *) usage "--budget takes KEY=SIZE, got $BSPEC" ;; esac
    BK="${BSPEC%%=*}"; BV="${BSPEC#*=}"
    [ -n "$BK" ] && [ -n "$BV" ] || usage "--budget takes KEY=SIZE, got $BSPEC"
    case "$BK" in *[!A-Za-z0-9]*) usage "--budget key must be letters and digits, got $BK" ;; esac
    case "$BV" in *[!0-9KkMm]*) usage "--budget size is a number of bytes with an optional K or M, got $BV" ;; esac
    BD="${BV%[KkMm]}"
    case "$BD" in ''|*[!0-9]*) usage "--budget size is a number of bytes with an optional K or M, got $BV" ;; esac
    # K is 1024 bytes and M is 1048576: sizes are file sizes, not marketing sizes.
    BN=$((10#$BD))
    case "$BV" in *[Kk]) BN=$((BN * 1024)) ;; *[Mm]) BN=$((BN * 1048576)) ;; esac
    BL=$(printf '%s' "$BK" | tr 'A-Z' 'a-z')
    case "$BL" in
      all) BCAN="all" ;;
      texture|audio|data|other) BCAN="type:$BL" ;;
      *) BCAN="ext:$BL" ;;
    esac
    case "
$BUDGETS" in *"
$BCAN="*) usage "--budget key $BK given twice" ;; esac
    BUDGETS="$BUDGETS$BCAN=$BN
"
    BUDGET_FLAGS="${BUDGET_FLAGS:+$BUDGET_FLAGS }$BSPEC"
    BGOT=0
  fi
done
if [ -n "$MAXDIM" ]; then
  case "$MAXDIM" in ''|*[!0-9]*) usage "--max-dim takes a whole number of pixels" ;; esac
  [ $((10#$MAXDIM)) -ge 1 ] || usage "--max-dim takes a number above 0"
  MAXDIM=$((10#$MAXDIM))
fi
if [ -n "$RATES" ]; then
  case "$RATES" in ''|*[!0-9,]*|,*|*,|*,,*) usage "--sample-rates takes comma-separated Hz values, got $RATES" ;; esac
fi
if [ -n "$NAMERE" ]; then
  # An invalid pattern is a usage error here, not an awk crash halfway through.
  R="$NAMERE" awk 'BEGIN { x = ("" ~ ENVIRON["R"]) }' >/dev/null 2>&1 || usage "--name-regex is not a valid regular expression: $NAMERE"
fi
CATF=$(printf '%s' "$CATF" | tr 'A-Z' 'a-z')

if [ -n "$ROOT_ARG" ]; then
  cd "$ROOT_ARG" 2>/dev/null || { echo "asset-scan: cannot read root $ROOT_ARG" >&2; exit 1; }
else
  cd "$HERE/../.." 2>/dev/null || { echo "asset-scan: cannot reach the repo root" >&2; exit 1; }
fi

# ----------------------------------------------------------------------- engine
# engine.name from project.local.yaml, then project.yaml, read by the shared
# yaml-get.awk as content-count.sh reads it; only when neither names one,
# project-state.sh's legacy fallback decides.
if [ -n "$ENGINE_ARG" ]; then
  RAW="$ENGINE_ARG"; ESRC="flag"
else
  RAW=""; ESRC=""
  [ -f "$HERE/yaml-get.awk" ] || { echo "asset-scan: $HERE/yaml-get.awk is missing; pass --engine" >&2; exit 1; }
  for yf in project.local.yaml project.yaml; do
    if [ -z "$RAW" ] && [ -f "$yf" ]; then
      RAW=$(YG_PATH=engine.name awk -f "$HERE/yaml-get.awk" "$yf")
      [ -z "$RAW" ] || ESRC="$yf"
    fi
  done
  if [ -z "$RAW" ] && [ -f "$HERE/project-state.sh" ]; then
    ROW=$(bash "$HERE/project-state.sh" --root . | awk -F'\t' '$1 == "engine" { print $2 "\t" $3 }')
    RAW="${ROW%%"$TAB"*}"; ESRC="${ROW#*"$TAB"}"
  fi
fi
if [ -z "$RAW" ] || [ "$RAW" = "-" ]; then
  printf 'engine\t-\tunset\n'
  echo "asset-scan: no engine is set (engine.name in project.yaml); pass --engine" >&2
  exit 3
fi
LOW=$(printf '%s' "$RAW" | tr '[:upper:]' '[:lower:]')
# The asset root is the skill's Phase 2: Assets/ on Unity.
case "$LOW" in
  unity) ENG=unity; ROOTDIR=Assets ;;
  *)
    if [ "$ESRC" = flag ]; then usage "--engine takes unity, got $RAW"; fi
    printf 'engine\t%s\t%s\n' "$RAW" "$ESRC"
    echo "asset-scan: engine $RAW is not supported here (this studio is Unity only)" >&2
    exit 3 ;;
esac

printf 'engine\t%s\t%s\n' "$ENG" "$ESRC"
# The exact name from the listing: -d would say yes to Assets for a directory
# called assets on a case-insensitive disk.
if [ -z "$(find . -maxdepth 1 -type d -name "$ROOTDIR" 2>/dev/null)" ]; then
  printf 'root\t%s\tabsent\n' "$ROOTDIR"
  echo "asset-scan: $ROOTDIR/ does not exist; nothing was scanned" >&2
  exit 4
fi
printf 'root\t%s\tpresent\n' "$ROOTDIR"

# --------------------------------------------------------------------- listing
ALLF=$(find "$ROOTDIR" -type f 2>/dev/null | sort)
CLASS=$(printf '%s\n' "$ALLF" | CATF="$CATF" awk '
  BEGIN { BINMODE = 3; catf = ENVIRON["CATF"] }
  length($0) > 0 {
    p = $0
    n = split(p, seg, "/")
    base = seg[n]
    ext = ""
    if (match(base, /\.[^.]*$/)) ext = tolower(substr(base, RSTART + 1))
    reason = ""
    if (base == ".gitkeep") reason = ".gitkeep"
    else if (ext == "meta") reason = ".meta"
    else if (ext == "cs") reason = ".cs"
    else if (ext == "asmdef") reason = ".asmdef"
    if (reason != "") { print "X\t" reason; next }
    cat = (n >= 3) ? seg[2] : "-"
    if (catf != "" && tolower(cat) != catf) next
    print "K\t" p
  }
')
KEPT=$(printf '%s\n' "$CLASS" | awk 'substr($0, 1, 2) == "K\t" { print substr($0, 3) }')

# PNG headers and audio descriptions are collected per file; sizes in one
# batch of wc -c.
PNGS=""; AUDIOS=""
if [ -n "$KEPT" ]; then
  PNGS=$(printf '%s\n' "$KEPT" | awk 'tolower($0) ~ /\.png$/')
  AUDIOS=$(printf '%s\n' "$KEPT" | awk 'tolower($0) ~ /\.(ogg|wav|mp3|flac|opus|m4a|aac|aif|aiff)$/')
fi
HAVEFILE=0
command -v file >/dev/null 2>&1 && HAVEFILE=1

# ------------------------------------------------------------------ measuring
{
  printf '%s\n' "$CLASS"
  if [ -n "$KEPT" ]; then
    printf '%s\n' "$KEPT" | awk 'length($0) > 0 { printf "./%s\n", $0 }' | tr '\n' '\0' | xargs -0 wc -c 2>/dev/null | \
      awk 'BEGIN { BINMODE = 3 } { i = index($0, "./"); if (i == 0) next; n = $1 + 0; print "S\t" n "\t" substr($0, i + 2) }'
  fi
  if [ -n "$PNGS" ]; then
    printf '%s\n' "$PNGS" | while IFS= read -r p; do
      [ -n "$p" ] || continue
      printf 'P\t%s\t' "$p"
      od -A n -t u1 -v -N 24 "./$p" 2>/dev/null | tr '\n' ' '
      printf '\n'
    done
  fi
  if [ -n "$AUDIOS" ]; then
    printf '%s\n' "$AUDIOS" | awk 'length($0) > 0 { print "L\t" $0 }'
    if [ "$HAVEFILE" = 1 ]; then
      printf '%s\n' "$AUDIOS" | awk 'length($0) > 0 { printf "./%s\n", $0 }' | tr '\n' '\0' | xargs -0 file -b 2>/dev/null | \
        awk 'BEGIN { BINMODE = 3 } { print "D\t" $0 }'
    fi
  fi
} | ROOTDIR="$ROOTDIR" CATF="$CATF" BUDGETS="$BUDGETS" BUDGET_FLAGS="$BUDGET_FLAGS" MAXDIM="$MAXDIM" \
    RATES="$RATES" NAMERE="$NAMERE" SHOWFILES="$SHOWFILES" HAVEFILE="$HAVEFILE" awk '
  BEGIN {
    BINMODE = 3
    rootdir = ENVIRON["ROOTDIR"]; catf = ENVIRON["CATF"]
    maxdim = ENVIRON["MAXDIM"] + 0; namere = ENVIRON["NAMERE"]; showfiles = ENVIRON["SHOWFILES"]
    havefile = ENVIRON["HAVEFILE"]
    # Budgets arrive one per line as key=bytes. The separator is the newline
    # itself, which BWK awk splits on anyway.
    bs = ENVIRON["BUDGETS"]
    nbl = split(bs, bl, "\n")
    for (i = 1; i <= nbl; i++) if (bl[i] != "") { p = index(bl[i], "="); B[substr(bl[i], 1, p - 1)] = substr(bl[i], p + 1) + 0; hasb = 1 }
    nra = 0
    rs = ENVIRON["RATES"]
    if (rs != "") { nra = split(rs, ral, ","); for (i = 1; i <= nra; i++) RA[ral[i] + 0] = 1 }
    # The tagged listing on stdin: K kept file, X left-out kind, S size,
    # P PNG header bytes, L audio file, D what file -b said about it (same
    # order as L).
    while ((getline line < "/dev/stdin") > 0) {
      tag = substr(line, 1, 1); rest = substr(line, 3)
      if (tag == "K") kept[++nk] = rest
      else if (tag == "X") xc[rest]++
      else if (tag == "S") { t = index(rest, "\t"); size[substr(rest, t + 1)] = substr(rest, 1, t - 1) + 0 }
      else if (tag == "P") { t = index(rest, "\t"); hdr[substr(rest, 1, t - 1)] = substr(rest, t + 1) }
      else if (tag == "L") lst[++nl] = rest
      else if (tag == "D") dsc[++nd] = rest
    }
    for (i = 1; i <= nl; i++) if (i <= nd) adesc[lst[i]] = dsc[i]
  }

  # --- helpers ---------------------------------------------------------------
  function ftype(e) {
    # The types the budgets and the texture checks talk about, by extension.
    if (e ~ /^(png|jpg|jpeg|webp|tga|bmp|exr|hdr|dds|ktx|ktx2)$/) return "texture"
    if (e ~ /^(ogg|wav|mp3|flac|opus|m4a|aac|aif|aiff)$/) return "audio"
    if (e ~ /^(json|yaml|yml)$/) return "data"
    return "other"
  }
  # Powers of two by halving: an odd number above 1 on the way down ends it.
  function pot(n) {
    if (n < 1) return 0
    while (n > 1) { if (n % 2 != 0) return 0; n = n / 2 }
    return 1
  }
  # The kHz form (44.1 kHz) is turned into Hz and rounded, so 22.05 is 22050.
  function rateof(d,    r) {
    if (match(d, /[0-9]+ Hz/)) return substr(d, RSTART, RLENGTH - 3) + 0
    if (match(d, /[0-9]+(\.[0-9]+)? kHz/)) { r = substr(d, RSTART, RLENGTH - 4) + 0; return int(r * 1000 + 0.5) }
    return ""
  }

  END {
    scanned = nk
    nodata = (scanned == 0) ? ("no assets under " rootdir) : ""
    if (catf != "") printf "category_filter\t%s\n", catf
    printf "scanned\t%d\n", scanned
    nx = split(".meta .cs .asmdef .gitkeep", xl, " ")
    for (i = 1; i <= nx; i++) printf "excluded\t%s\t%d\n", xl[i], xc[xl[i]]

    # --- per-file facts, in path order (the listing arrives sorted) ---
    for (i = 1; i <= nk; i++) {
      p = kept[i]
      n = split(p, seg, "/")
      base = seg[n]
      ex = ""
      if (match(base, /\.[^.]*$/)) ex = tolower(substr(base, RSTART + 1))
      cat = (n >= 3) ? seg[2] : "-"
      ty = ftype(ex)
      kcat[i] = cat; ktype[i] = ty
      catn[cat]++
      if (!(cat in catseen)) { catseen[cat] = 1; catlist[++ncat] = cat }
      by = (p in size) ? size[p] : -1
      kbytes[i] = by
    }
    for (i = 2; i <= ncat; i++) { x = catlist[i]; for (j = i - 1; j >= 1 && catlist[j] > x; j--) catlist[j + 1] = catlist[j]; catlist[j + 1] = x }
    for (i = 1; i <= ncat; i++) printf "category\t%s\t%d\n", catlist[i], catn[catlist[i]]

    # --- which checks run ---
    if (nodata != "") { namingst = "not_run"; namingd = nodata }
    else if (namere != "") { namingst = "ran"; namingd = "name_regex " namere }
    else { namingst = "not_run"; namingd = "no naming rule given; pass the art bible\047s rule with --name-regex" }
    if (nodata != "") { potst = "not_run"; potd = nodata }
    else { potst = "ran"; potd = "PNG width and height from the IHDR bytes" }
    if (nodata != "") { sizest = "not_run"; sized = nodata }
    else if (!hasb) { sizest = "not_run"; sized = "no --budget flag given" }
    else { sizest = "ran"; sized = ENVIRON["BUDGET_FLAGS"] }
    if (nodata != "") { dimst = "not_run"; dimd = nodata }
    else if (maxdim == 0) { dimst = "not_run"; dimd = "no --max-dim flag given" }
    else { dimst = "ran"; dimd = "--max-dim " maxdim }
    if (nodata != "") { ratest = "not_run"; rated = nodata }
    else if (havefile != 1) { ratest = "not_run"; rated = "file is not installed" }
    else { ratest = "ran"; rated = (nra > 0) ? ("file -b; allowed " ENVIRON["RATES"]) : "file -b; no --sample-rates flag given, none compared" }
    if (nodata != "") { orphst = "not_run"; orphd = nodata }
    else { orphst = "not_run"; orphd = "references live in scenes, prefabs and other assets, not in code" }
    missst = "not_run"; missd = "no reference syntax is defined for unity"

    printf "check\tnaming\t%s\t%s\n", namingst, namingd
    printf "check\tpot\t%s\t%s\n", potst, potd
    printf "check\tsize\t%s\t%s\n", sizest, sized
    printf "check\tdim\t%s\t%s\n", dimst, dimd
    printf "check\trate\t%s\t%s\n", ratest, rated
    printf "check\torphans\t%s\t%s\n", orphst, orphd
    printf "check\tmissing\t%s\t%s\n", missst, missd
    printf "check\tdata\tnot_run\tJSON and YAML validity and schemas are not checked here\n"
    printf "check\tformat\tnot_run\tfile formats are not checked here: the skill does not say how to tell a UI or 3D texture\n"
    printf "check\tlast_modified\tnot_run\tnot read: stat differs between GNU and BSD\n"

    # --- the rows, built per kind in path order ---
    nname = npot = nsize = ndim = nrate = nnot = norph = nmiss = nfile = 0
    for (i = 1; i <= nk; i++) {
      p = kept[i]; n = split(p, seg, "/"); base = seg[n]
      ex = ""
      if (match(base, /\.[^.]*$/)) ex = tolower(substr(base, RSTART + 1))
      ty = ktype[i]; by = kbytes[i]
      dims = "-"; w = -1; h = -1; rate = "-"
      if (namingst == "ran" && !(base ~ namere)) rname[++nname] = "NAMING\t" p "\tname_regex\tdoes not match " namere
      if (ty == "texture") {
        if (ex != "png") rnot[++nnot] = "NOTREAD\t" p "\tdims\tonly PNG headers are read, not " ex
        else {
          m = split(hdr[p], hb, " ")
          if (m < 24) rnot[++nnot] = "NOTREAD\t" p "\tdims\ttoo short to hold a PNG header"
          else if (hb[1] != 137 || hb[2] != 80 || hb[3] != 78 || hb[4] != 71 || hb[5] != 13 || hb[6] != 10 || hb[7] != 26 || hb[8] != 10) rnot[++nnot] = "NOTREAD\t" p "\tdims\tno PNG signature"
          else if (hb[13] != 73 || hb[14] != 72 || hb[15] != 68 || hb[16] != 82) rnot[++nnot] = "NOTREAD\t" p "\tdims\tno IHDR chunk after the signature"
          else {
            w = hb[17] * 16777216 + hb[18] * 65536 + hb[19] * 256 + hb[20]
            h = hb[21] * 16777216 + hb[22] * 65536 + hb[23] * 256 + hb[24]
            dims = w "x" h
            wp = pot(w); hp = pot(h)
            if (!wp || !hp) rpot[++npot] = "POT\t" p "\t" dims "\t" ((!wp && !hp) ? "both" : ((!wp) ? "width" : "height"))
            if (maxdim > 0 && (w > maxdim || h > maxdim)) rdim[++ndim] = "DIM\t" p "\t" dims "\t" maxdim
          }
        }
      }
      if (ty == "audio") {
        if (havefile != 1) rnot[++nnot] = "NOTREAD\t" p "\trate\tfile is not installed"
        else {
          r = rateof(adesc[p])
          if (r == "") rnot[++nnot] = "NOTREAD\t" p "\trate\tfile reports no sample rate"
          else {
            rate = r
            if (nra > 0 && !(r in RA)) rrate[++nrate] = "RATE\t" p "\t" r "\t" ENVIRON["RATES"]
          }
        }
      }
      if (hasb && by >= 0) {
        key = ""
        if (("ext:" ex) in B) key = "ext:" ex
        else if (("type:" ty) in B) key = "type:" ty
        else if ("all" in B) key = "all"
        if (key != "" && by > B[key]) rsize[++nsize] = "SIZE\t" p "\t" by "\t" B[key] "\t" (by - B[key]) "\t" key
      }
      if (showfiles == 1) rfile[++nfile] = "FILE\t" p "\t" kcat[i] "\t" ty "\t" ((by >= 0) ? by : "-") "\t" dims "\t" rate
    }
    # --- hits, then the rows ---
    printf "hits\tnaming\t%s\n", (namingst == "ran") ? nname : "-"
    printf "hits\tpot\t%s\n", (potst == "ran") ? npot : "-"
    printf "hits\tsize\t%s\n", (sizest == "ran") ? nsize : "-"
    printf "hits\tdim\t%s\n", (dimst == "ran") ? ndim : "-"
    printf "hits\trate\t%s\n", (ratest == "ran" && nra > 0) ? nrate : "-"
    printf "hits\tnotread\t%s\n", (potst == "ran" || ratest == "ran") ? nnot : "-"
    printf "hits\torphan\t%s\n", (orphst == "ran") ? norph : "-"
    printf "hits\tmissing\t%s\n", (missst == "ran") ? nmiss : "-"
    for (i = 1; i <= nname; i++) print rname[i]
    for (i = 1; i <= npot; i++) print rpot[i]
    for (i = 1; i <= nsize; i++) print rsize[i]
    for (i = 1; i <= ndim; i++) print rdim[i]
    for (i = 1; i <= nrate; i++) print rrate[i]
    for (i = 1; i <= nnot; i++) print rnot[i]
    for (i = 1; i <= nfile; i++) print rfile[i]
  }
'
exit 0
