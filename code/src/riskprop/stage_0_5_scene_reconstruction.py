"""Evidence-driven SUMO scene reconstruction for Stage 0.5.

The reconstruction uses only quantities observed in the two approved calibration
windows (or the bundled official NGSIM aggregates):

* five mainline lanes over the full 640 m segment;
* an on-ramp that merges into an added lane at the observed merge position;
* an auxiliary lane between the merge and the diverge;
* an off-ramp that continues the auxiliary lane at the observed diverge position;
* the observed boundary demand on each of those entries;
* an optional initial condition taken from the real congested state.

It is explicitly a *conditional* scene: the observed windows cannot identify the
downstream supply that holds the real segment on the congested branch, so any
capacity restriction is a declared scenario assumption and never a claimed real
mechanism.
"""
from __future__ import annotations

import json
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

from .stage_0_5_sumo import (
    Stage05EngineeringError,
    _netconvert_binary,
    _sumo_binary,
    build_candidate_network,
)

VERSION = "stage-0.5-scene-reconstruction-v1"

# Observed longitudinal support of the real geometry (metres along the segment).
SEGMENT_LENGTH_M = 669.18
MERGE_POSITION_M = 187.58
DIVERGE_POSITION_M = 399.22
ONRAMP_OBSERVED_START_M = 128.735
OFFRAMP_OBSERVED_END_M = 450.84

OBSERVED_GEOMETRY: dict[str, object] = {
    "schema_version": "stage_0_5.sumo-engineering.v2.network-candidate.v1",
    "network_id": "observed_geometry_candidate",
    "classification": "conditional_observed_geometry_candidate",
    "claim": "observed_geometry_from_ngsim_us101_lane_support_not_full_facility_replication",
    "design_basis": [
        "five mainline lanes over the observed 669 m, matching the official site description",
        "a dedicated lane starts exactly where the observed on-ramp lane ends (merge at 187.6 m)",
        "the added lane ends exactly where the observed off-ramp lane starts (diverge at 399.2 m)",
        "no traffic signal and no lane closure anywhere in the observed segment",
    ],
    "nodes": [
        {"id": "hwy_w", "x": 0.0, "y": 0.0},
        {"id": "hwy_m1", "x": MERGE_POSITION_M, "y": 0.0},
        {"id": "hwy_m2", "x": DIVERGE_POSITION_M, "y": 0.0},
        {"id": "hwy_e", "x": SEGMENT_LENGTH_M, "y": 0.0},
        {"id": "hwy_on", "x": 60.0, "y": -160.0},
        {"id": "hwy_off", "x": 560.0, "y": -160.0},
    ],
    "edges": [
        {"id": "main_0", "from": "hwy_w", "to": "hwy_m1", "lanes": 5, "speed_mps": 27.78, "priority": 2},
        {"id": "main_1", "from": "hwy_m1", "to": "hwy_m2", "lanes": 6, "speed_mps": 27.78, "priority": 2},
        {"id": "main_2", "from": "hwy_m2", "to": "hwy_e", "lanes": 5, "speed_mps": 27.78, "priority": 2},
        {"id": "onramp", "from": "hwy_on", "to": "hwy_m1", "lanes": 1, "speed_mps": 13.89, "priority": 1},
        {"id": "offramp", "from": "hwy_m2", "to": "hwy_off", "lanes": 1, "speed_mps": 13.89, "priority": 1},
    ],
    "routes": {
        "through": ["main_0", "main_1", "main_2"],
        "entering": ["onramp", "main_1", "main_2"],
        "exiting": ["main_0", "main_1", "offramp"],
    },
    "lane_change_enabled": True,
}

FIXED_VTYPE = dict(
    maxSpeed=27.78, speedFactor=1.0, speedDev=0.0, carFollowModel="Krauss", tau=1.0,
    minGap=2.5, accel=2.6, decel=4.5, apparentDecel=4.5, emergencyDecel=9.0, sigma=0.5,
    actionStepLength=0.1, sigmaStep=1.0, laneChangeModel="LC2013",
)

