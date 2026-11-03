"""P4 read-only measurement audit. Never launches traffic simulations.

Examples expose current software semantics; their numbers are not research parameters.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def probes(root):
    sys.path.insert(0, str(root / "code/src"))
    import pandas as pd
    from riskprop.formal_risk_measurement import (
        P2_FORMAL_CONFIG, rho_from_ttc, contribution_bounds,
        integrate_fixed_window, equal_vehicle_average, did_interval,
    )
    from riskprop.stage_i_mechanism import compare_paired_action
    from riskprop.prelock_metrics import integrated_ttc_exposure, post_encroachment_time

    results = []

    def record(name, actual, expected, status="VERIFIED_CURRENT_SEMANTICS"):
        def close(a, b):
            if isinstance(b, dict):
                return all(k in a and close(a[k], v) for k, v in b.items())
            if isinstance(b, (tuple, list)):
                return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
            if isinstance(b, (float, int)) and not isinstance(b, bool):
                return isinstance(a, (float, int)) and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
            return a == b
        assert close(actual, expected), (name, actual, expected)
        results.append({"id": name, "actual": actual, "expected": expected, "status": status})

    record("rho_no_P2_threshold_truncation", rho_from_ttc(5), math.exp(-5 / P2_FORMAL_CONFIG.tau_s))
    record("rho_invalid_zero", rho_from_ttc(0), None)
    for name, kw, expected in [
        ("known_outside", dict(measurement_status="missing", in_region=False, ttc_s=None), (0, 0, None)),
        ("unknown_region", dict(measurement_status="valid", in_region=None, ttc_s=1), (0, 1, None)),
        ("unreliable_region", dict(measurement_status="valid", in_region=False, region_reliable=False, ttc_s=1), (0, 1, None)),
        ("inside_missing", dict(measurement_status="missing", in_region=True, ttc_s=None), (0, 1, None)),
        ("inside_invalid", dict(measurement_status="invalid", in_region=True, ttc_s=0), (0, 1, None)),
        ("inside_reliable_not_applicable", dict(measurement_status="not_applicable", in_region=True, ttc_s=None), (0, 0, None)),
        ("inside_unreliable_not_applicable", dict(measurement_status="not_applicable", in_region=True, reliable=False, ttc_s=None), (0, 1, None)),
    ]:
        record(name, contribution_bounds(**kw), expected)

    def rows(times, value=0.2):
        return pd.DataFrame([dict(time_s=t, global_time_ms=round(t*1000), frame_id=round(t*10),
            diagnostic_clock_anchor_ms=0, dataset="DETERMINISTIC_MATH_ONLY", site="s", window_id="w",
            source_member="m", source_period="p", trajectory_id="v:entry1", leader_trajectory_id="l:entry1",
            leader_matched=True, identity_uncertain=False, leader_identity_uncertain=False,
            identity_break=False, observation_gap=False, lower=value, upper=value) for t in times])

    record("complete_constant_window", integrate_fixed_window(rows([0, .1, .2, .3]),
        window_start_s=0, window_end_s=.3), {"lower_mean": .2, "upper_mean": .2, "known_time_s": .3})
    record("gap_and_right_tail_keep_full_denominator", integrate_fixed_window(rows([0, .1, .3]),
        window_start_s=0, window_end_s=.4), {"lower_mean": .05, "upper_mean": .8, "known_time_s": .1, "unknown_time_s": .3})
    record("time_clip_between_brackets", integrate_fixed_window(rows([0, .1, .2]),
        window_start_s=.05, window_end_s=.15), {"lower_mean": .2, "upper_mean": .2})
    record("fully_unobserved_vehicle", integrate_fixed_window(pd.DataFrame(),
        window_start_s=0, window_end_s=1), {"lower_mean": 0, "upper_mean": 1, "unknown_time_s": 1})
    x = rows([0, .1]); x.loc[1, "leader_trajectory_id"] = "other"
    record("leader_switch_conservative_interval", integrate_fixed_window(x,
        window_start_s=0, window_end_s=.1), {"lower_mean": 0, "upper_mean": 1})
    x = rows([0, .1], 0); x["leader_matched"] = False; x["leader_trajectory_id"] = None
    record("point_zero_no_leader_not_a_proven_time_link", integrate_fixed_window(x,
        window_start_s=0, window_end_s=.1), {"lower_mean": 0, "upper_mean": 1})
    try:
        integrate_fixed_window(rows([0, 0, .1]), window_start_s=0, window_end_s=.1)
    except ValueError as e:
        record("duplicate_integration_time_rejected", str(e), "duplicate observation timestamps")
    else:
        raise AssertionError("duplicate times accepted")
    record("fixed_N_unknown_member_propagates", equal_vehicle_average([
        {"lower_mean": .2, "upper_mean": .2}, {"lower_mean": 0, "upper_mean": 1}]),
        {"lower_mean": .1, "upper_mean": .6, "vehicle_count": 2})
    record("averager_has_no_external_roster_check", equal_vehicle_average([
        {"lower_mean": .2, "upper_mean": .2}]), {"lower_mean": .2, "upper_mean": .2, "vehicle_count": 1},
        "VERIFIED_LIMITATION_NOT_APPROVAL")
    record("factorial_interval_not_an_estimator", did_interval(*[{"lower_mean": 0, "upper_mean": 1}]*4), [-2, 2])

    def compare(times, values, *, base_times=None, sustain=.3, base_inc="entry1", treat_inc="entry1"):
        btimes = times if base_times is None else base_times
        baseline = pd.DataFrame({"time_s": btimes, "vehicle_id": "v", "speed_mps": 0., "incarnation_id": base_inc})
        treatment = pd.DataFrame({"time_s": times, "vehicle_id": "v", "speed_mps": values, "incarnation_id": treat_inc})
        return compare_paired_action(baseline, treatment, treatment_start_s=0, speed_tolerance_mps=.1, sustain_s=sustain)

    record("action_long_gap_is_bridged", compare([0, .1, 10], [1, 1, 1]),
        {"first_action_change_time_s": 0, "effect_observed": True}, "VERIFIED_LIMITATION_NOT_APPROVAL")
    record("action_missing_row_is_dropped_and_bridged", compare([0, .1, .2], [1, float("nan"), 1]),
        {"first_action_change_time_s": 0, "effect_observed": True}, "VERIFIED_LIMITATION_NOT_APPROVAL")
    record("action_last_sample_gets_median_step_extension", compare([0, .1, .2], [1, 1, 1]),
        {"first_action_change_time_s": 0, "effect_observed": True}, "VERIFIED_LIMITATION_NOT_APPROVAL")
    record("action_incarnation_is_not_checked", compare([0, .1, .2], [1, 1, 1], base_inc="entry1", treat_inc="entry2"),
        {"first_action_change_time_s": 0, "effect_observed": True}, "VERIFIED_LIMITATION_NOT_APPROVAL")
    record("action_different_grids_not_resampled", compare([.05, .15, .25], [1, 1, 1], base_times=[0, .1, .2]),
        {"status": "unknown_no_common_observations", "effect_observed": None})
    try:
        compare([0, 0, .1], [1, 1, 1])
    except ValueError as e:
        record("action_duplicate_merge_fails_downstream", str(e), "times must be strictly increasing")
    else:
        raise AssertionError("duplicate compare did not fail")

    record("auxiliary_valid_flag_with_nan_TTC_becomes_zero", integrated_ttc_exposure(pd.DataFrame({
        "ttc_s": [float("nan")], "valid": [True], "dt_s": [1.], "collision": [False]}), threshold_s=2), 0.,
        "VERIFIED_LIMITATION_NOT_APPROVAL")
    record("auxiliary_PET_overlap_zero", post_encroachment_time((0, 2), (1, 3)), 0.)
    return {"status": "OFFLINE_SEMANTICS_VERIFIED_WITH_LIMITATIONS", "checks_passed": len(results),
        "failed": 0, "examples": results, "new_traffic_runs": 0,
        "scientific_parameters_selected": False, "scientific_claim_eligible": False}


def verify_bundle(root, here):
    lines = (here / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    sealed = set()
    for line in lines:
        h, rel = line.split("  ", 1)
        path = (here / rel).resolve()
        assert path.is_relative_to(here) and rel not in sealed
        assert digest(path.read_bytes()) == h, rel
        sealed.add(rel)
    assert sealed == {p.relative_to(here).as_posix() for p in here.rglob("*") if p.is_file()
        and p.name != "SHA256SUMS" and "__pycache__" not in p.parts}
    manifest = load(here / "source_manifest.json")
    variants = []
    for rel, hashes in manifest["files"].items():
        b = (root / rel).read_bytes()
        if digest(b) != hashes["worktree_sha256"]:
            assert digest(b) == hashes["git_blob_sha256"], rel
            assert digest(b.replace(b"\r\n", b"\n")) == hashes["lf_sha256"], rel
            variants.append(rel)
    result = probes(root)
    # JSON has arrays only; normalize Python tuple containers, not values.
    assert json.loads(json.dumps(result, allow_nan=False)) == load(here / "deterministic_examples.json")
    audit = load(root / "docs/research/P4/p4_implementation_audit.json")
    assert audit["definition_version"] == "AAD-SCI-DEF-20261102-P2T6-v0.4"
    assert audit["new_experiments"] == 0 and not audit["scientific_claim_eligible"]
    import csv
    dictionary = list(csv.DictReader((root / "docs/research/P4/p4_measurement_variable_dictionary.csv").open(encoding="utf-8", newline="")))
    keys = [(r["table"], r["field"]) for r in dictionary]
    assert len(keys) == len(set(keys)), "duplicate dictionary fields"
    for row in dictionary:
        assert all(row.get(k) for k in ("table", "field", "type", "unit", "meaning", "source", "nullable_when", "status"))
        assert row['status'] == 'PROPOSAL_NOT_DEPLOYED'
    trace = list(csv.DictReader((root / 'docs/research/P4/p4_measurement_traceability.csv').open(encoding='utf-8', newline='')))
    for row in trace:
        p = root / row['source_path']
        assert p.is_file(), row['source_path']
        assert 1 <= int(row['line_start']) <= int(row['line_end']) <= len(p.read_text(encoding='utf-8').splitlines()), row['finding_id']
    import re
    link_count = 0
    for p in (root / 'docs/research/P4').glob('*.md'):
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', p.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            assert (p.parent / target.split('#', 1)[0]).resolve().exists(), (p.name, target)
            link_count += 1
    assert len(dictionary) == audit['dictionary_fields']
    assert len(trace) == audit['traceability_findings']
    assert load(here/'protected_byte_check.json')['changed_files'] == []
    assert load(here/'tests.json')['process_guard']['blocked_attempts'] == []
    assert load(here/'validation.json')['new_SUMO_runs'] == 0
    return {"status": "P4_TASK1_PORTABLE_VERIFIED", "sealed_files": len(sealed),
        "source_files_verified": len(manifest["files"]), "deterministic_checks": result["checks_passed"],
        "dictionary_fields": len(keys), "traceability_findings": len(trace), 'local_document_links_checked': link_count,
        "explicit_git_line_ending_variants": variants,
        "new_traffic_runs": 0, "scientific_claim_eligible": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    p.add_argument("--probe-only", action="store_true")
    p.add_argument("--json-output", type=Path)
    args = p.parse_args()
    result = probes(args.repo_root.resolve()) if args.probe_only else verify_bundle(args.repo_root.resolve(), Path(__file__).resolve().parent)
    if args.json_output:
        args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "examples"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
