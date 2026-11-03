"""Offline P4 example runner and serialized bundle validator. Never starts SUMO."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from riskprop.p4_measurement_bundle import build_bundle, validate_bundle, write_bundle, assignment_result
from riskprop.p4_action_measurement import compare_actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--examples", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    def save(name, value):
        (args.output/name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    if args.examples:
        from p4_validation_cases import SOURCE, associations, inputs, paired_inputs
        # Actual source bytes match provenance's canonical SHA256.
        (args.output/"synthetic_source.json").write_text(json.dumps(SOURCE, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False), encoding="utf-8")
        for name, partial in (("interval", True), ("point", False)):
            s, r, states, p = inputs(partial=partial)
            data = dict(support=s, roster=r, states=states, provenance=p, associations=associations(states))
            save(name+"_input.json", data)
            b = build_bundle(**data)
            write_bundle(b, args.output/(name+"_bundle.json"))
            save(name+"_assignment.json", assignment_result(b))
            validate_bundle(b, artifact_root=args.output)
        s, r, states, p = inputs()
        r["complete_population"] = False
        save("unknown_scope_bundle.json", build_bundle(s,r,states,p,associations=associations(states)))
        from riskprop.p4_regional_risk import RegionalRiskAssembler
        from riskprop.p4_measurement_contract import P4InputError, stamp
        s,r,states,p = inputs()
        assembler = RegionalRiskAssembler(s,r,p)
        windows,_,_ = assembler.vehicle_windows(states)
        windows[0] = stamp("vehicle_window", {**windows[0], "member_id": "wrong-same-N"})
        try:
            assembler.aggregate(windows)
            raise AssertionError("same-N wrong identity accepted")
        except P4InputError as exc:
            save("same_N_wrong_identity.json", {"usage": "SYNTHETIC_VALIDATION_ONLY", "expected_N":3,
                "received_N":3, "status":"REJECTED", "error_code":exc.code})
        manifest, base, treat, p = paired_inputs()
        for x in treat[1:]:
            x["speed_mps"] -= 1.
            x["acceleration_mps2"] = -1.
        save("action_input.json", dict(manifest=manifest, baseline=base, treatment=treat, provenance=p))
        save("action_output.json", compare_actions(manifest, base, treat, p))
        print("P4_SYNTHETIC_EXAMPLES_VALIDATED")
    else:
        if args.input is None:
            parser.error("--input or --examples required")
        data = json.loads(args.input.read_text(encoding="utf-8"))
        b = build_bundle(**data)
        write_bundle(b, args.output/"measurement_bundle.json")
        save("assignment_result.json", assignment_result(b))
        print("P4_BUNDLE_VALIDATED")


if __name__ == "__main__":
    main()
