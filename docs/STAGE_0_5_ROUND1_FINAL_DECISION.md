# AAD Stage 0.5 Round1 Final Scientific Decision

## Status

`ROUND1_ENGINEERING_AND_EVIDENCE_READY` and `ROUND1_AWAITING_RESEARCHER_DECISION`.

The first-round engineering, offline analysis, evidence repair and static Round2 preparation are complete. This document does not declare `ROUND1_SCIENTIFIC_FREEZE_APPROVED`, does not open a Protocol Lock, and does not authorize SUMO/TraCI execution.

## Observation

Round1 Task 1 and Task 2 are accepted inputs to this decision. R0 was a design packet; R1 executed B10, B01 and B11 once each; B00 uses the accepted A03 trajectory `WEEK_0750_B00_IC1_s20261201_A03`. All formal source and target P2 counts in B00/B10/B01/B11 are zero. The offline event inventory contains B10=7, B01=1 and B11=19 full event segments, with evaluation-window onsets 5/0/17. B11 has 16/19 full segments on the auxiliary/unmapped lane, 16/17 within-window auxiliary onsets, two full `target_main` segments outside the window, and one within-window target-outside mainline segment. These are diagnostic segments, not formal P2 counts.

The fixed R1 main definitions are `S_UPSTREAM_MAIN` (main_0, lanes 1–5, y[0,150)), target mainline lanes 1–5, y[150,350), evaluation window [120,390), and `C_INPUT_ROUTE` (1112 IDs). The source region has reliable exposure but no qualified source event. Missing state and unresolved links remain unknown; no event-specific physical arrival time exists.

The accepted B00 A03 input is a 420 s, 0.05 s internal-step, 0.1 s recording-step, seed 20261201 run. Its actual five passenger vTypes use Krauss, `minGap=2.5`, `sigma=0.5`, `actionStepLength=0.1`, `sigmaStep=1.0`, LC2013, and heterogeneous tau values 0.7389146577, 1.0933428563, 1.3877275661, 1.8288599276 and 2.5614676647 s. The A03 input hashes are network `d69c79c4…bdc`, routes `b6df8d9c…a7574`, and configuration `c55b242f…c6c6`.

The historical 324-run method expansion used 9 configurations × 3 seeds × 12 observed pairs. Its `K_tau1.0_minGap1.0` configuration improved paired Brockfeld gap error by 7.31 percentage points and NRMSE gap by 0.0702 over its homogeneous `K_tau1.0` baseline; the three per-seed changes were all negative (−7.70, −7.05, −7.18 pp). This is a micro-level, pair-replay result. Its baseline was homogeneous tau=1.0, so it is not a direct network-level contrast to heterogeneous B00 A03. The same historical study found tau increases worsened the micro metric (+18.31/+40.70/+72.51 pp), minGap=5.0 worsened it (+29.75 pp), and stated that the physical standstill gap is not identified.

The real state-support evidence provides observed density, speed, low-speed, speed-dispersion, closing-speed and net-gap envelopes, but its own verdict says the interaction/state-support combination is not established for the prior candidates. Numeric macro tolerances and Stage 0.6 δ/h/B remain unapproved.

## Interpretation

The first-round evidence supports a narrow scientific choice: preserve the predeclared mainline estimand and isolate the auxiliary lane as a separate mechanism diagnostic. Changing source, target, window or cohort after seeing the event locations would change the estimand and would turn the zero-source result into a selection artifact.

The most defensible next micro candidate is a current-B00-preserving minGap reduction. Historical evidence makes minGap=1.0 the strongest single-factor proposal, but it does not establish that the network-level candidate will produce a source P2 event or preserve the macro state. The candidate therefore tests mechanism support; it is not a calibration claim and not a Stage 0.5 pass.

A weighted macro–micro score is scientifically inappropriate here. Macro state support is a necessary hard condition, while micro interaction and formal source P2 are the primary mechanism outcomes. A failed macro condition cannot be compensated by more P2 events, and a missing source event cannot be compensated by a macro match.

## Proposal

### Frozen research-space recommendation

| Item | Recommendation | State | Researcher approval |
|---|---|---|---|
| Formal source | `S_UPSTREAM_MAIN`, main_0, lanes 1–5, y[0,150) | Proposed / Awaiting Decision | Required |
| Formal target | Mainline lanes 1–5, y[150,350) | R1 diagnostic definition; protocol approval pending | Required |
| Evaluation window | [120,390) s | R1 fixed; not a Stage 0.5 protocol lock | Required |
| Main cohort | `C_INPUT_ROUTE`, 1112 pre-treatment route IDs | Used in R1; Proposed for Round2 | Required |
| Auxiliary lane | Separate secondary mechanism diagnostic; never pooled into formal P2 | Awaiting Decision | Required |
| Physical path | Identity continuity, ≤0.11 s continuity, verified native lane connection, time-indexed leader→follower witness; onset/confirmation/physical/message clocks separate | Proposed | Required |

