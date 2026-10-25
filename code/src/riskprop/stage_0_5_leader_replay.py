"""Leader-trajectory replay: test a car-following model against real followers.

Method grounding
----------------
* Brockfeld, Kühne & Wagner (2004), TRR 1876: the recorded leading car is fed into
  the model and the model produces the follower; the error is the normalised
  absolute gap deviation (Eq. 2)
  ``e = sum_t |g_sim(t) - g_obs(t)| / sum_t g_obs(t)``.
* Schrader et al. (2024), SUMO Conf. Proc. 5, sections 3.3.1-3.3.2: each
  leader-follower pair is driven through SUMO via TraCI with TraCI controlling the
  leader's position and velocity; the measure of performance is
  ``NRMSE(s,v,a) = NRMSE(s) + NRMSE(v) + NRMSE(a)`` with
  ``NRMSE(X) = RMSE(X, X_hat) / sqrt((1/n) sum_i X_i^2)`` (Eqs. 5-6).

Declared deviations from the sources (project choices, not paper claims):

* No optimiser is used. Two frozen configurations are compared on the same sample;
  no parameter search is performed.
* Acceleration is not scored: the observed acceleration is a differenced quantity
  whose noise handling has not been validated here, which is the precondition the
  project's own rules impose on acceleration metrics.
* ``minGap`` is held at the frozen value while ``tau`` varies, so a difference is
  attributable to the time-gap parameter only.

Data model used here
--------------------
A canonical state row is the *follower's* state, so::

    leader_y = follower_y + net_gap_m + leader_length

The leader's own position and speed are read from the leader's own trajectory rows
at the same observation clock. Leader length is not observed (the project records
vehicle length as Unverified), so the frozen passenger length is used on both the
observed and the simulated side of the net-gap reconstruction.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

VERSION = "stage-0.5-leader-replay-v1"

BASELINE_FOLLOWING = dict(
    maxSpeed=27.78, speedFactor=1.0, speedDev=0.0, carFollowModel="Krauss", tau=1.0,
    minGap=2.5, accel=2.6, decel=4.5, apparentDecel=4.5, emergencyDecel=9.0, sigma=0.5,
    actionStepLength=0.1, sigmaStep=1.0, laneChangeModel="LC2013",
)
CANDIDATE_TAU_S = 1.6
ASSUMED_LEADER_LENGTH_M = 4.4196

REQUIRED_COLUMNS = (
    "trajectory_id", "leader_trajectory_id", "time_s", "y_m", "speed_mps", "lane_id",
    "net_gap_m", "closing_speed_mps", "measurement_status", "identity_break",
    "observation_gap", "leader_matched", "frame_id", "global_time_ms",
)


class LeaderReplayError(ValueError):
    """Fail-closed error for selection, replay or metric violations."""


def configuration(tau: float, *, overrides: dict | None = None) -> dict[str, object]:
    params = dict(BASELINE_FOLLOWING)
    params["tau"] = float(tau)
    if overrides:
        params.update(overrides)
    for key in ("minGap", "accel", "decel", "sigma", "maxSpeed", "actionStepLength"):
        if params[key] != BASELINE_FOLLOWING[key]:
            raise LeaderReplayError(f"only tau may differ from the frozen baseline in this task: {key}")
    return params


def prepare_pairs(
    frame: pd.DataFrame,
    *,
    window: tuple[float, float],
    lanes: tuple[str, ...] = ("1", "2", "3", "4", "5"),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build reliable continuous following runs and return (runs, follower rows).

    Continuity, identity and quality semantics are inherited from Stage 0.2 and are
    not modified: adjacent 0.1 s observations, identical leader, no identity break,
    no observation gap, leader matched, evaluable status, single lane.
    """
    low, high = window
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise LeaderReplayError(f"missing_columns:{missing}")
    subset = frame[frame.lane_id.isin(lanes) & frame.time_s.between(low, high, inclusive="left")].copy()
    subset = subset.sort_values(["trajectory_id", "time_s"], kind="stable").reset_index(drop=True)
    same_trajectory = subset.trajectory_id.eq(subset.trajectory_id.shift())
    same_leader = subset.leader_trajectory_id.eq(subset.leader_trajectory_id.shift())
    adjacent = (
        same_trajectory & same_leader
        & subset.time_s.diff().sub(0.1).abs().lt(1e-9)
        & subset.frame_id.diff().eq(1)
        & subset.global_time_ms.diff().eq(100)
        & ~subset.identity_break.astype(bool)
        & ~subset.observation_gap.astype(bool)
        & subset.leader_matched.astype(bool)
    )
    evaluable = subset.measurement_status.isin(["valid", "not_applicable"])
    subset["run_id"] = (~(adjacent & evaluable & subset.leader_trajectory_id.notna())).cumsum()
    runs = []
    for run_id, group in subset.groupby("run_id", sort=True):
        if len(group) < 20 or not evaluable.loc[group.index].all():
            continue
        if group.lane_id.nunique() != 1 or group.leader_trajectory_id.nunique() != 1:
            continue
        runs.append(
            {
                "run_id": int(run_id),
                "trajectory_id": str(group.trajectory_id.iloc[0]),
                "leader_trajectory_id": str(group.leader_trajectory_id.iloc[0]),
                "lane_id": str(group.lane_id.iloc[0]),
                "start_s": float(group.time_s.iloc[0]),
                "end_s": float(group.time_s.iloc[-1]),
                "duration_s": float(group.time_s.iloc[-1] - group.time_s.iloc[0]) + 0.1,
                "states": int(len(group)),
                "gap_mean_m": float(group.net_gap_m.mean()),
                "speed_mean_mps": float(group.speed_mps.mean()),
                "pos_start": int(group.index[0]),
                "pos_end": int(group.index[-1]),
            }
        )
    return pd.DataFrame(runs), subset


