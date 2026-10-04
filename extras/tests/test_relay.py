import importlib.util, json, os, sys, tempfile, textwrap, time, unittest
from pathlib import Path
from types import SimpleNamespace

SCRIPTS = Path(__file__).parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("relay", SCRIPTS / "relay.py")
relay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(relay)

FAKE = textwrap.dedent('''
    import json, re, sys, time
    from pathlib import Path
    name = sys.argv[1]
    root = Path.cwd(); c = root / ".continuity"
    plan = json.loads((c / "plan.json").read_text())
    action = plan[name].pop(0) if plan.get(name) else "noop"
    (c / "plan.json").write_text(json.dumps(plan))
    def sethandoff(status, reason):
        t = (c / "HANDOFF.md").read_text()
        t = re.sub(r"^status:.*$", f"status: {status}", t, flags=re.M)
        t = re.sub(r"^reason:.*$", f"reason: {reason}", t, flags=re.M)
        (c / "HANDOFF.md").write_text(t)
    with open(c / "LOG.md", "a") as f: f.write(f"\\n## fake {name} {action} {time.time()}\\n")
    (c / "calls.txt").open("a").write(name + "\\n")
    if action == "limit": sethandoff("PAUSED", "limit-near")
    elif action == "switch": sethandoff("PAUSED", "model-switch")
    elif action == "limitmsg": print("Error: usage limit reached, try again later"); sethandoff("ACTIVE", "limit-hit"); sys.exit(1)
    elif action == "complete": sethandoff("PAUSED", "complete")
    elif action == "human": sethandoff("PAUSED", "needs-human")
    elif action == "crash": sethandoff("ACTIVE", "limit-hit"); sys.exit(1)
    elif action == "hang": sethandoff("ACTIVE", "manual"); time.sleep(30)
    # "noop": exits 0 without changing anything
''')

HANDOFF = "---\nstatus: PAUSED\nowner: unknown\nupdated: x\nreason: manual   # comment\n---\n# HANDOFF\n## 1. Next action\ngo\n"


def make_project(plan, models=("A", "B"), enabled=True, **relay_over):
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    c = root / ".continuity"
    c.mkdir()
    (c / "HANDOFF.md").write_text(HANDOFF)
    (c / "LOG.md").write_text("# LOG\n")
    (c / "plan.json").write_text(json.dumps(plan))
    fake = root / "fake.py"
    fake.write_text(FAKE)
    rcfg = {"enabled": enabled, "max_sessions": 6, "run_timeout_minutes": 1, "stall_limit": 2,
            "models": [{"name": n, "tool": n.lower(), "priority": i, "command": [sys.executable, str(fake), n, "{prompt}"]}
                       for i, n in enumerate(models, 1)]}
    rcfg.update(relay_over)
    (c / "config.json").write_text(json.dumps({"handoff_threshold_percent": 10, "relay": rcfg}))
    return tmp, root


def run(root, **kw):
    cfg, r = relay.load_relay(str(root))
    args = SimpleNamespace(dry_run=kw.get("dry_run", False), force=kw.get("force", False), max_sessions=None)
    return relay.cmd_run(str(root), cfg, r, args)


def calls(root):
    p = root / ".continuity" / "calls.txt"
    return p.read_text().split() if p.exists() else []


def snapshot(root, tool, remaining, observed_ago=0, resets_in=None):
    q = root / ".continuity" / "quota"
    q.mkdir(exist_ok=True)
    w = {"remaining_percent": remaining, "used_percent": 100 - remaining, "observed_at": time.time() - observed_ago}
    if resets_in is not None:
        w["resets_at"] = time.time() + resets_in
    (q / f"{tool}.json").write_text(json.dumps({"observed_at": time.time() - observed_ago, "windows": {"five_hour": w}}))


