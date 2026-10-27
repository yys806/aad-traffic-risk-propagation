"""Whole-input and audit-only syntax checks; no native dependencies imported."""
import ast
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'code/scripts'))
from stage_0_5_input_fidelity import inventory, compare_initial_policy


def main():
    p=json.loads((ROOT/'evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/proposal.json').read_bytes())
    inputs=p['runs'][0]['input_files']
    original=ROOT/'code/outputs/formal/calibration/stage_0_5_policy_a_preflight_v1/prepared_inputs/ID1_SUPPLY_0750'
    a=(original/'routes.rou.xml').read_bytes(); b=(ROOT/inputs['routes.rou.xml']).read_bytes()
    _,_,initial,_,_=inventory(a)
    targets=[k for k,v in initial.items() if float(v.get('departSpeed'))==10]
    result=compare_initial_policy(a,b,target_ids=targets)
    assert result['exact_allowed_bytes_only'] is True and result['changed_initial_count']==38
    assert (original/'network.net.xml').read_bytes()==(ROOT/inputs['network.net.xml']).read_bytes()
    cfg=ET.fromstring((original/'run.sumocfg').read_bytes())
    for tag,value in [('tripinfo-output','tripinfo.xml'),('tripinfo-output.write-unfinished','true'),('tripinfo-output.write-undeparted','true')]:
        ET.SubElement(cfg.find('output'),tag,value=value)
    assert ET.tostring(cfg)==ET.tostring(ET.fromstring((ROOT/inputs['run.sumocfg']).read_bytes()))
    checked=[]
    for path in sorted(Path(__file__).parent.glob('*.py')):
        ast.parse(path.read_text(encoding='utf-8'));checked.append(path.name)
    print(json.dumps(dict(status='Pass',whole_routes_comparison=result,
        entire_configuration_equal_after_exact_three_output_options=True,audit_scripts_syntax=checked)))


if __name__=='__main__': main()
