#!/usr/bin/env python3
"""project-continuity relay supervisor (stdlib only, macOS/Linux).

Runs AI CLIs one at a time in non-interactive mode so work passes from one model
to the next automatically: launch a CLI with the `continue` prompt, wait for it to
exit, read HANDOFF.md, pick the next available CLI, repeat.

    python3 .continuity/scripts/relay.py status
    python3 .continuity/scripts/relay.py run --dry-run
    python3 .continuity/scripts/relay.py run

Opt-in: `run` refuses to start unless config.json has "relay": {"enabled": true}.
Exit codes: 0 complete | 2 usage/config error | 20 no model available (quota low,
missing CLI) | 30 needs a human | 40 stalled (no progress) | 50 session limit reached.
Nothing here resets, buys or bypasses quota, and it never waits for a window to reset.
"""
import argparse, hashlib, importlib.util, json, os, shutil, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("quota_check", os.path.join(HERE, "quota_check.py"))
qc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qc)

DEFAULT_PROMPT = (
    "You are continuing a shared multi-model project. Read .continuity/PROTOCOL.md and follow its "
    "`continue` procedure now. The relay supervisor started this session and verified that the "
    "previous writer's process has exited, so a stale ACTIVE status means an interrupted session: "
    "follow RECOVERY. This session is non-interactive: do not ask questions. Work only inside the "
    "approved scope. Check quota as the protocol says. When quota reaches the threshold, run "
    "`handoff` (reason limit-near) and stop. When all approved work is done, run `handoff` with "
    "reason complete. If you need a human decision or approval, record the question in HANDOFF "
    "section 6, run `handoff` with reason needs-human, and stop."
)
DEFAULTS = {"enabled": False, "models": [], "max_sessions": 6, "run_timeout_minutes": 120,
            "stall_limit": 2, "prompt": DEFAULT_PROMPT}
STOP_REASONS = {"complete": 0, "needs-human": 30}
QUOTA_REASONS = {"limit-near", "limit-hit"}


def now_str():
    return time.strftime("%Y-%m-%d %H:%M %z")


