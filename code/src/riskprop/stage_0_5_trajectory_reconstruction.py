"""Read-only reconstruction of the real traffic formation process for Stage 0.5.

This module answers the Stage 0.5 question "why does SUMO reproduce the observed
cross-section flow but not the observed congestion" by describing, from the
already sealed Stage 0.2 canonical trajectory states, how the target traffic
state is formed: lane geometry, boundary flows, vehicle accumulation, sectional
speed/density evolution, congestion-wave localisation and the fundamental
diagram.

Boundaries of this module
-------------------------
* It only reads the two approved calibration windows. Sealed windows
  (``us101__0820_0835`` and Lankershim) are refused by construction.
* It never re-defines identity, clock, quality or P2 semantics owned by
  Stage 0.2. It only re-uses the sealed canonical parquet states.
* It does not run SUMO and does not write scientific Gate state.
* Every quantity is tagged Observation / Derived / Hypothesis / Unidentifiable
  so that an interpretation is never silently promoted to a measurement.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd

VERSION = "stage-0.5-trajectory-reconstruction-v1"

# Approved calibration windows and the single approved local evaluation region
# used by the 2026-10-20 approved-D1 reference. Values are inherited, not chosen
# here.
CALIBRATION_WINDOWS: dict[str, tuple[float, float]] = {
    "us101__0750_0805": (120.0, 840.0),
    "us101__0805_0820": (180.0, 840.0),
}
SEALED_WINDOW_IDS = ("0820_0835", "lankershim", "complete")
REGION_START_M = 150.0
REGION_END_M = 350.0
MAINLINE_LANES = ("1", "2", "3", "4", "5")
AUXILIARY_LANE = "6"
ONRAMP_LANE = "7"
OFFRAMP_LANE = "8"
LOW_SPEED_MPS = 5.0        # inherited low-speed descriptive threshold
JAM_SPEED_MPS = 10.0       # descriptive jam threshold for wave localisation
STATE_COLUMNS = (
    "dataset", "site", "window_id",
    "vehicle_id", "trajectory_id", "time_s", "y_m", "x_m", "speed_mps",
    "acceleration_mps2", "lane_id", "net_gap_m", "closing_speed_mps",
    "measurement_status", "identity_break", "observation_gap",
    "original_row_number", "source_member", "missing_reason", "ttc_s",
    "leader_matched", "leader_trajectory_id", "leader_identity_uncertain",
    "frame_id", "global_time_ms",
)
REQUIRED_STATE_COLUMNS = STATE_COLUMNS


class TrajectoryReconstructionError(ValueError):
    """Fail-closed error for schema, isolation or window violations."""


# --------------------------------------------------------------------------
# isolation and loading
# --------------------------------------------------------------------------
def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_calibration_states(path: str, window_id: str) -> pd.DataFrame:
    """Load one approved calibration window of canonical Stage 0.2 states.

    The loader is fail-closed: an unapproved window id, an unexpected
    ``dataset``/``site``/``window_id`` value or a missing column raises.
    """
    if window_id not in CALIBRATION_WINDOWS:
        raise TrajectoryReconstructionError(f"unapproved_window:{window_id}")
    if any(sealed in window_id for sealed in SEALED_WINDOW_IDS):
        raise TrajectoryReconstructionError(f"sealed_window_refused:{window_id}")
    frame = pd.read_parquet(path, columns=list(STATE_COLUMNS))
    missing = [column for column in REQUIRED_STATE_COLUMNS if column not in frame.columns]
    if missing:
        raise TrajectoryReconstructionError(f"missing_columns:{missing}")
    if frame.empty:
        raise TrajectoryReconstructionError("empty_state_table")
    if frame.dataset.unique().tolist() != ["NGSIM"] or frame.site.unique().tolist() != ["US-101"]:
        raise TrajectoryReconstructionError("unexpected_source")
    if frame.window_id.nunique() != 1:
        raise TrajectoryReconstructionError("mixed_windows")
    observed = str(frame.window_id.iloc[0])
    if observed != window_id.split("__")[-1]:
        raise TrajectoryReconstructionError(f"window_mismatch:{observed}")
    if pd.to_numeric(frame.lane_id, errors="coerce").isna().any():
        raise TrajectoryReconstructionError("non_numeric_lane_id")
    if not np.isfinite(frame[["time_s", "y_m", "speed_mps"]].to_numpy(float)).all():
        raise TrajectoryReconstructionError("nonfinite_state")
    frame = frame.copy()
    frame["lane_id"] = frame.lane_id.astype(str)
    return frame.sort_values(["trajectory_id", "time_s"], kind="stable").reset_index(drop=True)


def window_clock_span(frame: pd.DataFrame) -> tuple[float, float]:
    return float(frame.time_s.min()), float(frame.time_s.max())


def real_region_mask(states: pd.DataFrame) -> pd.Series:
    """Canonical approved D1 region mask: lanes 1-5 and 150 <= y < 350."""
    lane = pd.to_numeric(states.lane_id, errors="raise")
    y = pd.to_numeric(states.y_m, errors="raise")
    if not np.isfinite(lane).all() or not np.isfinite(y).all():
        raise TrajectoryReconstructionError("invalid_real_spatial_schema")
    return lane.isin([1, 2, 3, 4, 5]) & y.ge(REGION_START_M) & y.lt(REGION_END_M)


# --------------------------------------------------------------------------
# A1 geometry
# --------------------------------------------------------------------------
def lane_geometry(frame: pd.DataFrame) -> pd.DataFrame:
    """Per-lane longitudinal/lateral support. Pure observation."""
    grouped = frame.groupby("lane_id", sort=True).agg(
        states=("speed_mps", "size"),
        vehicles=("vehicle_id", "nunique"),
        trajectories=("trajectory_id", "nunique"),
        y_min_m=("y_m", "min"),
        y_max_m=("y_m", "max"),
        x_mean_m=("x_m", "mean"),
        speed_mean_mps=("speed_mps", "mean"),
    )
    grouped["y_span_m"] = grouped.y_max_m - grouped.y_min_m
    return grouped.reset_index()


def classify_lanes(geometry: pd.DataFrame) -> dict[str, object]:
    """Assign a road role to each observed lane from its longitudinal support.

    Rules are explicit and fail-closed: they are checked against the observed
    support so that a change in the underlying data cannot silently re-label a
    lane.
    """
    spans = {str(row.lane_id): (float(row.y_min_m), float(row.y_max_m)) for row in geometry.itertuples()}
    mainline, auxiliary, onramp, offramp, unknown = [], [], [], [], []
    for lane, (low, high) in spans.items():
        if lane in MAINLINE_LANES:
            if high - low < 400.0:
                raise TrajectoryReconstructionError(f"mainline_lane_short_support:{lane}")
            mainline.append(lane)
        elif lane == AUXILIARY_LANE:
            auxiliary.append(lane)
        elif lane == ONRAMP_LANE:
            onramp.append(lane)
        elif lane == OFFRAMP_LANE:
            offramp.append(lane)
        else:
            unknown.append(lane)
    if unknown:
        raise TrajectoryReconstructionError(f"unclassified_lanes:{unknown}")
    if len(mainline) != 5:
        raise TrajectoryReconstructionError("mainline_lane_count")
    on_low, on_high = spans[ONRAMP_LANE]
    aux_low, aux_high = spans[AUXILIARY_LANE]
    off_low, off_high = spans[OFFRAMP_LANE]
    if not (on_low < on_high <= aux_high and aux_low >= on_high - 1.0 and off_low >= aux_high - 1.0):
        raise TrajectoryReconstructionError("unexpected_auxiliary_chain")
    return {
        "status": "Observation",
        "mainline_lanes": sorted(mainline),
        "auxiliary_lane": AUXILIARY_LANE,
        "onramp_lane": ONRAMP_LANE,
        "offramp_lane": OFFRAMP_LANE,
        "mainline_support_m": [spans[lane][0] for lane in mainline],
        "onramp_support_m": [on_low, on_high],
        "auxiliary_support_m": [aux_low, aux_high],
        "offramp_support_m": [off_low, off_high],
        "interpretation": (
            "Five mainline lanes span the whole segment; the dedicated lane that "
            "starts where the short lane ends is the auxiliary lane between the "
            "on-ramp and the off-ramp. Official NGSIM metadata for this site state "
            "five mainline lanes throughout with one auxiliary lane between the "
            "Ventura Boulevard on-ramp and the Cahuenga Boulevard off-ramp."
        ),
        "classification_basis": "observed longitudinal support per lane_id (rule checked, fail-closed)",
    }


# --------------------------------------------------------------------------
# A2 boundary flows and conservation
# --------------------------------------------------------------------------
def boundary_crossings(
    frame: pd.DataFrame, *, at_m: float, lanes: tuple[str, ...], window: tuple[float, float]
) -> pd.DataFrame:
    """Vehicles crossing a longitudinal plane inside the window.

    Crossing time is linearly interpolated between the two adjacent 10 Hz
    observations. Vehicles whose observed trajectory starts or ends exactly on
    the plane are not counted as crossings.
    """
    low, high = window
    subset = frame[frame.lane_id.isin(lanes)].sort_values(["trajectory_id", "time_s"], kind="stable")
    grams = subset.groupby("trajectory_id", sort=False)
    previous_y = grams.y_m.shift()
    previous_t = grams.time_s.shift()
    span = subset.y_m - previous_y
    crossed = (previous_y < at_m) & (subset.y_m >= at_m) & span.gt(0)
    ratio = np.where(span.gt(0), (at_m - previous_y) / span, np.nan)
    crossing_time = previous_t + ratio * (subset.time_s - previous_t)
    keep = crossed & pd.Series(crossing_time, index=subset.index).between(low, high, inclusive="left")
    result = pd.DataFrame(
        {
            "trajectory_id": subset.trajectory_id[keep],
            "vehicle_id": subset.vehicle_id[keep],
            "lane_id": subset.lane_id[keep],
            "time_s": pd.Series(crossing_time, index=subset.index)[keep],
            "speed_mps": subset.speed_mps[keep],
            "net_gap_m": subset.net_gap_m[keep],
            "closing_speed_mps": subset.closing_speed_mps[keep],
        }
    ).sort_values("time_s", kind="stable")
    result["at_m"] = at_m
    result["window_s"] = [window] * len(result)
    return result.reset_index(drop=True)


def flow_table(crossings: pd.DataFrame, window: tuple[float, float], block_s: float = 30.0) -> pd.DataFrame:
    low, high = window
    if crossings.empty:
        return pd.DataFrame(columns=["block_start_s", "vehicles", "flow_veh_h", "mean_speed_mps"])
    blocks = np.arange(low, high, block_s)
    index = np.clip(((crossings.time_s.to_numpy() - low) // block_s).astype(int), 0, len(blocks) - 1)
    grouped = crossings.assign(block=index).groupby("block")
    table = pd.DataFrame(
        {
            "block_start_s": blocks,
            "vehicles": grouped.size().reindex(range(len(blocks)), fill_value=0).to_numpy(),
        }
    )
    table["flow_veh_h"] = table.vehicles / block_s * 3600.0
    table["mean_speed_mps"] = grouped.speed_mps.mean().reindex(range(len(blocks))).to_numpy()
    return table


def vehicle_conservation(
    frame: pd.DataFrame,
    *,
    region: tuple[float, float] = (REGION_START_M, REGION_END_M),
    lanes_in: tuple[str, ...] = MAINLINE_LANES,
    lanes_out: tuple[str, ...] = MAINLINE_LANES,
    window: tuple[float, float],
    label: str = "region",
    edge_average_s: float = 30.0,
) -> dict[str, object]:
    """N(t2)-N(t1) = N_in - N_out on one identical region and time interval.

    ``lanes_in``/``lanes_out`` differ where a lane physically starts or ends
    inside the region; a region whose cross-section is not identical at both
    ends is reported with the resulting interpretation caveat.
    """
    low, high = window
    occupancy = _occupancy_counts(frame, region=region, lanes=lanes_out)
    entry = _crossings_from_subset(frame, at_m=region[0], lanes=lanes_in, window=window)
    exit_crossings = _crossings_from_subset(frame, at_m=region[1], lanes=lanes_out, window=window)
    n_start = float(occupancy["edge_average_start"])
    n_end = float(occupancy["edge_average_end"])
    delta = n_end - n_start
    residual = delta - (len(entry) - len(exit_crossings))
    return {
        "status": "Derived",
        "label": label,
        "region_m": list(region),
        "window_s": list(window),
        "lanes_in": list(lanes_in),
        "lanes_out": list(lanes_out),
        "cross_section_identical": list(lanes_in) == list(lanes_out),
        "occupancy_start_mean": n_start,
        "occupancy_end_mean": n_end,
        "occupancy_edge_average_s": edge_average_s,
        "occupancy_delta": delta,
        "entered": int(len(entry)),
        "exited": int(len(exit_crossings)),
        "in_minus_out": int(len(entry) - len(exit_crossings)),
        "conservation_residual_vehicles": int(residual),
        "entering_flow_veh_h": len(entry) / (high - low) * 3600.0,
        "exiting_flow_veh_h": len(exit_crossings) / (high - low) * 3600.0,
        "entering_speed_mean_mps": float(entry.speed_mps.mean()) if len(entry) else None,
        "exiting_speed_mean_mps": None,
    }


def _occupancy_counts(
    frame: pd.DataFrame,
    *,
    region: tuple[float, float],
    lanes: tuple[str, ...],
    edge_average_s: float = 30.0,
) -> dict[str, float]:
    subset = frame[frame.lane_id.isin(lanes) & frame.y_m.ge(region[0]) & frame.y_m.lt(region[1])]
    per_time = subset.groupby("time_s").trajectory_id.nunique()
    if per_time.empty:
        return {"edge_average_start": 0.0, "edge_average_end": 0.0, "mean": 0.0}
    first = per_time.index.min()
    last = per_time.index.max()
    head = per_time[(per_time.index >= first) & (per_time.index < first + edge_average_s)]
    tail = per_time[(per_time.index > last - edge_average_s) & (per_time.index <= last)]
    return {
        "edge_average_start": float(head.mean()),
        "edge_average_end": float(tail.mean()),
        "mean": float(per_time.mean()),
    }


def _crossings_from_subset(
    frame: pd.DataFrame, *, at_m: float, lanes: tuple[str, ...], window: tuple[float, float]
) -> pd.DataFrame:
    low, high = window
    subset = frame[frame.lane_id.isin(lanes)].sort_values(["trajectory_id", "time_s"], kind="stable")
    grams = subset.groupby("trajectory_id", sort=False)
    previous_y = grams.y_m.shift()
    previous_t = grams.time_s.shift()
    span = subset.y_m - previous_y
    crossed = (previous_y < at_m) & (subset.y_m >= at_m) & span.gt(0)
    ratio = np.where(span.gt(0), (at_m - previous_y) / span, np.nan)
    crossing_time = pd.Series(previous_t + ratio * (subset.time_s - previous_t), index=subset.index)
    keep = crossed & crossing_time.between(low, high, inclusive="left")
    return pd.DataFrame(
        {
            "trajectory_id": subset.trajectory_id[keep],
            "lane_id": subset.lane_id[keep],
            "time_s": crossing_time[keep],
            "speed_mps": subset.speed_mps[keep],
        }
    )


def ramp_flows(frame: pd.DataFrame, *, window: tuple[float, float]) -> dict[str, object]:
    """On-ramp and off-ramp flows from the dedicated lanes' observed support."""
    low, high = window
    duration = high - low
    onramp = frame[frame.lane_id == ONRAMP_LANE]
    offramp = frame[frame.lane_id == OFFRAMP_LANE]
    on_first = onramp.groupby("trajectory_id").time_s.min()
    on_count = int(on_first.between(low, high, inclusive="left").sum())
    off_last = offramp.groupby("trajectory_id").y_m.max()
    off_first = offramp.groupby("trajectory_id").time_s.min()
    off_count = int(off_first.between(low, high, inclusive="left").sum())
    return {
        "status": "Derived",
        "window_s": list(window),
        "onramp_lane": ONRAMP_LANE,
        "onramp_support_m": [
            float(onramp.y_m.min()) if len(onramp) else None,
            float(onramp.y_m.max()) if len(onramp) else None,
        ],
        "onramp_entry_vehicles_in_window": on_count,
        "onramp_entry_flow_veh_h": on_count / duration * 3600.0,
        "offramp_lane": OFFRAMP_LANE,
        "offramp_support_m": [
            float(offramp.y_m.min()) if len(offramp) else None,
            float(offramp.y_m.max()) if len(offramp) else None,
        ],
        "offramp_entry_vehicles_in_window": off_count,
        "offramp_entry_flow_veh_h": off_count / duration * 3600.0,
        "offramp_last_observed_y_mean_m": float(off_last.mean()) if len(off_last) else None,
        "caveat": (
            "Entry instants on the dedicated lanes are the first observation on that "
            "lane, so they are lower bounds of the true ramp arrival times when a "
            "vehicle was already on the lane before the window."
        ),
    }


