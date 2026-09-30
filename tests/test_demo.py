"""Demo track tests: public-reads demo runs offline with no token."""

import json
import os
import subprocess
import sys

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
DEMO_DIR = os.path.join(REPO_ROOT, "demo")
DEMO_SCRIPT = os.path.join(DEMO_DIR, "demo_public.py")


def _scrubbed_env():
    env = dict(os.environ)
    env.pop("EVENTS_ACCESS_TOKEN", None)
    return env


def test_sample_files_are_valid_json():
    for name in ("sessions-sample.json", "schedule-sample.json", "sample-output.txt"):
        path = os.path.join(DEMO_DIR, name)
        assert os.path.exists(path), f"missing {name}"
    with open(os.path.join(DEMO_DIR, "sessions-sample.json"), encoding="utf-8") as f:
        sessions = json.load(f)
    assert len(sessions) >= 3
    with open(os.path.join(DEMO_DIR, "schedule-sample.json"), encoding="utf-8") as f:
        scheduled = json.load(f)
    assert len(scheduled) >= 2


def test_demo_runs_with_no_token():
    proc = subprocess.run(
        [sys.executable, DEMO_SCRIPT],
        capture_output=True,
        text=True,
        env=_scrubbed_env(),
        cwd=REPO_ROOT,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "no token, no network" in out
    assert "shortlist" in out
    assert "# clash: ANT301 x CON401" in out
    assert "open slots" in out
    assert "stack-aware" in out.lower() or "keywords" in out


def test_sample_output_matches_demo():
    with open(os.path.join(DEMO_DIR, "sample-output.txt"), encoding="utf-8") as f:
        checked_in = f.read()
    proc = subprocess.run(
        [sys.executable, DEMO_SCRIPT],
        capture_output=True,
        text=True,
        env=_scrubbed_env(),
        cwd=REPO_ROOT,
        timeout=30,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == checked_in.strip()