# Real lane id -> SUMO lane index per edge. SUMO index 0 is the rightmost lane.
LANE_INDEX_MAIN = {"1": 4, "2": 3, "3": 2, "4": 1, "5": 0}
LANE_INDEX_AUX = {"6": 0}

#: Analytic Krauss saturation capacity of one lane at the frozen vType parameters
#: (headway = tau + (length + minGap) / v).  Derived, not fitted.
FREE_FLOW_LANE_CAPACITY_VEH_H = 3600.0 / (
    FIXED_VTYPE["tau"] + (4.4196 + FIXED_VTYPE["minGap"]) / FIXED_VTYPE["maxSpeed"]
)

# Observed conditional demand per window. Boundary values are the trajectory
# crossings of the approved windows; ramp values are the official NGSIM direct
# counts (the trajectory first-observation count is recorded as the sensitivity).
CONDITIONS: dict[str, dict[str, object]] = {
    "us101__0750_0805": {
        "window_s": [120.0, 840.0],
        "mainline_flow_veh_h": 8345.0,
        "mainline_flow_source": "trajectory crossings of y=150 m on lanes 1-5, 1669 vehicles in 720 s",
        "onramp_flow_veh_h": 516.0,
        "onramp_flow_source": "official NGSIM input-output on-ramp flow 137 vehicles over 955 s",
        "onramp_flow_sensitivity_veh_h": 690.0,
        "offramp_flow_veh_h": 355.0,
        "offramp_flow_source": "trajectory first observation on the off-ramp lane, 71 vehicles in 720 s",
        "fleet_share": {"passenger": 0.962, "truck": 0.024, "motorcycle": 0.014},
        "fleet_length_m": {"passenger": 4.4196, "truck": 10.009694845360826, "motorcycle": 2.4384},
        "real_target": {"mean_speed_mps": 10.506118382234925, "density_veh_km_lane": 43.54361111111111},
        "initial_state_clock_s": 120.0,
    },
    "us101__0805_0820": {
        "window_s": [180.0, 840.0],
        "mainline_flow_veh_h": 7227.272727272728,
        "mainline_flow_source": "trajectory crossings of y=150 m on lanes 1-5, 1325 vehicles in 660 s",
        "onramp_flow_veh_h": 490.0,
        "onramp_flow_source": "official NGSIM input-output on-ramp flow 130 vehicles over 955 s",
        "onramp_flow_sensitivity_veh_h": 665.4545454545455,
        "offramp_flow_veh_h": 360.0,
        "offramp_flow_source": "trajectory first observation on the off-ramp lane, 66 vehicles in 660 s",
        "fleet_share": {"passenger": 0.973, "truck": 0.022, "motorcycle": 0.005},
        "fleet_length_m": {"passenger": 4.4196, "truck": 10.009694845360826, "motorcycle": 2.4384},
        "real_target": {"mean_speed_mps": 7.915276152134783, "density_veh_km_lane": 50.50545454545454},
        "initial_state_clock_s": 180.0,
    },
}

LOCAL_REGION_M = (150.0, 350.0)
LOCAL_LANES = ("1", "2", "3", "4", "5")


def scene_spec() -> dict[str, object]:
    return json.loads(json.dumps(OBSERVED_GEOMETRY))


def build_scene_network(root: Path) -> dict[str, object]:
    return build_candidate_network(root, scene_spec())


# --------------------------------------------------------------------------
# demand, routes, initial state
# --------------------------------------------------------------------------
def route_edges(route: str) -> list[str]:
    return list(OBSERVED_GEOMETRY["routes"][route])


def _depart_times(flow_veh_h: float, duration_s: float, phase: float) -> np.ndarray:
    if flow_veh_h <= 0:
        return np.zeros(0)
    interval = 3600.0 / flow_veh_h
    times = np.arange(phase * interval, duration_s - 0.05, interval)
    return np.round(np.ceil(times * 10 - 1e-9) / 10.0, 1)


