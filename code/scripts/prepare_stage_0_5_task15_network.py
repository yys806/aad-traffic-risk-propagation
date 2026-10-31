"""Build an isolated straight-line SUMO network prototype for Task15.

This prototype is engineering-only and never modifies or replaces the sealed
B00 network.  It provides three lanes, 1,000 m of longitudinal space and a
minimal route used solely for replay validation.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "local_research/staging/task15_20261031/network_prototype"
SUMO_BIN = Path(r"C:\Program Files (x86)\Eclipse\Sumo\bin")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    nodes = OUT / "nodes.nod.xml"
    edges = OUT / "edges.edg.xml"
    routes = OUT / "routes.rou.xml"
    cfg = OUT / "replay.sumocfg"
    net = OUT / "network.net.xml"
    nodes.write_text("""<nodes>\n  <node id=\"n0\" x=\"0\" y=\"0\"/>\n  <node id=\"n1\" x=\"1000\" y=\"0\"/>\n</nodes>\n""", encoding="utf-8")
    edges.write_text("""<edges>\n  <edge id=\"main_ext\" from=\"n0\" to=\"n1\" numLanes=\"3\" speed=\"30\" width=\"3.2\"/>\n</edges>\n""", encoding="utf-8")
    routes.write_text("""<routes>\n  <vType id=\"replay\" accel=\"2.6\" decel=\"4.5\" sigma=\"0\" tau=\"1.0\" length=\"4.4196\" minGap=\"1.0\" maxSpeed=\"30\"/>\n  <route id=\"r0\" edges=\"main_ext\"/>\n</routes>\n""", encoding="utf-8")
    cfg.write_text("""<configuration><input><net-file value=\"network.net.xml\"/><route-files value=\"routes.rou.xml\"/></input><time><begin value=\"0\"/><end value=\"60\"/><step-length value=\"0.05\"/></time><processing><time-to-teleport value=\"-1\"/><collision.action value=\"warn\"/><no-step-log value=\"true\"/></processing></configuration>\n""", encoding="utf-8")
    cmd = [str(SUMO_BIN / "netconvert.exe"), "--node-files", str(nodes), "--edge-files", str(edges), "--output-file", str(net), "--no-turnarounds", "true"]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    manifest = {
        "status": "BUILT_ISOLATED_ENGINEERING_NETWORK",
        "network": str(net.relative_to(ROOT)),
        "route": str(routes.relative_to(ROOT)),
        "config": str(cfg.relative_to(ROOT)),
        "length_m": 1000.0,
        "lanes": 3,
        "lane_width_m": 3.2,
        "speed_mps": 30.0,
        "preserves_sealed_b00": True,
        "background_traffic_equivalence": "Not claimed; straight-line replay prototype only",
        "files": {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)} for p in (nodes, edges, routes, cfg, net)},
    }
    (OUT / "manifest.json").write_text(__import__("json").dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"TASK15_NETWORK_BUILT {net.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
