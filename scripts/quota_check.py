#!/usr/bin/env python3
"""project-continuity quota helper (stdlib only).

Check:  quota_check.py --tool claude-code
Record: quota_check.py --tool codex --set-remaining 42 --window five_hour
        quota_check.py --tool gemini --used 870 --limit 1000 --window daily
        quota_check.py --tool cursor --set-used 90 --window monthly

Exit codes (check): 0 ok | 10 at/below threshold | 4 reading stale | 3 no reading
Exit 2 = usage error. Readings live in <root>/.continuity/quota/<tool>.json.
Threshold lives in <root>/.continuity/config.json. Never invents numbers.
"""
import argparse, json, os, sys, time, math, re


def find_root(start):
    d = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(d, ".continuity")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def fmt_t(epoch):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(epoch))


def number(value, minimum=0, maximum=float("inf")):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("expected a numeric value")
    value = float(value)
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError("numeric value out of range")
    return value


def record(path, args):
    now = int(time.time())
    try:
        if args.set_remaining is not None:
            rem = number(args.set_remaining, 0, 100)
        elif args.set_used is not None:
            rem = 100 - number(args.set_used, 0, 100)
        else:
            used = number(args.used)
            limit = number(args.limit)
            if limit <= 0 or used > limit:
                raise ValueError("invalid usage/limit")
            rem = 100 - 100 * used / limit
        reset = number(int(args.resets_at)) if args.resets_at is not None else None
    except (ValueError, TypeError, OverflowError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    snap = load_json(path, {})
    if not isinstance(snap, dict) or not isinstance(snap.get("windows", {}), dict):
        print("error: malformed existing quota file", file=sys.stderr)
        return 2
    windows = snap.setdefault("windows", {})
    # Preserve original timestamps when migrating legacy snapshots.
    for old in windows.values():
        if isinstance(old, dict):
            old.setdefault("observed_at", snap.get("observed_at", 0))
            old.setdefault("source", snap.get("source", "unknown"))
    w = {"observed_at": now, "source": args.source,
         "remaining_percent": round(rem, 1), "used_percent": round(100-rem, 1)}
    if reset is not None:
        w["resets_at"] = reset
    windows[args.window] = w
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + f".{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2, allow_nan=False)
    os.replace(tmp, path)
    print(f"recorded {args.tool}/{args.window}: {w['remaining_percent']}% remaining (source: {args.source})")
    return 0


def assess(snap, cfg, now=None):
    """Classify a snapshot for the relay supervisor. Returns (state, resets_at).
    state: 'low' (a fresh window is at/below threshold), 'ok', or 'unknown'
    (missing, stale, invalid, or window already reset). Never raises."""
    now = now or time.time()
    try:
        default_thr = number(cfg.get("handoff_threshold_percent", 10), 0, 100)
        thresholds = cfg.get("thresholds", {}) or {}
        monitored = cfg.get("windows", []) or []
        stale_after = number(cfg.get("stale_after_minutes", 30)) * 60
        if not isinstance(snap, dict) or not isinstance(snap.get("windows"), dict) or not snap["windows"]:
            return "unknown", None
    except (ValueError, AttributeError):
        return "unknown", None
    low, resets, fresh = [], [], 0
    for name in monitored or list(snap["windows"]):
        w = snap["windows"].get(name)
        try:
            rem = number(w.get("remaining_percent"), 0, 100)
            obs = number(w.get("observed_at", snap.get("observed_at", 0)))
            reset = number(w["resets_at"]) if w.get("resets_at") is not None else None
            thr = number(thresholds.get(name, default_thr), 0, 100)
            if obs <= 0 or obs > now or now - obs > stale_after or (reset is not None and obs < reset <= now):
                continue
        except (ValueError, AttributeError):
            continue
        fresh += 1
        if rem <= thr:
            low.append(name)
            if reset is not None:
                resets.append(reset)
    if low:
        return "low", (max(resets) if resets else None)
    return ("ok" if fresh else "unknown"), None


def check(path, cfg, args):
    try:
        if not isinstance(cfg, dict):
            raise ValueError("invalid configuration")
        default_thr = number(cfg.get("handoff_threshold_percent", 10), 0, 100)
        thresholds = cfg.get("thresholds", {})
        if not isinstance(thresholds, dict):
            raise ValueError("invalid thresholds")
        for value in thresholds.values():
            number(value, 0, 100)
        monitored = cfg.get("windows", [])
        if not isinstance(monitored, list) or any(not isinstance(n, str) for n in monitored):
            raise ValueError("invalid windows")
        stale_after = number(cfg.get("stale_after_minutes", 30)) * 60
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    snap = load_json(path, None)
    if not isinstance(snap, dict) or not isinstance(snap.get("windows"), dict) or not snap["windows"]:
        print(f"UNAVAILABLE: no valid quota reading for '{args.tool}'. Do not guess.")
        return 3
    now = time.time()
    hit, stale = [], False
    for name in monitored or list(snap["windows"]):
        w = snap["windows"].get(name)
        try:
            if not isinstance(w, dict):
                raise ValueError("missing reading")
            rem = number(w.get("remaining_percent"), 0, 100)
            obs = number(w.get("observed_at", snap.get("observed_at", 0)))
            reset = number(w["resets_at"]) if w.get("resets_at") is not None else None
            if obs <= 0 or obs > now or now-obs > stale_after or (reset is not None and obs < reset <= now):
                raise ValueError("stale or future reading")
        except ValueError:
            print(f"  {name}: invalid, missing or stale; refresh")
            stale = True
            continue
        thr = thresholds.get(name, default_thr)
        print(f"  {name}: {rem}% remaining (threshold {thr}%, observed {fmt_t(obs)}, source {w.get('source',snap.get('source','unknown'))})")
        if rem <= thr:
            hit.append(name)
    if hit:
        print(f"HANDOFF REQUIRED: {', '.join(hit)} at or below threshold.")
        return 10
    if stale:
        print("STALE: refresh invalid, missing or old readings.")
        return 4
    print("OK: above threshold.")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tool", default=os.environ.get("QUOTA_TOOL"),
                   help="claude-code | codex | gemini | cursor | other (or env QUOTA_TOOL)")
    p.add_argument("--root", default=".", help="project dir (default: cwd; .continuity is searched upward)")
    p.add_argument("--window", default="five_hour", help="window name when recording (five_hour, seven_day, daily, monthly...)")
    p.add_argument("--source", default="manual", help="where the number came from (e.g. '/status', 'user')")
    p.add_argument("--resets-at", help="epoch seconds when the window resets (optional)")
    p.add_argument("--set-remaining", type=float, metavar="PCT")
    p.add_argument("--set-used", type=float, metavar="PCT")
    p.add_argument("--used", type=float)
    p.add_argument("--limit", type=float)
    args = p.parse_args()
    if not args.tool or not re.fullmatch(r"[a-zA-Z0-9_-]+", args.tool):
        print("error: --tool is required (claude-code|codex|gemini|cursor|other)", file=sys.stderr)
        return 2
    root = find_root(args.root)
    if not root:
        print("error: .continuity/ not found; run init first", file=sys.stderr)
        return 2
    cfg = load_json(os.path.join(root, ".continuity", "config.json"), {})
    path = os.path.join(root, ".continuity", "quota", f"{args.tool}.json")
    if args.set_remaining is not None or args.set_used is not None or args.used is not None:
        return record(path, args)
    return check(path, cfg, args)


if __name__ == "__main__":
    sys.exit(main())