def build_route_file(
    path: Path,
    condition: str,
    *,
    duration_s: float,
    onramp_flow_veh_h: float | None = None,
) -> dict[str, object]:
    spec = CONDITIONS[condition]
    onramp_flow = spec["onramp_flow_veh_h"] if onramp_flow_veh_h is None else onramp_flow_veh_h
    mainline_flow = float(spec["mainline_flow_veh_h"])
    offramp_share = float(spec["offramp_flow_veh_h"]) / mainline_flow
    shares = spec["fleet_share"]
    lengths = spec["fleet_length_m"]
    order = ["passenger", "truck", "motorcycle"]
    cumulative = np.cumsum([shares[kind] for kind in order])
    root = ET.Element("routes")
    for index, kind in enumerate(order):
        ET.SubElement(
            root, "vType",
            dict(id=f"t{index}", vClass="passenger" if kind == "passenger" else ("truck" if kind == "truck" else "motorcycle"),
                 length=str(lengths[kind]), **{k: str(v) for k, v in FIXED_VTYPE.items()}),
        )
    for route in ("through", "entering", "exiting"):
        ET.SubElement(root, "route", dict(id=route, edges=" ".join(route_edges(route))))
    mainline_times = _depart_times(mainline_flow, duration_s, 0.5)
    counts = {kind: 0 for kind in order}
    offramp_count = 0
    pending: list[dict[str, str]] = []
    for index, depart in enumerate(mainline_times):
        u = ((index * 0.6180339887498949) + 0.5) % 1.0
        kind = order[min(int(np.searchsorted(cumulative, u)), len(order) - 1)]
        counts[kind] += 1
        use_offramp = ((index * 0.4142135623730951) % 1.0) < offramp_share
        offramp_count += int(use_offramp)
        pending.append(
            dict(id=f"m{index:05d}", type=f"t{order.index(kind)}", route="exiting" if use_offramp else "through",
                 depart=f"{depart:.1f}", departLane=str(index % 5), departPos="base", departSpeed="max")
        )
    onramp_times = _depart_times(float(onramp_flow), duration_s, 0.5)
    for index, depart in enumerate(onramp_times):
        pending.append(
            dict(id=f"r{index:05d}", type="t0", route="entering", depart=f"{depart:.1f}",
                 departLane="0", departPos="base", departSpeed="max")
        )
    pending.sort(key=lambda spec: float(spec["depart"]))
    for spec_ in pending:
        ET.SubElement(root, "vehicle", spec_)
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return {
        "condition": condition,
        "duration_s": duration_s,
        "mainline_flow_veh_h": mainline_flow,
        "onramp_flow_veh_h": float(onramp_flow),
        "offramp_share_of_mainline": offramp_share,
        "offramp_vehicles": offramp_count,
        "mainline_vehicles": int(len(mainline_times)),
        "onramp_vehicles": int(len(onramp_times)),
        "fleet_counts": counts,
    }


def real_lane_to_sumo(lane_id: str, y_m: float) -> tuple[str, int, float] | None:
    """Map an observed (lane, position) to a SUMO (edge, lane index, position).

    Positions are expressed on the real observed span; ``scale_position`` maps
    them onto the built network's edge length, which differs because netconvert
    extends edges to the junction midpoints.
    """
    if lane_id in LANE_INDEX_MAIN:
        lane = LANE_INDEX_MAIN[lane_id]
        if y_m < MERGE_POSITION_M:
            return "main_0", lane, y_m
        if y_m < DIVERGE_POSITION_M:
            return "main_1", lane + 1, y_m - MERGE_POSITION_M
        return "main_2", lane, y_m - DIVERGE_POSITION_M
    if lane_id == "6":
        if y_m < MERGE_POSITION_M:
            return None
        return "main_1", LANE_INDEX_AUX["6"], y_m - MERGE_POSITION_M
    if lane_id == "7":
        return "onramp", 0, max(0.0, y_m - ONRAMP_OBSERVED_START_M)
    return None


