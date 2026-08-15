# RiskProp Pilot Code

This folder is the first-pass code skeleton for the summer pilot topic:

> Mixed-autonomy risk event extraction, propagation graph construction, and counterfactual intervention analysis based on DRIFT/Flow rollout emissions.

## Current Scope

The current version reads an emission CSV and writes event, episode, graph, and role outputs:

- `risk_events.csv`: frame-level risk detections such as hard braking, low TTC, low THW, and near-miss.
- `risk_episodes.csv`: consecutive detections merged into event-level risk episodes.
- `risk_candidate_edges.csv`: all plausible time-space candidate relations between episodes.
- `risk_edges.csv`: selected direct propagation edges, capped per source and relation type.
- `risk_node_roles.csv`: transparent source/amplifier/absorber proxy scores.
- `risk_chains.csv`: a lightweight chain proxy table.
- `risk_summary.csv`: run-level propagation statistics.

## Expected Input Columns

The pipeline works best with these columns:

- `run_id`
- `time`
- `id` or `vehicle_id`
- `speed`
- `realized_accel` or `acceleration`
- `headway`
- `leader_id`
- `leader_rel_speed`
- `x`
- `lane`, or Flow's `edge_id` plus `lane_number`

Missing optional fields are filled with conservative defaults where possible.

Braking detections are non-overlapping. `hard_braking` uses `event_severity=hard|severe`; realized deceleration below `-15 m/s^2` is labeled `safe_speed_override_candidate` and excluded from ordinary braking. TTC and THW require a valid leader and physically valid headway.

## Run Example

```powershell
cd D:\shen\TJU\AAD\code
python -m pytest tests -q
python -m riskprop.cli --input examples\sample_emissions.csv --output outputs\sample_run
```

## Analyse Existing Flow Results

The first real Flow merge smoke was saved before episode analysis was added. Rebuild the direct graph and figures from its frame-level risk events with:

```powershell
python scripts\analyse_existing_run.py `
  --events outputs\feasibility_week\riskprop_real_merge_server\risk_events.csv `
  --output outputs\pilot_20260714\real_merge_20pct
```

This creates a compact result package containing direct-edge data, role scores, intervention-candidate screening, and analysis figures.

## Audit DRIFT Before Propagation Analysis

The qualification audit checks formal experiment coverage, like-for-like baseline comparisons, 95% confidence intervals, OOD results, raw emission fields, and risk-event semantics. On this machine the original emissions are available through WSL:

```powershell
python scripts\audit_drift_qualification.py `
  --raw-output-root "\\wsl.localhost\Ubuntu\home\shen\shen\mixed_autonomy_lab\outputs"
```

The report and supporting CSV/JSON files are written to `outputs\drift_qualification_20260716`. This audit is CPU-only. Model retraining is not part of the command.

## Extract The Formal Event Dataset

The formal extractor uses the adopted DRIFT emissions plus matching FS/PI formal runs. It reports event rates per 1000 vehicle-seconds, TTC/braking threshold sensitivity, adjacent-frame context, and a stratified review sample:

```powershell
python scripts\extract_full_risk_events.py `
  --raw-output-root "\\wsl.localhost\Ubuntu\home\shen\shen\mixed_autonomy_lab\outputs"
```

Outputs are written to `outputs\risk_event_dataset_20260716`. The local one-hop/multi-hop baseline may use non-boundary episodes after excluding `safe_speed_override_candidate`; interaction transitions and episodes adjacent to override candidates must remain separately flagged. IDM, Flow-AIL, and Flow-RL are not included at event level because their raw emissions are not present locally.

## Build The Local Propagation Baseline

After the formal event dataset is available, build the local one-hop/multi-hop baseline, vehicle-wise circular time-shift null, sensitivity tables, and ten figures with:

```powershell
python scripts\build_local_propagation_baseline.py `
  --input outputs\risk_event_dataset_20260716 `
  --output outputs\local_propagation_baseline_20260718 `
  --permutations 100 `
  --seed 20260718 `
  --workers 8
```

This command is CPU-only. It excludes `safe_speed_override_candidate` and vehicle entry/exit boundary episodes from the baseline graph, but keeps interaction-transition and adjacent-override context as explicit strata.

## Next Extension Points

1. Add a topology-aware longitudinal coordinate across merge edges.
2. Add unsafe merge/cut-in detection using lane and leader changes.
3. Add full chain traversal metrics: propagation depth, delay, distance, amplification ratio, and decay rate.
4. Test residual nonlocal candidates after conditioning on the local baseline and context strata.
5. Add counterfactual experiment wrappers that call the existing DRIFT rollout code.
