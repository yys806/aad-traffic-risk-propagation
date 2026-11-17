"""Path 3: isolated two-arm experiment with a gap-sensitive risk measure and a
headway-based (rather than speed-cap) response.

Why this exists (see docs/DECISION_path3_20261116.md and EXPERIMENT_eidm_calibration):

1. The simulator cannot reproduce near-crashes. SUMO's EIDM disables perception error and
   reaction time below 3 m gap (`EST_REAC_THRESHOLD`), and real near-conflicts in our data
   occur at 0.3-4.6 m. So any risk measure that only fires on genuine near-crashes is pinned
   at its floor and cannot discriminate between conditions.

2. The previous risk measure fired only when the follower was actively closing on its leader
   (`closing <= 1e-6 -> 0`). In steady car-following nobody is closing, so the mean risk
   collapsed to 9.3e-5 and the two arms were indistinguishable for reasons that had nothing
   to do with the treatment.

Path 3 changes three things, and nothing else:

  (a) RISK MEASURE. TTC is computed against a leader that brakes at a fixed deceleration,
      which is always defined and responds directly to the gap:
            gap = (v_f - v_l) t + 0.5 b_l t^2   ->   t = [-(v_f - v_l) + sqrt((v_f-v_l)^2 + 2 b_l gap)] / b_l
      The paper's mapping rho = exp(-TTC / tau) is kept unchanged; only how TTC is defined
      changes. Rationale: the quantity a remote risk message is supposed to change is the
      following gap, so the measure must be a function of the gap.

  (b) RESPONSE. The controller increases the car-following time headway (TraCI setTau)
      instead of capping speed. Capping speed uniformly does not open gaps, and inside a
      platoon it compresses them, which is why the earlier run moved regional risk in the
      wrong direction (+0.0134).

  (c) CONTENT MATTERS. The size of the headway increase is graded by the payload's own
      fields: risk level, the vehicle's depth into the affected zone, and the remaining
      validity fraction. A content-blind blanket action cannot reproduce it.

Arms, and what each contrast identifies:

  opn0  no response at all.
  sham  content-blind blanket headway increase on every in-region vehicle, same schedule.
        Same magnitude, no message content consulted.
  opn1  content-graded headway increase driven by the adopted message.

  D(opn1 - opn0)   total effect of the message-triggered response
  D(sham - opn0)   effect of an equally sized but content-blind action
  D(opn1 - sham)   the part attributable to message content  <- the information effect

Status: engineering pilot. Not a formal Stage I run, not Protocol-Locked.

Usage:
  python code/scripts/run_stage1_path3.py --seeds 1 --risk-mode braking --response headway
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
sys.path.insert(0, str(ROOT / "code" / "scripts"))

import run_stage1_isolated_two_arm as base  # isolation setup, already RNG-verified
from riskprop.message_driven_longitudinal_controller import (  # noqa: E402
    LocalState, Message, RiskPayload, byte_hash, validate_message,
    PAYLOAD_SCHEMA, PARAMETER_STATUS,
)
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

SUMO = "sumo"
STEP = base.STEP
WARMUP = base.WARMUP
END = base.END
TGT_REGION = base.TGT_REGION
TTC_TAU = base.TTC_TAU

# Leader braking used in the risk measure. 4.5 m/s^2 is the vType's decel, i.e. the
# capability the simulated vehicles actually have.
LEADER_BRAKE = 4.5

NATIVE_TAU = 0.6            # vType tau in routes_xml()
RISK_TAU_DELTA = {"LOW": 0.3, "MEDIUM": 0.7, "HIGH": 1.2}   # seconds of extra headway
TAU_CAP = 3.0


def ttc_braking(gap: float, v_f: float, v_l: float, b: float = LEADER_BRAKE) -> float:
    """Time to collision if the follower holds speed and the leader brakes at `b`.

    Always defined and positive, unlike the instantaneous closing-speed TTC which is
    undefined whenever the follower is not closing.
    """
    dv = v_f - v_l
    disc = dv * dv + 2.0 * b * gap
    if disc <= 0.0:
        return 0.0
    return max(0.0, (-dv + math.sqrt(disc)) / b)


def ttc_instant(gap: float, v_f: float, v_l: float) -> float | None:
    """Old measure, kept for comparison: undefined (None) unless the follower is closing."""
    closing = v_f - v_l
    if closing <= 1e-6:
        return None
    return gap / closing


def rho_from_ttc(ttc: float) -> float:
    return math.exp(-ttc / TTC_TAU)


def headway_delta(risk_level: str, x: float, now: float,
                  valid_from: float, valid_until: float,
                  content_graded: bool) -> float:
    """Extra safe time headway a vehicle takes on, in seconds.

    content_graded=True uses the payload's own content: the zone geometry and the remaining
    validity. content_graded=False is the blanket sham action: the same peak magnitude for
    every in-region vehicle, independent of position and of message fields.
    """
    peak = RISK_TAU_DELTA[risk_level]
    if not content_graded:
        return peak
    lo, hi = TGT_REGION
    centre, half = 0.5 * (lo + hi), 0.5 * (hi - lo)
    depth = 1.0 - abs(x - centre) / half           # 1 at zone centre, 0 at either end
    depth = min(1.0, max(0.2, depth))
    span = max(1e-6, valid_until - valid_from)
    validity = min(1.0, max(0.1, (valid_until - now) / span))
    return peak * depth * validity


@dataclass
class ArmResult:
    arm: str
    seed: int
    event_time_s: float | None
    risk_meantime: float | None      # vehicle-time normalised
    risk_roster: float | None        # fixed-roster normalised (old definition)
    exposure_veh_s: float
    n_in_region_mean: float | None
    region_speed_mean: float | None
    n_adopted: int
    n_applied: int
    lifecycle: list
    tau_mean: float | None = None   # mean tau over in-region vehicles, averaged over steps
    tau_p90: float | None = None
    n_measured_mean: float | None = None   # vehicles per step entering the risk average
    n_no_leader_mean: float | None = None  # in-region vehicles excluded for lack of a leader


def run_arm(tmp: Path, seed: int, arm: str, risk_mode: str, response: str,
            sham_delta: float = RISK_TAU_DELTA["HIGH"]) -> ArmResult:
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "net.net.xml").write_text(base.net_xml(), encoding="utf-8")
    (tmp / "routes.rou.xml").write_text(base.routes_xml(), encoding="utf-8")

    opn = 1 if arm == "opn1" else 0
    sham = arm == "sham"
    cfg = tmp / f"run_{arm}.sumocfg"
    cfg.write_text(
        f"""<configuration>
    <input><net-file value="net.net.xml"/><route-files value="routes.rou.xml"/></input>
    <time><begin value="0"/><end value="{END}"/><step-length value="{STEP}"/></time>
    <processing><time-to-teleport value="-1"/><no-step-log value="true"/></processing>
    <random_number><seed value="{seed}"/></random_number>
