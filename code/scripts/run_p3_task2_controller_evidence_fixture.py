"""Run bounded P3 synthetic contract checks. No SUMO, seeds or real communication."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "src"))
from riskprop.controller_evidence import EvidenceError, schema_description
from p3_controller_evidence_fixtures import invalid_fixtures, journal_from_records, scenario_records


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)

    def write(name, value):
        (output/name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")

    results = {}
    for name in ("A", "B", "C", "D", "E", "G", "H"):
        journal = journal_from_records(scenario_records(name))
        audit = journal.validate()
        journal.write(output/("fixture_"+name+".json"))
        results[name] = {k:v for k,v in audit.items() if k != "timeline"}
    negative = {}
    for name, (records, expected) in invalid_fixtures().items():
        try:
            journal_from_records(records).validate()
        except EvidenceError as exc:
            negative[name] = {"expected": expected, "actual": exc.code, "status": "PASS" if exc.code == expected else "FAIL"}
        else:
            negative[name] = {"expected": expected, "actual": "NO_ERROR", "status": "FAIL"}
    assert all(v["status"] == "PASS" for v in negative.values()), negative
    write("schema.json", schema_description())
    write("linkage_results.json", {"fixture_only": True, "scientific_claim_eligible": False, "scenarios": results, "F": negative})
    root=CODE.parent
    git=lambda *args:subprocess.run(["git",*args],cwd=root,capture_output=True,text=True,check=True).stdout.strip()
    write("provenance.json", {"task_id":"AAD-P3-TASK2-20261103", "git_sha":git("rev-parse","HEAD"),
        "git_dirty_status":git("status","--short"), "python":sys.version, "platform":platform.platform(),
        "command":sys.argv, "fixture_only":True, "scientific_claim_eligible":False,
        "new_SUMO_runs":0, "new_seeds":0, "new_V_runs":0, "locked_holdout_reads":0,
        "numeric_fixture_values":"synthetic examples, not scientific thresholds or frozen TTL",
        "implementation_sha256":{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [CODE/"src/riskprop/controller_evidence.py",CODE/"scripts/p3_controller_evidence_fixtures.py",Path(__file__)]}})
    files=sorted(p for p in output.iterdir() if p.is_file())
    (output/"SHA256SUMS").write_text("".join(hashlib.sha256(p.read_bytes()).hexdigest()+"  "+p.name+"\n" for p in files),encoding="utf-8",newline="\n")
    return {"status":"PASS", "positive_scenarios":list(results), "negative_cases":len(negative), "output":str(output), "scientific_claim_eligible":False}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    print(json.dumps(run(parser.parse_args().output),ensure_ascii=False))
