"""Stage I isolated two-arm experiment (scr=1, opn in {0,1}).

Design, as fixed by docs/DECISION_next_step_20261116.md:
  - Two physically disconnected edges. Source road carries the source-risk treatment;
    target road carries the vehicles whose regional risk is measured.
  - Isolation is structural: t_phy-resp = +inf by construction (main.tex 313-319), so this
    arm needs no F0. Verified beforehand by test_isolation_rng_coupling.py (27,770/27,770
    samples bit-identical on the target edge when the source edge changes).
  - scr=1 throughout. The two arms differ ONLY in whether the information channel is open.
    opn=0: no message ever reaches a target controller. opn=1: once the source event is
    confirmed, a traceable message is generated, delivered, validated and adopted.
  - Same seed, same network, same target-road traffic; the only manipulated factor is opn.

What this produces: for each arm, the target-region aggregate risk and the message
lifecycle log (generated / delivered / validated / adopted / applied). The difference
between arms is the Effect; the lifecycle log is the Attribution evidence.

Status: engineering pilot. Not a formal Stage I run, not Protocol-Locked.

Usage:
  python code/scripts/run_stage1_isolated_two_arm.py --seeds 1
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))

from riskprop.message_driven_longitudinal_controller import (  # noqa: E402
    LocalState, PolicyConfig, PolicyInput, RiskPayload, Message,
    byte_hash, validate_message, longitudinal_policy,
    PAYLOAD_SCHEMA, PARAMETER_STATUS,
)
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

SUMO = "sumo"
STEP = 0.05
WARMUP = 40.0      # let the platoon finish inserting and the region fill before measuring
END = 80.0
# The road must be long enough that the target region stays populated for the whole
# evaluation window. With a 2000 m road and vehicles at 15 m/s, the region emptied by
# t=30 s, i.e. before the post-event window closed, and the measured risk was meaningless.
EDGE_LEN = 6000.0
TGT_REGION = (3000.0, 4000.0)    # target region: 1000 m, in the middle of the road
FILL_START = 5900.0              # fill the road upstream so the region is replenished
FILL_GAP = 15.0
TGT_COHORT_START = 5900.0
SOURCE_POS = 100.0               # source vehicle start (upstream end of the source road)
SOURCE_BRAKE_AT = 400.0          # must be downstream of SOURCE_POS and reachable within END
SOURCE_BRAKE_DUR = 12.0
TTC_TAU = 15.364279197080283     # approved risk mapping constant (2026-10-12)
RISK_EVENT_TTC = 2.0             # Formal P2 threshold


def net_xml() -> str:
    return f"""<net version="1.20" junctionCornerDetail="5" limitTurnSpeed="5.50">
    <edge id="src" from="s0" to="s1" priority="1" numLanes="1" speed="30.00" length="{EDGE_LEN}">
        <lane id="src_0" index="0" speed="30.00" length="{EDGE_LEN}" shape="0.00,-10.00 {EDGE_LEN:.2f},-10.00"/>
    </edge>
    <edge id="tgt" from="t0" to="t1" priority="1" numLanes="1" speed="30.00" length="{EDGE_LEN}">
        <lane id="tgt_0" index="0" speed="30.00" length="{EDGE_LEN}" shape="0.00,10.00 {EDGE_LEN:.2f},10.00"/>
    </edge>
    <junction id="s0" type="dead_end" x="0.00" y="-10.00"/>
    <junction id="s1" type="dead_end" x="{EDGE_LEN:.2f}" y="-10.00"/>
    <junction id="t0" type="dead_end" x="0.00" y="10.00"/>
    <junction id="t1" type="dead_end" x="{EDGE_LEN:.2f}" y="10.00"/>