REAL_SPAN_M = {
    "main_0": (0.0, MERGE_POSITION_M),
    "main_1": (MERGE_POSITION_M, DIVERGE_POSITION_M),
    "main_2": (DIVERGE_POSITION_M, SEGMENT_LENGTH_M),
}


def network_edge_lengths(network: Path) -> dict[str, float]:
    tree = ET.parse(str(network))
    lengths: dict[str, float] = {}
    for edge in tree.getroot().findall("edge"):
        identifier = edge.get("id", "")
        if identifier.startswith(":"):
            continue
        lanes = edge.findall("lane")
        if lanes:
            lengths[identifier] = float(lanes[0].get("length"))
    return lengths


def scale_position(edge: str, edge_relative_m: float, lengths: dict[str, float]) -> float:
    if edge not in lengths:
        return edge_relative_m
    if edge in REAL_SPAN_M:
        low, high = REAL_SPAN_M[edge]
        fraction = min(max(edge_relative_m / max(high - low, 1e-9), 0.0), 1.0)
        return fraction * lengths[edge]
    return min(max(edge_relative_m, 0.0), lengths[edge])


def start_edge_routes(route: str, edge: str) -> str:
    """Deprecated helper kept for callers that only need the identifier."""
    return f"from_{edge}_{'entering' if edge == 'onramp' else route}"


def build_initial_state(
    states: pd.DataFrame,
    condition: str,
    *,
    clock_s: float | None = None,
    minimum_spacing_m: float = 1.0,
    edge_lengths: dict[str, float] | None = None,
) -> dict[str, object]:
    """Initial vehicle set taken from the real observed state at one instant."""
    spec = CONDITIONS[condition]
    instant = float(spec["initial_state_clock_s"]) if clock_s is None else clock_s
    frame = states[(states.time_s - instant).abs() < 1e-9]
    if frame.empty:
        observed = states.time_s.unique()
        nearest = observed[np.argmin(np.abs(observed - instant))]
        frame = states[(states.time_s - nearest).abs() < 1e-9]
        instant = float(nearest)
    offramp_trajectories = set(states.loc[states.lane_id == "8", "trajectory_id"].astype(str))
    waterfall = frame.sort_values(["lane_id", "y_m"], ascending=[True, False])
    records: list[dict[str, object]] = []
    dropped: list[dict[str, object]] = []
    occupancy: dict[tuple[str, int], float] = {}
    for row in waterfall.itertuples():
        mapped = real_lane_to_sumo(str(row.lane_id), float(row.y_m))
        if mapped is None:
            dropped.append({"trajectory_id": str(row.trajectory_id), "reason": "outside_observed_geometry"})
            continue
        edge, lane, position = mapped
        position = scale_position(edge, position, edge_lengths or {})
        length = float(spec["fleet_length_m"]["passenger"])
        key = (edge, lane)
        limit = occupancy.get(key)
        if limit is not None and position > limit - (length + FIXED_VTYPE["minGap"] + minimum_spacing_m):
            dropped.append({"trajectory_id": str(row.trajectory_id), "reason": "position_overlap"})
            continue
        occupancy[key] = position
        trajectory = str(row.trajectory_id)
        route = "entering" if str(row.lane_id) == "7" else ("exiting" if trajectory in offramp_trajectories else "through")
        records.append(
            {
                "id": f"i{len(records):04d}",
                "trajectory_id": trajectory,
                "edge": edge,
                "lane_index": lane,
                "position_m": position,
                "speed_mps": float(row.speed_mps),
                "route": route,
                "observed_lane": str(row.lane_id),
                "observed_y_m": float(row.y_m),
            }
        )
    return {
        "status": "Observation",
        "clock_s": instant,
        "observed_states_at_clock": int(len(frame)),
        "accepted": records,
        "dropped": dropped,
        "accepted_count": len(records),
        "dropped_count": len(dropped),
        "minimum_spacing_m": minimum_spacing_m,
        "note": "vehicles that overlap by less than length + minGap + margin in the same SUMO lane are dropped and reported; the injected state is therefore a subset of the observed state, not a resampling of it",
    }


