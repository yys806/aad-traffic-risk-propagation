"""No-data Git clone software checks; refuse the main workspace.

Python audit only, not OS/native isolation certification. Native SUMO tests are
deselected; attempts to launch SUMO/netconvert or read the source workspace fail.
The audit survives pytest failures. No simulator is needed or invoked.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-workspace", type=Path, required=True)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--test", action="append", help="Explicit offline tests/test_*.py selection; native exclusions and no-data audit still apply")
    args = parser.parse_args()
    if args.test and (args.full or any(not p.startswith("tests/test_") or not p.endswith(".py") or ".." in p or "\\" in p for p in args.test)):
        raise SystemExit("Refused: --test requires explicit relative tests/test_*.py files and cannot combine --full")
    repo = Path(__file__).resolve().parents[2]
    source = args.source_workspace.resolve()
    if repo == source or not (repo / ".git").is_dir() or (repo / "dataset").exists() or (repo / "code/outputs/formal").exists():
        raise SystemExit("Refused: requires separate Git clone without dataset/formal outputs")
    out = repo / "code/tmp/research_v2_validation" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + "_" + str(os.getpid()))
    out.mkdir(parents=True, exist_ok=True)
    # Imports occur after clone identity check; package metadata stays in runtime roots.
    import site
    runtimes = [Path(sys.base_prefix).resolve(), Path(site.getusersitepackages()).resolve()]
    runtimes += [Path(p).resolve() for p in site.getsitepackages()]
    # Narrow runtime font resources; do not allow general profile/system reads.
    runtimes += [Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
                 Path(os.environ["LOCALAPPDATA"]) / "Microsoft/Windows/Fonts",
                 Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "Microsoft Office/Windows/Fonts"]
    # Ambient editable projects/plugin entry points are not validation inputs.
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    sys.path[:] = [value for value in sys.path if Path(value or os.getcwd()).resolve().is_relative_to(repo) or
                   any(Path(value or os.getcwd()).resolve().is_relative_to(p) for p in runtimes)]
    temporary = out / "system_tmp"
    temporary.mkdir()
    os.environ["MPLCONFIGDIR"] = str(out / "matplotlib")
    tempfile.tempdir = str(temporary)
    for name in ["TEMP", "TMP", "TMPDIR"]:
        os.environ[name] = str(temporary)
    import pytest
    audit = {"scope": "Python parent audit in no-data Git clone; not OS/native certification", "denied": [], "processes": [],
             "source_workspace": str(source), "clone": str(repo), "sumo_launches": 0, "tests": args.test or ("full software" if args.full else "targeted")}
    null_devices = {"nul", r"\\.\nul", r"\\?\nul", os.path.normcase(os.devnull)}

    def hook(event, values):
        if event == "open" and isinstance(values[0], (str, bytes)):
            value = os.fsdecode(values[0])
            if os.path.normcase(value).replace("/", "\\") in null_devices or value.startswith("<"):
                return
            path = Path(value).resolve()
            mode, flags = values[1], values[2]
            writing = bool(isinstance(mode, str) and any(c in mode for c in "wax+"))
            writing |= bool(isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            allowed = path.is_relative_to(repo) if writing else (path.is_relative_to(repo) or any(path.is_relative_to(p) for p in runtimes))
            if path.is_relative_to(source) and not path.is_relative_to(repo):
                allowed = False
            if not allowed:
                audit["denied"].append({"path": str(path), "write": writing})
                raise PermissionError("validation_scope_denied:" + str(path))
        if event == "subprocess.Popen":
            command = str(values[1])
            executable = os.fsdecode(values[0]) if values[0] else ""
            # Parent Python audit does not propagate to arbitrary native children.
            if any(word in (executable + " " + command).lower() for word in ["sumo.exe", "netconvert.exe", "sumo-gui", '"sumo"', "'sumo'", '"netconvert"', "'netconvert'"]):
                audit["sumo_launches"] += 1
                audit["denied"].append({"process": command})
                raise PermissionError("simulation_forbidden_in_software_validation")
            audit["processes"].append({"executable": executable, "command": command})

    sys.dont_write_bytecode = True
    sys.addaudithook(hook)
    sys.path.insert(0, str(repo / "code/src"))
    os.chdir(repo / "code")
    # Fixed explicit exclusion, independent of whether SUMO is on PATH.
    excluded = ["test_real_sumo_stage_0_1_seals_nonempty_four_cell_package_and_read_only_audit",
                "test_sumo_baseline_engineering_run_is_sealed_and_contract_complete",
                "test_sumo_probe_fixture_confirms_a_p2_event_in_both_adapters",
                "test_sumo_run_is_reproducible_for_the_same_seed_and_config",
                "test_sumo_internal_and_recorded_steps_are_separately_configurable",
                "test_sumo_warmup_window_is_respected_and_unbuilt_scenarios_are_refused",
                "test_sumo_smoke_runs_never_change_the_stage_gate"]
    tests = ["tests"] if args.full else ["tests/test_stage_0_5_research_ledger.py", "tests/test_interaction_task_boundary.py",
                                        "tests/test_stage_0_5_d1_measurement.py", "tests/test_project_docs.py"]
    if args.test:
        tests = args.test
    command = tests + ["-q", "-p", "no:cacheprovider", "--basetemp=" + str(out / ("full_tmp" if args.full else "targeted_tmp")),
                       "-k", "not (" + " or ".join(excluded) + ")"]
    status = 1
    try:
        status = pytest.main(command)
    finally:
        audit["exit_code"] = int(status)
        (out / ("full_audit.json" if args.full else "targeted_audit.json")).write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("VALIDATION_AUDIT_PATH=" + str(out))
    return 1 if audit["denied"] else status


if __name__ == "__main__":
    raise SystemExit(main())
