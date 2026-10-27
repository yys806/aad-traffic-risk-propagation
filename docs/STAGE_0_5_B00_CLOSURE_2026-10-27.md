# B00 closure and first native execution — 2026-10-27

## Current task

Active: AAD-0.5-B00-CLOSURE-AND-FIRST-NATIVE-RUN-V1. The researcher explicitly authorized ENG-01/02/03 repair, validation, exact new candidate authorization, and direct B00 execution after hard checks. Authorization derives from this chat; no digital signature or independently authenticated identity is asserted. This document will be completed with the actual B00 result in the same task.

## Verified engineering changes

- ENG-01: bound policy accepted_build, source/runtime hashes and exact run ID are mandatory before reserve; ledger, Linux preflight and envelope/controller verify the same decision. No optional production bypass remains.
- ENG-02: collision API missing, exception, None, bool, noninteger and negative values cannot become zero. Rejected raw frames and original exceptions survive; coverage gaps remain sticky even after later recovery. Collision vehicle count is explicitly distinct from event count. Collision and teleport stop rules remain intact.
- ENG-03: summary is sealed and independently checked over every 0.05 s step; startup loaded IDs are captured explicitly. Summary counters, identity journal, actual departure/delay, TripInfo and FCD are reconciled. Legitimate pending does not require all vehicles to insert or finish. Aggregate discarded identities remain unresolved unless explicit identity evidence exists.
- Official SUMO 1.26.0 source semantics and hashes: docs/audits/stage_0_5_b00_closure_20261027/source_semantics/api_semantics.json.

## Verification before formal candidate

Current no-data Git checkout: 1361 passed, 16 skipped, 7 explicitly deselected native tests; no denied accesses or SUMO attempts in the parent software audit. Earlier dedicated related-module suite: 335 passed / 2 skipped. Final compileall passed. Current minimal native integration SMOKE_V4_20261027_CLOSURE_R7: one version process, one simulation, one real TraCI connection, 3 s / 60 steps; Linux and independent Windows receipt checks Pass, including complete summary/identity/TripInfo checks. It verifies engineering only, not the B00 research outcome.

Machine proof: docs/audits/stage_0_5_b00_closure_20261027/software_validation.json and integration/independent_windows_acceptance.json in that audit directory.

## Preserved failures and limits

The earlier primary-workspace full pytest attempt is invalid for admission: 1330 passed / 35 failed / 1 error / 3 skipped, native tests were not excluded, and no process/data-access audit existed. Exact native process count and restricted-data access cannot retrospectively be certified; neither is silently reported as zero. Details: docs/audits/stage_0_5_b00_closure_20261027/validation_scope_incident.json. The historical POLICY-A-VALIDATION-SCOPE-01 remains Not Accepted.

Provisional candidate-v7 was generated too early and is superseded, not a final authorization. Its bytes, policies, envelopes and synthetic outputs remain locally unchanged; its exact digest/status is registered in candidate_v7_provisional_status.json. Raw logs are not added to portable evidence. Staging/import/cache prelaunch failures remain in their exclusive task directories. R6 failed before native launch because a helper omitted -B and generated unbound psutil bytecode after the manifest snapshot; R7 rebinds the resulting files and runs with bytecode writes disabled. No hard lock or threshold was weakened.

Candidate-v6 and its SHA b43e2d3af03dd53dd23bee3abd027725f298f58c97a2ae73d868ca9168a229b3, old false policy, historical SMOKE and failures remain unchanged. The final B00 candidate is generated only after implementation and validation, then SHA-bound to the chat authorization and envelope. No research-definition changes: seed 20261201, 420 s, native .05 s, FCD .1 s, [120,390), DS38, D1/common reference/18-cell contract, no B00 treatment.

## Execution result

B00 has not launched at this source-repair commit. The task continues directly through postcommit Git verification, final exact binding, live preflight and execution; this is not a request for renewed researcher approval.
