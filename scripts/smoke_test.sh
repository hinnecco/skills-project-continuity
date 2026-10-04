#!/usr/bin/env bash
# Smoke test of the relay with your REAL CLIs (Claude Code, Codex, Antigravity).
#
#   bash scripts/smoke_test.sh [target-dir]        (default: ~/relay-teste)
#
# What it does:
#   1. creates a tiny test project (from the skill's templates) with ONE approved task:
#      create hello.py + a unit test;
#   2. enables the relay and shows `status` and `--dry-run`;
#   3. asks for your confirmation before `relay.py run`, because that launches the real
#      CLIs and uses their quota.
# Nothing outside the target directory is touched. Env: THRESHOLD (default 10) sets the
# quota handoff threshold in percent remaining.

set -u
SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-$HOME/relay-teste}"
THRESHOLD="${THRESHOLD:-10}"

command -v python3 >/dev/null || { echo "python3 not found"; exit 2; }
if [ -e "$TARGET" ] && [ -n "$(ls -A "$TARGET" 2>/dev/null)" ]; then
  echo "Target '$TARGET' already exists and is not empty. Pass another directory or remove it first."
  exit 2
fi

mkdir -p "$TARGET/.continuity/scripts" && cd "$TARGET" || exit 2
T="$SKILL/assets/templates"
cp "$T"/PROTOCOL.md "$T"/CONTEXT.md "$T"/HANDOFF.md "$T"/LOG.md "$T"/QUOTA.md "$T"/config.json .continuity/
cp "$SKILL"/scripts/quota_check.py "$SKILL"/scripts/relay.py "$SKILL"/scripts/claude_statusline.sh .continuity/scripts/
for f in AGENTS.md CLAUDE.md GEMINI.md; do cp "$T/pointer.md" "$f"; done
printf '.continuity/quota/\n.continuity/relay/\n__pycache__/\n' > .gitignore
command -v git >/dev/null && git init -q 2>/dev/null

python3 - "$THRESHOLD" <<'EOF'
import json, re, sys
thr = float(sys.argv[1])
cp = ".continuity/config.json"
c = json.load(open(cp))
c["handoff_threshold_percent"] = thr
c["relay"]["enabled"] = True
for m in c["relay"]["models"]:               # let Claude run the project's unit tests
    if m["name"] == "claude-code":
        i = m["command"].index("--allowedTools") + 1
        m["command"][i] += ",Bash(python3 -m unittest:*)"
json.dump(c, open(cp, "w"), indent=2)

p = ".continuity/CONTEXT.md"
s = open(p).read()
s = s.replace("# CONTEXT - <project name>", "# CONTEXT - relay smoke test")
s = s.replace("- Goal: <one sentence>", "- Goal: tiny project to test model-to-model relay")
s = s.replace("- Run / test commands: <commands, or unknown>", "- Run / test commands: `python3 -m unittest`")
s = s.replace('- Binding constraints: <e.g. "do not touch /legacy", "no new dependencies">', "- Binding constraints: Python standard library only; only touch hello.py and test_hello.py")
s = s.replace("| <item> | <name, YYYY-MM-DD> | <chat / file> |", "| T1: create hello.py with function greet(name) returning 'Hello, <name>!' and test_hello.py with a unittest | smoke-test script | scripts/smoke_test.sh |")
s = s.replace("| T1 | <task> | todo | - |", "| T1 | hello.py + test_hello.py | todo | - |")
open(p, "w").write(s)

p = ".continuity/HANDOFF.md"
s = open(p).read()
s = s.replace("reason: needs-human", "reason: manual")
s = s.replace("Await the user's brief.", "Do T1 from CONTEXT 'Approved scope': create hello.py and test_hello.py, run `python3 -m unittest`, record evidence in LOG. Then hand off with reason complete.")
open(p, "w").write(s)
EOF

echo
echo "Test project: $TARGET   (quota threshold: ${THRESHOLD}% remaining)"
echo "================ relay status ================"
python3 .continuity/scripts/relay.py status
echo
echo "================ next model (dry-run) ================"
python3 .continuity/scripts/relay.py run --dry-run | cut -c1-200
echo
echo "'run' launches the real CLIs shown above as 'ready' and uses their quota."
printf "Run the relay now? [y/N] "
read -r ans
case "$ans" in
  y|Y|yes|YES) ;;
  *) echo "Not running. To run later: cd '$TARGET' && python3 .continuity/scripts/relay.py run"; exit 0;;
esac

python3 .continuity/scripts/relay.py run
code=$?
echo
echo "relay exit code: $code  (0 complete | 20 no model | 30 needs human | 40 stalled | 50 session limit)"
echo "================ LOG (last 40 lines) ================"
tail -40 .continuity/LOG.md
echo "================ HANDOFF header ================"
sed -n 1,8p .continuity/HANDOFF.md
echo "================ session logs ================"
ls -1 .continuity/relay 2>/dev/null
echo "================ result check ================"
if [ -f hello.py ]; then python3 -m unittest 2>&1 | tail -4; else echo "hello.py was not created"; fi
echo
echo "Send the output above (and any .continuity/relay/*.log of a failed session) back to adjust the commands."
exit $code