def select_pairs(runs: pd.DataFrame, *, count: int, min_duration_s: float = 8.0, max_duration_s: float = 25.0) -> pd.DataFrame:
    """Frozen selection rule: duration closest to the cap first, then identity."""
    if runs.empty:
        return runs
    eligible = runs[runs.duration_s.ge(min_duration_s)].copy()
    eligible["duration_capped"] = eligible.duration_s.clip(upper=max_duration_s)
    eligible = eligible.sort_values(
        ["duration_capped", "trajectory_id", "start_s"], ascending=[False, True, True]
    )
    return eligible.head(count).reset_index(drop=True)


def pair_observations(subset: pd.DataFrame, run: pd.Series, *, max_duration_s: float = 25.0) -> pd.DataFrame:
    """Assemble the observed leader/follower series for one run."""
    group = subset.iloc[int(run.pos_start): int(run.pos_end) + 1].copy()
    group = group[group.time_s.le(group.time_s.iloc[0] + max_duration_s + 1e-9)]
    leader_id = str(run.leader_trajectory_id)
    leader_rows = subset[subset.trajectory_id.eq(leader_id)][["time_s", "y_m", "speed_mps"]].rename(
        columns={"y_m": "leader_y_m", "speed_mps": "leader_speed_mps"}
    )
    merged = group[["time_s", "y_m", "speed_mps", "net_gap_m", "closing_speed_mps", "lane_id"]].merge(
        leader_rows, on="time_s", how="inner", validate="one_to_one"
    )
    if merged.empty:
        raise LeaderReplayError(f"leader_rows_missing:{leader_id}")
    merged = merged.sort_values("time_s").reset_index(drop=True)
    merged["follower_y_m"] = merged.y_m
    merged["follower_speed_mps"] = merged.speed_mps
    # The reported net gap already subtracts the leader's real (unknown) length, so
    # the leader length is inferred from the two observed positions instead of being
    # assumed:
    #   reported_gap = (leader_y - follower_y) - leader_length
    inferred = merged.leader_y_m - merged.follower_y_m - merged.net_gap_m
    leader_length = float(np.median(inferred))
    spread = float(np.max(inferred) - np.min(inferred))
    if not (1.0 <= leader_length <= 20.0):
        raise LeaderReplayError(f"implausible_inferred_leader_length:{leader_length:.3f}")
    if spread > 1.0:
        raise LeaderReplayError(f"unstable_inferred_leader_length:{spread:.3f}")
    merged["leader_length_inferred_m"] = leader_length
    merged["leader_length_inference_spread_m"] = spread
    merged["observed_gap_m"] = merged.leader_y_m - merged.follower_y_m - leader_length
    merged["reported_gap_m"] = merged.net_gap_m
    merged["gap_definition_residual_m"] = merged.observed_gap_m - merged.reported_gap_m
    return merged


def insertion_safe_speed(gap_m: float, leader_speed_mps: float, *, decel: float, tau: float) -> float:
    """Largest insertion speed that satisfies SUMO's Krauss safe-speed check.

    Solves ``v*tau + v^2/(2b) <= gap + v_leader^2/(2b)``. Used only to make the
    observed initial state acceptable at insertion; the observed speed is restored
    under model control in the first replay step.
    """
    limit = max(gap_m, 0.0) + leader_speed_mps ** 2 / (2.0 * decel)
    a = 1.0 / (2.0 * decel)
    discriminant = tau * tau + 4.0 * a * limit
    return float((-tau + math.sqrt(max(discriminant, 0.0))) / (2.0 * a))


