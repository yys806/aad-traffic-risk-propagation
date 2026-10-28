# Stage 0.5 Round2 Task1 Prelaunch Decision

## Status

`ROUND1_ENGINEERING_AND_EVIDENCE_READY` and `ROUND1_AWAITING_RESEARCHER_DECISION`. The candidate input is statically valid, but no native launch is allowed until the researcher confirms the scientific space, physical-path policy and macro rule.

## Macro rule candidates

- **A — strict joint support (recommended):** each 30 s block must be inside the observed pooled density–speed envelope at the existing cross-window baseline coverage, and the closing-speed support must meet the same baseline. Existing 30-cell offline comparison: 10 pass.
- **B — macro-only permissive:** require mean state and pooled block coverage at the existing baseline, but do not gate on closing support. Existing comparison: 11 pass; it admits one previously mechanism-incompatible case and is therefore less suitable for the stated micro-first objective.
- **C — descriptor-only:** report macro descriptors without a numeric pass rule. Existing comparison is `INSUFFICIENT_EVIDENCE`; it cannot authorize a joint experiment.

Rule A is the unique recommendation. Its numbers come from the existing real-domain envelopes and cross-window baseline; they are candidate acceptance values, not Stage 0.6 δ/h/B or a new scientific tolerance freeze.

## Confirmation required

Please confirm all of the following before the first native launch: preserve `S_UPSTREAM_MAIN`, target lanes 1–5 y[150,350), window [120,390), `C_INPUT_ROUTE`, separate auxiliary diagnostics, the proposed time-indexed physical-path witness, and macro Rule A; approve one primary candidate run with current-B00 heterogeneous Krauss and only `minGap=1.0`.

Evidence: `evidence/results/RES-STAGE-0.5-ROUND2-TASK1-PREFLIGHT-20261028/`.