# --------------------------------------------------------------------------
# A3 local state, space-time structure and fundamental diagram
# --------------------------------------------------------------------------
def local_state(
    frame: pd.DataFrame,
    *,
    region: tuple[float, float] = (REGION_START_M, REGION_END_M),
    lanes: tuple[str, ...] = MAINLINE_LANES,
    window: tuple[float, float],
) -> dict[str, object]:
    """Local per-lane density/speed/flow for the approved D1 region."""
    low, high = window
    lane_km = (region[1] - region[0]) / 1000.0 * len(lanes)
    subset = frame[frame.lane_id.isin(lanes) & frame.y_m.ge(region[0]) & frame.y_m.lt(region[1]) & frame.time_s.between(low, high, inclusive="left")]
    vehicle_s = len(subset) / 10.0
    density = vehicle_s / (high - low) / lane_km
    speed = float(subset.speed_mps.mean())
    return {
        "status": "Observation",
        "region_m": list(region),
        "lanes": list(lanes),
        "lane_km": lane_km,
        "coverage_s": high - low,
        "local_vehicle_s": vehicle_s,
        "density_veh_km_lane": density,
        "speed_mean_mps": speed,
        "flow_veh_h_lane_consistency": density * speed * 3.6,
        "low_speed_share": float((subset.speed_mps < LOW_SPEED_MPS).mean()),
        "speed_sd_mps": float(subset.speed_mps.std(ddof=1)),
        "speed_quantiles_mps": [float(x) for x in subset.speed_mps.quantile([0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0])],
        "acceleration_mean_mps2": float(subset.acceleration_mps2.mean()),
        "acceleration_sd_mps2": float(subset.acceleration_mps2.std(ddof=1)),
        "states": int(len(subset)),
    }