class RelayTests(unittest.TestCase):
    def test_disabled_by_default(self):
        tmp, root = make_project({}, enabled=False)
        with tmp:
            self.assertEqual(run(root), 2)
            self.assertEqual(calls(root), [])

    def test_baton_passes_until_complete(self):
        tmp, root = make_project({"A": ["limit"], "B": ["limit", "complete"]}, models=("A", "B"))
        with tmp:
            # A hands off (limit) -> B ; B hands off (limit) -> A (noop, nothing) ... plan decides
            code = run(root, force=True)
            self.assertEqual(code, 0)
            self.assertEqual(calls(root)[:2], ["A", "B"])
            self.assertIn("RELAY", (root / ".continuity" / "LOG.md").read_text())

    def test_model_that_hit_limit_is_skipped_next(self):
        tmp, root = make_project({"A": ["limit"], "B": ["complete"]})
        with tmp:
            self.assertEqual(run(root, force=True), 0)
            self.assertEqual(calls(root), ["A", "B"])

    def test_crash_leaves_active_and_next_model_takes_over(self):
        tmp, root = make_project({"A": ["crash"], "B": ["complete"]})
        with tmp:
            self.assertEqual(run(root, force=True), 0)
            self.assertEqual(calls(root), ["A", "B"])

    def test_quota_low_model_is_skipped(self):
        tmp, root = make_project({"B": ["complete"]})
        with tmp:
            snapshot(root, "a", 4)
            self.assertEqual(run(root, force=True), 0)
            self.assertEqual(calls(root), ["B"])

    def test_stale_low_reading_does_not_block(self):
        tmp, root = make_project({"A": ["complete"]})
        with tmp:
            snapshot(root, "a", 4, observed_ago=7200)  # old reading: window probably recovered
            self.assertEqual(run(root, force=True), 0)
            self.assertEqual(calls(root), ["A"])

    def test_all_models_low_stops_with_20(self):
        tmp, root = make_project({})
        with tmp:
            snapshot(root, "a", 3, resets_in=3600)
            snapshot(root, "b", 5, resets_in=7200)
            self.assertEqual(run(root, force=True), 20)
            self.assertEqual(calls(root), [])

    def test_missing_cli_is_skipped(self):
        tmp, root = make_project({"B": ["complete"]})
        with tmp:
            cfgp = root / ".continuity" / "config.json"
            cfg = json.loads(cfgp.read_text())
            cfg["relay"]["models"][0]["command"] = ["definitely-not-a-real-cli-xyz"]
            cfgp.write_text(json.dumps(cfg))
            self.assertEqual(run(root, force=True), 0)
            self.assertEqual(calls(root), ["B"])

    def test_needs_human_stops_and_requires_force_to_start(self):
        tmp, root = make_project({"A": ["human"]})
        with tmp:
            h = root / ".continuity" / "HANDOFF.md"
            h.write_text(HANDOFF.replace("reason: manual", "reason: needs-human"))
            self.assertEqual(run(root), 30)
            self.assertEqual(calls(root), [])
            self.assertEqual(run(root, force=True), 30)  # A ran once, then asked for a human
            self.assertEqual(calls(root), ["A"])

    def test_stall_detection(self):
        tmp, root = make_project({"A": ["noop", "noop", "noop"], "B": ["noop", "noop", "noop"]}, stall_limit=1)
        with tmp:
            # fake always appends to LOG, so emulate stall by a model that changes nothing
            (root / "fake.py").write_text("import sys\n")
            self.assertEqual(run(root, force=True), 40)

    def test_session_limit(self):
        tmp, root = make_project({"A": ["limit"] * 5, "B": ["limit"] * 5}, max_sessions=3)
        with tmp:
            self.assertEqual(run(root, force=True), 50)
            self.assertEqual(len(calls(root)), 3)

    def test_timeout_kills_child(self):
        tmp, root = make_project({"A": ["hang"], "B": ["complete"]}, run_timeout_minutes=0.03)
        with tmp:
            t = time.time()
            self.assertEqual(run(root, force=True), 0)
            self.assertLess(time.time() - t, 20)
            self.assertEqual(calls(root), ["A", "B"])

    def test_model_switch_skips_departing_model(self):
        tmp, root = make_project({"A": ["switch"], "B": ["complete"]})
        with tmp:
            self.assertEqual(run(root, force=True), 0)
            self.assertEqual(calls(root), ["A", "B"])

    def test_limit_message_in_log_puts_model_on_cooldown(self):
        tmp, root = make_project({"A": ["limitmsg"], "B": ["complete"]})
        with tmp:
            self.assertEqual(run(root, force=True), 0)
            self.assertEqual(calls(root), ["A", "B"])
            snap = json.loads((root / ".continuity" / "quota" / "a.json").read_text())
            self.assertEqual(snap["windows"]["relay_limit"]["remaining_percent"], 0.0)
            cfg, r = relay.load_relay(str(root))
            self.assertEqual(relay.model_state(str(root), cfg, r["models"][0])[0], "quota-low")
            # next run: A is still cooling down, so B goes first even though A has priority 1
            (root / ".continuity" / "HANDOFF.md").write_text(HANDOFF)
            (root / ".continuity" / "plan.json").write_text(json.dumps({"B": ["complete"]}))
            self.assertEqual(run(root, force=True), 0)
            self.assertEqual(calls(root), ["A", "B", "B"])

    def test_crash_without_limit_message_records_no_observation(self):
        tmp, root = make_project({"A": ["crash"], "B": ["complete"]})
        with tmp:
            self.assertEqual(run(root, force=True), 0)
            self.assertFalse((root / ".continuity" / "quota" / "a.json").exists())

    def test_relay_limit_window_counts_even_when_windows_are_listed(self):
        snap = {"windows": {"relay_limit": {"remaining_percent": 0, "observed_at": time.time()},
                            "five_hour": {"remaining_percent": 80, "observed_at": time.time()}}}
        state, _ = relay.qc.assess(snap, {"windows": ["five_hour"]}, time.time())
        self.assertEqual(state, "low")

    def test_dry_run_launches_nothing(self):
        tmp, root = make_project({"A": ["complete"]})
        with tmp:
            self.assertEqual(run(root, force=True, dry_run=True), 0)
            self.assertEqual(calls(root), [])

    def test_invalid_config(self):
        tmp, root = make_project({})
        with tmp:
            cfgp = root / ".continuity" / "config.json"
            cfgp.write_text(json.dumps({"relay": {"models": [{"name": "x"}]}}))
            with self.assertRaises(ValueError):
                relay.load_relay(str(root))


if __name__ == "__main__":
    unittest.main()
