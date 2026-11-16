"""Find the correct key prefix for EIDM car-following parameters, by behaviour.

SUMO ignores unknown <param> keys silently, so a wrong prefix produces "the parameter had
no effect" with no error. This test uses a scenario where car-following actually matters
(a slow leader that forces the follower to brake) and tries both plausible key styles:

    cf.<name>            e.g. cf.sigmaerror
    cf.<model>.<name>    e.g. cf.eidm.sigmaerror

A key is accepted if changing it changes the follower's speed trace.

Usage:
  python code/scripts/find_cf_param_prefix.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "src"))
from riskprop.stage_0_5_fixed_leader_traci import load_traci  # noqa: E402

SUMO = "sumo"
STEP = 0.05
END = 40.0
SEED = 20261116


def net_xml() -> str:
    return """<net version="1.20"><edge id="E" from="n0" to="n1" priority="1" numLanes="1" speed="30.00" length="3000"><lane id="E_0" index="0" speed="30.00" length="3000" shape="0,0 3000,0"/></edge><junction id="n0" type="dead_end" x="0" y="0"/><junction id="n1" type="dead_end" x="3000" y="0"/></net>"""


def run(workdir: Path, params: dict[str, str], model: str = "EIDM") -> np.ndarray:
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "net.net.xml").write_text(net_xml(), encoding="utf-8")
    attrs, tag_params = [], []
    for k, v in params.items():
        if k.startswith("@"):          # "@name" -> vType attribute
            attrs.append(f'{k[1:]}="{v}"')
        else:
            tag_params.append(f'<param key="{k}" value="{v}"/>')
    extra = "".join(tag_params)
    attr_str = (" " + " ".join(attrs)) if attrs else ""
    routes = f"""<routes>
  <vType id="e" carFollowModel="{model}" accel="2.6" decel="4.5" length="5" minGap="1.0" maxSpeed="30"{attr_str}>{extra}</vType>
  <vType id="slow" carFollowModel="Krauss" accel="2.6" decel="4.5" length="5" minGap="1.0" maxSpeed="30"/>
  <route id="r" edges="E"/>
  <vehicle id="lead" type="slow" route="r" depart="0" departPos="600" departSpeed="12">
    <stop lane="E_0" duration="8" startPos="900" endPos="900" speed="0"/>
  </vehicle>
  <vehicle id="f1" type="e" route="r" depart="0" departPos="585" departSpeed="12"/>
  <vehicle id="f2" type="e" route="r" depart="0" departPos="570" departSpeed="12"/>
  <vehicle id="f3" type="e" route="r" depart="0" departPos="555" departSpeed="12"/>
</routes>"""
    (workdir / "r.rou.xml").write_text(routes, encoding="utf-8")
    cfg = f"""<configuration>
    <input><net-file value="net.net.xml"/><route-files value="r.rou.xml"/></input>
    <time><begin value="0"/><end value="{END}"/><step-length value="{STEP}"/></time>
    <processing><time-to-teleport value="-1"/><no-step-log value="true"/></processing>
    <random_number><seed value="{SEED}"/></random_number>
</configuration>"""
    (workdir / "c.sumocfg").write_text(cfg, encoding="utf-8")

    traci = load_traci()
    traci.start([SUMO, "-c", str(workdir / "c.sumocfg"), "--no-step-log", "true",
                 "--collision.action", "warn"])
    ids = ["lead", "f1", "f2", "f3"]
    out = {v: [] for v in ids}
    try:
        for _ in range(int(round(END / STEP))):
            traci.simulationStep()
            present = set(traci.vehicle.getIDList())
            for v in ids:
                out[v].append(traci.vehicle.getSpeed(v) if v in present else np.nan)
    finally:
        traci.close()
    return np.array([out[v] for v in ids], dtype=float)


def main() -> int:
    scratch = ROOT / "code/outputs/analysis/_prefix_probe"
    base = run(scratch / "base", {})
    print(f"baseline mean speed {np.nanmean(base):.3f}, follower min "
          f"{np.nanmin(base[1]):.3f}\n")

    trials = [
        ("attr minGap (sanity)", "@minGap", "6.0"),
        ("attr tau (sanity)", "@tau", "3.0"),
        ("attr sigmaerror", "@sigmaerror", "0.60"),
        ("attr sigmaError", "@sigmaError", "0.60"),
        ("attr treaction", "@treaction", "2.50"),
        ("attr tReaction", "@tReaction", "2.50"),
        ("param sigmaerror", "sigmaerror", "0.60"),
        ("param cf.sigmaerror", "cf.sigmaerror", "0.60"),
        ("param cf.eidm.sigmaerror", "cf.eidm.sigmaerror", "0.60"),
        ("param cf.EIDM.sigmaerror", "cf.EIDM.sigmaerror", "0.60"),
    ]
    print(f"{'key':<28}{'max|Δ|':>14}{'accepted':>10}")
    print("-" * 52)
    res = []
    for label, key, val in trials:
        arr = run(scratch / f"t_{abs(hash(label))%10000}", {key: val})
        both = np.isfinite(arr) & np.isfinite(base)
        d = float(np.max(np.abs(arr[both] - base[both]))) if both.any() else 0.0
        ok = "YES" if d > 1e-9 else "no"
        print(f"{label:<28}{d:>14.6e}{ok:>10}")
        res.append({"label": label, "key": key, "value": val, "max_delta": d,
                    "accepted": d > 1e-9})

    outdir = ROOT / "code/outputs/analysis/cf_param_prefix_20261116"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "probe.json").write_text(json.dumps(res, indent=2, ensure_ascii=False),
                                       encoding="utf-8")
    good = [r for r in res if r["accepted"]]
    print(f"\n可用写法: {[r['key'] for r in good]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())