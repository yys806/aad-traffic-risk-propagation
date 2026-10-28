from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/WEEK_0750_B00_IC1_s20261201_A03"
CANDIDATE = ROOT / "evidence/admission/AAD-S0.5-ROUND2-TASK1-20261028/candidate-v1/inputs"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_round2_candidate_is_a_static_single_factor_input() -> None:
    assert _sha(BASE / "network.net.xml") == _sha(CANDIDATE / "network.net.xml")
    assert _sha(BASE / "run.sumocfg") == _sha(CANDIDATE / "run.sumocfg")
    base = ET.parse(BASE / "routes.rou.xml").getroot()
    candidate = ET.parse(CANDIDATE / "routes.rou.xml").getroot()
    for kind in ("route", "vehicle"):
        base_rows = {x.get("id"): dict(x.attrib) for x in base.findall(kind)}
        candidate_rows = {x.get("id"): dict(x.attrib) for x in candidate.findall(kind)}
        assert base_rows == candidate_rows
    base_types = {x.get("id"): dict(x.attrib) for x in base.findall("vType")}
    candidate_types = {x.get("id"): dict(x.attrib) for x in candidate.findall("vType")}
    changed = []
    for ident, attrs in base_types.items():
        delta = {
            key: (attrs.get(key), candidate_types[ident].get(key))
            for key in set(attrs) | set(candidate_types[ident])
            if attrs.get(key) != candidate_types[ident].get(key)
        }
        if delta:
            changed.append((ident, delta))
    assert len(changed) == 5
    assert all(set(delta) == {"minGap"} for _, delta in changed)
    assert all(delta["minGap"] == ("2.5", "1.0") for _, delta in changed)
