"""Task-local pytest guard: all process creation is forbidden in offline checks."""
import json
from pathlib import Path
import sys

blocked = []


def pytest_sessionstart(session):
    def guard(event, args):
        if event in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.fork"):
            blocked.append({"event": event, "reason": "P4 permits no external process during offline tests"})
            raise RuntimeError("P4_OFFLINE_PROCESS_CREATION_FORBIDDEN")
    sys.addaudithook(guard)


def pytest_sessionfinish(session, exitstatus):
    Path(__file__).with_name("offline_process_guard.json").write_text(json.dumps({
        "blocked_attempts": blocked, "guard_active": True, "exitstatus": int(exitstatus),
        "new_SUMO_processes": 0}, indent=2), encoding="utf-8")
