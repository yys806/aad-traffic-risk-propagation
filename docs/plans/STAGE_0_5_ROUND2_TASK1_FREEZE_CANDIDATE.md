# Stage 0.5 Round2 Task1 Freeze Candidate

## Approval status

`Ready for Researcher Approval`; no native run has been authorized or started. This freeze candidate is the sole primary proposal prepared by Round1 Task3.

## Exact candidate

Experiment: `AAD-S0.5-ROUND2-TASK1`

Candidate: `AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1`

Base: accepted `WEEK_0750_B00_IC1_s20261201_A03`, `B00_EXECUTED_MEASUREMENT_ACCEPTED`.

The candidate copies the accepted A03 network and configuration and changes only the five `B_het_*_passenger` `minGap` attributes in `routes.rou.xml` from 2.5 m to 1.0 m. All heterogeneous tau values, sigma, action-step, lane-change, acceleration/deceleration, routes, vehicle IDs, initial states, seed, duration and schedule remain unchanged.

Base input SHA256:

- `network.net.xml`: `d69c79c4c2303125e696d86b5907cbd1e043f21971dde4c4903eb3ccf84dbdcf`
- `routes.rou.xml`: `b6df8d9ce52b56fac50899cc2e6d1329c7858325aae0f0c86c76d77f796a7574`
- `run.sumocfg`: `c55b242f09b6a86527852bf686f06f3347abc44aa1c16c199c51935ce93dc6c6`

Candidate input SHA256:

- `network.net.xml`: `d69c79c4c2303125e696d86b5907cbd1e043f21971dde4c4903eb3ccf84dbdcf`
- `routes.rou.xml`: `a4c78db55984cc8c320b06ec2e257bdf6d4902c0dfdf015348157e30cdb80e79`
- `run.sumocfg`: `c55b242f09b6a86527852bf686f06f3347abc44aa1c16c199c51935ce93dc6c6`

## Fixed design

- Scene: US-101 0750.
- Seed: 20261201 for the one primary paired candidate attempt.
- Duration: 420 s.
- Internal step: 0.05 s.
- Recording step: 0.1 s.
- Evaluation window: [120,390) s.
- Source: `S_UPSTREAM_MAIN`, main_0, lanes 1–5, y[0,150).
- Target: mainline lanes 1–5, y[150,350).
- Cohort: `C_INPUT_ROUTE`, 1112 pre-treatment route-eligible IDs.
- Formal P2: existing TTC<2 s, duration ≥0.2 s, max gap ≤0.11 s, reliable identity/quality semantics.
- Physical path: proposed time-indexed identity/lane/leader witness; no message-clock substitution.

The accepted B00 trajectory and measurement are reused. A new candidate trajectory is required because changing minGap changes behavior; the baseline is not rerun.

## Execution and stop rules

Primary budget is exactly one candidate attempt, with no parameter search, seed selection, intensity search or repeated retries. Use the existing Stage 0.5 native admission/capsule and measurement chain. The current native build is locked until explicit approval.

Stop immediately on native error, input/hash drift, identity or clock mismatch, incomplete lifecycle, collision/teleport/discard, resource/isolation failure, incomplete receipt, invalid formal measurement, macro hard-constraint failure or any unapproved parameter drift. Do not change thresholds, duration, continuity, window, source, target, cohort, seed or auxiliary-lane inclusion to rescue a failure.

If the primary run qualifies on every necessary layer and produces a source P2, an independent seed (proposed separately) may be considered. It is not pre-authorized by this document.

## Acceptance matrix

The acceptance is conjunctive and has no weighted average:

| Layer | Required evidence | Status of numeric rule |
|---|---|---|
| Macro | 30 s block speed/density/low-speed/share/dispersion/closing-speed and target support against real-domain envelopes | Existing envelope is evidence; δ/h/B not frozen |
| Micro | Identity-resolved net gap, closing speed, relative motion, time continuity and lane connection | Measurement fields and continuity contract available; scientific path rule Proposed |
| Formal risk | Source P2, target P2, event duration, TTC, reliable exposure and statuses | Existing formal P2 rule unchanged |
| Engineering | 420 s/8400 steps, receipt, lifecycle, input hashes, resources, isolation | Reuse accepted B00/R1 checks; candidate must pass anew |
| Scientific eligibility | All necessary layers pass and no post-outcome selection | Proposed Round2 eligibility gate; not Stage 0.5 Pass |

Outcomes are interpreted as follows:

- source P2 + macro pass: eligible for independent-confirmation decision;
- source P2 + macro fail: mechanism result is not joint success and stops;
- no source P2: no-source result, no parameter search;
- engineering failure: preserve failure, no scientific interpretation;
- observation insufficiency: preserve unknown, no imputation.

## Reproducibility bindings

The machine-readable specification, decision matrix, candidate selection, acceptance matrix, validation record, manifest and SHA256SUMS are in `evidence/results/RES-STAGE-0.5-ROUND1-TASK3-DECISION-20261028/`. Candidate inputs are in `evidence/admission/AAD-S0.5-ROUND2-TASK1-20261028/candidate-v1/`. The current source hashes and reused R1/B00 evidence bindings are recorded in `round2_experiment_spec.json`.

## Non-goals

This candidate does not alter formal P2, does not open locked holdout, does not freeze Stage 0.6, does not create a Protocol Lock and does not authorize Stage I.

## Static verification

The candidate input test plus project-doc tests passed (14 passed), and compileall passed. These checks inspect only files and XML; they do not start SUMO/TraCI. Machine validation and SHA results are recorded in the Round1 Task3 evidence directory.