def replay_pair(
    observed: pd.DataFrame,
    *,
    run: pd.Series,
    work: Path,
    params: dict[str, object],
    seed: int,
    internal_step_s: float = 0.05,
    record_step_s: float = 0.1,
    clamp_initial_speed: bool = False,
    insertion_checks: str = "native",
    max_insert_wait_s: float = 10.0,
    shared_network: Path | None = None,
) -> dict[str, object]:
    from .stage_0_5_sumo import _ensure_traci_importable, _netconvert_binary, _sumo_binary

    work.mkdir(parents=True, exist_ok=True)
    times = observed.time_s.to_numpy(dtype=float) - float(observed.time_s.iloc[0])
    leader_y = observed.leader_y_m.to_numpy(dtype=float)
    leader_v = observed.leader_speed_mps.to_numpy(dtype=float)
    follower_y = observed.follower_y_m.to_numpy(dtype=float)
    follower_v = observed.follower_speed_mps.to_numpy(dtype=float)
    vehicle_length = float(observed.leader_length_inferred_m.iloc[0])
    params = dict(params)
    params["length"] = vehicle_length
    length = float(max(1200.0, leader_y.max() + 400.0))

    shared = Path(shared_network) if shared_network is not None else None
    if shared is not None and shared.is_file():
        # every pair uses the same 1200 m single-lane edge, so the network is built
        # once and shared; this changes nothing about the model or the recording
        import os as _os
        network = shared
        built = type("R", (), {"returncode": 0, "stderr": ""})()
        network_ref = _os.path.relpath(network.resolve(), work.resolve()).replace("\\", "/")
        length = 1200.0
        _skip_network_build = True
    else:
        _skip_network_build = False
    nodes = work / "nodes.nod.xml"
    edges = work / "edges.edg.xml"
    nodes.write_text(
        f'<nodes><node id="w" x="0" y="0" type="priority"/><node id="e" x="{length:.2f}" y="0" type="priority"/></nodes>',
        encoding="utf-8",
    )
    edges.write_text(
        '<edges><edge id="lane" from="w" to="e" priority="2" numLanes="1" speed="27.78"/></edges>',
        encoding="utf-8",
    )
    if not _skip_network_build:
        network = work / "replay.net.xml"
        built = subprocess.run(
            [_netconvert_binary(), "-n", str(nodes), "-e", str(edges), "-o", str(network), "--no-turnarounds", "true"],
            capture_output=True, text=True, timeout=120,
        )
        if built.returncode != 0:
            raise LeaderReplayError(f"netconvert_failed:{built.stderr[-400:]}")
        network_ref = network.name
    elif shared is not None and not shared.is_file():
        shared.parent.mkdir(parents=True, exist_ok=True)
        built = subprocess.run(
            [_netconvert_binary(), "-n", str(nodes), "-e", str(edges), "-o", str(shared), "--no-turnarounds", "true"],
            capture_output=True, text=True, timeout=120,
        )
        if built.returncode != 0:
            raise LeaderReplayError(f"netconvert_failed:{built.stderr[-400:]}")
        import os as _os
        network = shared
        network_ref = _os.path.relpath(network.resolve(), work.resolve()).replace("\\", "/")

    routes = work / "replay.rou.xml"
    vtype = " ".join(f'{key}="{value}"' for key, value in params.items())
    initial_gap = float(leader_y[0] - follower_y[0] - vehicle_length)
    safe_speed = insertion_safe_speed(
        initial_gap, float(leader_v[0]), decel=float(params["decel"]), tau=float(params["tau"])
    )
    # The observed initial speed is inserted as-is. SUMO's own insertion safety check
    # may reject it; that rejection is reported as a representability finding rather
    # than being masked by clamping, because a clamped initial speed changes the very
    # response being measured.
    depart_speed = float(max(float(follower_v[0]), 0.1))
    if clamp_initial_speed:
        depart_speed = float(max(0.1, min(depart_speed, 0.95 * safe_speed)))
    routes.write_text(
        f'<routes><vType id="cf" {vtype}/><route id="r" edges="lane"/>'
        f'<vehicle id="leader" type="cf" route="r" depart="0" departLane="0" departPos="{leader_y[0]:.3f}" departSpeed="{max(leader_v[0], 0.1):.3f}"/>'
        f'<vehicle id="follower" type="cf" route="r" depart="0" departLane="0" departPos="{follower_y[0]:.3f}" departSpeed="{depart_speed:.3f}"/>'
        "</routes>",
        encoding="utf-8",
    )
    config = work / "replay.sumocfg"
    extra_processing = ""
    if insertion_checks == "none":
        # documented SUMO option: skip the insertion-time safety checks so that the
        # observed initial state can be entered at its observed departure time. It
        # affects insertion only; the vehicle is under normal model control afterwards.
        extra_processing = '<insertion-checks value="none"/>'
    elif insertion_checks != "native":
        raise LeaderReplayError(f"unknown_insertion_checks:{insertion_checks}")
    config.write_text(
        f'<configuration><input><net-file value="{network_ref}"/><route-files value="{routes.name}"/></input>'
        f'<time><begin value="0"/><end value="{times[-1] + 1.0:.2f}"/><step-length value="{internal_step_s}"/></time>'
        '<processing><step-method.ballistic value="true"/><threads value="1"/><time-to-teleport value="-1"/>'
        f'<collision.action value="warn"/>{extra_processing}</processing><seed value="{seed}"/></configuration>',
        encoding="utf-8",
    )

    _ensure_traci_importable()
    import traci

    label = f"replay_{run.trajectory_id[:10]}_{seed}"
    records = {"t": [], "leader_y": [], "leader_target_y": [], "follower_y": [], "follower_v": [], "leader_v": []}
    traci.start(
        [_sumo_binary(), "-c", str(config), "--no-step-log", "true", "--duration-log.statistics", "false"],
        label=label,
    )
    connection = traci.getConnection(label)
    try:
        # SUMO retries a blocked insertion on later steps instead of dropping the
        # vehicle, so the replay waits for the follower and records the delay. The
        # earlier implementation aborted after 0.25 s and therefore mis-reported a
        # delayed insertion as a rejection.
        load_steps = 0
        wait_steps = int(round(max_insert_wait_s / internal_step_s))
        while load_steps < wait_steps and "leader" not in set(connection.vehicle.getIDList()):
            connection.simulationStep()
            load_steps += 1
        if "leader" not in set(connection.vehicle.getIDList()):
            raise LeaderReplayError("leader_never_inserted")
        while load_steps < wait_steps and "follower" not in set(connection.vehicle.getIDList()):
            connection.simulationStep()
            load_steps += 1
        identifiers = set(connection.vehicle.getIDList())
        if "follower" not in identifiers:
            raise LeaderReplayError(
                f"insertion_delayed_beyond_wait:{sorted(identifiers)}:gap={initial_gap:.3f}:safe={safe_speed:.3f}:depart={depart_speed:.3f}"
            )
        insertion_delay_s = float(connection.simulation.getTime()) - float(times[0])
        start_offset = connection.vehicle.getLanePosition("follower") - float(follower_y[0])
        if abs(start_offset) > 1.0:
            raise LeaderReplayError(f"follower_insertion_offset:{start_offset:.3f}")
        clock_offset = float(connection.simulation.getTime())
        steps_per_record = max(1, int(round(record_step_s / internal_step_s)))
        # the delay shifts the follower's phase; the first recorded sample is aligned to
        # the observed sample whose clock matches the follower's own elapsed time
        start_index = int(round(insertion_delay_s / record_step_s))
        for index in range(start_index, len(times)):
            next_index = min(index + 1, len(times) - 1)
            for sub in range(steps_per_record):
                fraction = (sub + 1) / steps_per_record
                target_position = float(leader_y[index] + fraction * (leader_y[next_index] - leader_y[index]))
                target_speed = float(leader_v[index] + fraction * (leader_v[next_index] - leader_v[index]))
                # pre-compensate the motion SUMO applies within the step so that the
                # leader lands on the observed position at the end of the step
                connection.vehicle.moveTo("leader", "lane_0", target_position - max(target_speed, 0.0) * internal_step_s)
                connection.vehicle.setSpeed("leader", max(target_speed, 0.0))
                connection.simulationStep()
            # label each record with the observation clock of the sample it represents,
            # so the simulated and observed series are index-aligned by construction
            records["t"].append(float(times[index]))
            records["leader_y"].append(float(connection.vehicle.getLanePosition("leader")))
            records["leader_target_y"].append(float(leader_y[next_index]))
            records["follower_y"].append(float(connection.vehicle.getLanePosition("follower")))
            records["follower_v"].append(float(connection.vehicle.getSpeed("follower")))
            records["leader_v"].append(float(connection.vehicle.getSpeed("leader")))
    finally:
        connection.close()

    simulated = pd.DataFrame(records)
    simulated["gap_m"] = simulated.leader_y - simulated.follower_y - vehicle_length
    observed = observed.iloc[start_index:].reset_index(drop=True)
    if len(observed) != len(simulated):
        raise LeaderReplayError(f"alignment_mismatch:{len(observed)}:{len(simulated)}")
    if len(simulated) < 2:
        raise LeaderReplayError("replay_produced_no_trajectory")
    return {
        "run_id": int(run.run_id),
        "trajectory_id": str(run.trajectory_id),
        "leader_trajectory_id": str(run.leader_trajectory_id),
        "lane_id": str(run.lane_id),
        "seed": int(seed),
        "tau_s": float(params["tau"]),
        "vehicle_length_m": vehicle_length,
        "leader_length_inference_spread_m": float(observed.leader_length_inference_spread_m.iloc[0]),
        "duration_s": float(simulated.t.iloc[-1]),
        "initial_depart_speed_mps": depart_speed,
        "insertion_delay_s": insertion_delay_s,
        "insertion_checks": insertion_checks,
        "start_index": start_index,
        "insertion_safe_speed_mps": safe_speed,
        "initial_speed_representable": bool(depart_speed <= safe_speed + 1e-9),
        "initial_speed_clamped": bool(clamp_initial_speed and abs(depart_speed - float(follower_v[0])) > 1e-9),
        "initial_speed_offset_mps": float(depart_speed - float(follower_v[0])),
        "observed_initial_speed_mps": float(follower_v[0]),
        "insertion_load_steps": load_steps,
        "clock_offset_s": clock_offset,
        "leader_target_max_abs_deviation_m": float(np.max(np.abs(simulated.leader_y - simulated.leader_target_y))),
        "network_sha256_source": network.as_posix(),
        "config_source": config.as_posix(),
        "observed": observed,
        "simulated": simulated,
    }


