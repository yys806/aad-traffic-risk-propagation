"""Engineering contract for the Task9 fixed-leader paired experiment.

This module deliberately stops before SUMO execution.  It validates the two
sealed heterogeneous B00 arms, checks that a future pair really shares the
leader input and achieved initial state, and computes the signed kinematic
decomposition used by Task8.  It does not select physical segments, alter the
Formal P2/D1 definitions, or treat synthetic fixtures as observations.
"""
from __future__ import annotations

import hashlib
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

SEEDS = (20261101, 20261102, 20261103)
MIN_GAPS = (2.5, 1.0)
TAU_VALUES = (
    0.7389146576529666,
    1.093342856277335,
    1.3877275660721775,
    1.8288599276236361,
    2.5614676647488244,
)


class FixedLeaderPairError(ValueError):
    """Fail-closed error for unfair or incomplete paired input."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xml_differences(a: ET.Element, b: ET.Element, path: str = "root") -> list[dict[str, object]]:
    """Return structural XML differences without normalising away semantics."""
    differences: list[dict[str, object]] = []
    if a.tag != b.tag:
        differences.append({"path": path, "field": "tag", "arm_a": a.tag, "arm_b": b.tag})
    for key in sorted(set(a.attrib) | set(b.attrib)):
        if a.get(key) != b.get(key):
            differences.append({"path": path, "field": key, "arm_a": a.get(key), "arm_b": b.get(key)})
    if (a.text or "").strip() != (b.text or "").strip():
        differences.append({"path": path, "field": "text", "arm_a": a.text, "arm_b": b.text})
    if len(a) != len(b):
        differences.append({"path": path, "field": "children", "arm_a": len(a), "arm_b": len(b)})
    for index, (left, right) in enumerate(zip(a, b)):
        differences.extend(xml_differences(left, right, f"{path}/{left.tag}[{index}]"))
    return differences


def audit_arm_configs(
    routes_a: Path,
    routes_b: Path,
    network_a: Path,
    network_b: Path,
    config_a: Path,
    config_b: Path,
) -> dict[str, object]:
    """Verify that the sealed arms differ only in the five passenger minGap fields."""
    roots = (ET.parse(routes_a).getroot(), ET.parse(routes_b).getroot())
    differences = xml_differences(*roots)
    expected_paths = {f"root/vType[{i}]" for i in range(5)}
    if len(differences) != 5 or any(
        d["field"] != "minGap" or d["arm_a"] != "2.5" or d["arm_b"] != "1.0"
        or d["path"] not in expected_paths for d in differences
    ):
        raise FixedLeaderPairError("arm_config_difference_is_not_minGap_only")
    equal_files = {
        "network.net.xml": sha256(network_a) == sha256(network_b),
        "run.sumocfg": sha256(config_a) == sha256(config_b),
    }
    if not all(equal_files.values()):
        raise FixedLeaderPairError("network_or_simulation_config_differs")
    vtypes_a = roots[0].findall("vType")
    taus = [float(v.get("tau")) for v in vtypes_a]
    if taus != list(TAU_VALUES):
        raise FixedLeaderPairError("heterogeneous_tau_values_changed")
    return {
        "differences": differences,
        "equal_files": equal_files,
        "tau_heterogeneity": taus,
        "arms": {"A": "B00_minGap2.5", "B": "B00_minGap1.0"},
        "status": "Verified_static_configuration_only",
    }


def _finite(name: str, values: object) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or len(array) < 2 or not np.isfinite(array).all():
        raise FixedLeaderPairError(f"invalid_{name}")
    return array


def validate_common_input(arm_a, arm_b) -> dict[str, object]:
    """Require byte-equivalent clocks/leader input and matched achieved initials.

    The caller must pass two tabular objects with these columns:
    ``time_s``, ``leader_y_m``, ``leader_speed_mps``, ``follower_speed_mps`` and
    ``net_gap_m``.  Exact equality is intentional: no post-hoc time shift,
    arm-specific interpolation or tolerance is silently introduced here.
    """
    required = {"time_s", "leader_y_m", "leader_speed_mps", "follower_speed_mps", "net_gap_m"}
    for label, frame in (("arm_a", arm_a), ("arm_b", arm_b)):
        missing = required - set(frame.columns)
        if missing:
            raise FixedLeaderPairError(f"{label}_missing_columns:{sorted(missing)}")
    if len(arm_a) != len(arm_b) or len(arm_a) < 2:
        raise FixedLeaderPairError("paired_length_mismatch")
    for column in ("time_s", "leader_y_m", "leader_speed_mps"):
        if not np.array_equal(arm_a[column].to_numpy(), arm_b[column].to_numpy()):
            raise FixedLeaderPairError(f"leader_input_mismatch:{column}")
    for column in ("follower_speed_mps", "net_gap_m"):
        if not (math.isfinite(float(arm_a[column].iloc[0])) and math.isfinite(float(arm_b[column].iloc[0]))):
            raise FixedLeaderPairError(f"nonfinite_initial:{column}")
        if float(arm_a[column].iloc[0]) != float(arm_b[column].iloc[0]):
            raise FixedLeaderPairError(f"initial_state_mismatch:{column}")
    _finite("time", arm_a.time_s)
    return {
        "status": "Verified_common_leader_and_initial_state",
        "rows": int(len(arm_a)),
        "time_start_s": float(arm_a.time_s.iloc[0]),
        "time_end_s": float(arm_a.time_s.iloc[-1]),
        "leader_input_columns": ["time_s", "leader_y_m", "leader_speed_mps"],
        "matched_initial_columns": ["follower_speed_mps", "net_gap_m"],
        "time_shift_applied": False,
        "arm_specific_posthoc_filter": False,
    }


def kinematic_decomposition(
    time_s,
    follower_speed_mps,
    leader_speed_mps,
    net_gap_m,
) -> dict[str, float]:
    """Compute Task8's signed C decomposition on observed samples only."""
    t = _finite("time", time_s)
    vf = _finite("follower_speed", follower_speed_mps)
    vl = _finite("leader_speed", leader_speed_mps)
    gap = _finite("net_gap", net_gap_m)
    if not (len(t) == len(vf) == len(vl) == len(gap)):
        raise FixedLeaderPairError("decomposition_length_mismatch")
    dt = np.diff(t)
    if np.any(dt <= 0) or not np.allclose(dt, dt[0], rtol=0, atol=1e-9):
        raise FixedLeaderPairError("nonuniform_or_nonpositive_time_grid")
    horizon = float(t[-1] - t[0])
    trap = lambda x: float(np.sum(dt * 0.5 * (x[:-1] + x[1:])))
    c_initial = float((vf[0] - vl[0]) * horizon)
    c_f = trap(vf - vf[0])
    c_l = -trap(vl - vl[0])
    c = trap(vf - vl)
    c_gap = float(gap[0] - gap[-1])
    residual = float(c_gap - c)
    closure_error = float(c - c_initial - c_f - c_l)
    if abs(closure_error) > 1e-8:
        raise FixedLeaderPairError(f"decomposition_algebraic_closure:{closure_error}")
    return {
        "horizon_s": horizon,
        "C_initial_m": c_initial,
        "C_f_m": c_f,
        "C_l_m": c_l,
        "C_m": c,
        "C_gap_m": c_gap,
        "R_m": residual,
        "closure_error_m": closure_error,
    }


def compare_arms(arm_a, arm_b) -> dict[str, object]:
    """Return paired arm differences after the common-input contract passes."""
    common = validate_common_input(arm_a, arm_b)
    a = kinematic_decomposition(arm_a.time_s, arm_a.follower_speed_mps,
                                arm_a.leader_speed_mps, arm_a.net_gap_m)
    b = kinematic_decomposition(arm_b.time_s, arm_b.follower_speed_mps,
                                arm_b.leader_speed_mps, arm_b.net_gap_m)
    delta = {f"delta_{key}": float(b[key] - a[key]) for key in
             ("C_initial_m", "C_f_m", "C_l_m", "C_m", "C_gap_m", "R_m")}
    if abs(delta["delta_C_initial_m"]) > 1e-12 or abs(delta["delta_C_l_m"]) > 1e-12:
        raise FixedLeaderPairError("exact_cancellation_conditions_failed")
    if abs(delta["delta_C_m"] - delta["delta_C_f_m"]) > 1e-8:
        raise FixedLeaderPairError("delta_C_not_equal_delta_Cf")
    return {"common_input": common, "arm_a": a, "arm_b": b, "differences": delta,
            "exact_cancellation_checked": True}