VALID_START_VARIANTS: dict[str, tuple[str, ...]] = {
    "main_0": ("through", "exiting"),
    "main_1": ("through", "exiting"),
    "main_2": ("through",),
    "onramp": ("entering",),
}


def route_chain_from(edge: str, kind: str, route_map: dict[str, object]) -> list[str]:
    base = list(route_map[kind])
    if edge not in base:
        raise sr_error_invalid_chain(edge, kind)
    return base[base.index(edge):]


def sr_error_invalid_chain(edge: str, kind: str) -> ValueError:
    return ValueError(f"no route chain starts on {edge} for kind {kind}")


def write_initial_state_route_file(
    path: Path,
    condition: str,
    initial: dict[str, object],
    *,
    duration_s: float,
    route_map: dict[str, object] | None = None,
) -> dict[str, object]:
    spec = CONDITIONS[condition]
    route_map = route_map or OBSERVED_GEOMETRY["routes"]
    root = ET.Element("routes")
    shares = spec["fleet_share"]
    lengths = spec["fleet_length_m"]
    order = ["passenger", "truck", "motorcycle"]
    for index, kind in enumerate(order):
        ET.SubElement(
            root, "vType",
            dict(id=f"t{index}", vClass="passenger" if kind == "passenger" else ("truck" if kind == "truck" else "motorcycle"),
                 length=str(lengths[kind]), **{k: str(v) for k, v in FIXED_VTYPE.items()}),
        )
    for kind, edges in route_map.items():
        ET.SubElement(root, "route", dict(id=kind, edges=" ".join(edges)))
    start_routes: dict[tuple[str, str], str] = {}
    for edge, kinds in VALID_START_VARIANTS.items():
        for kind in kinds:
            identifier = f"from_{edge}_{kind}"
            chain = route_chain_from(edge, kind, route_map)
            start_routes[(edge, kind)] = identifier
            ET.SubElement(root, "route", dict(id=identifier, edges=" ".join(chain)))
    for record in initial["accepted"]:
        kind = "entering" if record["edge"] == "onramp" else record["route"]
        if (record["edge"], kind) not in start_routes:
            kind = "through"
        ET.SubElement(
            root, "vehicle",
            dict(id=record["id"], type="t0", route=start_routes[(record["edge"], kind)], depart="0.0",
                 departLane=str(record["lane_index"]), departPos=f"{record['position_m']:.2f}",
                 departSpeed=f"{max(record['speed_mps'], 0.1):.2f}"),
        )
    # post-initialisation arrivals continue at the observed boundary demand
    mainline_flow = float(spec["mainline_flow_veh_h"])
    offramp_share = float(spec["offramp_flow_veh_h"]) / mainline_flow
    cumulative = np.cumsum([shares[kind] for kind in order])
    pending: list[dict[str, str]] = []
    for index, depart in enumerate(_depart_times(mainline_flow, duration_s, 0.5)):
        u = ((index * 0.6180339887498949) + 0.5) % 1.0
        kind = order[min(int(np.searchsorted(cumulative, u)), len(order) - 1)]
        use_offramp = ((index * 0.4142135623730951) % 1.0) < offramp_share
        pending.append(
            dict(id=f"m{index:05d}", type=f"t{order.index(kind)}", route="exiting" if use_offramp else "through",
                 depart=f"{depart:.1f}", departLane=str(index % 5), departPos="base", departSpeed="max")
        )
    for index, depart in enumerate(_depart_times(float(spec["onramp_flow_veh_h"]), duration_s, 0.5)):
        pending.append(
            dict(id=f"r{index:05d}", type="t0", route="entering", depart=f"{depart:.1f}",
                 departLane="0", departPos="base", departSpeed="max")
        )
    pending.sort(key=lambda spec_: float(spec_["depart"]))
    for spec_ in pending:
        ET.SubElement(root, "vehicle", spec_)
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return {"initial_vehicles": len(initial["accepted"]), "dropped": len(initial["dropped"])}


