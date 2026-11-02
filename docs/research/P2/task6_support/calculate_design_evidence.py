"""Task6 documentation-only audit/design calculations; no simulation or holdout access."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'evidence/research/P2_TASK6_20261102/design_evidence.json'
HIST = [
 'code/outputs/calibration/p2_task3_20261102_v2/calibration_runs.csv',
 'code/outputs/calibration/p2_task3_20261102_v2/calibration_summary.csv',
 'code/outputs/calibration/p2_task3_20261102_v2/calibration_config.json',
 'code/outputs/calibration/p2_task3_20261102_v2/provenance.json',
 'code/outputs/calibration/p2_task3_20261102_v2/SHA256SUMS',
 'code/outputs/calibration/p2_task3_sumo_b_20261102/detector_results.csv',
 'code/outputs/calibration/p2_task3_sumo_b_20261102/run_audits.csv',
 'code/outputs/calibration/p2_task3_sumo_b_20261102/measurement_audit.json',
 'code/outputs/calibration/p2_task3_sumo_b_20261102/provenance.json',
 'code/outputs/calibration/p2_task3_sumo_b_20261102/SHA256SUMS',
 'code/outputs/formal/task18_20261101/primary_results.csv',
 'code/outputs/formal/task18_20261101/supplementary_results.csv',
 'code/outputs/analysis/task19_20261101/analysis_dataset_run_level.csv',
 'code/outputs/analysis/task19_20261101/paired_all_sources.csv',
 'code/src/riskprop/formal_risk_measurement.py',
 'code/src/riskprop/formal_design.py',
 'docs/research/P1/ESTIMAND_SPECIFICATION.md',
 'docs/research/P1/CAUSAL_DAG.md',
 'docs/research/P1/THEORY_AND_CAUSAL_MODEL.md',
 'docs/research/P2/P2_TASK3_CALIBRATION_RESULTS.md',
 'docs/research/P2/P2_TASK4_LITERATURE_AND_NOVELTY_AUDIT.md',
 'docs/research/P2/P2_TASK5_STATISTICAL_METHOD_NOTES.md',
 'docs/research/P2/P2_TASK5_OVERLEAF_AUDIT.md',
 'doc/literature-notes/P2_TASK5_SOURCE_AUDIT_20261102.json',
]
DOCS = [
 'docs/research/P2/P2_TASK6_FINAL_REPORT.md',
 'docs/research/P2/P2_TASK6_PARAMETER_DETERMINATION_EXPERIMENT_PROTOCOL.md',
 'docs/research/P2/P2_TASK6_RESEARCHER_DECISIONS.md',
 'docs/research/definitions/README.md',
 'docs/research/definitions/CORE_SCIENTIFIC_DEFINITIONS.md',
 'docs/research/definitions/SYMBOL_REGISTER.md',
 'docs/research/definitions/PARAMETER_AND_CALIBRATION_REGISTER.md',
 'docs/research/definitions/EVIDENCE_AND_ASSUMPTION_LEDGER.md',
 'docs/research/definitions/OVERLEAF_ALIGNMENT.md',
 'docs/research/P2/task6_support/calculate_design_evidence.py',
]

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def cdf(k: int, n: int, p: float) -> float:
    if k < 0: return 0.0
    if k >= n or p == 0: return 1.0
    if p == 1: return 0.0
    terms = [math.lgamma(n+1)-math.lgamma(i+1)-math.lgamma(n-i+1)
             + i*math.log(p)+(n-i)*math.log1p(-p) for i in range(k+1)]
    peak = max(terms)
    return min(1.0, math.exp(peak)*math.fsum(math.exp(v-peak) for v in terms))

def cp_upper(x: int, n: int, beta: float) -> float:
    if x == n: return 1.0
    low, high = 0.0, 1.0
    for _ in range(70):
        mid = (low+high)/2
        if cdf(x, n, mid) > beta: low = mid
        else: high = mid
    return (low+high)/2

def zero_n(pstar: float, beta: float) -> int:
    return math.ceil(math.log(beta)/math.log1p(-pstar))

def power_n(pstar: float, good: float, beta: float, power: float = .9) -> dict:
    crit = -1
    for n in range(1, 50001):
        while crit+1 <= n and cdf(crit+1, n, pstar) <= beta:
            crit += 1
        achieved = cdf(crit, n, good)
        if achieved >= power:
            return dict(n=n, max_bad=crit, achieved_power=achieved,
                        true_good_bad_rate=good, acceptance_bad_rate=pstar,
                        per_claim_failure=beta, target_power=power)
    raise RuntimeError('design cap 50000 insufficient; do not invent n')

def calculations() -> dict:
    favorable, powered, joint_powered, feasibility = [], [], [], []
    for total_failure in [.05, .005]:
        for family in [1, 12, 15]:
            beta = total_failure/family
            for p in [.0025, .005, .01, .05, .1]:
                n = zero_n(p, beta)
                assert 1-math.exp(math.log(beta)/n) <= p+1e-13
                assert n == 1 or 1-math.exp(math.log(beta)/(n-1)) > p-1e-13
                favorable.append(dict(family_failure=total_failure, family_size=family,
                    bad_rate_limit=p, per_claim_failure=beta, zero_bad_n=n,
                    all_success_sensitivity=1-p, upper_zero_bad=cp_upper(0,n,beta)))
        for family in [1, 15]:
            for pstar, good in [(.01,.002),(.05,.01),(.0025,.0005)]:
                item = power_n(pstar,good,total_failure/family)
                item.update(family_failure=total_failure,family_size=family)
                powered.append(item)
                if family > 1:
                    joint = power_n(pstar, good, total_failure/family, power=1-.1/family)
                    joint.update(family_failure=total_failure, family_size=family,
                                 joint_power_target=.9,
                                 power_method="Bonferroni type-II allocation; all claims need their own adequate n")
                    joint_powered.append(joint)
    for eta in [.01,.05]:
        for unknown in [0,.005,.02,.05]:
            for family in [1,3,603]:
                margin = eta-unknown
                feasibility.append(dict(eta=eta, observed_possible_arrival_floor=unknown,
                    family_size=family, alpha_P=.02,
                    sufficient_hoeffding_n_for_strict_upper=(math.floor(math.log(family/.02)/(2*margin**2))+1 if margin>0 else None),
                    status=('infeasible regardless of n' if margin<=0 else 'favorable-floor planning only')))
    assert abs(cdf(0,10,.1)-.9**10)<1e-12
    assert abs(cp_upper(0,6,.05)-(1-.05**(1/6)))<1e-12
    assert zero_n(.01,.05)==299 and zero_n(.05,.05)==59
    return dict(assumptions='independent homogeneous Bernoulli units; no cluster/frame pooling; all numerical standards are proposals',
        family_sizes='1,12,15 are planning illustrations; actual J_V includes all endpoints/strata/candidates/neighborhood claims',
        best_case_not_power=favorable, exact_acceptance_power=powered,
        exact_acceptance_power_scope="per-claim power only, not joint-family success probability",
        conservative_joint_power_planning=joint_powered,
        cdf_feasibility=feasibility,
        historical_single_claim_zero_alarm_cp_upper_95={str(n):cp_upper(0,n,.05) for n in [6,24]},
        interaction_precision_formula='n >= ceil(8*log(2*K_int/beta_int)/epsilon_int**2) for D in [-2,2]',
        risk_sufficient_power_formula='balanced n > 2*R**2*(sqrt(log(4*J_R/alpha_R))+sqrt(log(2*J_R/beta_pow)))**2/g**2; floor+1 for strict acceptance, without measurement-width loss')

def audit() -> dict:
    v2=rows(HIST[0]); b=rows(HIST[5]); audits=rows(HIST[6])
    ma=json.loads((ROOT/HIST[7]).read_text(encoding='utf-8'))
    primary=rows(HIST[10]); supplementary=rows(HIST[11]); t19=rows(HIST[12]); pairs=rows(HIST[13])
    assert len(v2)==32256 and len(b)==2520 and len(audits)==60
    assert len({(r['split'],r['scenario'],r['panel_seed']) for r in v2})==768
    assert all(r['alarm']=='False' for r in b)
    assert all(r['qualified_witness']=='False' for r in audits)
    assert len(primary)==60 and len(supplementary)==40 and len(t19)==100 and len(pairs)==50
    manifest_checks=[]
    for folder in ['code/outputs/calibration/p2_task3_20261102_v2','code/outputs/calibration/p2_task3_sumo_b_20261102']:
        items={}
        for line in (ROOT/folder/'SHA256SUMS').read_text(encoding='utf-8-sig').splitlines():
            if not line.strip(): continue
            digest,name=line.split(maxsplit=1)
            items[name.lstrip('*').replace(chr(92),'/')]=digest
        for rel in HIST:
            path=ROOT/rel
            if path.parent != ROOT/folder or path.name=='SHA256SUMS': continue
            expected=items.get(path.name)
            if expected is None:
                expected=items.get(rel)
            if expected is not None:
                actual=sha(path)
                assert actual==expected, f'historical source drift: {rel}'
                manifest_checks.append(rel)
    return dict(v2=dict(panels=768,candidates=len({r['detector_id'] for r in v2}),evaluations=len(v2),domain='synthetic_measurement_verification'),
        controlled_B=dict(run_records=len(audits),evaluations=len(b),alarms=0,
            qualified_witnesses=0, peak_mean_decline_mps=[min(x['peak_mean_decline_mps'] for x in ma['runs']),max(x['peak_mean_decline_mps'] for x in ma['runs'])],
            independent_cohort_positive_labels='not available', cross_condition_seed_reuse=True),
        task9_18_19=dict(primary=len(primary),supplementary=len(supplementary),task19_same_runs=len(t19),pairs=len(pairs),
            independence='not three datasets; shared candidate/input/seed dependencies retained'),
        historical_manifest_selected_files_verified=manifest_checks,
        historical_raw_trajectories_not_reprocessed=True)

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    if args.verify:
        saved=json.loads(OUT.read_text(encoding='utf-8'))
        for entry in saved['input_hashes']:
            assert sha(ROOT/entry['path'])==entry['sha256'],entry['path']
        assert saved['design_calculations']==calculations()
        assert saved['historical_data_audit']==audit()
        print('TASK6_DESIGN_EVIDENCE_OK')
        return
    sources=[]
    for rel in HIST+DOCS:
        path=ROOT/rel
        assert path.is_file(),rel
        sources.append(dict(path=rel,bytes=path.stat().st_size,sha256=sha(path)))
    result=dict(schema_version='aad.p2.task6.design.v1',date='2026-11-02',
        status='DESIGN_COMPLETE_CONDITIONAL_EXECUTION_NOT_AUTHORIZED',
        scientific_status='Formal A=0; independent Qualified=0; F0 and population TR/TP Unknown',
        new_simulation_or_calibration_runs=0,locked_holdout_reads=0,
        audit_base_git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        script_version_sha256=sha(Path(__file__)),
        input_hashes=sources,historical_data_audit=audit(),design_calculations=calculations(),
        source_read_scope='explicit HIST and DOCS allowlist only; no recursive raw/holdout enumeration',
        reference_reading='Task5 method/source audit reused; NIST official exact-binomial page targeted verification only',
        no_formal_gate_protocol_or_production_logic_changed=True)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('TASK6_DESIGN_EVIDENCE_WRITTEN',len(sources),'hashed inputs')
    for r in result['design_calculations']['exact_acceptance_power']:
        print(json.dumps(r))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