def brockfeld_error(observed_gap: np.ndarray, simulated_gap: np.ndarray) -> float:
    """Brockfeld et al. (2004) Eq. 2, expressed in percent."""
    observed_gap = np.asarray(observed_gap, dtype=float)
    simulated_gap = np.asarray(simulated_gap, dtype=float)
    denominator = float(observed_gap.sum())
    if not np.isfinite(denominator) or denominator <= 0:
        raise LeaderReplayError("degenerate_brockfeld_denominator")
    return float(np.abs(simulated_gap - observed_gap).sum() / denominator * 100.0)


def nrmse(observed: np.ndarray, simulated: np.ndarray) -> float:
    """Normalised RMSE as written in Schrader et al. (2024) Eq. 6."""
    observed = np.asarray(observed, dtype=float)
    simulated = np.asarray(simulated, dtype=float)
    denominator = math.sqrt(float(np.mean(observed ** 2)))
    if not np.isfinite(denominator) or denominator <= 0:
        raise LeaderReplayError("degenerate_nrmse_denominator")
    return float(math.sqrt(float(np.mean((observed - simulated) ** 2))) / denominator)


def pair_metrics(record: dict[str, object], *, settle_s: float = 0.0) -> dict[str, object]:
    observed = record["observed"]
    simulated = record["simulated"]
    if settle_s > 0:
        cutoff = float(observed.time_s.iloc[0]) + settle_s
        observed = observed[observed.time_s.ge(cutoff)].reset_index(drop=True)
        simulated = simulated[simulated.t.ge(settle_s - 1e-9)].reset_index(drop=True)
        if len(observed) != len(simulated) or len(observed) < 10:
            raise LeaderReplayError(f"settling_slice_mismatch:{len(observed)}:{len(simulated)}")
    observed_gap = observed.observed_gap_m.to_numpy(dtype=float)
    simulated_gap = simulated.gap_m.to_numpy(dtype=float)
    observed_v = observed.follower_speed_mps.to_numpy(dtype=float)
    simulated_v = simulated.follower_v.to_numpy(dtype=float)
    observed_time = observed.time_s.to_numpy(dtype=float) - float(observed.time_s.iloc[0])
    leader_v_observed = np.gradient(observed.leader_y_m.to_numpy(dtype=float), observed_time)
    leader_v_simulated = np.gradient(simulated.leader_y.to_numpy(dtype=float), simulated.t.to_numpy(dtype=float))
    closing_observed = observed_v - leader_v_observed
    closing_simulated = simulated_v - leader_v_simulated
    headway_observed = np.where(closing_observed > 0, observed_gap / np.where(closing_observed > 0, closing_observed, np.nan), np.nan)
    headway_simulated = np.where(closing_simulated > 0, simulated_gap / np.where(closing_simulated > 0, closing_simulated, np.nan), np.nan)
    from .stage_0_5_d1_measurement import time_gap_values
    observed_gaps = time_gap_values(observed_gap, observed_v, closing_observed, record.get("vehicle_length_m"))
    simulated_gaps = time_gap_values(simulated_gap, simulated_v, closing_simulated, record.get("vehicle_length_m"))
    return {
        "measurement_schema": "explicit-time-gap-v1",
        "legacy_field_replacements": {"time_headway_mean_observed_s": "closing_time_proxy_mean_observed_s", "time_headway_mean_simulated_s": "closing_time_proxy_mean_simulated_s"},
        "legacy_observed_time_gap_definition": "mean(g/max(v_f,0.1)); retained for old stratification consumers only",
        "net_time_gap_mean_observed_s": float(np.nanmean(observed_gaps["net_time_gap_s"])) if np.isfinite(observed_gaps["net_time_gap_s"]).any() else None,
        "front_bumper_time_headway_mean_observed_s": float(np.nanmean(observed_gaps["front_bumper_time_headway_s"])) if np.isfinite(observed_gaps["front_bumper_time_headway_s"]).any() else None,
        "net_time_gap_mean_simulated_s": float(np.nanmean(simulated_gaps["net_time_gap_s"])) if np.isfinite(simulated_gaps["net_time_gap_s"]).any() else None,
        "run_id": record["run_id"],
        "trajectory_id": record["trajectory_id"],
        "lane_id": record["lane_id"],
        "tau_s": record["tau_s"],
        "seed": record["seed"],
        "duration_s": record["duration_s"],
        "states": int(len(observed_gap)),
        "brockfeld_gap_error_pct": brockfeld_error(observed_gap, simulated_gap),
        "nrmse_gap": nrmse(observed_gap, simulated_gap),
        "nrmse_speed": nrmse(observed_v, simulated_v),
        "gap_bias_m": float(np.mean(simulated_gap - observed_gap)),
        "gap_mae_m": float(np.mean(np.abs(simulated_gap - observed_gap))),
        "speed_bias_mps": float(np.mean(simulated_v - observed_v)),
        "speed_mae_mps": float(np.mean(np.abs(simulated_v - observed_v))),
        "closing_mean_observed_mps": float(np.nanmean(closing_observed)),
        "closing_mean_simulated_mps": float(np.nanmean(closing_simulated)),
        "closing_negative_share_observed": float(np.nanmean(closing_observed < 0)),
        "closing_negative_share_simulated": float(np.nanmean(closing_simulated < 0)),
        "observed_time_gap_mean_s": float(np.mean(observed_gap / np.maximum(observed_v, 0.1))),
        "observed_speed_mean_mps": float(np.mean(observed_v)),
        "closing_time_proxy_mean_observed_s": float(np.nanmean(headway_observed)) if np.isfinite(headway_observed).any() else None,
        "closing_time_proxy_mean_simulated_s": float(np.nanmean(headway_simulated)) if np.isfinite(headway_simulated).any() else None,
        "leader_target_max_abs_deviation_m": record["leader_target_max_abs_deviation_m"],
        "gap_definition_residual_abs_max_m": float(np.max(np.abs(observed.gap_definition_residual_m))),
        "vehicle_length_m": record["vehicle_length_m"],
        "leader_length_inference_spread_m": record["leader_length_inference_spread_m"],
        "settle_s_excluded": float(settle_s),
        "nrmse_acceleration": None,
        "nrmse_acceleration_reason": "withheld: the observed acceleration is differenced and its noise handling is not validated here",
    }