def space_time(
    frame: pd.DataFrame,
    *,
    lanes: tuple[str, ...] = MAINLINE_LANES,
    window: tuple[float, float],
    y_step_m: float = 50.0,
    t_step_s: float = 60.0,
    y_high_m: float | None = None,
) -> dict[str, object]:
    """Space-time speed and density surfaces for the mainline lanes."""
    low, high = window
    upper = float(frame.y_m.max()) if y_high_m is None else y_high_m
    y_edges = np.arange(0.0, upper + y_step_m, y_step_m)
    t_edges = np.arange(low, high + t_step_s, t_step_s)
    subset = frame[frame.lane_id.isin(lanes) & frame.time_s.between(low, high, inclusive="left")].copy()
    subset["y_bin"] = pd.cut(subset.y_m, bins=y_edges, right=False, labels=y_edges[:-1]).astype(float)
    subset["t_bin"] = pd.cut(subset.time_s, bins=t_edges, right=False, labels=t_edges[:-1]).astype(float)
    cell_lane_km = y_step_m / 1000.0 * len(lanes)
    speed = subset.pivot_table(index="y_bin", columns="t_bin", values="speed_mps", aggfunc="mean")
    count = subset.pivot_table(index="y_bin", columns="t_bin", values="speed_mps", aggfunc="size")
    density = count * 0.1 / t_step_s / cell_lane_km
    low_speed = subset.assign(low=subset.speed_mps.lt(LOW_SPEED_MPS)).pivot_table(
        index="y_bin", columns="t_bin", values="low", aggfunc="mean"
    )
    return {
        "status": "Observation",
        "y_step_m": y_step_m,
        "t_step_s": t_step_s,
        "y_edges_m": [float(x) for x in y_edges],
        "t_edges_s": [float(x) for x in t_edges],
        "speed_mps": speed,
        "density_veh_km_lane": density,
        "low_speed_share": low_speed,
    }


