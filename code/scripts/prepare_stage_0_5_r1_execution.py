"""Prepare and execute the exact Stage 0.5-R1 diagnostic arms.

This entrypoint is deliberately separate from the historical B00 admission
builder.  It reuses only the already accepted current-source Linux capsule
integration (week_r9) and creates one immutable capsule/policy/envelope per
R1 arm.  The scientific design is data, not inferred from outcomes.

The script is intended to run inside the authorized Ubuntu WSL workspace with
the Windows checkout mounted at /mnt/d/shen/TJU/AAD.  It never reruns B00.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


TASK = "AAD-0.5-READY-TO-ADMIT-V3"  # admission schema namespace; R1 id is explicit below
R1_TASK = "AAD-S0.5-R1-EXECUTE-20261028"
RESULT_ID = "RES-STAGE-0.5-R1-DIAGNOSTICS-20261028"
SOURCES = [
    "stage_0_5_execution_v2.py", "stage_0_5_linux_isolation.py",
    "stage_0_5_isolation_admission.py", "stage_0_5_identity_observation.py",
    "stage_0_5_input_fidelity.py", "stage_0_5_isolation_v2.py",
    "stage_0_5_research_ledger.py", "stage_0_5_linux_runtime_v4.py",
    "stage_0_5_native_capsule_v4.py", "stage_0_5_linux_controller_v4.py",
    "stage_0_5_linux_execution_v4.py", "probe_stage_0_5_linux_isolation.py",
]
LANES = [f"main_2_{i}" for i in range(5)]
BASELINE_ROUTE = "evidence/admission/AAD-WEEK-2026-10-27-TO-STAGE-I-V1/candidate-v1/routes.rou.xml"
BASELINE_NET = "evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v2/inputs/network.net.xml"
BASELINE_CFG = "evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v2/inputs/run.sumocfg"
RAMP_ROUTE = "evidence/admission/AAD-S0.5-R0-20261028/candidate-v1/ramp_routes.rou.xml"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as f:
        f.write(value if isinstance(value, bytes) else canonical(value) + b"\n")


def prepare(repo: Path, root: Path):
    """Create three exact capsules.  Existing R1 roots are never overwritten."""
    root = root.resolve()
    if root.exists():
        raise RuntimeError(f"exclusive_new_r1_root_required:{root}")
    root.mkdir(parents=True)
    # The runtime and current-source staging are independently bound.  The
    # week_r9 integration receipt is only an engineering prerequisite; no B00
    # input or authorization is copied into an R1 capsule.
    integration = Path("/home/shen/AAD/code/tmp/stage05_v4_20261027_week_r9")
    runtime_src = integration / "runtime_manifest.json"
    probe_src = integration / "probe_results/record.json"
    if not runtime_src.exists() or not probe_src.exists():
        raise RuntimeError("current_source_smoke_staging_missing")

    # Imports resolve against the WSL source copy, exactly as the production
    # capsule does.
    sys.path.insert(0, str(root))
    for name in SOURCES:
        src = repo / "code/scripts" / name
        dst = root / name
        shutil.copyfile(src, dst)
    shutil.copyfile(runtime_src, root / "runtime_manifest.json")
    shutil.copyfile(probe_src, root / "probe_results_record.json")
    runtime = json.loads((root / "runtime_manifest.json").read_bytes())
    probe = json.loads((root / "probe_results_record.json").read_bytes())

    # Current-source smoke receipt is checked before R1 material is produced.
    smoke_acceptance = integration / "smoke_capsule/engineering_acceptance.json"
    if not smoke_acceptance.exists():
        raise RuntimeError("current_source_smoke_acceptance_missing")
    smoke = json.loads(smoke_acceptance.read_bytes())
    if smoke.get("status") != "Pass" or smoke.get("runtime_manifest_sha256") != sha(runtime_src):
        raise RuntimeError("current_source_smoke_acceptance_not_verified")
    controller_source = {n: sha(root / n) for n in SOURCES}
    if smoke.get("controller_sha256") is None:
        raise RuntimeError("smoke_controller_binding_missing")

    # Keep all R1 records in the Windows repository evidence tree; WSL capsule
    # paths are retained in the binding because the native run is WSL-local.
    evidence = repo / "evidence/results" / RESULT_ID
    if evidence.exists():
        raise RuntimeError("exclusive_new_result_required")
    evidence.mkdir(parents=True)
    input_root = evidence / "inputs"
    input_root.mkdir()
    for name, rel in {
        "network.net.xml": BASELINE_NET,
        "B00_routes.rou.xml": BASELINE_ROUTE,
        "ramp_routes.rou.xml": RAMP_ROUTE,
        "run.sumocfg": BASELINE_CFG,
    }.items():
        shutil.copyfile(repo / rel, input_root / name)

    # Use the existing fixed research resource budget; only one arm is ever
    # started by this process at a time.
    budget = json.loads((repo / "code/configs/stage_0_5_ready_to_admit_v3.json").read_bytes())
    limits = budget["single_attempt_limits"]
    import stage_0_5_linux_runtime_v4 as runtime_mod
    import stage_0_5_native_capsule_v4 as capsule_mod

    arms = {
        "B10": (False, "B00_routes.rou.xml", [dict(start_s=0, end_s=180, speed_mps=10), dict(start_s=180, end_s=240, speed_mps=5), dict(start_s=240, end_s=420, speed_mps=10)]),
        "B01": (True, "ramp_routes.rou.xml", [dict(start_s=0, end_s=420, speed_mps=10)]),
        "B11": (True, "ramp_routes.rou.xml", [dict(start_s=0, end_s=180, speed_mps=10), dict(start_s=180, end_s=240, speed_mps=5), dict(start_s=240, end_s=420, speed_mps=10)]),
    }
    prepared = {}
    for arm, (ramp, route_name, schedule) in arms.items():
        run_id = f"AAD-S0.5-R1-{arm}-20261028"
        adir = root / arm
        adir.mkdir()
        inputs = adir / "inputs"
        inputs.mkdir()
        shutil.copyfile(input_root / "network.net.xml", inputs / "network.net.xml")
        shutil.copyfile(input_root / route_name, inputs / "routes.rou.xml")
        shutil.copyfile(input_root / "run.sumocfg", inputs / "run.sumocfg")
        run = dict(id=run_id, arm=arm, duration_s=420, internal_step_s=0.05,
                   recording_step_s=0.1, evaluation_elapsed_s=[120, 390], seed=20261201,
                   factors=dict(supply=any(x["speed_mps"] == 5 for x in schedule), ramp=ramp),
                   supply_target_lanes=LANES, lane_speed_schedule=schedule,
                   input_files={n: str(inputs / n) for n in ["network.net.xml", "routes.rou.xml", "run.sumocfg"]},
                   input_sha256={n: sha(inputs / n) for n in ["network.net.xml", "routes.rou.xml", "run.sumocfg"]},
                   capsule_input_sha256={n: sha(inputs / n) for n in ["network.net.xml", "routes.rou.xml", "run.sumocfg"]},
                   single_attempt_limits=limits)
        capsule = adir / "research_capsule"
        source_files = {n: str(root / n) for n in SOURCES}
        policy_path, policy = runtime_mod.make_policy(capsule, runtime, root / "runtime_manifest.json",
                                                       source_files, run["input_files"], run,
                                                       accepted_build=True, capability_record=root / "probe_results_record.json")
        proposal = dict(schema=capsule_mod.SCHEMA, task_id=TASK, r1_task_id=R1_TASK,
                        result_id=RESULT_ID, arm=arm, status="R1 exact execution proposal",
                        runs=[run], runtime=runtime, runtime_manifest_path=str(root / "runtime_manifest.json"),
                        runtime_manifest_sha256=sha(root / "runtime_manifest.json"),
                        controller_source_sha256=controller_source,
                        native_environment=dict(policy["environment"], PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1"),
                        capsule_policy_path=str(policy_path), capsule_policy_sha256=sha(policy_path),
                        kernel_probe_sha256=sha(root / "probe_results_record.json"),
                        single_attempt_limits=limits,
                        isolation=dict(accepted_for_new_task=True, source="current-source-week-r9-smoke",
                                       smoke_acceptance_sha256=sha(smoke_acceptance),
                                       smoke_controller_sha256=smoke["controller_sha256"],
                                       smoke_runtime_manifest_sha256=smoke["runtime_manifest_sha256"]),
                        previous_baseline_run_id="WEEK_0750_B00_IC1_s20261201_A03",
                        scientific_design=dict(source_region="S_UPSTREAM_MAIN", target_region="main_0/main_1 lanes 1-5 [150,350)m",
                                               cohort="C_INPUT_ROUTE", p2_config="code/configs/stage_0_2_formal_risk_measurement_p2_v1.json",
                                               physical_path_policy="time-expanded qualified witness; missing support is uncertain"))
        proposal_path = adir / "proposal.json"
        write(proposal_path, proposal)
        approval = dict(task_id=TASK, r1_task_id=R1_TASK, run_id=run_id,
                        proposal_sha256=sha(proposal_path), decision_record="Researcher-approved AAD-S0.5-R1-EXECUTE-20261028; exact arm " + arm,
                        execution_allowed=True, researcher_confirmed=True, protocol_frozen=True,
                        admission=dict(initialization_policy_approved=True, measurement_contract_approved=True, input_fidelity_approved=True),
                        arm=arm)
        envelope = dict(proposal_path=str(proposal_path), proposal_sha256=sha(proposal_path), run_id=run_id, approval=approval)
        write(adir / "envelope.json", envelope)
        write(evidence / f"run_admission_{arm}.json", dict(schema="aad.r1.run-admission.v1", task_id=R1_TASK,
            arm=arm, run_id=run_id, proposal_path=str(proposal_path), proposal_sha256=sha(proposal_path),
            policy_path=str(policy_path), policy_sha256=sha(policy_path), envelope_path=str(adir / "envelope.json"),
            envelope_sha256=sha(adir / "envelope.json"), input_sha256=run["input_sha256"],
            source_sha256=controller_source, runtime_manifest_sha256=sha(root / "runtime_manifest.json"),
            engineering_smoke_acceptance_sha256=sha(smoke_acceptance), status="AUTHORIZED_FOR_ONE_RUN"))
        prepared[arm] = dict(stage=str(adir), proposal=str(proposal_path), envelope=str(adir / "envelope.json"),
                             envelope_sha256=sha(adir / "envelope.json"), run_id=run_id)
    write(evidence / "r1_design_freeze.json", dict(schema="aad.r1.design-freeze.v1", task_id=R1_TASK,
        status="Verified / Agreed", source_region="S_UPSTREAM_MAIN", target_region=dict(edges=["main_0", "main_1"], lanes=[1,2,3,4,5], y_m=[150,350], window_s=[120,390]),
        cohort="C_INPUT_ROUTE", p2_rule="code/configs/stage_0_2_formal_risk_measurement_p2_v1.json",
        baseline_run_id="WEEK_0750_B00_IC1_s20261201_A03", arms=prepared,
        source_authority="researcher task AAD-S0.5-R1-EXECUTE-20261028"))
    write(evidence / "preparation_binding.json", dict(source_sha256=controller_source, runtime_manifest_sha256=sha(root / "runtime_manifest.json"),
        current_source_smoke_acceptance_sha256=sha(smoke_acceptance), input_files={n: sha(input_root / n) for n in ["network.net.xml", "B00_routes.rou.xml", "ramp_routes.rou.xml", "run.sumocfg"]}))
    print(json.dumps(prepared, ensure_ascii=False, sort_keys=True))


def execute(root: Path):
    """Launch each exact envelope once, then independently verify its receipt."""
    sys.path.insert(0, str(root))
    import stage_0_5_linux_execution_v4 as driver
    import stage_0_5_native_capsule_v4 as capsule_mod
    evidence = Path("/mnt/d/shen/TJU/AAD/evidence/results") / RESULT_ID
    results = {}
    for arm in ("B10", "B01", "B11"):
        adir = root / arm
        env = json.loads((adir / "envelope.json").read_bytes())
        try:
            acceptance = driver.launch_linux(str(adir / "envelope.json"), sha(adir / "envelope.json"))
            archive = Path(json.loads((adir / "proposal.json").read_bytes())["capsule_policy_path"]).parent / "archive"
            proposal = json.loads((adir / "proposal.json").read_bytes())
            independent = capsule_mod.verify_receipt(archive, proposal, env["proposal_sha256"], proposal["capsule_policy_sha256"])
            results[arm] = dict(status="Pass", acceptance=acceptance, independent_receipt=independent,
                                archive=str(archive), archive_sha256={p.name: sha(p) for p in archive.iterdir() if p.is_file()})
            # Copy all sealed artifacts and the exact proposal/envelope to the
            # repository evidence tree after verification.
            out = evidence / arm
            out.mkdir()
            for p in archive.iterdir():
                if p.is_file(): shutil.copyfile(p, out / p.name)
            for p in [adir / "proposal.json", adir / "envelope.json", adir / "engineering_acceptance.json"]:
                if p.exists(): shutil.copyfile(p, out / p.name)
            (out / "independent_receipt.json").write_bytes(canonical(independent) + b"\n")
            (out / "execution_summary.json").write_bytes(canonical(results[arm]) + b"\n")
        except BaseException as exc:
            results[arm] = dict(status="Failed", error=type(exc).__name__ + ":" + str(exc), envelope=env)
            (evidence / arm).mkdir(exist_ok=True)
            (evidence / arm / "execution_failure.json").write_bytes(canonical(results[arm]) + b"\n")
    (evidence / "execution_results.json").write_bytes(canonical(results) + b"\n")
    print(json.dumps(results, ensure_ascii=False, sort_keys=True))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["prepare", "execute"])
    ap.add_argument("--repo-root", type=Path, default=Path("/mnt/d/shen/TJU/AAD"))
    ap.add_argument("--stage-root", type=Path, default=Path("/home/shen/AAD/code/tmp/stage05_r1_20261028"))
    a = ap.parse_args(argv)
    if a.mode == "prepare":
        prepare(a.repo_root.resolve(), a.stage_root)
    else:
        execute(a.stage_root.resolve())


if __name__ == "__main__":
    main()
