"""Portable stdlib-only evidence verification. No simulator, dataset or process calls."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from verify_mathematics import verify


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,
        separators=(",",":"),allow_nan=False).encode("utf-8")).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root",type=Path)
    parser.add_argument("--byte-profile",choices=("working-tree","git-blob"),default="working-tree")
    a=parser.parse_args()
    package=Path(__file__).resolve().parent
    def read(path): return json.loads(path.read_text(encoding="utf-8"))
    manifest={}
    for line in (package/"SHA256SUMS").read_text(encoding="utf-8").splitlines():
        h,name=line.split("  ",1)
        target=(package/name).resolve()
        assert target.is_relative_to(package) and target.is_file(),name
        assert name not in manifest and digest(target)==h,name
        manifest[name]=h
    actual={p.relative_to(package).as_posix() for p in package.rglob("*")
        if p.is_file() and p.name!="SHA256SUMS" and "__pycache__" not in p.parts}
    assert set(manifest)==actual,"package file set differs"
    math_result=verify(package/"examples")
    assert math_result==read(package/"mathematics.json"),"independent math result differs"
    tests=read(package/"tests.json")
    assert tests["final"]["passed"]==172 and tests["final"]["failed"]==0
    assert not tests["process_guard"]["blocked_attempts"] and tests["process_guard"]["guard_active"]
    for name in ("interval_bundle.json","point_bundle.json","unknown_scope_bundle.json"):
        bundle=read(package/"examples"/name)
        assert bundle["bundle_sha256"]==canonical({k:v for k,v in bundle.items() if k!="bundle_sha256"})
        assert bundle["usage"]=="SYNTHETIC_VALIDATION_ONLY"
        for rows in bundle["records"].values():
            for row in rows:
                assert row["record_sha256"]==canonical({k:v for k,v in row.items() if k!="record_sha256"})
        src=bundle["records"]["provenance"][0]
        assert digest(package/"examples"/src["source_ref"])==src["source_sha256"]
    pair=read(package/"examples/action_input.json")
    action=read(package/"examples/action_output.json")
    base={s["state_id"]:s for s in pair["baseline"]}
    treat={s["state_id"]:s for s in pair["treatment"]}
    for row in action["action_comparisons"]:
        b,t=base[row["baseline_state_id"]],treat[row["treatment_state_id"]]
        assert row["delta_speed_mps"]==t["speed_mps"]-b["speed_mps"]
        assert row["delta_acceleration_mps2"]==t["acceleration_mps2"]-b["acceleration_mps2"]
        assert row["onset_status"]=="THRESHOLD_UNSET"
    for row in action["action_timing"]:
        assert row["formal_T_U_s"] is None and row["persistence_confirmation_time_s"] is None
    source_count=0
    if a.repo_root:
        root=a.repo_root.resolve()
        for item in read(package/"source_manifest.json")["files"]:
            path=(root/item["path"]).resolve()
            expected=item["sha256"] if a.byte_profile=="working-tree" else item["git_blob_sha256"]
            assert path.is_relative_to(root) and digest(path)==expected,item["path"]
            source_count+=1
        protection=read(package/"protected_bytes.json")
        protected=protection["protected_hashes"] if a.byte_profile=="working-tree" else protection["protected_git_hashes"]
        for name,h in protected.items():
            assert digest(root/name)==h,name
        for item in protection["definition_prefix_checks"]:
            size=item["original_bytes"] if a.byte_profile=="working-tree" else item["git_original_bytes"]
            expected=item["original_sha256"] if a.byte_profile=="working-tree" else item["git_original_sha256"]
            assert hashlib.sha256((root/item["path"]).read_bytes()[:size]).hexdigest()==expected,item["path"]
        assert protection["definition_count"]==27
        fields=list(csv.DictReader((root/"docs/research/P4/p4_measurement_variable_dictionary_v1.csv").open(encoding="utf-8",newline="")))
        keys={(r["entity"],r["field"]) for r in fields if r["status"]=="IMPLEMENTED"}
        bundle=read(package/"examples/interval_bundle.json")
        for entity,rows in bundle["records"].items():
            for row in rows:
                assert all((entity,k) in keys for k in row),entity
    print(json.dumps({"status":"P4_TASK2_EVIDENCE_VERIFIED","package_files":len(manifest),
        "source_files_verified":source_count,"math_checks":math_result["checks_passed"],
        "new_traffic_runs":0,"causal_effect_claimed":False},ensure_ascii=False))


if __name__=="__main__":
    main()