def fundamental_diagram(
    frame: pd.DataFrame,
    *,
    lanes: tuple[str, ...] = MAINLINE_LANES,
    window: tuple[float, float],
    y_step_m: float = 100.0,
    t_step_s: float = 30.0,
) -> pd.DataFrame:
    """Per-cell (density, flow, speed) triples with the q = k v consistency check."""
    low, high = window
    upper = float(frame.y_m.max())
    y_edges = np.arange(0.0, upper + y_step_m, y_step_m)
    t_edges = np.arange(low, high + t_step_s, t_step_s)
    subset = frame[frame.lane_id.isin(lanes) & frame.time_s.between(low, high, inclusive="left")].copy()
    subset["y_bin"] = pd.cut(subset.y_m, bins=y_edges, right=False, labels=y_edges[:-1]).astype(float)
    subset["t_bin"] = pd.cut(subset.time_s, bins=t_edges, right=False, labels=t_edges[:-1]).astype(float)
    cell_lane_km = y_step_m / 1000.0 * len(lanes)
    grouped = subset.groupby(["t_bin", "y_bin"], observed=True).agg(
        states=("speed_mps", "size"),
        speed_mean_mps=("speed_mps", "mean"),
        low_speed_share=("speed_mps", lambda values: float((values < LOW_SPEED_MPS).mean())),
    )
    grouped["density_veh_km_lane"] = grouped.states * 0.1 / t_step_s / cell_lane_km
    grouped["flow_veh_h_lane"] = grouped.density_veh_km_lane * grouped.speed_mean_mps * 3.6
    return grouped.reset_index()


