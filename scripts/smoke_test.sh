#!/usr/bin/env bash
# Smoke test of the relay with your REAL CLIs (Claude Code, Codex, Antigravity).
#
#   bash scripts/smoke_test.sh [target-dir]            default target: ~/relay-teste
#   TWO_TASKS=1 bash scripts/smoke_test.sh [target]    force a real model-to-model handoff
#
# What it does:
#   1. creates a tiny test project (from the skill's templates) with approved task(s):
#      one task (hello.py + test), or with TWO_TASKS=1 two tasks (hello.py, goodbye.py) where the
#      model must hand off with reason `model-switch` after each task, so the relay has to launch a
#      DIFFERENT model for the second task;
#   2. checks which CLIs are installed and that their headless flags exist;
#   3. enables the relay and shows `status` and `--dry-run`;
#   4. asks for confirmation before `relay.py run`, because that launches the real CLIs and uses
#      their quota.
# Nothing outside the target directory is touched. Env: THRESHOLD (default 10) = quota handoff
# threshold in percent remaining.

set -u
SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-$HOME/relay-teste}"
THRESHOLD="${THRESHOLD:-10}"
TWO_TASKS="${TWO_TASKS:-0}"

command -v python3 >/dev/null || { echo "python3 not found"; exit 2; }
if [ -e "$TARGET" ] && [ -n "$(ls -A "$TARGET" 2>/dev/null)" ]; then
  echo "Target '$TARGET' already exists and is not empty. Pass another directory or remove it first."
  exit 2
fi

echo "================ CLIs on this machine ================"
for c in claude codex agy; do
  if command -v "$c" >/dev/null; then printf '%-7s %s   ' "$c" "$(command -v "$c")"; "$c" --version 2>&1 | head -1; else echo "$c: NOT FOUND"; fi
done
if command -v codex >/dev/null && ! codex exec --help 2>&1 | grep -q -- '--sandbox'; then
  echo "WARNING: 'codex exec --help' does not mention --sandbox; check the codex command in config.json."
fi
if command -v claude >/dev/null && ! claude --help 2>&1 | grep -q -- '--allowedTools\|--allowed-tools'; then
  echo "WARNING: 'claude --help' does not mention --allowedTools; check the claude command in config.json."
fi
if command -v agy >/dev/null && ! agy --help 2>&1 | grep -q -- '--print\|-p'; then
  echo "WARNING: 'agy --help' does not mention -p/--print; check the antigravity command in config.json."
fi
echo

mkdir -p "$TARGET/.continuity/scripts" && cd "$TARGET" || exit 2
T="$SKILL/assets/templates"
cp "$T"/PROTOCOL.md "$T"/CONTEXT.md "$T"/HANDOFF.md "$T"/LOG.md "$T"/QUOTA.md "$T"/config.json .continuity/
cp "$SKILL"/scripts/quota_check.py "$SKILL"/scripts/relay.py "$SKILL"/scripts/claude_statusline.sh .continuity/scripts/
for f in AGENTS.md CLAUDE.md GEMINI.md; do cp "$T/pointer.md" "$f"; done
printf '.continuity/quota/\n.continuity/relay/\n__pycache__/\n' > .gitignore
command -v git >/dev/null && git init -q 2>/dev/null

python3 - "$THRESHOLD" "$TWO_TASKS" <<'EOF'
import json, sys
thr, two = float(sys.argv[1]), sys.argv[2] == "1"
cp = ".continuity/config.json"
c = json.load(open(cp))
c["handoff_threshold_percent"] = thr
c["relay"]["enabled"] = True
for m in c["relay"]["models"]:               # let Claude run the project's unit tests
    if m["name"] == "claude-code":
        i = m["command"].index("--allowedTools") + 1
        m["command"][i] += ",Bash(python3 -m unittest:*)"
json.dump(c, open(cp, "w"), indent=2)

s = open(".continuity/CONTEXT.md").read()
s = s.replace("# CONTEXT - <project name>", "# CONTEXT - relay smoke test")
s = s.replace("- Goal: <one sentence>", "- Goal: tiny project to test model-to-model relay")
s = s.replace("- Run / test commands: <commands, or unknown>", "- Run / test commands: `python3 -m unittest`")
t1 = "T1: create hello.py with function greet(name) returning 'Hello, <name>!' and test_hello.py with a unittest"
t2 = "T2: create goodbye.py with function farewell(name) returning 'Goodbye, <name>!' and test_goodbye.py with a unittest"
constraint = "Python standard library only; only touch the files named in the task"
if two:
    constraint += ". RELAY TEST: after finishing EACH task, run `handoff` with reason `model-switch` so a different model does the next task; only after the last task use reason `complete`"
s = s.replace('- Binding constraints: <e.g. "do not touch /legacy", "no new dependencies">', "- Binding constraints: " + constraint)
rows = f"| {t1} | smoke-test script | scripts/smoke_test.sh |"
board = "| T1 | hello.py + test_hello.py | todo | - |"
if two:
    rows += f"\n| {t2} | smoke-test script | scripts/smoke_test.sh |"
    board += "\n| T2 | goodbye.py + test_goodbye.py | todo | - |"
s = s.replace("| <item> | <name, YYYY-MM-DD> | <chat / file> |", rows)
s = s.replace("| T1 | <task> | todo | - |", board)
open(".continuity/CONTEXT.md", "w").write(s)

h = open(".continuity/HANDOFF.md").read()
h = h.replace("reason: needs-human", "reason: manual")
h = h.replace("Await the user's brief.", "Do T1 from CONTEXT 'Approved scope', run `python3 -m unittest`, record evidence in LOG, then follow the handoff rule in CONTEXT constraints.")
open(".continuity/HANDOFF.md", "w").write(h)
EOF

echo "Test project: $TARGET   (quota threshold: ${THRESHOLD}% remaining, two tasks: $([ "$TWO_TASKS" = 1 ] && echo yes || echo no))"
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
echo "================ models that ran (from LOG) ================"
grep -E "launching|exited|limit message|stopped" .continuity/LOG.md | sed 's/^- //'
echo "================ LOG (last 40 lines) ================"
tail -40 .continuity/LOG.md
echo "================ HANDOFF header ================"
sed -n 1,8p .continuity/HANDOFF.md
echo "================ session logs ================"
ls -1 .continuity/relay 2>/dev/null
echo "================ result check ================"
ls hello.py test_hello.py goodbye.py test_goodbye.py 2>/dev/null
python3 -m unittest 2>&1 | tail -4
echo
echo "Send the output above (and any .continuity/relay/*.log of a failed session) back to adjust the commands."
exit $code