def summarise(rows: list[dict[str, object]], *, resamples: int = 2000, seed: int = 20261020) -> dict[str, object]:
    """Per-configuration summary and paired differences across the same pairs."""
    frame = pd.DataFrame(rows)
    if frame.empty:
        return {"configs": {}, "note": "no replayed pair produced metrics"}
    summary: dict[str, object] = {"configs": {}, "cluster_unit": "leader-follower trajectory pair"}
    metrics = ("brockfeld_gap_error_pct", "nrmse_gap", "nrmse_speed", "gap_bias_m", "gap_mae_m", "speed_bias_mps", "speed_mae_mps", "observed_time_gap_mean_s")
    for tau, group in frame.groupby("tau_s", sort=True):
        entry: dict[str, object] = {"pairs": int(len(group))}
        for metric in metrics:
            values = group[metric].to_numpy(dtype=float)
            entry[metric] = {
                "mean": float(values.mean()),
                "median": float(np.median(values)),
                "min": float(values.min()),
                "max": float(values.max()),
            }
        summary["configs"][f"{tau:.2f}"] = entry
    taus = sorted(frame.tau_s.unique().tolist())
    if len(taus) == 2:
        frame = frame.copy()
        key_columns = [column for column in ("window", "pair_index", "trajectory_id") if column in frame.columns]
        frame["_pair_key"] = frame[key_columns].astype(str).agg("|".join, axis=1)
        left = frame[frame.tau_s == taus[0]].drop_duplicates("_pair_key").set_index("_pair_key")
        right = frame[frame.tau_s == taus[1]].drop_duplicates("_pair_key").set_index("_pair_key")
        common = sorted(set(left.index) & set(right.index))
        paired: dict[str, object] = {"paired_pairs": len(common), "baseline_tau": taus[0], "candidate_tau": taus[1]}
        generator = np.random.default_rng(seed)
        for metric in metrics:
            if not common:
                continue
            differences = right.loc[common, metric].to_numpy(dtype=float) - left.loc[common, metric].to_numpy(dtype=float)
            draws = np.array([generator.choice(differences, len(differences), replace=True).mean() for _ in range(resamples)])
            paired[metric] = {
                "mean_difference": float(np.mean(differences)),
                "ci95": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))],
                "improved_pairs": int((differences < 0).sum()),
                "worsened_pairs": int((differences > 0).sum()),
                "direction": "lower_is_better",
            }
        paired["interval_note"] = (
            "paired bootstrap over leader-follower pairs, within-source sampling sensitivity only; "
            "this is not a science tolerance and not a validation result"
        )
        summary["paired_difference"] = paired
    return summary


