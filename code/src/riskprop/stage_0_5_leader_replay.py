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
    network = work / "replay.net.xml"
    built = subprocess.run(
        [_netconvert_binary(), "-n", str(nodes), "-e", str(edges), "-o", str(network), "--no-turnarounds", "true"],
        capture_output=True, text=True, timeout=120,
    )
    if built.returncode != 0:
        raise LeaderReplayError(f"netconvert_failed:{built.stderr[-400:]}")

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
    config.write_text(
        f'<configuration><input><net-file value="{network.name}"/><route-files value="{routes.name}"/></input>'
        f'<time><begin value="0"/><end value="{times[-1] + 1.0:.2f}"/><step-length value="{internal_step_s}"/></time>'
        '<processing><step-method.ballistic value="true"/><threads value="1"/><time-to-teleport value="-1"/>'
        f'<collision.action value="warn"/></processing><seed value="{seed}"/></configuration>',
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
        load_steps = 0
        while load_steps < 5 and not {"leader", "follower"} <= set(connection.vehicle.getIDList()):
            connection.simulationStep()
            load_steps += 1
        identifiers = set(connection.vehicle.getIDList())
        if not {"leader", "follower"} <= identifiers:
            raise LeaderReplayError(
                f"insertion_failed:{sorted(identifiers)}:gap={initial_gap:.3f}:safe={safe_speed:.3f}:depart={depart_speed:.3f}"
            )
        start_offset = connection.vehicle.getLanePosition("follower") - float(follower_y[0])
        if abs(start_offset) > 1.0:
            raise LeaderReplayError(f"follower_insertion_offset:{start_offset:.3f}")
        clock_offset = float(connection.simulation.getTime())
        steps_per_record = max(1, int(round(record_step_s / internal_step_s)))
        for index in range(len(times)):
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
    return {
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
        "time_headway_mean_observed_s": float(np.nanmean(headway_observed)) if np.isfinite(headway_observed).any() else None,
        "time_headway_mean_simulated_s": float(np.nanmean(headway_simulated)) if np.isfinite(headway_simulated).any() else None,
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
