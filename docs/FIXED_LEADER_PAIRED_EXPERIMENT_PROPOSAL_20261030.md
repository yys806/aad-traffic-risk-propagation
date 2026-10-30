# Fixed-leader paired experiment — minimum matrix proposal

Date: 2026-10-30. Research direction: Agreed / conditional. Exact repetition matrix: **Proposed / Awaiting Researcher Decision**. Execution: **Blocked / Not Run**. This is independent of the closed original Round2 candidate; it does not authorize original-candidate confirmation or Round3 execution.

## Existing evidence and configuration binding

Task6 reused the historical 324-run grid: 12 pairs × 9 configurations × 3 seeds, each 20 s. Direct inspection of `RES-STAGE-0.5-METHOD-EXPANSION-V1/response_plan.json` and `response_metrics.csv` confirms seeds **20261101, 20261102, 20261103**. Old paired records use homogeneous tau=1.0 and sigma=0.5. They are not current heterogeneous B00, not physically verified independent reference, and not a power calculation for the new experiment. The old package's run_metadata hash mismatch and missing trajectory_coverage_matrix remain historical issues; only individually verified response artifacts are reused.

Across 12 historical pairs, median within-pair, three-seed SD of gap error is 1.4713 percentage points for homogeneous baseline and 1.8311 for homogeneous minGap1.0; maximum SDs are 3.8741/3.9892 pp. Median lag SD is 0.3031/0.3103 s, maximum 0.8737 s in both. These describe old seed variability; they neither prove adequacy nor justify changing sigma or choosing favorable seeds. Full unrounded values and input hashes are in the bounded closure audit.

Direct XML comparison of the actual sealed B00 A03 and Round2 run inputs finds exactly five differences: `B_het_c0_passenger` through `B_het_c4_passenger`, minGap 2.5→1.0. All other route elements/attributes match; `network.net.xml` and `run.sumocfg` are byte-identical. The five tau values remain 0.7389146576529666, 1.093342856277335, 1.3877275660721775, 1.8288599276236361 and 2.5614676647488244. No homogeneous substitute is permitted. Historical run duration420 s and seed20261201 do not become the new replay duration or seed plan.

## Proposed exact paired repetition matrix

For each physically qualified segment i (N is currently Unknown):

| Paired replicate | Seed | Arm A | Arm B |
|---|---:|---|---|
| 1 | 20261101 | actual B00 vType/context, minGap2.5 | same, minGap1.0 only |
| 2 | 20261102 | same frozen input and initial state | identical paired input and initial state |
| 3 | 20261103 | same frozen input and initial state | identical paired input and initial state |

Recommendation: three predeclared repeats per arm per segment, **6N total runs**. Reusing the complete historical seed set gives a finite, auditable starting design with stochastic spread visible; it is not a guarantee of statistical precision. Do not run until researcher approval of this exact matrix and all physical/engineering gates. N, segment IDs, durations and initial states cannot be honestly frozen before physical-quality review; no cases are selected here. No automatic additional repeats if results are zero, noisy or unfavorable.

## Cost and feasibility

If qualified segment lengths are T_i seconds, cost is 6×sum(T_i) simulated vehicle-pair seconds and, preserving 0.05 s native steps, about120×sum(T_i) steps plus separately documented initialization. At 0.1 s measurement cadence it is about60×sum(T_i) recorded pair states, excluding endpoints. Numerical wall time, disk size, N and exact horizon are Unknown until input qualification and implementation profiling. The old grid totals6480 simulated seconds but supplies no verified wall-time estimate for this setup. Record actual available disk before any large run; no history cleanup.

Existing fixed-input engineering must be checked statically first, then under a separately frozen admission record only when all gates pass. Require real leader trajectory enforcement and readback; interpolation, initial matching, lag estimator and permitted numerical tracking error need documented physical support and approval before execution. Normal network simulation cannot substitute for fixed input. Retain insertion delay and achieved initial state; an unmatched initial state blocks the pair rather than shifting time or discarding an unfavorable arm.

## Metrics and uncertainty proposal

Report gap distribution; positive closing-speed distribution; joint gap–closing distribution; TTC distribution/tail using unchanged definitions; follower speed response; response timing/dynamics; Formal P2 members/onset/confirmation; D1 local exposure. Show raw sample counts, unique followers/segments, observable durations, missingness and per-seed paired values. C and D1 stay separate; unresolved native/formal endpoint and clock differences must be disclosed and fixed only by a new researcher decision if required for execution.

Proposed uncertainty: per-segment paired A/B differences for all three seeds with range and SD; segment-level paired resampling only if enough distinct qualified segments exist, using one shared resampling index across both arms and all metrics. Bootstrap seed20261030 and2000 resamples are a proposal for review, not an implemented statistical protocol. With too few segments retain individual values and Unknown population uncertainty; repeated frames or seeds are not independent vehicles or independent days. No scientific equivalence tolerance, effect-size threshold or power claim is invented. Final estimators/bins/lag rules and uncertainty plan must be frozen before running.

## Failure and stop rules

Stop before launch if license/time/space/physical quality, stable identity, leader-input extraction, fair matching, environment/resources, exact seed approval or frozen metrics are missing. Stop the affected pair/campaign on identity/time discontinuity, unverifiable enforced leader input, unmatched initial conditions, any non-minGap arm difference, collision/teleport, native error, resource limit or incomplete measurement. Preserve failed attempts and diagnostics; no seed replacement, hidden exclusion, automatic retry or modified scientific threshold. Report observations only; interpretation and next candidate choice remain with the researcher.