# ---------------------------------------------------------------------------
# 2026-10-20 method expansion: configuration catalogue, local/long-run split,
# response-lag diagnostics and stratified selection.
# ---------------------------------------------------------------------------
KRAUSS_BASELINE_NAME = "K_tau1.0"

#: Bounded, single-factor diagnostic catalogue. Only the listed attributes change
#: relative to BASELINE_FOLLOWING; everything else stays frozen. ``status`` records
#: whether the value has an observational anchor or is an engineering exploration
#: range, and ``source`` records why the value is on the list at all.
CONFIGURATIONS: dict[str, dict[str, object]] = {
    "K_tau1.0": {"model": "Krauss", "overrides": {}, "status": "frozen baseline",
                 "source": "sealed Stage 0.5 candidate vType"},
    "K_tau1.3": {"model": "Krauss", "overrides": {"tau": 1.3}, "status": "engineering exploration",
                 "source": "lower bracket of the macro-implied 1.53-1.63 s equivalent"},
    "K_tau1.6": {"model": "Krauss", "overrides": {"tau": 1.6}, "status": "engineering exploration",
                 "source": "previously declared candidate from the macro-implied equivalent"},
    "K_tau2.0": {"model": "Krauss", "overrides": {"tau": 2.0}, "status": "engineering exploration",
                 "source": "upper bracket of the same equivalent"},
    "K_tau1.0_minGap1.0": {"model": "Krauss", "overrides": {"minGap": 1.0}, "status": "engineering exploration",
                           "source": "one-factor minGap profile; the real standstill gap is not identifiable"},
    "K_tau1.0_minGap5.0": {"model": "Krauss", "overrides": {"minGap": 5.0}, "status": "engineering exploration",
                           "source": "one-factor minGap profile; the real standstill gap is not identifiable"},
    "K_tau1.0_sigma0.0": {"model": "Krauss", "overrides": {"sigma": 0.0}, "status": "engineering exploration",
                          "source": "removes the dawdling term to bound randomness without removing the model"},
    "IDM_T1.0": {"model": "IDM", "overrides": {"tau": 1.0, "delta": 4.0}, "status": "model comparison",
                 "source": "IDM desired time headway T; an equal numeric value to Krauss tau is NOT an equivalence claim"},
    "IDM_T1.6": {"model": "IDM", "overrides": {"tau": 1.6, "delta": 4.0}, "status": "model comparison",
                 "source": "IDM at the same numeric T as the falsified Krauss candidate"},
}

