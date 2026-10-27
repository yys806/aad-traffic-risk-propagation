"""Deterministic, scoped error evidence; never approves scientific tolerances."""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from riskprop.formal_risk_measurement import P2_FORMAL_CONFIG, integrate_fixed_window, rho_from_ttc
from riskprop.prelock_metrics import derive_delta_eq, evaluate_timestep_convergence
from riskprop.prelock_validation import _analytic_truth_audit, _path_truth_audit


def records(times, values):
    return pd.DataFrame([dict(time_s=float(t), global_time_ms=float(t)*1000, frame_id=i,
        diagnostic_clock_anchor_ms=0, dataset='analytic', site='fixture', window_id='fixed',
        source_member='deterministic', source_period='p', trajectory_id='f', leader_trajectory_id='l',
        leader_matched=True, identity_uncertain=False, leader_identity_uncertain=False,
        identity_break=False, observation_gap=False, lower=float(v), upper=float(v))
        for i,(t,v) in enumerate(zip(times, values))])


def sampled_rho(ttc0, horizon, step):
    count=round(horizon/step)
    if not math.isclose(count*step,horizon,abs_tol=1e-10):
        raise ValueError('fixture horizon must have an observed right endpoint')
    times=np.arange(count+1)*step
    values=[rho_from_ttc(ttc0-t) for t in times]
    if any(v is None for v in values):
        raise ValueError('fixture cannot cross collision/missing boundary')
    result=integrate_fixed_window(records(times,values),window_start_s=0,window_end_s=horizon,expected_step_s=step)
    if abs(result['unknown_time_s'])>1e-8:
        raise ValueError('unexpected integration observation gap')
    independent=math.fsum((float(times[i+1])-float(times[i]))*values[i] for i in range(count))/horizon
    return result['lower_mean'], independent


def build_budget():
    # Fixed before evaluation: full Cartesian grid, no selection on pass/failure.
    # A bounded smooth rear-end class, not a global bound on SUMO dynamics.
    tau=P2_FORMAL_CONFIG.tau_s
    groups={k:[] for k in ('numerical_errors','timestep_errors','analyzer_errors','reconstruction_errors')}
    cases=[]
    for ttc0 in (1.0,2.0,4.0,8.0,16.0):
        for horizon in (.2,.4,.8):
            metrics={step:sampled_rho(ttc0,horizon,step) for step in (.1,.05,.02,.01)}
            truth=tau/horizon*(math.exp(-(ttc0-horizon)/tau)-math.exp(-ttc0/tau))
            with localcontext() as ctx:
                ctx.prec=50
                d_tau=Decimal(str(tau));d_ttc=Decimal(str(ttc0))
                decimal_rho=float((-d_ttc/d_tau).exp())
            numerical=abs(rho_from_ttc(ttc0)-decimal_rho)
            analyzer=max(abs(a-b) for a,b in metrics.values())
            timestep=max(abs(metrics[.05][0]-metrics[.02][0]),abs(metrics[.1][0]-truth))
            for key,value in [('numerical_errors',numerical),('analyzer_errors',analyzer),('timestep_errors',timestep)]:
                groups[key].append(value)
            cases.append(dict(ttc0_s=ttc0,horizon_s=horizon,analytic_mean_rho=truth,
                metric_by_step={str(s):v[0] for s,v in metrics.items()},
                abs_error_by_step={str(s):abs(v[0]-truth) for s,v in metrics.items()},
                direction=evaluate_timestep_convergence({s:v[0] for s,v in metrics.items()},zero_tolerance=None)))
    reconstruction=[]
    # Two rounded position endpoints and two rounded velocities: each difference
    # can err by one 0.01 unit. Enumerate both signs; never collapse missing to0.
    for gap in (1.,2.,5.,10.,20.,40.):
        for closing in (.5,1.,2.,5.,10.):
            baseline=rho_from_ttc(gap/closing)
            for gap_error in (-.01,.01):
                for closing_error in (-.01,.01):
                    measured=rho_from_ttc((gap+gap_error)/(closing+closing_error))
                    error=abs(measured-baseline)
                    groups['reconstruction_errors'].append(error)
                    reconstruction.append(dict(gap_m=gap,closing_mps=closing,gap_error_m=gap_error,
                        closing_error_mps=closing_error,absolute_rho_error=error))
    quantile=.99
    bounds={name:float(np.quantile(values,quantile,method='higher')) for name,values in groups.items()}
    delta=derive_delta_eq(**groups,quantile=quantile)
    return dict(schema_version='aad.stage06.error-budget.v1',gate_status='pending_scientific_tolerances_and_dynamic_calibration',
        scientific_claim_eligible=False,metric='formal exp(-TTC/tau), fixed-window time-normalized mean on fully observed smooth closing fixtures',
        tau_s=tau,rule=dict(quantile=quantile,method='higher',aggregation='max of four source quantiles; existing derive_delta_eq unchanged',
            all_cases_retained=True,statistical_scope='Deterministic fixture envelope; not population99% coverage or an empirical SUMO trajectory error bound'),
        scope=dict(ttc0_s=[1.,2.,4.,8.,16.],horizon_s=[.2,.4,.8],steps_s=[.1,.05,.02,.01],
            reconstruction='conditional position/velocity precision0.01; gap>=1m, closing>=0.5m/s; actual FCD precision must be checked',
            exclusions=['near-zero closing','leader switches','missing observation','collision boundary','dynamic SUMO time-step sensitivity','physical real-world model discrepancy','P2 count-rate tolerance']),
        groups=groups,group_bounds=bounds,delta_eq_fixture_candidate=delta,
        compound_bounds=dict(two_arm_difference=2*delta,four_arm_DID=4*delta,
            note='Worst-case triangle bound across arm measurement errors; no independent-error assumption'),
        joint_source_sum_bound=sum(bounds.values()),
        joint_bound_note='Source errors can accumulate; the existing max rule is a candidate convention, not a guaranteed combined-error bound',
        cases=cases,reconstruction_cases=reconstruction,analytic_truth=_analytic_truth_audit(),physical_path_truth=_path_truth_audit(),
        path_scope='Existing archived-path four fixtures; tau_p exact for complete chains.0.1s observation quantization gives at most one frame for a single known arrival edge, not a global path bound.',
        scientific_approval=False,unresolved=['Actual paired dynamic0.1/0.05/0.02 runs and endpoint-specific error budget',
            'Researcher SESOI and tolerance adoption','Actual paired calibration variance and independent confirmatory sample size'])


