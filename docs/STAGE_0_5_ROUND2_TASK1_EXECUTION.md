# AAD Stage 0.5 Round2 Task1 Execution

## Status

`ROUND2_TASK1_ENGINEERING_AND_EVIDENCE_READY`; the primary candidate result is recorded and `ROUND2_TASK1_SCIENTIFIC_RESULT_RECORDED`. The source P2 criterion was not met, so the run is not eligible for an independent-seed confirmation. Stage 0.5 Gate, Stage 0.6, Protocol Lock and Stage I are unchanged.

The researcher-approved bindings remain fixed: `S_UPSTREAM_MAIN` on `main_0` lanes 1–5 with `y[0,150) m`; target mainline lanes 1–5 with `y[150,350) m`; evaluation window `[120,390) s`; `C_INPUT_ROUTE` (1112 IDs); auxiliary lanes are separate diagnostics; Rule A is the strict joint macro-support rule. The only candidate change was the five `B_het_c0..c4_passenger` `minGap` values from 2.5 m to 1.0 m.

## Observation

The exact candidate `AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1` was started once, with seed `20261201`, 420 s duration, 0.05 s internal steps and 0.1 s recording. It completed 8,400 native steps inside the existing Linux capsule. There was one candidate SUMO process and one TraCI connection; no retry, independent seed, locked-holdout read or post-outcome selection occurred. The separate current-source engineering smoke was run once with synthetic inputs.

The native execution ledger records `reserved → running → completed` with wall time 396.642 s and 149,579,624 bytes of artifacts. The first in-process measurement attempt ended as `measurement_rejected` because the proposal pointed `capability_evidence_path` at a staging record rather than the kernel capability record. The original ledger event is retained. A zero-launch remeasurement of the same sealed artifacts, using the existing `measure_completed_capsule` chain and a corrected evidence binding, passed all eight checks: input fidelity, initialization accounting, identity/clock, D1 contract, all 18 common cells, full-context events, resources and task isolation. The repaired result does not rewrite the original ledger status. See [the final machine package](../evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/execution_final_v1/), [the assessment](../code/outputs/formal/calibration/aad_round2_task1_assessment_v1/assessment_result.json) and [the full ledger](../docs/audits/stage_0_5_ready_to_admit_v3/execution_events.jsonl).

Rule A **passes** for the candidate. The target-region mean state is density `44.0526 veh/km/lane`, speed `10.3333 m/s`, and inside the existing pooled density–speed envelope. All 18 `[120,390) s × y[150,350) m` 30 s cells have valid support; pooled speed coverage is `1.0000` and pooled closing-speed coverage is `1.0000`, against the existing cross-window baseline `0.63636`. Target speed SD is `3.1597 m/s`, low-speed share is `0.0662`, and the candidate remains within the observed support envelope. The paired B00 A03 also passes Rule A (speed coverage `1.0000`, closing coverage `0.8333`). These are evidence-derived Rule A values, not new Stage 0.6 tolerances.

The micro interaction changed materially relative to B00 A03 in the fixed target cohort. Mean net gap decreased from `20.9223 m` to `18.7783 m` (median `18.7104 → 16.5804 m`; p05 `9.0904 → 7.1904 m`). Mean closing speed increased from `0.2173` to `0.3111 m/s`; speed mean changed `10.4645 → 10.3333 m/s`, speed SD `2.8709 → 3.1597 m/s`, and low-speed share `0.0432 → 0.0662`. Valid-TTC states with `0<TTC<2 s` changed from `0` to `4`; the candidate minimum valid TTC was `1.1147 s` versus B00 minimum `3.7918 s`. Identity-resolved leader fraction was `0.8881 → 0.8983`, while native-lane continuity remained complete in both arms. These results show a tighter and more variable micro interaction, not merely a change in aggregate speed.

The unchanged risk definition produced **zero formal source-region onsets** for the candidate and B00. The candidate produced one qualified target-cohort event under the existing D1/P2 adapter: follower `m00485`, leader `r00036`, `main_1_1` lane 5, onset `271.8 s`, confirmation `272.0 s`, end `272.1 s`, span `0.3 s`, with `10,572.4 veh-s` local evaluable exposure and diagnostic rate `0.3405` per evaluable vehicle-hour. Its onset is at `y=189.904 m`, so it is a `target_main` event and cannot be counted as a source event. The exploratory all-space segment inventory contains one `target_main` segment and no auxiliary-lane segment. The adapter records `formal_equivalence_accepted=false`; therefore this is a fixed-rule formal-definition/D1 result, not a Stage 0.5 scientific-equivalence claim.

## Interpretation

At the fixed source, target, window, cohort and seed, reducing heterogeneous `minGap` to 1.0 m improved the local interaction tail enough to produce a target-region event while preserving Rule A macro support. It did not produce the required source-region P2. The primary single-factor hypothesis therefore fails for the stated source estimand in this one authorized run. The result must not be rescued by moving the source, changing the window, pooling auxiliary events, changing TTC or duration, choosing another seed or increasing perturbation strength.

The target event has identity, time and lane continuity within the local adapter, but no event-specific physical influence arrival time is promoted. The physical-path policy still requires a time-indexed identity, lane-connection and leader-to-follower witness; a message or local confirmation timestamp is not a physical arrival timestamp. Its status remains `Unknown` for scientific path propagation.

## Proposal

Treat this run as a completed single-factor mechanism test with a real macro pass and a real **no-source-P2** outcome. Close the primary Round2 search branch under the frozen stopping rule. Retain the target interaction result as secondary diagnostic evidence only. Any new candidate, changed estimand or independent seed requires a separate researcher decision and a new exact admission record; this task authorizes none.

## Awaiting Researcher Decision

| Item | Evidence-based state | Researcher action |
|---|---|---|
| Frozen research space and Rule A | Used exactly and macro PASS | No change needed |
| `minGap=1.0 m` as a source-P2 mechanism candidate | Source P2 = 0; target interaction changed | Decide whether to close this branch as a source-mechanism failure |
| Independent seed confirmation | Not eligible because source P2 was absent | Do not authorize automatically |
| Auxiliary-lane role or estimand change | No auxiliary event was mixed; current estimand remains fixed | Any change requires a new scientific decision |
| Stage 0.6 δ/h/B and Stage I | Not frozen or authorized | Remain outside this task |

## Blocked / Unresolved

- No formal source-region P2 was observed, so independent confirmation is blocked by the approved stop rule.
- The one target event is not evidence of an event-specific physical arrival time; physical propagation remains `Unknown`.
- The D1/P2 adapter's `formal_equivalence_accepted` flag remains false, as in the accepted B00/R1 chain.
- The original measurement rejection remains in the ledger as history; the all-pass zero-launch remeasurement is a separate evidence record.
- Stage 0.5 Gate, Stage 0.6, Protocol Lock and Stage I are not promoted by this result.

## Evidence and validation

- [Round2 final machine evidence](../evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/execution_final_v1/)
- [Offline comparison](../evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/round2_offline_comparison.json)
- [Candidate output root](../code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1/)
- [Task-specific admission tests](../code/tests/test_stage_0_5_round2_task1_admission.py)
- [Round1 decision](STAGE_0_5_ROUND1_FINAL_DECISION.md) and [Round2 freeze candidate](plans/STAGE_0_5_ROUND2_TASK1_FREEZE_CANDIDATE.md)

The final machine package manifest excludes itself and `SHA256SUMS`; the package keeps compact summaries and hashes for the sealed raw outputs instead of copying the large trajectory files.