FROZEN_ATTRIBUTES = ("maxSpeed", "speedFactor", "speedDev", "accel", "decel", "apparentDecel",
                     "emergencyDecel", "actionStepLength", "sigmaStep", "laneChangeModel")

LOCAL_WINDOW_S = 5.0
LONG_RUN_START_S = 10.0
RESPONSE_HORIZON_S = 5.0
BRAKE_ACCEL_THRESHOLD = -0.5
MIN_EPISODE_S = 0.5


def build_vtype(config_name: str) -> dict[str, object]:
    """Return the vType attribute dict for one catalogue entry."""
    if config_name not in CONFIGURATIONS:
        raise LeaderReplayError(f"unknown_configuration:{config_name}")
    entry = CONFIGURATIONS[config_name]
    params = dict(BASELINE_FOLLOWING)
    params["carFollowModel"] = entry["model"]
    for key, value in dict(entry["overrides"]).items():
        params[key] = value
    return params


def assert_single_factor(config_name: str) -> dict[str, object]:
    """Fail-closed check that a catalogue entry changes at most one frozen attribute.

    ``delta`` is allowed alongside ``tau`` only for the IDM entries, where ``delta``
    is a model-structure attribute with no Krauss counterpart rather than a tuning
    factor of the frozen model.
    """
    if config_name == KRAUSS_BASELINE_NAME:
        return {"changed": [], "reason": "frozen baseline"}
    params = build_vtype(config_name)
    changed = [key for key in FROZEN_ATTRIBUTES + ("tau", "minGap", "sigma")
               if key in params and params[key] != BASELINE_FOLLOWING[key]]
    if len(changed) > 1 and not (params["carFollowModel"] == "IDM" and set(changed) <= {"tau", "delta"}):
        raise LeaderReplayError(f"multi_factor_configuration:{config_name}:{changed}")
    return {"changed": changed}


def slice_record(record: dict[str, object], *, start_s: float, end_s: float | None) -> dict[str, object]:
    """Return a record restricted to a clock sub-window of the aligned series."""
    observed = record["observed"]
    simulated = record["simulated"]
    mask_o = observed.time_s.ge(float(observed.time_s.iloc[0]) + start_s)
    if end_s is not None:
        mask_o &= observed.time_s.le(float(observed.time_s.iloc[0]) + end_s)
    observed = observed[mask_o].reset_index(drop=True)
    mask_s = simulated.t.ge(start_s - 1e-9)
    if end_s is not None:
        mask_s &= simulated.t.le(end_s + 1e-9)
    simulated = simulated[mask_s].reset_index(drop=True)
    if len(observed) != len(simulated) or len(observed) < 5:
        raise LeaderReplayError(f"slice_alignment:{len(observed)}:{len(simulated)}")
    sliced = dict(record)
    sliced["observed"] = observed
    sliced["simulated"] = simulated
    return sliced


def brake_episodes(acceleration, times, *, threshold: float = BRAKE_ACCEL_THRESHOLD,
                   min_duration_s: float = MIN_EPISODE_S) -> list[dict[str, float]]:
    """Contiguous episodes where a derived acceleration stays below a threshold."""
    below = np.asarray(acceleration, dtype=float) < threshold
    episodes: list[dict[str, float]] = []
    start = None
    for index, flag in enumerate(below):
        if flag and start is None:
            start = index
        elif not flag and start is not None:
            if times[index - 1] - times[start] >= min_duration_s:
                episodes.append({"start_index": int(start), "end_index": int(index - 1),
                                 "start_s": float(times[start]), "end_s": float(times[index - 1])})
            start = None
    if start is not None and times[-1] - times[start] >= min_duration_s:
        episodes.append({"start_index": int(start), "end_index": int(len(times) - 1),
                         "start_s": float(times[start]), "end_s": float(times[-1])})
    return episodes