def observed_quantization_sensitivity(path):
    """Conditional endpoint sensitivity on accepted calibration states, not truth."""
    path=Path(path)
    d=pd.read_parquet(path,columns=['net_gap_m','closing_speed_mps','measurement_status','ttc_valid'])
    valid=d.measurement_status.eq('valid') & d.ttc_valid.fillna(False)
    g=pd.to_numeric(d.net_gap_m,errors='coerce').to_numpy(float)
    c=pd.to_numeric(d.closing_speed_mps,errors='coerce').to_numpy(float)
    supported=valid.to_numpy() & np.isfinite(g) & np.isfinite(c) & (g>.01) & (c>.01)
    gs,cs=g[supported],c[supported]
    if not len(gs):
        raise ValueError('no observed states support this conditional quantization calculation')
    tau=P2_FORMAL_CONFIG.tau_s;base=np.exp(-gs/cs/tau)
    error=np.maximum.reduce([np.abs(np.exp(-(gs+dg)/(cs+dc)/tau)-base)
        for dg in (-.01,.01) for dc in (-.01,.01)])
    return dict(source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        valid_states=int(valid.sum()),supported_states=int(supported.sum()),
        excluded_boundary_states=int(valid.sum()-supported.sum()),
        higher99_absolute_rho_sensitivity=float(np.quantile(error,.99,method='higher')),
        maximum_absolute_rho_sensitivity=float(error.max()),
        interpretation='Four corners of +/-0.01 gap/closing perturbations of encoded native states; conditional precision sensitivity, not empirically known reconstruction error or a physical bias bound',
        treatment_contrast_direction='Unknown; B00 alone has no treatment contrast',
        exclusions='Missing/invalid observations, zero/near-zero closing, identity/leader switches and dynamic integration errors are not bounded by this calculation')


def write_budget(output,measured_state=None):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    audit=build_budget()
    if measured_state is not None:
        audit['observed_quantization_sensitivity']=observed_quantization_sensitivity(measured_state)
    for name,value in [('audit.json',audit)]:
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    repo=Path(__file__).resolve().parents[2]
    closure=['code/scripts/run_stage_0_6_error_budget_v1.py','code/src/riskprop/formal_risk_measurement.py',
        'code/src/riskprop/prelock_metrics.py','code/src/riskprop/prelock_validation.py',
        'code/src/riskprop/real_trajectory.py','code/src/riskprop/stage_0_1_sumo.py']
    manifest=dict(schema_version='aad.stage06.error-budget-manifest.v2',files={'audit.json':digest(output/'audit.json')},
        source_sha256={name:digest(repo/name) for name in closure})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (output/'SHA256SUMS').write_text(''.join(digest(output/name)+'  '+name+'\n' for name in ('audit.json','manifest.json')),encoding='utf-8',newline='\n')
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--measured-state',type=Path)
    args=parser.parse_args();result=write_budget(args.output,args.measured_state)
    print(json.dumps({k:result[k] for k in ('gate_status','group_bounds','delta_eq_fixture_candidate','compound_bounds')}))