def read_handoff(root):
    """Return (front_matter_dict, body). Missing file -> ({}, '')."""
    try:
        with open(os.path.join(root, ".continuity", "HANDOFF.md"), encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return {}, ""
    meta, body = {}, text
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                body = "\n".join(lines[i + 1:])
                break
            if ":" in lines[i]:
                k, v = lines[i].split(":", 1)
                meta[k.strip()] = v.split("#")[0].strip()
    return meta, body


def fingerprint(root):
    h = hashlib.sha256()
    try:
        with open(os.path.join(root, ".continuity", "LOG.md"), "rb") as f:
            h.update(f.read())
    except OSError:
        pass
    h.update(read_handoff(root)[1].encode("utf-8"))
    return h.hexdigest()


def log_entry(root, lines):
    path = os.path.join(root, ".continuity", "LOG.md")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n## {now_str()} | relay-supervisor | - | RELAY\n" + "\n".join(f"- {l}" for l in lines) + "\n")
    except OSError:
        pass


def load_relay(root):
    cfg = qc.load_json(os.path.join(root, ".continuity", "config.json"), {})
    if not isinstance(cfg, dict):
        raise ValueError("config.json is not an object")
    r = dict(DEFAULTS)
    r.update(cfg.get("relay") or {})
    if not isinstance(r["models"], list):
        raise ValueError("relay.models must be a list")
    for m in r["models"]:
        if not isinstance(m, dict) or not m.get("name") or not m.get("tool") or not isinstance(m.get("command"), list) or not m["command"]:
            raise ValueError("each relay model needs name, tool and a non-empty command list")
        if not all(isinstance(a, str) for a in m["command"]):
            raise ValueError("relay command entries must be strings")
    r["models"] = sorted(r["models"], key=lambda m: m.get("priority", 100))
    return cfg, r


def model_state(root, cfg, m):
    """('ready'|'disabled'|'missing-cli'|'quota-low', detail, resets_at)"""
    if m.get("enabled", True) is False:
        return "disabled", "disabled in config", None
    if shutil.which(m["command"][0]) is None:
        return "missing-cli", f"'{m['command'][0]}' not found on PATH", None
    snap = qc.load_json(os.path.join(root, ".continuity", "quota", f"{m['tool']}.json"), None)
    state, resets = qc.assess(snap, cfg, time.time())
    if state == "low":
        return "quota-low", "quota at/below threshold", resets
    return "ready", "quota ok" if state == "ok" else "quota unknown (the model checks at continue)", None


def pick(root, cfg, r, skip_name):
    notes, resets = [], []
    for m in r["models"]:
        st, detail, rs = model_state(root, cfg, m)
        if st == "ready" and m["name"] == skip_name:
            notes.append(f"{m['name']}: skipped (its last session hit the limit, crashed or hung)")
            continue
        if st != "ready":
            notes.append(f"{m['name']}: {detail}")
            if rs:
                resets.append(rs)
            continue
        return m, notes, resets
    return None, notes, resets


def build_argv(m, r, root):
    return [a.replace("{prompt}", r["prompt"]).replace("{root}", root) for a in m["command"]]


def kill_group(proc):
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except (ProcessLookupError, PermissionError):
            return
        try:
            proc.wait(timeout=10)
            return
        except subprocess.TimeoutExpired:
            continue


def launch(root, m, r):
    logdir = os.path.join(root, ".continuity", "relay")
    os.makedirs(logdir, exist_ok=True)
    logpath = os.path.join(logdir, f"{time.strftime('%Y%m%d-%H%M%S')}-{m['name']}.log")
    env = dict(os.environ, QUOTA_TOOL=m["tool"], CONTINUITY_RELAY="1")
    timeout = float(r["run_timeout_minutes"]) * 60
    with open(logpath, "wb") as lf:
        try:
            proc = subprocess.Popen(build_argv(m, r, root), cwd=root, stdin=subprocess.DEVNULL, stdout=lf,
                                    stderr=subprocess.STDOUT, env=env, start_new_session=True)
        except OSError as e:
            return None, False, logpath, f"could not start: {e}"
        try:
            rc = proc.wait(timeout=timeout)
            return rc, False, logpath, ""
        except subprocess.TimeoutExpired:
            kill_group(proc)
            return None, True, logpath, "timeout"
        except KeyboardInterrupt:
            kill_group(proc)
            raise


def cmd_status(root, cfg, r):
    meta, body = read_handoff(root)
    print(f"project: {root}")
    print(f"relay enabled: {bool(r['enabled'])}   max_sessions: {r['max_sessions']}   timeout: {r['run_timeout_minutes']} min")
    print(f"HANDOFF: status={meta.get('status', '?')} reason={meta.get('reason', '?')} owner={meta.get('owner', '?')} updated={meta.get('updated', '?')}")
    if not r["models"]:
        print("no relay.models configured")
    for m in r["models"]:
        st, detail, rs = model_state(root, cfg, m)
        extra = f" (window resets {time.strftime('%Y-%m-%d %H:%M', time.localtime(rs))})" if rs else ""
        print(f"  [{m.get('priority', '-')}] {m['name']:<14} tool={m['tool']:<12} {st}: {detail}{extra}")
    return 0


def cmd_run(root, cfg, r, args):
    if not r["enabled"]:
        print('relay is disabled. It is opt-in: set "relay": {"enabled": true} in .continuity/config.json '
              "after reviewing each model's command and permissions.", file=sys.stderr)
        return 2
    if not r["models"]:
        print("no relay.models configured", file=sys.stderr)
        return 2
    max_sessions = args.max_sessions or int(r["max_sessions"])
    sessions = stalls = 0
    last_name = None
    first = True
    while True:
        meta, _ = read_handoff(root)
        status, reason = meta.get("status", ""), meta.get("reason", "")
        if status == "PAUSED" and reason in STOP_REASONS and not (first and args.force):
            print(f"stop: HANDOFF is PAUSED with reason '{reason}'" + (" (all approved work done)." if reason == "complete" else ": a human decision is needed (see HANDOFF section 6)."))
            return STOP_REASONS[reason]
        if sessions >= max_sessions:
            print(f"stop: session limit reached ({max_sessions}). Re-run to continue.")
            log_entry(root, [f"stopped: session limit {max_sessions} reached"])
            return 50
        cand, notes, resets = pick(root, cfg, r, last_name)
        if not cand:
            when = f" Earliest window reset: {time.strftime('%Y-%m-%d %H:%M', time.localtime(min(resets)))}." if resets else ""
            print("stop: no model available." + when + "\n  " + "\n  ".join(notes))
            log_entry(root, ["stopped: no model available"] + notes)
            return 20
        argv = build_argv(cand, r, root)
        if args.dry_run:
            shown = " ".join("<prompt>" if a == r["prompt"] else a for a in argv)
            print(f"next: {cand['name']} ({cand['tool']})\n  command: {shown}" + ("\n  " + "\n  ".join(notes) if notes else ""))
            return 0
        print(f"[{now_str()}] session {sessions + 1}/{max_sessions}: launching {cand['name']}")
        log_entry(root, [f"launching {cand['name']} ({cand['tool']}); previous: {last_name or 'none'}; HANDOFF status={status or '?'} reason={reason or '?'}"] + notes)
        before = fingerprint(root)  # measured after our own entry, so only the model's work counts
        rc, timed_out, logpath, err = launch(root, cand, r)
        after = fingerprint(root)
        sessions += 1
        first = False
        meta2, _ = read_handoff(root)
        outcome = f"{cand['name']} exited rc={rc}" + (" (timed out, killed)" if timed_out else "") + (f" ({err})" if err and not timed_out else "")
        outcome += f"; HANDOFF status={meta2.get('status', '?')} reason={meta2.get('reason', '?')}; log {os.path.relpath(logpath, root)}"
        print("  " + outcome)
        log_entry(root, [outcome])
        stalls = stalls + 1 if after == before else 0
        if stalls >= int(r["stall_limit"]):
            print(f"stop: no progress recorded in {stalls} consecutive sessions (stalled).")
            log_entry(root, [f"stopped: stalled after {stalls} sessions without progress"])
            return 40
        clean = (not timed_out) and rc == 0 and meta2.get("status") == "PAUSED"
        # A model that hit its limit, crashed, hung or left ACTIVE is not asked again right away.
        last_name = cand["name"] if (meta2.get("reason") in QUOTA_REASONS or not clean) else None


def find_root(start):
    return qc.find_root(start)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["status", "run"])
    p.add_argument("--root", default=".")
    p.add_argument("--dry-run", action="store_true", help="show the next model and exit")
    p.add_argument("--force", action="store_true", help="start even if HANDOFF says needs-human/complete (first launch only)")
    p.add_argument("--max-sessions", type=int, help="override relay.max_sessions")
    args = p.parse_args()
    root = find_root(args.root)
    if not root:
        print("error: .continuity/ not found; run init first", file=sys.stderr)
        return 2
    try:
        cfg, r = load_relay(root)
    except ValueError as e:
        print(f"error: invalid relay config: {e}", file=sys.stderr)
        return 2
    if args.command == "status":
        return cmd_status(root, cfg, r)
    try:
        return cmd_run(root, cfg, r, args)
    except KeyboardInterrupt:
        print("\ninterrupted: child stopped. HANDOFF may be ACTIVE; the next session will run RECOVERY.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