### Unique Round2 candidate

`B00_Krauss_heterogeneous_minGap1.0` is the single preferred proposal:

- copy the accepted A03 network, configuration, routes, identities, seed, duration, step sizes and measurement chain;
- change only `minGap` from 2.5 m to 1.0 m on the five `B_het_*_passenger` vTypes;
- preserve each heterogeneous tau, sigma=0.5, LC2013, action-step and all vehicle-level fields;
- run one primary candidate attempt at seed 20261201, paired to the accepted B00 baseline; do not rerun B00;
- permit an independent-seed confirmation only after the primary candidate passes engineering, formal source-event, macro hard-constraint and measurement checks, and only after separate researcher approval.

The exact candidate inputs and SHA bindings are in `evidence/admission/AAD-S0.5-ROUND2-TASK1-20261028/candidate-v1/inputs/` and `evidence/results/RES-STAGE-0.5-ROUND1-TASK3-DECISION-20261028/round2_experiment_spec.json`.

### Joint acceptance recommendation

The proposed acceptance is conjunctive:

1. **Macro hard constraint:** report 30 s block speed mean/dispersion, density, low-speed share, closing-speed distribution and target-region support against the existing real-domain envelopes. No new numeric δ/h/B is invented here. If the applicable approved state-support rule is false or undecidable, stop.
2. **Micro interaction:** require identity-resolved following, valid measurement status, ≤0.11 s continuity, verified lane continuity, net-gap/closing-speed distributions and time-continuous relative motion.
3. **Formal risk:** use the unchanged formal rule: 0<TTC<2 s, duration ≥0.2 s, max gap ≤0.11 s, reliable exposure and existing source/target/window/cohort definitions. Do not reclassify auxiliary events as formal source events.
4. **Engineering:** require the same 420 s/8400-step lifecycle, clock, identity, collision/teleport/discard, resource, isolation and native receipt checks as accepted B00/R1.
5. **Scientific eligibility:** only a candidate satisfying every necessary layer becomes eligible for the independent-seed decision. It does not pass Stage 0.5 automatically.

## Awaiting Researcher Decision

A single confirmation can approve or reject the following set:

| Decision | Recommended value |
|---|---|
| Formal source | Preserve `S_UPSTREAM_MAIN` |
| Formal target/window | Preserve lanes 1–5, y[150,350), [120,390) s |
| Cohort | Preserve `C_INPUT_ROUTE` (1112 IDs) |
| Auxiliary lane | Keep separate secondary diagnostic |
| Physical path | Adopt the time-indexed identity/lane/leader witness rule |
| Round2 primary candidate | Approve one-run current-B00 heterogeneous `minGap=1.0` proposal |
| Independent seed | Do not authorize in advance; decide only if primary candidate qualifies |
| Macro tolerances / Stage 0.6 δ/h/B | Remain unapproved in this task |

## Blocked / Unresolved

- No current-B00 network-level result exists for minGap=1.0; this task deliberately does not create one.
- The physical standstill gap is not identified by existing evidence.
- Numeric macro tolerances and Stage 0.6 δ/h/B are not frozen.
- The current native execution build remains locked pending explicit researcher approval and the applicable admission checks.
- A Round2 candidate with no source P2, failed macro support, engineering failure or incomplete observation must stop without parameter search or semantic rescue.

## Round1 closure

Round1 meets the engineering and evidence closure requirement. It is awaiting the compact researcher decision above. It does not constitute Stage 0.5 scientific Gate passage, Stage 0.6 freeze or Stage I authorization.

## Evidence

- First-round report: `docs/STAGE_0_5_FIRST_ROUND_OFFLINE_DECISION_20261028.md`
- First-round evidence: `evidence/results/RES-STAGE-0.5-FIRST-ROUND-OFFLINE-DECISION-20261028/`
- Round1 Task3 evidence: `evidence/results/RES-STAGE-0.5-ROUND1-TASK3-DECISION-20261028/`
- Round2 candidate inputs: `evidence/admission/AAD-S0.5-ROUND2-TASK1-20261028/candidate-v1/`

## Static verification

The static Round2 candidate test and project-doc tests pass (14 passed); compileall passes. No SUMO/TraCI was started. Machine hashes are in the Round1 Task3 evidence package.