def response_metrics(record: dict[str, object]) -> dict[str, object]:
    """Perturbation-propagation comparison between the observed and simulated pair.

    Project-defined definition (motivated by the oscillation-propagation literature
    but not taken from it): leader braking episodes are contiguous intervals where
    the derived leader acceleration stays below -0.5 m/s^2 for at least 0.5 s. For
    every episode the follower's speed drop within a fixed 5 s horizon and the lag
    between the leader's speed minimum and the follower's speed minimum are reported.
    """
    observed = record["observed"]
    simulated = record["simulated"]
    out: dict[str, object] = {"episode_definition": "derived leader accel < -0.5 m/s^2 for >= 0.5 s",
                              "horizon_s": RESPONSE_HORIZON_S}
    series = []
    for label, frame, time_column, leader_column, follower_column in (
        ("observed", observed, "time_s", "leader_y_m", "follower_speed_mps"),
        ("simulated", simulated, "t", "leader_y", "follower_v"),
    ):
        times = frame[time_column].to_numpy(dtype=float) - float(frame[time_column].iloc[0])
        leader_speed = np.gradient(frame[leader_column].to_numpy(dtype=float), times)
        leader_accel = np.gradient(leader_speed, times)
        follower_speed = frame[follower_column].to_numpy(dtype=float)
        episodes = brake_episodes(leader_accel, times)
        drops, lags, minima = [], [], []
        for episode in episodes:
            segment = slice(episode["start_index"], min(episode["end_index"] + 1, len(times)))
            segment_speed = leader_speed[segment]
            minima.append(float(segment_speed.min()))
            leader_min_index = episode["start_index"] + int(np.argmin(segment_speed))
            leader_min_time = float(times[leader_min_index])
            window = (times >= episode["start_s"]) & (times <= episode["start_s"] + RESPONSE_HORIZON_S)
            if window.sum() < 3:
                continue
            follower_segment = follower_speed[window]
            follower_times = times[window]
            follower_base = float(follower_speed[episode["start_index"]])
            drops.append(float(follower_base - follower_segment.min()))
            lags.append(float(follower_times[int(np.argmin(follower_segment))] - leader_min_time))
        series.append({
            "series": label,
            "episodes": len(episodes),
            "events_used": len(drops),
            "mean_follower_drop_mps": float(np.mean(drops)) if drops else None,
            "max_follower_drop_mps": float(np.max(drops)) if drops else None,
            "mean_lag_s": float(np.mean(lags)) if lags else None,
            "leader_min_speed_mean_mps": float(np.mean(minima)) if minima else None,
        })
    out["series"] = series
    observed_entry, simulated_entry = series
    out["amplitude_ratio_sim_over_obs"] = (
        simulated_entry["mean_follower_drop_mps"] / observed_entry["mean_follower_drop_mps"]
        if observed_entry["mean_follower_drop_mps"] else None
    )
    out["lag_difference_s"] = (
        simulated_entry["mean_lag_s"] - observed_entry["mean_lag_s"]
        if observed_entry["mean_lag_s"] is not None and simulated_entry["mean_lag_s"] is not None else None
    )
    return out


def stratified_selection(runs: pd.DataFrame, *, per_window: int,
                         strata=(0.0, 1.0, 1.5, 2.5, 1e9)) -> pd.DataFrame:
    """Deterministic selection covering the observed time-gap range.

    The observed gap-over-speed of each run is binned with the declared strata and
    runs are taken round-robin across bins by duration. This avoids the earlier
    failure mode of selecting only the longest pairs.
    """
    if runs.empty:
        return runs
    frame = runs.copy()
    frame["observed_time_gap_s"] = frame.gap_mean_m / frame.speed_mean_mps.clip(lower=0.1)
    frame["stratum"] = pd.cut(frame.observed_time_gap_s, bins=list(strata), right=False,
                              labels=[f"{strata[i]}-{strata[i + 1]}" for i in range(len(strata) - 1)])
    frame = frame[frame.stratum.notna()]
    frame = frame.sort_values(["stratum", "duration_s", "trajectory_id"], ascending=[True, False, True])
    picked: list[dict] = []
    picked_ids: set[int] = set()
    guard = 0
    while len(picked) < per_window and guard < 1000:
        added = False
        for stratum in frame.stratum.cat.categories:
            candidates = frame[(frame.stratum == stratum) & (~frame.run_id.isin(picked_ids))]
            if candidates.empty:
                continue
            row = candidates.iloc[0]
            picked.append(row.to_dict())
            picked_ids.add(int(row.run_id))
            added = True
            if len(picked) >= per_window:
                break
        if not added:
            break
        guard += 1
    return pd.DataFrame(picked).reset_index(drop=True)