def occupancy_series(
    frame: pd.DataFrame,
    *,
    region: tuple[float, float] = (REGION_START_M, REGION_END_M),
    lanes: tuple[str, ...] = MAINLINE_LANES,
    window: tuple[float, float],
    block_s: float = 30.0,
) -> pd.DataFrame:
    """Regional vehicle count inside each lane and in total, per time block."""
    low, high = window
    subset = frame[frame.lane_id.isin(lanes) & frame.y_m.ge(region[0]) & frame.y_m.lt(region[1]) & frame.time_s.between(low, high, inclusive="left")].copy()
    subset["block"] = ((subset.time_s - low) // block_s).astype(int)
    per_lane = subset.groupby(["block", "lane_id"]).apply(
        lambda part: part.groupby("time_s").trajectory_id.nunique().mean(), include_groups=False
    )
    total = subset.groupby("block").apply(
        lambda part: part.groupby("time_s").trajectory_id.nunique().mean(), include_groups=False
    )
    table = per_lane.unstack("lane_id").add_prefix("vehicles_lane_")
    table["vehicles_total"] = total
    table["block_start_s"] = low + table.index * block_s
    return table.reset_index(drop=True)


def jam_waves(
    frame: pd.DataFrame,
    *,
    lanes: tuple[str, ...] = MAINLINE_LANES,
    window: tuple[float, float],
    threshold_mps: float = JAM_SPEED_MPS,
    y_step_m: float = 50.0,
    t_step_s: float = 30.0,
) -> dict[str, object]:
    """Localise low-speed waves in (y, t) and report their time origin.

    A cell is "slow" when its mean speed is below ``threshold_mps``. Connected
    slow cells (4-neighbourhood) are grouped into components; each component is
    characterised by its earliest time block and the longitudinal direction in
    which it grows afterwards. This is descriptive evidence about where a
    congestion episode is first visible and how it spreads; it is not a
    bottleneck attribution.
    """
    low, high = window
    upper = float(frame.y_m.max())
    y_edges = np.arange(0.0, upper + y_step_m, y_step_m)
    t_edges = np.arange(low, high + t_step_s, t_step_s)
    grid = space_time(
        frame, lanes=lanes, window=window, y_step_m=y_step_m, t_step_s=t_step_s, y_high_m=upper
    )["speed_mps"]
    grid = grid.reindex(index=y_edges[:-1], columns=t_edges[:-1])
    slow = (grid < threshold_mps).to_numpy()
    visited = np.zeros_like(slow, dtype=bool)
    components: list[dict[str, object]] = []
    rows, cols = slow.shape
    for row in range(rows):
        for column in range(cols):
            if not slow[row, column] or visited[row, column]:
                continue
            stack = [(row, column)]
            visited[row, column] = True
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_column = stack.pop()
                cells.append((current_row, current_column))
                for delta_row, delta_column in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row, next_column = current_row + delta_row, current_column + delta_column
                    if 0 <= next_row < rows and 0 <= next_column < cols and slow[next_row, next_column] and not visited[next_row, next_column]:
                        visited[next_row, next_column] = True
                        stack.append((next_row, next_column))
            times = [t_edges[column] for _, column in cells]
            positions = [y_edges[row] for row, _ in cells]
            first_time = min(times)
            first_positions = [y_edges[row] for row, column in cells if t_edges[column] == first_time]
            last_time = max(times)
            last_positions = [y_edges[row] for row, column in cells if t_edges[column] == last_time]
            components.append(
                {
                    "cells": len(cells),
                    "duration_s": float(last_time - first_time + t_step_s),
                    "first_time_s": float(first_time),
                    "first_y_min_m": float(min(first_positions)),
                    "first_y_max_m": float(max(first_positions)),
                    "last_time_s": float(last_time),
                    "last_y_min_m": float(min(last_positions)),
                    "last_y_max_m": float(max(last_positions)),
                    "growth": (
                        "upstream" if min(last_positions) < min(first_positions)
                        else "downstream" if max(last_positions) > max(first_positions)
                        else "stationary"
                    ),
                }
            )
    components.sort(key=lambda item: (-item["cells"], item["first_time_s"]))
    return {
        "status": "Observation",
        "threshold_mps": threshold_mps,
        "y_step_m": y_step_m,
        "t_step_s": t_step_s,
        "slow_cell_fraction": float(slow.mean()),
        "components": components[:20],
    }


def sectional_minimum(frame: pd.DataFrame, *, window: tuple[float, float], lanes: tuple[str, ...] = MAINLINE_LANES, y_step_m: float = 100.0, t_step_s: float = 300.0) -> pd.DataFrame:
    """Per time block: the section with the lowest mean speed and its value."""
    grid = space_time(frame, lanes=lanes, window=window, y_step_m=y_step_m, t_step_s=t_step_s)["speed_mps"]
    records = []
    for column in grid.columns:
        profile = grid[column].dropna()
        if profile.empty:
            continue
        records.append(
            {
                "t_start_s": float(column),
                "slowest_section_m": float(profile.idxmin()),
                "min_speed_mps": float(profile.min()),
                "upstream_speed_mps": float(profile.iloc[0]),
                "downstream_speed_mps": float(profile.iloc[-1]),
            }
        )
    return pd.DataFrame(records)


# --------------------------------------------------------------------------
# interaction statistics
# --------------------------------------------------------------------------
def interaction_stats(
    frame: pd.DataFrame,
    *,
    region: tuple[float, float] = (REGION_START_M, REGION_END_M),
    lanes: tuple[str, ...] = MAINLINE_LANES,
    window: tuple[float, float],
) -> dict[str, object]:
    low, high = window
    subset = frame[frame.lane_id.isin(lanes) & frame.y_m.ge(region[0]) & frame.y_m.lt(region[1]) & frame.time_s.between(low, high, inclusive="left")]
    gap = subset.net_gap_m.dropna()
    closing = subset.closing_speed_mps.dropna()
    time_headway = np.where(closing.to_numpy() > 0, gap.to_numpy()[: len(closing)] / np.where(closing.to_numpy() > 0, closing.to_numpy(), np.nan), np.nan)
    time_headway = time_headway[np.isfinite(time_headway)]
    return {
        "status": "Observation",
        "region_m": list(region),
        "window_s": list(window),
        "states": int(len(subset)),
        "measurement_status_counts": {str(k): int(v) for k, v in subset.measurement_status.value_counts().items()},
        "missing_reason_counts": (
            {str(k): int(v) for k, v in subset.missing_reason.value_counts().items()}
            if "missing_reason" in subset.columns else {}
        ),
        "leader_matched_share": float(subset.leader_matched.mean()) if "leader_matched" in subset.columns else None,
        "net_gap_m": _describe(gap),
        "closing_speed_mps": _describe(closing),
        "closing_speed_negative_share": float((closing < 0).mean()),
        "net_gap_over_speed_s": _describe(pd.Series(time_headway)) if len(time_headway) else None,
    }


def _describe(values: pd.Series) -> dict[str, object] | None:
    clean = pd.Series(values).dropna()
    if clean.empty:
        return None
    return {
        "n": int(len(clean)),
        "mean": float(clean.mean()),
        "sd": float(clean.std(ddof=1)) if len(clean) > 1 else None,
        "quantiles": [float(x) for x in clean.quantile([0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0])],
    }


# --------------------------------------------------------------------------
# uncertainty
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class ClusterInterval:
    point: float
    low: float
    high: float
    clusters: int
    resamples: int
    status: str


def cluster_bootstrap(
    frame: pd.DataFrame,
    *,
    region: tuple[float, float] = (REGION_START_M, REGION_END_M),
    lanes: tuple[str, ...] = MAINLINE_LANES,
    window: tuple[float, float],
    metric: str = "speed",
    resamples: int = 2000,
    seed: int = 20261021,
) -> ClusterInterval:
    """Trajectory-cluster bootstrap for one local aggregate.

    The interval covers within-source sampling variability of the trajectory
    clusters only. It is not a rate confidence interval and not a science
    tolerance.
    """
    low, high = window
    lane_km = (region[1] - region[0]) / 1000.0 * len(lanes)
    subset = frame[frame.lane_id.isin(lanes) & frame.y_m.ge(region[0]) & frame.y_m.lt(region[1]) & frame.time_s.between(low, high, inclusive="left")]
    grouped = subset.groupby("trajectory_id")
    if metric == "speed":
        per_cluster = grouped.speed_mps.mean()
        statistic = lambda values: float(np.average(values, weights=counts))
    elif metric == "density":
        counts = grouped.size().div(10.0)
        per_cluster = counts
        statistic = lambda values: float(values.sum() / (high - low) / lane_km)
    else:
        raise TrajectoryReconstructionError(f"unknown_metric:{metric}")
    counts = grouped.size().to_numpy(float)
    values = per_cluster.to_numpy(float)
    generator = np.random.default_rng(seed)
    n_clusters = len(values)
    draws = np.empty(resamples, dtype=float)
    if metric == "speed":
        for index in range(resamples):
            pick = generator.integers(0, n_clusters, n_clusters)
            draws[index] = np.average(values[pick], weights=counts[pick])
    else:
        for index in range(resamples):
            pick = generator.integers(0, n_clusters, n_clusters)
            draws[index] = values[pick].sum() / (high - low) / lane_km
    point = statistic(values)
    return ClusterInterval(
        point=float(point),
        low=float(np.quantile(draws, 0.025)),
        high=float(np.quantile(draws, 0.975)),
        clusters=int(n_clusters),
        resamples=resamples,
        status="Conditional cluster bootstrap sensitivity; within-source only, not a science tolerance",
    )
