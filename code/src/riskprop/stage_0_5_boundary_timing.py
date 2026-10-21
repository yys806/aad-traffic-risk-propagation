"""Real boundary arrival timing and relative-speed anomaly diagnostics.

AAD-0.5-ARRIVAL-TIMING (result ``RES-STAGE-0.5-ARRIVAL-TIMING-V1``).

Two responsibilities:

1. Reconstruct the *real* boundary arrival sequence of the two approved
   calibration windows and pair it with an arrival-timing-only control arm, so
   that the effect of arrival structure can be tested with everything else held
   identical (network, supply, behaviour, initial state, vehicle identity,
   route, type, lane, number of events).
2. Replace the inherited absolute 10 m/s slow-cell descriptor with a
   density-conditioned relative-speed anomaly diagnostic whose threshold comes
   from the real block residuals themselves, and characterise whether anomalous
   cells form space-time structures that propagate upstream.

Boundaries of this module
-------------------------
* Read-only with respect to Stage 0.2 semantics: no identity, clock, quality or
  P2 definition is touched.
* Only the two approved calibration windows are read.  The validation window and
  the locked holdout are refused by construction.
* Every quantity is tagged Observation / Derived / Hypothesis / Unidentifiable.
"""
from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

from . import stage_0_5_state_support as ss

VERSION = "stage-0.5-boundary-timing-v1"

#: Declared entry planes.  A real mainline vehicle counts as an *entry event* when
#: its first observation is inside the reliably covered upstream strip; the value
#: is declared once here and used identically for both windows.
ENTRY_Y_MAX_M = 30.0
#: An on-ramp vehicle is an entry event when its first observation is on the
#: observed on-ramp lane, which is a separate facility with its own coverage.
ONRAMP_LANE = "7"
OFFRAMP_LANE = "8"

#: Space-time cell geometry for the anomaly diagnostic.
CELL_Y_M = 50.0
CELL_T_S = 30.0
CELL_MIN_OBS = 50
#: Declared geometry of the wave diagnostic.  The definition was fixed on the real
#: calibration windows only: at 30 s blocks the independent propagation estimate
#: cannot resolve the lag (every pair peaks at lag 0), while at 10 s blocks both
#: real windows give a concordant upstream front near -5 m/s.  No simulated outcome
#: of this task was inspected when this value was chosen.
WAVE_Y_M = 50.0
WAVE_T_S = 10.0
WAVE_MIN_OBS = 30
WAVE_ALPHA = 0.15
WAVE_SENSITIVITY = {"t_step_s": (10.0, 15.0), "alpha": (0.10, 0.15, 0.20)}
#: Corroboration and null-significance requirements for a propagating structure.
XCORR_MIN_PAIRS = 6
XCORR_MIN_UPSTREAM_SHARE = 0.5
NULL_MAX_EXCEEDANCE = 0.05
#: Density band width and residual tail used to call a cell anomalous.
BASELINE_BAND_VEH_KM_LANE = 7.5
ANOMALY_ALPHA = 0.10
#: Declared relative-speed anomaly definitions.  ``density_conditioned`` follows the
#: task book's suggestion (cell speed minus the real density-conditioned median);
#: ``temporal_position`` removes both the static longitudinal profile and the
#: density effect by comparing a cell with the same position's own distribution
#: inside the same frame, so no absolute speed threshold is involved.
ANOMALY_DEFINITIONS = ("density_conditioned", "temporal_position")
#: Declared quantile for the temporal-position definition and the sensitivity grid
#: over which the structural verdict must be invariant.
TEMPORAL_ALPHA = 0.15
TEMPORAL_ALPHA_SENSITIVITY = (0.10, 0.15, 0.20, 0.25)
#: Maximum cross-correlation lag searched between adjacent longitudinal positions.
MAX_LAG_BLOCKS = 5
#: Permutation null for spatial structure.
NULL_RESAMPLES = 1000
NULL_SEED = 20261231

CALIBRATION_WINDOWS = tuple(ss.CALIBRATION_WINDOWS)


class BoundaryTimingError(ValueError):
    """Fail-closed error for schema, isolation or plan violations."""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------------------