</net>"""


def cohort_size() -> int:
    """How many target-road vehicles the fill produces (same rule as routes_xml)."""
    n, i = 0, 0
    while TGT_COHORT_START - FILL_GAP * i >= 100.0:
        n += 1
        i += 1
    return n


def routes_xml() -> str:
    # speedDev>0 gives drivers different desired speeds, the heterogeneity real traffic has.
    # With speedDev=0 every vehicle runs at 15 m/s and no closing speed ever forms, so the
    # regional risk is identically zero and the two arms cannot be compared at all.
    vt = ('<vType id="cal" carFollowModel="Krauss" accel="2.6" decel="4.5" sigma="0.5"'
          ' tau="0.6" length="5" minGap="2.5" maxSpeed="30" speedFactor="1" speedDev="0.12"/>')
    vehs = []
    i = 0
    while True:
        pos = TGT_COHORT_START - FILL_GAP * i
        if pos < 100.0:
            break
        vehs.append(f'<vehicle id="T{i}" type="cal" route="rt" depart="0" departPos="{pos:.2f}"'
                    f' departSpeed="15" departLane="0"/>')
        i += 1

    # source vehicle: stops for SOURCE_BRAKE_DUR starting at SOURCE_BRAKE_AT
    vehs.append(
        f'<vehicle id="S0" type="cal" route="rs" depart="{WARMUP:.1f}" departPos="{SOURCE_POS:.2f}"'
        f' departSpeed="15" departLane="0">'
        f'<stop lane="src_0" duration="{SOURCE_BRAKE_DUR}" startPos="{SOURCE_BRAKE_AT:.0f}"'
        f' endPos="{SOURCE_BRAKE_AT:.0f}" speed="0"/></vehicle>')
    return f'<routes>{vt}<route id="rs" edges="src"/><route id="rt" edges="tgt"/>{"" .join(vehs)}</routes>'


def run_arm(tmp: Path, seed: int, opn: int, policy_cfg: PolicyConfig):
    cfg = tmp / f"run_opn{opn}.sumocfg"
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
    tgt_ids = [f"T{i}" for i in range(cohort_size())]

    # --- source-event detection (independent of any controller) ---
    src_speed_hist: list[float] = []
    event_time: float | None = None
    src_speed0 = None

    # --- message lifecycle (Attribution evidence) ---
    lifecycle: list[dict] = []
    adopted_by: set[str] = set()
    applied_by: set[str] = set()
    adopted_msg: dict[str, tuple[Message, RiskPayload]] = {}

    # --- per-step target-region risk accumulation ---
    risk_samples: list[float] = []
    region_frac: list[float] = []
    mean_speed: list[float] = []
    roster: tuple[str, ...] | None = None
    tgt_series = {v: {"x": [], "v": []} for v in tgt_ids}

    try:
        for k in range(steps):
            now = k * STEP
            traci.simulationStep()
            present = set(traci.vehicle.getIDList())

            # ---- source event: vehicle actually decelerating, not planned injection time
            if "S0" in present:
                s_spd = traci.vehicle.getSpeed("S0")
                if src_speed0 is None:
                    src_speed0 = s_spd
                src_speed_hist.append(s_spd)
                if event_time is None and src_speed0 is not None and s_spd < src_speed0 - 1.0:
                    event_time = now
                    lifecycle.append({"phase": "source_event_confirmed", "t": round(now, 3),
                                      "source_id": "S0", "speed_mps": round(s_spd, 3)})
                    event_confirmed_t = now

            # ---- target vehicles: risk measurement + controller adoption
            in_region = []
            for v in tgt_ids:
                if v not in present:
                    tgt_series[v]["x"].append(np.nan)
                    tgt_series[v]["v"].append(np.nan)
                    continue
                x = traci.vehicle.getLanePosition(v)
                sp = traci.vehicle.getSpeed(v)
                tgt_series[v]["x"].append(x)
                tgt_series[v]["v"].append(sp)
                if TGT_REGION[0] <= x < TGT_REGION[1]:
                    in_region.append((v, x, sp))

            # ---- lock the roster at the first step after warmup (main.tex 230: the
            # denominator N must be FIXED across conditions, and a vehicle that leaves the
            # region still occupies a slot with zero risk rather than being dropped, which
            # is what made the earlier version report a spurious 74x rise).
            if roster is None and now >= WARMUP:
                roster = tuple(sorted(v for v, _, _ in in_region))
                lifecycle.append({"phase": "roster_locked", "t": round(now, 3),
                                  "n_vehicles": len(roster)})
            if roster is None:
                continue   # warmup: traffic still inserting, nothing is measured

            # ---- risk per locked roster vehicle, fixed denominator
            vals = []
            n_in_region = 0
            for v in roster:
                if v not in present:
                    vals.append(0.0)
                    continue
                x = traci.vehicle.getLanePosition(v)
                sp = traci.vehicle.getSpeed(v)
                inside = TGT_REGION[0] <= x < TGT_REGION[1]
                if not inside:
                    vals.append(0.0)   # outside: zero risk, but keeps its slot
                    continue
                n_in_region += 1
                lead = traci.vehicle.getLeader(v, 200.0)
                if not lead:
                    vals.append(0.0)
                    continue
                lid, gap = lead
                if gap <= 0 or lid not in present:
                    vals.append(0.0)
                    continue
                lsp = traci.vehicle.getSpeed(lid)
                closing = sp - lsp
                if closing <= 1e-6:
                    vals.append(0.0)
                    continue
                ttc = gap / closing
                vals.append(math.exp(-ttc / TTC_TAU))
            step_risk = float(np.sum(vals) / len(roster)) if roster else 0.0
            risk_samples.append(step_risk)
            region_frac.append(n_in_region / len(roster) if roster else 0.0)
            mean_speed.append(float(np.mean([sp for _, _, sp in in_region])) if in_region else float("nan"))

            # ---- controller adoption: only if the source event has been confirmed
            if opn == 1 and event_time is not None:
                for v, x, sp in in_region:
                    lead = traci.vehicle.getLeader(v, 200.0)
                    lid, gap = (lead[0], float(lead[1])) if lead else (None, None)
                    lsp = (traci.vehicle.getSpeed(lid)
                           if lid is not None and lid in present else None)
                    pos = traci.vehicle.getPosition(v)
                    try:
                        state = LocalState(
                            vehicle_id=v,
                            vehicle_incarnation_id=f"{v}@0",
                            simulation_time_s=now,
                            simulation_step=k,
                            edge_id="tgt",
                            lane_id="tgt_0",
                            lane_position_m=x,
                            position_xy_m=(float(pos[0]), float(pos[1])),
                            speed_mps=sp,
                            acceleration_mps2=float(traci.vehicle.getAcceleration(v)),
                            original_max_speed_mps=30.0,
                            lane_max_speed_mps=30.0,
                            leader_id=lid,
                            leader_speed_mps=lsp,
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
                                valid_until=round(event_time + 30.0, 3),
                            )
                            raw = payload.to_bytes()
                            msg = Message(
                                message_id=f"msg-{v}-01",
                                sender_id="SRC-EDGE",
                                receiver_id=v,
                                source_event_id="evt-S0-01",
                                raw_payload=raw,
                                payload_hash=byte_hash(raw),
                            )
                            lifecycle.append({"phase": "message_generated", "t": round(now, 3),
                                              "vehicle_id": v, "message_id": msg.message_id,
                                              "payload_hash": msg.payload_hash})
                            check = validate_message(msg, state)
                            lifecycle.append({"phase": "message_validation", "t": round(now, 3),
                                              "vehicle_id": v, "status": check.status,
                                              "reason": check.reason})
                            if check.status != "VALID":
                                continue
                            lifecycle.append({"phase": "message_adopted", "t": round(now, 3),
                                              "vehicle_id": v, "message_id": msg.message_id})
                            adopted_msg[v] = (msg, payload)
                            adopted_by.add(v)
                        msg, payload = adopted_msg[v]
                        out = longitudinal_policy(
                            PolicyInput(local_state=state,
                                        messages=((msg.message_id, payload),)),
                            policy_cfg)
                        if out.target_speed_reference_mps is not None:
                            traci.vehicle.setMaxSpeed(v, out.target_speed_reference_mps)
                            applied_by.add(v)
                    except Exception as exc:  # noqa: BLE001 - record, never swallow
                        lifecycle.append({"phase": "policy_error", "t": round(now, 3),
                                          "vehicle_id": v, "error": f"{type(exc).__name__}: {exc}"})
    finally:
        traci.close()

    risk = np.asarray(risk_samples, dtype=float)
    return {
        "arm": f"opn{opn}",
        "seed": seed,
        "event_time_s": event_time,
        "roster_size": len(roster) if roster else 0,
        "risk_mean": float(np.nanmean(risk)) if risk.size else None,
        "risk_max": float(np.nanmax(risk)) if risk.size else None,
        "risk_sum_s": float(np.nansum(risk) * STEP) if risk.size else None,
        "region_time_fraction_mean": float(np.nanmean(region_frac)) if region_frac else None,
        "region_speed_mean": float(np.nanmean(mean_speed)) if mean_speed else None,
        "n_adopted": len(adopted_by),
        "n_applied": len(applied_by),
        "lifecycle": lifecycle,
        "tgt_series": {v: {"x": [None if not np.isfinite(x) else round(float(x), 3) for x in d["x"]],
                           "v": [None if not np.isfinite(x) else round(float(x), 3) for x in d["v"]]}
                       for v, d in tgt_series.items()},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--out", default="code/outputs/analysis/stage1_isolated_20261116")
    args = ap.parse_args()

    cfg_path = ROOT / "code/configs/p7_task2_engineering_candidate_v2.json"
    raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    policy_cfg = PolicyConfig.from_dict(raw)

    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)

    results = []
    for s in range(args.seeds):
        seed = 20261116 + s
        scratch = outdir / f"_scratch_{seed}"
        scratch.mkdir(parents=True, exist_ok=True)
        (scratch / "net.net.xml").write_text(net_xml(), encoding="utf-8")
        (scratch / "routes.rou.xml").write_text(routes_xml(), encoding="utf-8")
        for opn in (0, 1):
            r = run_arm(scratch, seed, opn, policy_cfg)
            results.append(r)
            print(f"seed={seed} arm={r['arm']} event_t={r['event_time_s']} "
                  f"risk_mean={r['risk_mean']:.6g} adopted={r['n_adopted']} applied={r['n_applied']}")

        # paired contrast within this seed
        a0 = next(x for x in results if x["seed"] == seed and x["arm"] == "opn0")
        a1 = next(x for x in results if x["seed"] == seed and x["arm"] == "opn1")
        if a0["risk_sum_s"] is not None and a1["risk_sum_s"] is not None:
            print(f"  seed={seed} Δrisk_sum_s = {a1['risk_sum_s'] - a0['risk_sum_s']:+.6g}")

    # strip the heavy series from the summary file, keep it in a side file
    summary = [{k: v for k, v in r.items() if k != "tgt_series"} for r in results]
    (outdir / "arms_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (outdir / "arms_series.json").write_text(
        json.dumps({f"{r['seed']}_{r['arm']}": r["tgt_series"] for r in results}),
        encoding="utf-8")
    print(f"\nwrote {outdir/'arms_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())