def write_sumo_config(
    path: Path,
    *,
    network: Path,
    routes: Path,
    duration_s: float,
    seed: int,
    internal_step_s: float = 0.05,
    fcd_period_s: float = 0.1,
    fcd_path: Path | None = None,
    summary_path: Path | None = None,
) -> Path:
    fcd = fcd_path or path.parent / "fcd.xml"
    summary = summary_path or path.parent / "summary.xml"
    import os as _os
    net_rel = _os.path.relpath(Path(network).resolve(), Path(path).resolve().parent).replace("\\", "/")
    route_rel = _os.path.relpath(Path(routes).resolve(), Path(path).resolve().parent).replace("\\", "/")
    path.write_text(
        "<configuration>"
        f"<input><net-file value=\"{net_rel}\"/><route-files value=\"{route_rel}\"/></input>"
        f"<time><begin value=\"0\"/><end value=\"{duration_s}\"/><step-length value=\"{internal_step_s}\"/></time>"
        "<processing><step-method.ballistic value=\"true\"/><threads value=\"1\"/>"
        "<time-to-teleport value=\"-1\"/><collision.action value=\"warn\"/></processing>"
        f"<output><fcd-output value=\"{fcd.name}\"/><device.fcd.period value=\"{fcd_period_s}\"/>"
        f"<summary-output value=\"{summary.name}\"/></output>"
        f"<seed value=\"{seed}\"/></configuration>",
        encoding="utf-8",
    )
    return path


# --------------------------------------------------------------------------
# execution and measurement
# --------------------------------------------------------------------------
def run_sumo(config: Path, *, wall_limit_s: float = 900.0) -> dict[str, object]:
    started = time.perf_counter()
    process = subprocess.run(
        [_sumo_binary(), "-c", str(config), "--no-step-log", "true", "--duration-log.statistics", "true"],
        capture_output=True, text=True, timeout=wall_limit_s,
    )
    wall = time.perf_counter() - started
    log = process.stdout + process.stderr
    if process.returncode != 0:
        raise Stage05EngineeringError(f"sumo failed: {log[-2000:]}")
    return {"returncode": process.returncode, "wall_s": wall, "log_tail": log[-4000:],
            "teleports": int(log.count("Teleporting")), "collisions": int(log.count("collision"))}


def parse_fcd(path: Path, edge_lengths: dict[str, float] | None = None) -> pd.DataFrame:
    """Parse FCD output and map SUMO edge positions back to real segment metres.

    netconvert extends each edge to the junction midpoints, so the built edge
    length differs from the observed real span. Without the inverse scaling the
    measured region would silently shrink and every density would be biased.
    """
    edge_lengths = edge_lengths or {}
    records: list[tuple[float, str, str, int, float, float]] = []
    current = float("nan")
    for event, element in ET.iterparse(str(path), events=("start", "end")):
        if event == "start" and element.tag == "timestep":
            current = float(element.get("time"))
        elif event == "end" and element.tag == "vehicle":
            lane = element.get("lane", "")
            edge, _, index_text = lane.rpartition("_")
            position = float(element.get("pos"))
            if edge in REAL_SPAN_M and edge in edge_lengths and edge_lengths[edge] > 0:
                low, high = REAL_SPAN_M[edge]
                position = low + position * (high - low) / edge_lengths[edge]
            elif edge == "onramp":
                position = position + ONRAMP_OBSERVED_START_M
            records.append(
                (current, element.get("id"), edge, int(index_text), position, float(element.get("speed")))
            )
            element.clear()
        elif event == "end" and element.tag == "timestep":
            element.clear()
    frame = pd.DataFrame(records, columns=["time_s", "vehicle_id", "edge", "lane_index", "y_m", "speed_mps"])
    frame["lane_id"] = None
    for prefix, width in (("main_0", 5), ("main_1", 6), ("main_2", 5)):
        subset = frame[frame.edge == prefix]
        if subset.empty:
            continue
        lane = subset.lane_index.to_numpy()
        if width == 6:
            real = np.where(lane == 0, "6", pd.Series(6 - lane).astype(str).to_numpy())
        else:
            real = pd.Series(5 - lane).astype(str).to_numpy()
        frame.loc[subset.index, "lane_id"] = real
    frame.loc[frame.edge == "onramp", "lane_id"] = "7"
    frame.loc[frame.edge == "offramp", "lane_id"] = "8"
    return frame.sort_values(["time_s", "vehicle_id"], kind="stable").reset_index(drop=True)