# 1. real boundary arrival reconstruction
# --------------------------------------------------------------------------
def entry_events(states: pd.DataFrame, condition: str, *,
                 duration_s: float = ss.DECLARED_DURATION_S,
                 entry_y_max_m: float = ENTRY_Y_MAX_M) -> dict[str, object]:
    """Reconstruct the real boundary arrival sequence of one approved window.

    Inclusion rules (declared before any simulator run):

    * the vehicle's *first* canonical observation inside the approved window span
      defines its boundary event; the event time is that observation time and the
      event position is that observation position;
    * a mainline event requires the first observation to be on lanes 1-5 and at
      ``y <= entry_y_max_m`` (the reliably covered upstream strip);
    * an on-ramp event requires the first observation to be on the observed
      on-ramp lane;
    * vehicles whose first observation is exactly at the window start belong to
      the injected initial state and are **not** entry events (this is the
      double-counting guard);
    * events later than the declared simulation horizon are excluded.

    Every excluded vehicle is recorded with its reason.
    """
    if condition not in ss.CALIBRATION_WINDOWS:
        raise BoundaryTimingError(f"unapproved_window:{condition}")
    window_start, window_end = ss.APPROVED_SPANS[condition]
    frame = states.copy()
    frame["lane_id"] = frame.lane_id.astype(str)
    frame = frame[frame.time_s.ge(window_start) & frame.time_s.lt(window_end)]
    ordered = frame.sort_values(["trajectory_id", "time_s"], kind="stable")
    first = ordered.groupby("trajectory_id", sort=False).first().reset_index()
    ever_offramp = set(frame.loc[frame.lane_id == OFFRAMP_LANE, "trajectory_id"].astype(str))
    initial_ids = set(first.loc[first.time_s.le(window_start + 1e-9), "trajectory_id"].astype(str))

    events: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    for row in first.itertuples():
        trajectory = str(row.trajectory_id)
        lane = str(row.lane_id)
        sim_time = float(row.time_s) - float(window_start)
        reason = ""
        stream = ""
        if trajectory in initial_ids:
            reason = "initial_state_vehicle"
        elif lane in ss.MAINLINE_LANES:
            if float(row.y_m) > float(entry_y_max_m):
                reason = "first_observation_downstream_of_entry"
            else:
                stream = "mainline"
        elif lane == ONRAMP_LANE:
            stream = "onramp"
        else:
            reason = "first_observation_not_at_boundary"
        if not reason and sim_time >= duration_s:
            reason = "beyond_simulation_horizon"
        if reason:
            excluded.append({"trajectory_id": trajectory, "reason": reason,
                             "lane_id": lane, "y_m": float(row.y_m), "time_s": float(row.time_s)})
            continue
        events.append({
            "event_id": f"{condition}::{stream}::{len(events):05d}",
            "window_id": condition,
            "stream": stream,
            "trajectory_id": trajectory,
            "real_time_s": float(row.time_s),
            "sim_time_s": sim_time,
            "observed_lane_id": lane,
            "observed_y_first_m": float(row.y_m),
            "observed_speed_first_mps": float(row.speed_mps),
            "route": ("entering" if stream == "onramp"
                      else ("exiting" if trajectory in ever_offramp else "through")),
        })
    events.sort(key=lambda item: (item["sim_time_s"], item["event_id"]))
    return {
        "status": "Observation",
        "condition": condition,
        "window_s": [float(window_start), float(window_end)],
        "duration_s": float(duration_s),
        "entry_y_max_m": float(entry_y_max_m),
        "trajectories_in_window": int(len(first)),
        "initial_state_vehicles": int(len(initial_ids)),
        "events": events,
        "excluded": excluded,
        "event_counts": {
            "mainline": int(sum(1 for item in events if item["stream"] == "mainline")),
            "onramp": int(sum(1 for item in events if item["stream"] == "onramp")),
            "total": int(len(events)),
        },
        "exclusion_reasons": pd.Series([item["reason"] for item in excluded]).value_counts().to_dict()
        if excluded else {},
        "basis": (
            "first canonical observation inside the approved window span; mainline events must "
            "sit on lanes 1-5 with y <= entry_y_max_m, on-ramp events on the observed on-ramp lane; "
            "the injected initial-state vehicles are excluded by construction"
        ),
    }


def uniform_arrivals(count: int, duration_s: float) -> np.ndarray:
    """Candidate uniformisation rule declared in the task book: t_i = (i+0.5)T/N."""
    if count <= 0:
        return np.zeros(0)
    if not np.isfinite(duration_s) or duration_s <= 0:
        raise BoundaryTimingError("invalid_duration")
    index = np.arange(count, dtype=float)
    return (index + 0.5) * float(duration_s) / float(count)


def paired_arrival_tables(events: list[dict[str, object]], *,
                          duration_s: float = ss.DECLARED_DURATION_S) -> dict[str, pd.DataFrame]:
    """Build the E and U arms: identical item-by-item, arrival times are the only difference.

    The uniform arm assigns the i-th uniform slot of a stream to the i-th earliest
    real arrival of the *same* stream, so the pairing is order preserving and the
    per-stream event counts are identical by construction.
    """
    frame = pd.DataFrame(events)
    if frame.empty:
        raise BoundaryTimingError("empty_event_table")
    frame = frame.sort_values(["stream", "sim_time_s", "event_id"], kind="stable").reset_index(drop=True)
    uniform = np.empty(len(frame), dtype=float)
    for stream, group in frame.groupby("stream", sort=False):
        uniform[group.index.to_numpy()] = uniform_arrivals(len(group), duration_s)
    frame["arrival_time_s"] = frame.sim_time_s.astype(float)
    frame["arm_E_time_s"] = frame.sim_time_s.astype(float)
    frame["arm_U_time_s"] = uniform
    frame["arm_E_order"] = np.arange(len(frame))
    frame["arm_U_order"] = frame.groupby("stream", sort=False).cumcount()
    return {"events": frame}