</configuration>""", encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(cfg), "--no-step-log", "true", "--collision.action", "warn"])
    steps = int(round(END / STEP))
    tgt_ids = [f"T{i}" for i in range(base.cohort_size())]

    lifecycle: list[dict] = []
    adopted_by: set[str] = set()
    applied_by: set[str] = set()
    adopted_msg: dict[str, tuple[Message, RiskPayload]] = {}
    sham_done = False

    event_time: float | None = None
    src_speed0 = None

    roster: tuple[str, ...] | None = None
    tau_applied_samples: list[float] = []     # mean tau actually set, per step
    tau_native_samples: list[float] = []      # mean tau of in-region vehicles, per step
    risk_roster_samples: list[float] = []
    risk_meantime_sum = 0.0
    exposure_steps = 0
    n_measured_samples: list[float] = []      # how many vehicles had a usable leader
    n_no_leader_samples: list[float] = []      # in-region vehicles with no leader / bad gap
    n_in_region_samples: list[float] = []
    region_speed_samples: list[float] = []

    try:
        for k in range(steps):
            now = k * STEP
            traci.simulationStep()
            present = set(traci.vehicle.getIDList())

            # ---- source event, anchored to an observed deceleration, not a planned time
            if "S0" in present:
                s_spd = traci.vehicle.getSpeed("S0")
                if src_speed0 is None:
                    src_speed0 = s_spd
                if event_time is None and src_speed0 is not None and s_spd < src_speed0 - 1.0:
                    event_time = now
                    lifecycle.append({"phase": "source_event_confirmed", "t": round(now, 3),
                                      "source_id": "S0", "speed_mps": round(s_spd, 3)})

            in_region = []
            for v in tgt_ids:
                if v not in present:
                    continue
                x = traci.vehicle.getLanePosition(v)
                sp = traci.vehicle.getSpeed(v)
                if TGT_REGION[0] <= x < TGT_REGION[1]:
                    in_region.append((v, x, sp))

            if roster is None and now >= WARMUP:
                roster = tuple(sorted(v for v, _, _ in in_region))
                lifecycle.append({"phase": "roster_locked", "t": round(now, 3),
                                  "n_vehicles": len(roster)})
            if roster is None:
                continue

            # ---- record the actual headway state so the two arms can be compared on the
            # SIZE of the action, not just its effect (a smaller action producing a larger
            # effect is a content-targeting claim and must be evidenced, not assumed)
            if in_region:
                tau_now = [float(traci.vehicle.getTau(v)) for v, _, _ in in_region]
                tau_native_samples.append(float(np.mean(tau_now)))

            # ---- risk over EVERY vehicle currently in the region.
            # The earlier version measured risk only over the roster locked at t=WARMUP while
            # the treatment was applied to whoever was in the region at each step. That left
            # 27-29 treated vehicles per run outside the risk measurement entirely, which
            # biases the effect downward and makes the reported coverage meaningless.
            # Measuring over in_region puts the treated set and the measured set in one-to-one
            # correspondence. The fixed-roster figure is still computed, from the same
            # per-vehicle values, so the old definition stays comparable.
            per_veh: dict[str, float] = {}
            n_no_leader = 0
            for v, _x_v, _sp_v in in_region:
                if v not in present:
                    continue
                sp = traci.vehicle.getSpeed(v)
                lead = traci.vehicle.getLeader(v, 200.0)
                if not lead:
                    n_no_leader += 1
                    continue
                lid, gap = lead
                if gap <= 0 or lid not in present:
                    n_no_leader += 1
                    continue
                lsp = traci.vehicle.getSpeed(lid)
                if risk_mode == "braking":
                    per_veh[v] = rho_from_ttc(ttc_braking(gap, sp, lsp))
                else:
                    t = ttc_instant(gap, sp, lsp)
                    per_veh[v] = 0.0 if t is None else rho_from_ttc(t)

            # vehicle-time normalisation (D2 decision): mean over vehicles actually measured,
            # then averaged across steps. Denominator = measurable in-region vehicle-steps.
            if per_veh:
                risk_meantime_sum += float(np.mean(list(per_veh.values())))
                exposure_steps += 1
                n_measured_samples.append(float(len(per_veh)))
            # fixed-roster normalisation (old definition, kept for comparison):
            # roster members outside the region or without a leader contribute 0.
            risk_roster_samples.append(
                float(sum(per_veh.get(v, 0.0) for v in roster) / len(roster))
                if roster else 0.0)
            n_no_leader_samples.append(float(n_no_leader))
            n_in_region_samples.append(float(len(in_region)))
            if in_region:
                region_speed_samples.append(float(np.mean([sp for _, _, sp in in_region])))

            # ---- sham: content-blind blanket headway increase, same schedule
            if sham and event_time is not None and response == "headway":
                if not sham_done:
                    sham_done = True
                    lifecycle.append({"phase": "sham_started", "t": round(now, 3),
                                      "note": f"blanket headway increase delta={sham_delta}, "
                                              f"no message content"})
                for v, x, sp in in_region:
                    try:
                        # Content-blind blanket increase. delta is either the HIGH peak
                        # (unmatched dose, tests "more action vs graded action") or a
                        # constant matched to the message arm's mean dose, which is the
                        # only version that isolates content from dose.
                        delta = sham_delta
                        traci.vehicle.setTau(v, min(TAU_CAP, NATIVE_TAU + delta))
                        applied_by.add(v)
                    except Exception as exc:  # noqa: BLE001 - record, never swallow
                        lifecycle.append({"phase": "sham_error", "t": round(now, 3),
                                          "vehicle_id": v, "error": f"{type(exc).__name__}: {exc}"})

            # ---- opn1: message generated, delivered, validated, adopted, applied
            if opn == 1 and event_time is not None:
                for v, x, sp in in_region:
                    lead = traci.vehicle.getLeader(v, 200.0)
                    lid, gap = (lead[0], float(lead[1])) if lead else (None, None)
                    lsp = (traci.vehicle.getSpeed(lid)
                           if lid is not None and lid in present else None)
                    pos = traci.vehicle.getPosition(v)
                    try:
                        state = LocalState(
                            vehicle_id=v, vehicle_incarnation_id=f"{v}@0",
                            simulation_time_s=now, simulation_step=k,
                            edge_id="tgt", lane_id="tgt_0", lane_position_m=x,
                            position_xy_m=(float(pos[0]), float(pos[1])),
                            acceleration_mps2=float(traci.vehicle.getAcceleration(v)),
                            speed_mps=sp, original_max_speed_mps=30.0,
                            lane_max_speed_mps=30.0,
                            leader_id=lid, leader_speed_mps=lsp,
                            net_gap_m=(max(0.0, gap) if gap is not None else None),
                        )
                        if v not in adopted_by:
                            payload = RiskPayload(
                                payload_schema_version=PAYLOAD_SCHEMA,
                                parameter_status=PARAMETER_STATUS,
                                source_event_id="evt-S0-01",
                                event_type="SYNTHETIC_REMOTE_RISK",
                                risk_level="HIGH",
                                affected_edge_id="tgt",
                                lane_position_min_m=TGT_REGION[0],
                                lane_position_max_m=TGT_REGION[1],
                                target_vehicle_ids=(v,),
                                generated_time=round(event_time, 3),
                                valid_from=round(event_time, 3),
                                valid_until=round(event_time + 45.0, 3),
                            )
                            raw = payload.to_bytes()
                            msg = Message(message_id=f"msg-{v}-01", sender_id="SRC-EDGE",
                                          receiver_id=v, source_event_id="evt-S0-01",
                                          raw_payload=raw, payload_hash=byte_hash(raw))
                            lifecycle.append({"phase": "message_generated", "t": round(now, 3),
                                              "vehicle_id": v, "message_id": msg.message_id})
                            check = validate_message(msg, state)
                            lifecycle.append({"phase": "message_validation", "t": round(now, 3),
                                              "vehicle_id": v, "status": check.status})
                            if check.status != "VALID":
                                continue
                            lifecycle.append({"phase": "message_adopted", "t": round(now, 3),
                                              "vehicle_id": v, "message_id": msg.message_id})
                            adopted_msg[v] = (msg, payload)
                            adopted_by.add(v)
                        _msg, payload = adopted_msg[v]
                        delta = headway_delta(payload.risk_level, x, now,
                                              payload.valid_from, payload.valid_until,
                                              content_graded=True)
                        traci.vehicle.setTau(v, min(TAU_CAP, NATIVE_TAU + delta))
                        applied_by.add(v)
                    except Exception as exc:  # noqa: BLE001
                        lifecycle.append({"phase": "policy_error", "t": round(now, 3),
                                          "vehicle_id": v, "error": f"{type(exc).__name__}: {exc}"})
    finally:
        traci.close()

    exposure_veh_s = exposure_steps * STEP * (len(roster) if roster else 0)
    return ArmResult(
        arm=arm, seed=seed, event_time_s=event_time,
        risk_meantime=(risk_meantime_sum / exposure_steps) if exposure_steps else None,
        risk_roster=(float(np.mean(risk_roster_samples)) if risk_roster_samples else None),
        exposure_veh_s=round(exposure_veh_s, 3),
        n_in_region_mean=(float(np.mean(n_in_region_samples)) if n_in_region_samples else None),
        region_speed_mean=(float(np.mean(region_speed_samples)) if region_speed_samples else None),
        n_adopted=len(adopted_by), n_applied=len(applied_by), lifecycle=lifecycle,
        tau_mean=(float(np.mean(tau_native_samples)) if tau_native_samples else None),
        tau_p90=(float(np.percentile(tau_native_samples, 90)) if tau_native_samples else None),
        n_measured_mean=(float(np.mean(n_measured_samples)) if n_measured_samples else None),
        n_no_leader_mean=(float(np.mean(n_no_leader_samples)) if n_no_leader_samples else None),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--risk-mode", choices=["braking", "instant"], default="braking")
    ap.add_argument("--response", choices=["headway", "none"], default="headway")
    ap.add_argument("--sham-delta", type=float, default=RISK_TAU_DELTA["HIGH"],
                    help="constant headway increase (s) for the content-blind sham arm; "
                         "set it to the message arm's mean dose to isolate content from dose")
    ap.add_argument("--out", default="code/outputs/analysis/stage1_path3_20261116")
    args = ap.parse_args()

    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)

    results: dict[str, dict[str, ArmResult]] = {}
    for s in range(args.seeds):
        seed = 20261116 + s
        arms = {}
        for arm in ("opn0", "sham", "opn1"):
            scratch = outdir / f"_scratch_{seed}_{arm}"
            arms[arm] = run_arm(scratch, seed, arm, args.risk_mode, args.response,
                                sham_delta=args.sham_delta)
            r = arms[arm]
            print(f"seed={seed} arm={arm:<5} event_t={r.event_time_s} "
                  f"risk_meantime={r.risk_meantime} risk_roster={r.risk_roster} "
                  f"exposure={r.exposure_veh_s} adopted={r.n_adopted} applied={r.n_applied} "
                  f"tau_mean={r.tau_mean} tau_p90={r.tau_p90} "
                  f"measured={r.n_measured_mean} no_leader={r.n_no_leader_mean}")
        results[str(seed)] = arms

    print("\n--- contrasts (vehicle-time normalised) ---")
    summary = {}
    for seed, arms in results.items():
        o0 = arms["opn0"].risk_meantime
        sh = arms["sham"].risk_meantime
        o1 = arms["opn1"].risk_meantime
        if None in (o0, sh, o1):
            print(f"seed={seed}: incomplete, skipped")
            continue
        row = {"opn0": o0, "sham": sh, "opn1": o1,
               "d_opn1_opn0": o1 - o0, "d_sham_opn0": sh - o0, "d_opn1_sham": o1 - sh,
               "rel_opn1_opn0": (o1 - o0) / o0 if o0 else None,
               "rel_opn1_sham": (o1 - sh) / sh if sh else None}
        summary[seed] = row
        print(f"seed={seed}  opn0={o0:.6g}  sham={sh:.6g}  opn1={o1:.6g}")
        print(f"    Δ(opn1-opn0) = {row['d_opn1_opn0']:+.6g}   "
              f"({row['rel_opn1_opn0']:+.2%} vs opn0)")
        print(f"    Δ(sham-opn0) = {row['d_sham_opn0']:+.6g}   <- 内容无关的整体响应")
        print(f"    Δ(opn1-sham) = {row['d_opn1_sham']:+.6g}   <- 消息内容本身的效应")
        if row["rel_opn1_sham"] is not None:
            print(f"    相对 sham 变化 {row['rel_opn1_sham']:+.2%}")

    payload = {
        "config": {"seeds": args.seeds, "risk_mode": args.risk_mode,
                   "response": args.response, "leader_brake_mps2": LEADER_BRAKE,
                   "native_tau_s": NATIVE_TAU, "tau_cap_s": TAU_CAP,
                   "risk_tau_delta_s": RISK_TAU_DELTA, "ttc_tau": TTC_TAU},
        "arms": {s: {a: r.__dict__ for a, r in arms.items()} for s, arms in results.items()},
        "contrasts": summary,
    }
    (outdir / "path3_summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {outdir/'path3_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())