def scene_metrics(
    frame: pd.DataFrame,
    *,
    region_m: tuple[float, float] = LOCAL_REGION_M,
    lanes: tuple[str, ...] = LOCAL_LANES,
    window_s: tuple[float, float],
    block_s: float = 30.0,
) -> dict[str, object]:
    low, high = window_s
    lane_km = (region_m[1] - region_m[0]) / 1000.0 * len(lanes)
    subset = frame[
        frame.lane_id.isin(lanes) & frame.y_m.ge(region_m[0]) & frame.y_m.lt(region_m[1])
        & frame.time_s.between(low, high, inclusive="left")
    ]
    vehicle_s = len(subset) / 10.0
    density = vehicle_s / (high - low) / lane_km if high > low else float("nan")
    speed = float(subset.speed_mps.mean()) if len(subset) else float("nan")
    blocks = []
    if len(subset):
        block_index = ((subset.time_s - low) // block_s).astype(int)
        for index, part in subset.groupby(block_index):
            blocks.append(
                {
                    "block_start_s": float(low + index * block_s),
                    "speed_mean_mps": float(part.speed_mps.mean()),
                    "density_veh_km_lane": len(part) / 10.0 / block_s / lane_km,
                    "low_speed_share": float((part.speed_mps < 5.0).mean()),
                    "vehicles": int(part.vehicle_id.nunique()),
                }
            )
    return {
        "status": "Observation",
        "window_s": list(window_s),
        "region_m": list(region_m),
        "lanes": list(lanes),
        "lane_km": lane_km,
        "local_vehicle_s": vehicle_s,
        "speed_mean_mps": speed,
        "density_veh_km_lane": density,
        "flow_veh_h_lane_consistency": density * speed * 3.6,
        "low_speed_share": float((subset.speed_mps < 5.0).mean()) if len(subset) else float("nan"),
        "speed_quantiles_mps": [float(x) for x in subset.speed_mps.quantile([0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0])] if len(subset) else [],
        "blocks": blocks,
    }


def state_support(metrics: dict[str, object], condition: str) -> dict[str, object]:
    target = CONDITIONS[condition]["real_target"]
    blocks = metrics["blocks"]
    speed_envelope = (
        [min(block["speed_mean_mps"] for block in blocks), max(block["speed_mean_mps"] for block in blocks)]
        if blocks else None
    )
    density_envelope = (
        [min(block["density_veh_km_lane"] for block in blocks), max(block["density_veh_km_lane"] for block in blocks)]
        if blocks else None
    )
    inside_speed = bool(speed_envelope and speed_envelope[0] <= target["mean_speed_mps"] <= speed_envelope[1])
    inside_density = bool(density_envelope and density_envelope[0] <= target["density_veh_km_lane"] <= density_envelope[1])
    return {
        "condition": condition,
        "real_target": target,
        "simulated_mean_speed_mps": metrics["speed_mean_mps"],
        "simulated_density_veh_km_lane": metrics["density_veh_km_lane"],
        "predeclared_block_speed_envelope": speed_envelope,
        "predeclared_block_density_envelope": density_envelope,
        "target_speed_inside_block_envelope": inside_speed,
        "target_density_inside_block_envelope": inside_density,
        "state_supported": bool(inside_speed and inside_density),
        "rule": "each real target mean speed and density must lie inside the envelope of the predeclared 30 s evaluation blocks of the simulated run; a necessary state-support check only, not a science tolerance and not an equivalence test",
        "not_a_science_tolerance": True,
    }


def build_scene_capsule(root: Path) -> dict[str, object]:
    network = build_scene_network(root / "network")
    return {"network": network["network"], "spec": scene_spec()}