def arrival_summary(table: pd.DataFrame) -> dict[str, object]:
    """Per-stream arrival counts, rates and inter-arrival structure for one table."""
    result: dict[str, object] = {"status": "Observation", "streams": {}}
    time_column = "arrival_time_s" if "arrival_time_s" in table.columns else "sim_time_s"
    for stream, group in table.groupby("stream", sort=True):
        times = np.sort(group[time_column].to_numpy(float))
        gaps = np.diff(times)
        result["streams"][stream] = {
            "events": int(len(times)),
            "first_s": float(times.min()) if len(times) else None,
            "last_s": float(times.max()) if len(times) else None,
            "rate_veh_h": float(len(times) / 420.0 * 3600.0 / 1.0) if len(times) else None,
            "gap_mean_s": float(gaps.mean()) if len(gaps) else None,
            "gap_sd_s": float(gaps.std(ddof=1)) if len(gaps) > 1 else None,
            "gap_p05_s": float(np.quantile(gaps, 0.05)) if len(gaps) else None,
            "gap_p50_s": float(np.quantile(gaps, 0.50)) if len(gaps) else None,
            "gap_p95_s": float(np.quantile(gaps, 0.95)) if len(gaps) else None,
            "gap_max_s": float(gaps.max()) if len(gaps) else None,
            "gap_zero_share": float((gaps <= 1e-9).mean()) if len(gaps) else None,
            "gap_cv": float(gaps.std(ddof=1) / gaps.mean()) if len(gaps) > 1 and gaps.mean() > 0 else None,
            "routes": group.route.value_counts().to_dict(),
            "lanes": group.observed_lane_id.value_counts().to_dict(),
        }
    # burstiness over a declared 30 s aggregation
    for stream, group in table.groupby("stream", sort=True):
        times = group[time_column].to_numpy(float)
        blocks = np.floor(times / CELL_T_S).astype(int)
        counts = pd.Series(blocks).value_counts().reindex(range(int(420 // CELL_T_S)), fill_value=0)
        result["streams"][stream]["max_30s_count"] = int(counts.max())
        result["streams"][stream]["min_30s_count"] = int(counts.min())
        result["streams"][stream]["count_30s_cv"] = (float(counts.std(ddof=1) / counts.mean())
                                                     if counts.mean() > 0 else None)
    return result


def arrival_difference(table: pd.DataFrame) -> pd.DataFrame:
    """Per-event declared-vs-real time offset of the uniformised arm (audit table)."""
    frame = table.copy()
    frame["uniform_minus_real_s"] = frame.arm_U_time_s - frame.arm_E_time_s
    return frame


# --------------------------------------------------------------------------
# 2. route files with an exact arrival list
# --------------------------------------------------------------------------
def event_lane_index(event: dict[str, object]) -> int:
    """SUMO departure lane index for one event."""
    lane = str(event["observed_lane_id"])
    if lane in ss.MAINLINE_LANES:
        from .stage_0_5_scene_reconstruction import LANE_INDEX_MAIN
        return int(LANE_INDEX_MAIN[lane])
    if lane == ONRAMP_LANE:
        return 0
    raise BoundaryTimingError(f"event_lane_not_at_boundary:{lane}")


def write_arrival_route_file(path: Path, condition: str, behaviour: str,
                             types: list[dict[str, object]], table: pd.DataFrame, *,
                             time_column: str, initial_records: list[dict[str, object]] | None = None,
                             duration_s: float = ss.DECLARED_DURATION_S,
                             edge_speed_limits: dict[str, float] | None = None,
                             edge_lane_counts: dict[str, int] | None = None) -> dict[str, object]:
    """Write a route file whose *new* vehicles are exactly the given arrival table.

    The initial state is injected first, then one ``<vehicle>`` element per event
    with an explicit departure time, lane and speed.  Both arms call this function
    with the same table apart from ``time_column``.
    """
    import numpy as np  # local import keeps the module import surface small
    spec = ss.observed_geometry_spec(ss.FREE_SPEED_MPS)
    routes = spec["routes"]
    root = ET.Element("routes")
    for entry in types:
        ET.SubElement(root, "vType", dict(
            id=entry["id"], vClass=entry["vClass"], length=str(entry["length_m"]),
            tau=str(entry["tau"]), sigma=str(entry["sigma"]),
            **{k: str(v) for k, v in ss.FIXED_VTYPE_FIELDS.items()}))
    for route, edges in routes.items():
        ET.SubElement(root, "route", dict(id=route, edges=" ".join(edges)))
    start_routes: dict[tuple[str, str], str] = {}
    valid_start = {"main_0": ("through", "exiting"), "main_1": ("through", "exiting"),
                   "main_2": ("through",), "onramp": ("entering",)}
    for edge, kinds in valid_start.items():
        for kind in kinds:
            chain = list(routes[kind])
            if edge not in chain:
                raise BoundaryTimingError(f"invalid_start_chain:{edge}:{kind}")
            identifier = f"from_{edge}_{kind}"
            start_routes[(edge, kind)] = identifier
            ET.SubElement(root, "route", dict(id=identifier,
                                              edges=" ".join(chain[chain.index(edge):])))
    class_ids = [entry["id"] for entry in types]
    limits = dict(edge_speed_limits or {})
    counts = dict(edge_lane_counts or {})
    injected = 0
    for record in (initial_records or []):
        kind = "entering" if record["edge"] == "onramp" else str(record["route"])
        if (record["edge"], kind) not in start_routes:
            kind = "through"
        class_index = min(int(ss._quasi_rank(str(record["trajectory_id"])) * len(class_ids)),
                          len(class_ids) - 1)
        speed = max(float(record["speed_mps"]), 0.1)
        allowed = float(limits.get(str(record["edge"]), speed))
        speed = min(speed, allowed)
        lane_index = int(record["lane_index"])
        lane_index = min(lane_index, int(counts.get(str(record["edge"]), lane_index + 1)) - 1)
        ET.SubElement(root, "vehicle", dict(
            id=f"i{injected:04d}_{record['id']}", type=class_ids[class_index],
            route=start_routes[(record["edge"], kind)], depart="0.0",
            departLane=str(lane_index), departPos=f"{float(record['position_m']):.2f}",
            departSpeed=f"{speed:.2f}"))
        injected += 1
    written = 0
    written_ids: list[dict[str, object]] = []
    for event in table.sort_values(time_column, kind="stable").itertuples():
        route = str(event.route)
        lane_index = event_lane_index(dict(observed_lane_id=event.observed_lane_id))
        class_index = min(int(ss._quasi_rank(str(event.trajectory_id)) * len(class_ids)),
                          len(class_ids) - 1)
        speed = max(float(event.observed_speed_first_mps), 0.1)
        edge = "onramp" if route == "entering" else "main_0"
        allowed = float(limits.get(edge, speed))
        speed = min(speed, allowed)
        vehicle_id = f"e{written:05d}_{event.event_id.split('::')[-1]}"
        depart = float(getattr(event, time_column))
        ET.SubElement(root, "vehicle", dict(
            id=vehicle_id, type=class_ids[class_index], route=route,
            depart=f"{depart:.2f}", departLane=str(lane_index),
            departPos="base", departSpeed=f"{speed:.2f}"))
        written_ids.append({"vehicle_id": vehicle_id, "event_id": str(event.event_id),
                            "stream": str(event.stream), "declared_depart_s": depart,
                            "declared_lane": str(event.observed_lane_id),
                            "declared_speed_mps": speed})
        written += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return {"initial_vehicles": injected, "event_vehicles": written,
            "vtype_ids": class_ids, "time_column": time_column,
            "event_vehicle_ids": written_ids}


# --------------------------------------------------------------------------
# 3. density-conditioned relative-speed anomaly diagnostic
# --------------------------------------------------------------------------
def space_time_cells(frame: pd.DataFrame, *, window: tuple[float, float],
                     lanes: tuple[str, ...] = ss.MAINLINE_LANES,
                     y_step_m: float = CELL_Y_M, t_step_s: float = CELL_T_S,
                     y_max_m: float | None = None, min_obs: int = CELL_MIN_OBS) -> pd.DataFrame:
    """Non-overlapping (y, t) cells with density, mean speed and observation count.

    Density uses 0.1 s state rows over the cell's time width and the cell's lane
    count, exactly as the project's existing block descriptors do.
    """
    low, high = window
    frame = frame.copy()
    frame["lane_id"] = frame.lane_id.astype(str)
    subset = frame[frame.lane_id.isin(lanes) & frame.time_s.ge(low) & frame.time_s.lt(high)]
    if y_max_m is not None:
        subset = subset[subset.y_m.lt(y_max_m)]
    if subset.empty:
        return pd.DataFrame(columns=["t_block", "y_block", "t_start_s", "y_start_m",
                                     "obs", "speed_mps", "density_veh_km_lane"])
    subset = subset.assign(
        t_block=np.floor((subset.time_s - low) / t_step_s).astype(int),
        y_block=np.floor(subset.y_m / y_step_m).astype(int),
    )
    rows: list[dict[str, object]] = []
    for (t_block, y_block), part in subset.groupby(["t_block", "y_block"], sort=True):
        if len(part) < min_obs:
            continue
        vehicle_s = len(part) * 0.1
        rows.append({
            "t_block": int(t_block),
            "y_block": int(y_block),
            "t_start_s": float(low + t_block * t_step_s),
            "y_start_m": float(y_block * y_step_m),
            "obs": int(len(part)),
            "speed_mps": float(part.speed_mps.mean()),
            "density_veh_km_lane": vehicle_s / t_step_s / (y_step_m / 1000.0 * len(lanes)),
        })
    return pd.DataFrame(rows)


def density_speed_baseline(cells: pd.DataFrame, *,
                           band_veh_km_lane: float = BASELINE_BAND_VEH_KM_LANE) -> dict[str, object]:
    """Density-conditioned baseline speed, taken from the real cells only."""
    if cells.empty:
        raise BoundaryTimingError("empty_cells_for_baseline")
    centres: list[float] = []
    medians: list[float] = []
    counts: list[int] = []
    unique = np.unique(cells.density_veh_km_lane.round(6).to_numpy(float))
    for centre in np.unique(np.round(unique / band_veh_km_lane) * band_veh_km_lane):
        select = np.abs(cells.density_veh_km_lane.to_numpy(float) - centre) <= band_veh_km_lane
        if int(select.sum()) < 5:
            continue
        centres.append(float(centre))
        medians.append(float(np.median(cells.speed_mps.to_numpy(float)[select])))
        counts.append(int(select.sum()))
    if not centres:
        raise BoundaryTimingError("empty_baseline_bands")
    return {"status": "Observation", "band_veh_km_lane": float(band_veh_km_lane),
            "centres_veh_km_lane": centres, "median_speed_mps": medians, "cell_counts": counts,
            "density_min_veh_km_lane": float(min(centres)), "density_max_veh_km_lane": float(max(centres))}


def speed_residuals(cells: pd.DataFrame, baseline: dict[str, object]) -> np.ndarray:
    """Observed cell speed minus the real density-conditioned median speed."""
    reference = np.interp(cells.density_veh_km_lane.to_numpy(float),
                          baseline["centres_veh_km_lane"], baseline["median_speed_mps"])
    return cells.speed_mps.to_numpy(float) - reference


def anomaly_threshold(real_cells: pd.DataFrame, baseline: dict[str, object],
                      alpha: float = ANOMALY_ALPHA) -> float:
    """Declared low tail of the real residual distribution."""
    return float(np.quantile(speed_residuals(real_cells, baseline), alpha))


def anomalous_cells(cells: pd.DataFrame, baseline: dict[str, object],
                    threshold: float) -> pd.DataFrame:
    frame = cells.copy()
    frame["residual_mps"] = speed_residuals(cells, baseline)
    frame["anomalous"] = frame.residual_mps <= threshold
    return frame


def _components(mask: np.ndarray, connectivity: int = 8) -> list[list[tuple[int, int]]]:
    """Connected anomalous components in the (position, time) grid.

    Connectivity is 8-neighbour by declaration: a wave front that advances one
    position per time step is a diagonal chain, and a 4-neighbour rule would cut it
    into per-position segments.  The same connectivity is used for the realised mask
    and for every permutation null, so the null comparison is unaffected.
    """
    rows, columns = mask.shape
    offsets = ((1, 0), (-1, 0), (0, 1), (0, -1))
    if connectivity == 8:
        offsets = offsets + ((1, 1), (1, -1), (-1, 1), (-1, -1))
    visited = np.zeros_like(mask, dtype=bool)
    out: list[list[tuple[int, int]]] = []
    for row in range(rows):
        for column in range(columns):
            if not mask[row, column] or visited[row, column]:
                continue
            stack = [(row, column)]
            visited[row, column] = True
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_column = stack.pop()
                cells.append((current_row, current_column))
                for delta_row, delta_column in offsets:
                    next_row, next_column = current_row + delta_row, current_column + delta_column
                    if (0 <= next_row < rows and 0 <= next_column < columns
                            and mask[next_row, next_column] and not visited[next_row, next_column]):
                        visited[next_row, next_column] = True
                        stack.append((next_row, next_column))
            out.append(cells)
    return out


def _mask_grid(cells: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y_blocks = np.sort(cells.y_block.unique())
    t_blocks = np.sort(cells.t_block.unique())
    grid = np.zeros((len(y_blocks), len(t_blocks)), dtype=bool)
    y_index = {value: index for index, value in enumerate(y_blocks)}
    t_index = {value: index for index, value in enumerate(t_blocks)}
    for row in cells.itertuples():
        if row.anomalous:
            grid[y_index[row.y_block], t_index[row.t_block]] = True
    return grid, y_blocks, t_blocks


def wave_structure(anomalous: pd.DataFrame, *, t_step_s: float = CELL_T_S,
                   y_step_m: float = CELL_Y_M, min_component_cells: int = 2,
                   min_time_blocks_for_slope: int = 3) -> dict[str, object]:
    """Classify the space-time structure of anomalous cells.

    Returns one of three declared levels:

    * ``no_structure`` - no component reaches ``min_component_cells``;
    * ``local_anomaly_no_propagation`` - components exist but none spans
      ``min_time_blocks_for_slope`` time blocks, so no front can be tracked;
    * ``propagating_structure`` - at least one component spans enough time blocks
      for a front slope to be estimated; the slope sign then gives the direction
      (upstream when the front moves towards smaller y).
    """
    empty = {"status": "Observation", "level": "no_structure", "components": [],
             "largest_component_cells": 0, "front_slope_mps": None,
             "front_direction": None, "anomalous_cells": 0, "cells_total": int(len(anomalous))}
    if anomalous.empty or not anomalous["anomalous"].any():
        return empty
    grid, y_blocks, t_blocks = _mask_grid(anomalous)
    raw = _components(grid)
    components: list[dict[str, object]] = []
    for cells in raw:
        if len(cells) < min_component_cells:
            continue
        times = sorted({column for _, column in cells})
        front: list[tuple[float, float]] = []
        for column in times:
            rows = [row for row, candidate in cells if candidate == column]
            # the front is the centroid of the component at that time block, which is
            # robust to a few extra cells elsewhere in the same component
            front.append((float(t_blocks[column] * t_step_s),
                          float(y_blocks[rows].mean() * y_step_m)))
        slope = None
        if len(front) >= min_time_blocks_for_slope and len({round(item[1], 6) for item in front}) > 1:
            time_values = np.array([item[0] for item in front], dtype=float)
            position_values = np.array([item[1] for item in front], dtype=float)
            slope = float(np.polyfit(time_values, position_values, 1)[0])
        components.append({
            "cells": int(len(cells)),
            "time_blocks": int(len(times)),
            "first_time_s": float(t_blocks[times[0]] * t_step_s),
            "last_time_s": float(t_blocks[times[-1]] * t_step_s),
            "y_min_m": float(y_blocks[min(row for row, _ in cells)] * y_step_m),
            "y_max_m": float(y_blocks[max(row for row, _ in cells)] * y_step_m),
            "front_slope_mps": slope,
            "front_direction": None if slope is None else ("upstream" if slope < 0 else "downstream"),
        })
    components.sort(key=lambda item: (-item["cells"], item["first_time_s"]))
    largest = components[0] if components else None
    if not components:
        level = "no_structure"
    elif largest["front_slope_mps"] is None:
        level = "local_anomaly_no_propagation"
    else:
        level = "propagating_structure"
    return {
        "status": "Observation",
        "level": level,
        "components": components[:20],
        "largest_component_cells": int(largest["cells"]) if largest else 0,
        "front_slope_mps": largest["front_slope_mps"] if largest else None,
        "front_direction": largest["front_direction"] if largest else None,
        "upstream_component_count": int(sum(1 for item in components
                                            if item["front_direction"] == "upstream")),
        "anomalous_cells": int(anomalous["anomalous"].sum()),
        "cells_total": int(len(anomalous)),
        "declared_levels": ["no_structure", "local_anomaly_no_propagation",
                            "propagating_structure"],
    }


def temporal_position_anomaly(cells: pd.DataFrame, *, alpha: float = TEMPORAL_ALPHA) -> pd.DataFrame:
    """Scale-free relative-speed anomaly: a temporal slowdown at a fixed position.

    A cell is anomalous when its mean speed is at or below the ``alpha`` quantile
    of the cell speeds observed at the *same longitudinal position* inside the
    same frame.  No absolute speed threshold, no corridor-average reference and no
    externally supplied free-flow speed is used, so the rule is applicable to a
    congested frame whose mean speed sits near any candidate absolute threshold.
    """
    if cells.empty:
        raise BoundaryTimingError("empty_cells")
    frame = cells.copy()
    threshold = frame.groupby("y_block")["speed_mps"].transform(
        lambda series: series.quantile(alpha))
    frame["position_threshold_mps"] = threshold.astype(float)
    frame["anomalous"] = frame.speed_mps <= frame.position_threshold_mps
    return frame


def anomaly_table(cells: pd.DataFrame, baseline: dict[str, object], threshold: float,
                  definition: str = "temporal_position",
                  alpha: float = TEMPORAL_ALPHA) -> pd.DataFrame:
    """Anomaly table for one declared definition."""
    if definition == "density_conditioned":
        return anomalous_cells(cells, baseline, threshold)
    if definition == "temporal_position":
        return temporal_position_anomaly(cells, alpha=alpha)
    raise BoundaryTimingError(f"unknown_anomaly_definition:{definition}")


def cross_correlation_propagation(cells: pd.DataFrame, *, max_lag_blocks: int = MAX_LAG_BLOCKS,
                                  t_step_s: float = CELL_T_S,
                                  y_step_m: float = CELL_Y_M) -> dict[str, object]:
    """Independent propagation estimator from adjacent-position speed cross-correlation.

    For each pair of adjacent longitudinal positions the lag maximising the
    correlation of the two de-meaned speed series is found.  A positive lag means
    the upstream position reproduces the downstream position's pattern later, i.e.
    the pattern travelled upstream.  The implied speed is ``-dy / (lag * dt)``.
    """
    if cells.empty:
        raise BoundaryTimingError("empty_cells")
    pivoted = cells.pivot_table(index="t_block", columns="y_block", values="speed_mps")
    pivoted = pivoted.sort_index()
    pairs: list[dict[str, object]] = []
    for left, right in zip(pivoted.columns[:-1], pivoted.columns[1:]):
        upstream = pivoted[left]
        downstream = pivoted[right]
        common = upstream.notna() & downstream.notna()
        if int(common.sum()) < 6:
            continue
        a = upstream[common].to_numpy(float)
        b = downstream[common].to_numpy(float)
        a = a - a.mean()
        b = b - b.mean()
        if not np.isfinite(a).all() or not np.isfinite(b).all() or a.std() == 0 or b.std() == 0:
            continue
        best_lag, best_correlation = 0, -np.inf
        for lag in range(-max_lag_blocks, max_lag_blocks + 1):
            if lag >= 0:
                x, y = a[lag:], b[:len(b) - lag] if lag else b
            else:
                x, y = a[:lag], b[-lag:]
            if len(x) < 4:
                continue
            correlation = float(np.corrcoef(x, y)[0, 1])
            if np.isfinite(correlation) and correlation > best_correlation:
                best_lag, best_correlation = lag, correlation
        if not np.isfinite(best_correlation):
            continue
        pairs.append({
            "upstream_y_block": int(left),
            "downstream_y_block": int(right),
            "best_lag_blocks": int(best_lag),
            "best_correlation": float(best_correlation),
            "implied_speed_mps": float(-y_step_m / (best_lag * t_step_s)) if best_lag else None,
            "direction": ("upstream" if best_lag > 0 else
                          "downstream" if best_lag < 0 else "stationary"),
        })
    speeds = [item["implied_speed_mps"] for item in pairs if item["implied_speed_mps"] is not None]
    return {
        "status": "Observation",
        "pairs": len(pairs),
        "lag_mean_blocks": float(np.mean([item["best_lag_blocks"] for item in pairs])) if pairs else None,
        "upstream_share": (float(np.mean([item["direction"] == "upstream" for item in pairs]))
                           if pairs else None),
        "median_implied_speed_mps": float(np.median(speeds)) if speeds else None,
        "detail": pairs,
    }


def permutation_null(anomalous: pd.DataFrame, *, resamples: int = NULL_RESAMPLES,
                     seed: int = NULL_SEED, min_component_cells: int = 2,
                     axis: str = "time_within_position") -> dict[str, object]:
    """Space-time permutation null for the largest anomalous component.

    ``axis='time_within_position'`` permutes a row's anomalous cells across time,
    which preserves how often each position is anomalous and destroys the
    space-time arrangement that a propagating structure requires.  That is the
    matching null for the temporal-position definition.  ``axis='position_within_time'``
    is the matching null for the density-conditioned definition.
    """
    if anomalous.empty or not anomalous["anomalous"].any():
        return {"status": "Derived", "resamples": 0, "observed_largest_cells": 0,
                "null_mean_largest_cells": None, "exceedance_rate": None, "axis": axis}
    grid, _, _ = _mask_grid(anomalous)
    observed = max((len(part) for part in _components(grid)), default=0)
    if axis not in ("time_within_position", "position_within_time"):
        raise BoundaryTimingError(f"unknown_null_axis:{axis}")
    generator = np.random.default_rng(seed)
    null_sizes: list[int] = []
    for _ in range(int(resamples)):
        shuffled = np.zeros_like(grid)
        if axis == "time_within_position":
            for row in range(grid.shape[0]):
                count = int(grid[row, :].sum())
                if count == 0:
                    continue
                columns = generator.choice(grid.shape[1], size=count, replace=False)
                shuffled[row, columns] = True
        else:
            for column in range(grid.shape[1]):
                count = int(grid[:, column].sum())
                if count == 0:
                    continue
                rows = generator.choice(grid.shape[0], size=count, replace=False)
                shuffled[rows, column] = True
        null_sizes.append(max((len(part) for part in _components(shuffled)), default=0))
    null_array = np.array(null_sizes, dtype=float)
    return {
        "status": "Derived",
        "resamples": int(resamples),
        "seed": int(seed),
        "axis": axis,
        "observed_largest_cells": int(observed),
        "null_mean_largest_cells": float(null_array.mean()),
        "null_p95_largest_cells": float(np.quantile(null_array, 0.95)),
        "exceedance_rate": float((null_array >= observed).mean()),
        "min_component_cells": int(min_component_cells),
    }


def synthetic_wave_scenarios(*, n_time: int = 30, n_y: int = 12,
                             t_step_s: float = WAVE_T_S, y_step_m: float = WAVE_Y_M
                             ) -> dict[str, pd.DataFrame]:
    """Deterministic constructed cells used to verify the diagnostic's discrimination.

    Every scenario shares the same baseline field and differs only in how a
    low-speed band is placed in space and time:

    ``upstream``      the band starts downstream and moves towards smaller y;
    ``stationary``    the band stays at one longitudinal position;
    ``downstream``    the band moves towards larger y;
    ``none``          no band at all (only the deterministic ripple);
    ``gappy``         the upstream band with two time blocks removed.
    """
    time_index = np.arange(n_time)
    y_index = np.arange(n_y)
    # The dither must not itself propagate: each longitudinal position gets its own
    # temporal frequency, so the control scenarios contain no coherent lag.
    frequency = 0.7 + 0.13 * y_index
    generator = np.random.default_rng(20261221)
    dither = generator.normal(0.0, 0.35, size=(n_time, n_y))
    base = 12.0 + dither

    def frame(band: np.ndarray | None) -> pd.DataFrame:
        speed = base.copy()
        if band is not None:
            speed[band] -= 6.0
        rows = []
        for time_position, y_position in np.ndindex(speed.shape):
            rows.append({
                "t_block": int(time_position),
                "y_block": int(y_position),
                "t_start_s": float(time_position * t_step_s),
                "y_start_m": float(y_position * y_step_m),
                "obs": int(600),
                "speed_mps": float(speed[time_position, y_position]),
                "density_veh_km_lane": float(40.0 + 5.0 * np.sin(y_position / 4.0)),
            })
        return pd.DataFrame(rows)

    def band_mask(positions: np.ndarray) -> np.ndarray:
        mask = np.zeros((n_time, n_y), dtype=bool)
        for time_position, y_position in enumerate(positions):
            if 0 <= y_position < n_y:
                mask[time_position, y_position] = True
        return mask

    moving_up = band_mask(np.array([n_y - 2 - (index // 3) for index in time_index]))
    moving_down = band_mask(np.array([1 + (index // 3) for index in time_index]))
    stationary = band_mask(np.full(n_time, n_y // 2))
    gappy_mask = moving_up.copy()
    gappy_mask[8:10, :] = False
    return {
        "upstream": frame(moving_up),
        "stationary": frame(stationary),
        "downstream": frame(moving_down),
        "none": frame(None),
        "gappy": frame(gappy_mask),
    }


def classify_wave_structure(structure: dict[str, object], propagation: dict[str, object],
                            null: dict[str, object]) -> dict[str, object]:
    """Combine the component structure, the independent lag estimate and the null.

    Declared levels:

    * ``no_structure`` - no component reaches the minimum size;
    * ``local_anomaly_no_propagation`` - components exist but the space-time structure
      is not beyond the permutation null, or no nonzero propagation lag is resolved
      at all;
    * ``uncorroborated_structure`` - coherent structure beyond the null exists and a
      propagation lag is resolved, but it is not an upstream lag;
    * ``propagating_structure`` - coherent structure beyond the null *and* an
      independently resolved upstream lag.

    The propagation arbiter is the cross-correlation lag; the component front slope is
    reported as a descriptive companion, not as the decision variable, because a
    growing or shrinking blob can move its centroid without any wave.
    """
    reasons: list[str] = []
    if structure["level"] == "no_structure":
        return {"level": "no_structure", "reasons": ["no_component_at_or_above_minimum_size"]}
    pairs = int(propagation.get("pairs") or 0)
    share = propagation.get("upstream_share")
    speed = propagation.get("median_implied_speed_mps")
    resolved = pairs >= XCORR_MIN_PAIRS and any(
        int(item["best_lag_blocks"]) != 0 for item in propagation.get("detail", []))
    exceedance = null.get("exceedance_rate")
    weak: list[str] = []
    if exceedance is None or float(exceedance) > NULL_MAX_EXCEEDANCE:
        weak.append(f"not_beyond_permutation_null:{exceedance}")
    if pairs < XCORR_MIN_PAIRS:
        weak.append(f"too_few_cross_correlation_pairs:{pairs}")
    if not resolved:
        weak.append("no_nonzero_cross_correlation_lag_resolved")
    if weak:
        # no coherent, resolvable space-time structure: keep the weakest level
        return {"level": "local_anomaly_no_propagation", "reasons": weak}
    if share is None or float(share) < XCORR_MIN_UPSTREAM_SHARE:
        return {"level": "uncorroborated_structure",
                "reasons": [f"cross_correlation_upstream_share_below_threshold:{share}"]}
    if speed is None or float(speed) >= 0.0:
        return {"level": "uncorroborated_structure",
                "reasons": [f"cross_correlation_speed_not_upstream:{speed}"]}
    return {"level": "propagating_structure", "reasons": []}


def anomaly_report(cells: pd.DataFrame, baseline: dict[str, object], threshold: float,
                   *, definition: str = "temporal_position", alpha: float = WAVE_ALPHA,
                   t_step_s: float = WAVE_T_S, y_step_m: float = WAVE_Y_M,
                   resamples: int = NULL_RESAMPLES, seed: int = NULL_SEED) -> dict[str, object]:
    """Full diagnostic for one trajectory frame under one declared definition."""
    marked = anomaly_table(cells, baseline, threshold, definition=definition, alpha=alpha)
    structure = wave_structure(marked, t_step_s=t_step_s, y_step_m=y_step_m)
    null_axis = ("time_within_position" if definition == "temporal_position"
                 else "position_within_time")
    null = permutation_null(marked, resamples=resamples, seed=seed, axis=null_axis)
    propagation = cross_correlation_propagation(cells, t_step_s=t_step_s, y_step_m=y_step_m)
    classification = classify_wave_structure(structure, propagation, null)
    return {
        "status": "Observation",
        "definition": definition,
        "alpha": float(alpha),
        "cell_y_m": float(y_step_m),
        "cell_t_s": float(t_step_s),
        "cells": int(len(marked)),
        "anomalous_cells": int(marked["anomalous"].sum()) if len(marked) else 0,
        "anomalous_share": float(marked["anomalous"].mean()) if len(marked) else None,
        "threshold_mps": float(threshold),
        "structure": structure,
        "null": null,
        "cross_correlation": propagation,
        "classification": classification,
        "level": classification["level"],
    }


def wave_sensitivity(frame: pd.DataFrame, window: tuple[float, float],
                     baseline: dict[str, object], threshold: float, *,
                     definition: str = "temporal_position",
                     resamples: int = 200, seed: int = NULL_SEED) -> dict[str, object]:
    """Declared sensitivity of the wave verdict over the diagnostic settings."""
    result: dict[str, object] = {"status": "Observation", "grid": []}
    for t_step in WAVE_SENSITIVITY["t_step_s"]:
        cells = space_time_cells(frame, window=window, y_step_m=WAVE_Y_M, t_step_s=t_step,
                                 min_obs=WAVE_MIN_OBS)
        for alpha in WAVE_SENSITIVITY["alpha"]:
            report = anomaly_report(cells, baseline, threshold, definition=definition,
                                    alpha=alpha, t_step_s=t_step, y_step_m=WAVE_Y_M,
                                    resamples=resamples, seed=seed)
            result["grid"].append({
                "t_step_s": float(t_step),
                "alpha": float(alpha),
                "cells": report["cells"],
                "level": report["level"],
                "largest_component_cells": report["structure"]["largest_component_cells"],
                "front_slope_mps": report["structure"]["front_slope_mps"],
                "cross_correlation_upstream_share": report["cross_correlation"]["upstream_share"],
                "cross_correlation_median_speed_mps": report["cross_correlation"]["median_implied_speed_mps"],
            })
    levels = {item["level"] for item in result["grid"]}
    shares = [item["cross_correlation_upstream_share"] for item in result["grid"]
              if item["cross_correlation_upstream_share"] is not None]
    result["level_set"] = sorted(levels)
    result["verdict_invariant"] = bool(
        len(levels) == 1 and levels == {"propagating_structure"})
    result["min_upstream_share"] = float(min(shares)) if shares else None
    return result
