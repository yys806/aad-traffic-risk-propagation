# Task10 historical reuse audit

## Existing results reused

- Task4/5: formal source counts 167/159, target counts 174/252, unique onset attribution, and independent two-window scope were reused without re-extracting Formal P2.
- Task6: gap–closing joint distributions, event/control contexts, residuals, leader/lane transition flags and population diagnostics were reused from the sealed Task6 package and local identity-context tables.
- Task8: five-second `C_initial/C_f/C_l/C/C_gap/R`, fixed onset-leader diagnostics, seven SUMO near-threshold cases and the official Krauss source map were reused. `R` was not recomputed as a new method.
- Task9: static B00/Round2 arm audit, common-input contract, seed set and blocked physical-input status were reused from the Task9 evidence package.

## Existing code and methods

- `code/scripts/analyze_stage_0_5_round2_task6_micro_interaction.py` and its saved identity-context outputs supply the quality and transition fields.
- `code/scripts/analyze_stage_0_5_post_r2_task8_kinematic_mechanism.py` supplies the existing decomposition and residual definitions.
- `code/src/riskprop/stage_0_5_fixed_leader_pair.py` supplies Task9's fail-closed arm/input contract.
- Punzo-style internal consistency, platoon/gap consistency and jerk/spectral method boundaries were taken from the existing literature map; no new DSTE/STMap pipeline was trained or implemented.

## New work in Task10

1. Event/control quality comparison over the existing Task6 source contexts at the declared one-second anchor.
2. A bounded feasibility decision for event-level PreciseNGSIM crosswalk using the existing Task7.1 inspection records.
3. A time-expanded source→target same-trajectory candidate audit on the two canonical windows, with B's five witness components reported as PASS/FAIL/UNKNOWN.
4. A final Task9 readiness decision and Round2 final decision.

## Not repeated

No full Formal P2 extraction, Task6 rerun, Task8 decomposition rerun, historical 324-run replay, video acquisition, new data request, SUMO/TraCI execution, third window read, holdout read, parameter search or Formal P2/D1/B definition change was performed.
