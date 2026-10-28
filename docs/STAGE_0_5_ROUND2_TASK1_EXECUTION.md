# AAD Stage 0.5 Round2 Task1 Execution

## Status

`ROUND2_TASK1_ENGINEERING_BLOCKED_BEFORE_CANDIDATE_NATIVE_LAUNCH`.

The researcher approved the frozen research space, Rule A, and one `minGap=1.0 m` candidate attempt. The current-source engineering smoke completed successfully inside the existing Linux capsule. The 420 s research candidate was not started because the current admission guard has no valid contract for this declared route-level factor. This report does not declare a Stage 0.5 pass, a Stage 0.6 freeze, a Protocol Lock, or Stage I authorization.

## Observation

The approved scientific bindings are unchanged: `S_UPSTREAM_MAIN` on `main_0` lanes 1–5 with `y[0,150) m`, mainline target lanes 1–5 with `y[150,350) m`, evaluation window `[120,390) s`, cohort `C_INPUT_ROUTE` (1112 IDs), and an auxiliary-lane diagnostic kept out of formal P2. Rule A is the approved conjunctive macro rule: each applicable 30 s block must remain inside the real-data pooled envelope, pooled block coverage must meet the existing cross-window baseline, and closing-speed coverage must meet that baseline. No new δ/h/B value was introduced.

The candidate input remains the Round1 binding `AAD-S0.5-ROUND2-TASK1-20261028-candidate-v1`: only the five `B_het_c0..c4_passenger` vTypes change `minGap` from 2.5 m to 1.0 m. Network, configuration, vehicle identities, departures, heterogeneous tau, sigma, actionStepLength, sigmaStep, lane-change and all formal definitions remain unchanged. The binding and SHA evidence are in [candidate_input_binding.json](../evidence/admission/AAD-S0.5-ROUND2-TASK1-20261028/candidate-v1/candidate_input_binding.json) and the Round1 [experiment specification](../evidence/results/RES-STAGE-0.5-ROUND1-TASK3-DECISION-20261028/round2_experiment_spec.json).

A new source staging was created with `prepare_stage_0_5_linux_stage_v4.py` under `/home/shen/AAD/code/tmp/stage05_v4_round2_task1_20261028`. It records source-closure SHA256 `15a30d0406e4a0bc6a7e3f5200315c04b56c9ce785c10c09e6c1a7da4c18ba41`, runtime-manifest SHA256 `703c433d85647e3b100ec407a0dfd9a629059905476ec544a320f56cd18a67c7`, SUMO 1.26.0 and TraCI protocol 22.

The required current-source engineering smoke ran once with synthetic inputs only. Its independent receipt is `Pass`, with identity, summary, collision-coverage, tripinfo, isolation, resource and network probes all passing. The receipt, controller receipt and exact staging metadata are retained in [engineering_smoke](../evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/engineering_smoke/).

The candidate native start count is zero; candidate TraCI connections are zero; locked holdout reads are zero. The engineering smoke used one SUMO process and one TraCI connection. No candidate FCD, lifecycle log, C6/D1 measurement or formal P2 result exists.

## Interpretation

The smoke result qualifies the current-source capsule as an engineering runtime/control test. It is not evidence about candidate traffic, P2, macro support or micro interaction.

The current `technical_preflight_v4` compares a research proposal against the existing B00/R1 run-definition contract and calls the existing route-factor validator. That contract accepts the prior supply/ramp forms but has no reviewed representation for a vType-only `minGap` factor. A candidate-specific policy/proposal therefore cannot pass the existing preflight without changing a persistent admission guard. Treating the candidate route as its own base, bypassing the validator, or launching through a hand-built envelope would invalidate the integrity boundary and was not done.

Because the candidate never started, source P2, target P2, macro Rule A, net-gap/closing-speed/TTC distributions, D1 exposure and event-specific physical-path witness are all `Unknown`/not evaluated. Missing results are not zero and do not support a no-effect conclusion.

## Proposal

Retain the single approved candidate and the fixed one-attempt budget. If the admission extension is approved, it must be a narrowly scoped branch that:

1. accepts only `AAD-S0.5-ROUND2-TASK1`;
2. permits exactly five declared `B_het_*_passenger` `minGap` changes from 2.5 to 1.0;
3. rechecks every other vType, vehicle, route, seed, clock, supply, window, cohort and measurement field against A03;
4. keeps the existing capsule, receipt, ledger, C6/D1/P2 chain and Rule A unchanged; and
5. binds the new proposal, policy, current-source smoke receipt and candidate input hashes before any candidate process is created.

No second candidate, seed search, threshold change, window move, auxiliary-lane pooling or perturbation increase is proposed.

## Awaiting Researcher Decision

| Item | Current state | Decision needed |
|---|---|---|
| Research space, Rule A and one minGap candidate | Approved | None |
| Narrow persistent admission extension for the minGap factor | Blocked by engineering guard and automatic review | Explicit approval required |
| Independent seed | Not authorized | Decide only after a qualifying primary result |
| Stage 0.6 δ/h/B | Unapproved | Remains outside this task |

## Blocked / Unresolved

The candidate experiment has no scientific outcome because the native candidate launch was withheld before process creation. The automatic approval review rejected the attempted core-guard patch because it could broaden allowed scientific-definition fields and weaken an existing integrity boundary. The exact rejection and the safe next step are recorded in [engineering_block.json](../evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/engineering_block.json). This is an engineering admission block, not evidence that `minGap=1.0` failed scientifically.

## Evidence and validation

- [Prelaunch validation](../evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/prelaunch_validation.json)
- [Decision matrix](../evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/decision_matrix.json)
- [Acceptance matrix](../evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/acceptance_matrix.json)
- [Run record](../evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/run_record.json)
- [Manifest](../evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/manifest.json) and [SHA256SUMS](../evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/SHA256SUMS)

The evidence package manifest excludes itself and `SHA256SUMS`; an independent verification found 18 payload files and 19 SHA lines with no hash or byte-count errors.
