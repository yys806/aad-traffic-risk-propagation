# B00 closure and first native execution — 2026-10-27

## Current task

Final status: BLOCKED_BY_VERIFIED_HARD_FAILURE. Task AAD-0.5-B00-CLOSURE-AND-FIRST-NATIVE-RUN-V1. The researcher explicitly authorized ENG-01/02/03 repair, validation, exact new candidate authorization, and direct B00 execution after hard checks. Authorization derives from this chat; no digital signature or independently authenticated identity is asserted. One actual B00 was launched and stopped on the first native error; no complete baseline measurement exists.

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

Pure-Git current source checks:165 passed. Per-process Git longpaths fixed two fixture path-limit failures, earlier logs retained. Final candidate source files41 are exact committed bytes. Live Linux/runtime/resource preflight technical_errors=[]; exact chat-derived authorization passed. No renewed researcher approval was requested.

Candidate: evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v8-closure-20261027/.
Proposal SHA: 685f934a5bf12685ce600155b599fe808bb77bfce571d6894c319fceb389aa67.
Authorization SHA: b6a2dd6b08afb63a31da07f6b1447295ce73a68cc073ca800a68f64dc2268694.
Envelope SHA: e74e5fffa6657583d3155edd62d8dfa77ec8a54160cd7e9efff13d8b379df35e.
Policy SHA: 284e46ca55bd20c4679d72189547ba78b981ff52b4660ebf936e7e5f7c0bd11e.
Runtime SHA: 703c433d85647e3b100ec407a0dfd9a629059905476ec544a320f56cd18a67c7 (8037 files).
The exact final proposal retains immutable false internal approval flags; the separate exact authorization records the delegated user mandate. No claim is made that the user manually typed or signed this new hash. The new accepted policy is independent; old false policy is untouched.

Normal ExecutionAdapter -> ledger -> broker/controller launched B00 once: one version process, one simulation, one real TraCI connection; SUMO1.26.0/protocol22. Capsule exit1, outer wall10.38203798s. Requested horizon420s was not completed. Only t=0 initial identity snapshot is valid; zero post-step frames accepted. Final actual native time and native process exit code were not reliably observed.

Native error: Error: Vehicle 'i0007_i0007' will not be able to depart using the given velocity (slow lane ahead), time=0.00.

Frozen i0007 declares speed15.23m/s, lane5, position233.91 on main_1(length234.04), route main_1 main_2. All downstream main_2 lanes have10m/s in the exact network/baseline. i0007 is outside the 38 original numeric10 DS38 vehicles. Existing NativeBackend.step stops on this native Error. Changing initial speed/position/lane, downstream limit or native-error-stop semantics exceeds the task's frozen scientific scope. This is a specific verified scientific-input/rule conflict. Exact input/runtime/source/command bindings preserve reproducibility; there was one verified occurrence and no identical rerun merely to reconfirm it.

Population1150=117 initial+1033 noninitial. Initial snapshot loaded118 explicit IDs (117 initial plus the first noninitial). Observer states Unknown117/not_yet_scheduled1033 apply only to t=0, not final departure states. Final actual inserted/running/pending/undeparted/arrived/removed/discarded counts are Unknown. Error or absence from FCD does not establish discard/pending. Full-run collision/teleport counts are Unknown; initial zero is not substituted. FCD/summary/TripInfo are truncated, with no completed timestep/summary/TripInfo record. No18-cell state/D1 support or effect estimate is evaluated or accepted. Controls were applied before the failed step but no post-step control readback receipt was sealed; B00 control evidence is incomplete.

Original controller error: native_error_log_stop_preserve_identity_unknown. Secondary independent receipt rejection: required_runtime_record_not_sealed, recorded as ledger failed. Both causes remain, original error is not overwritten. Resources:22 samples, peak sampled RSS103133184B, output1645751B, max sample gap0.312313401s, no watchdog failure. Kernel receipt:descendants_reaped=true,remaining_pids=[]. Controller close returned FatalTraCIError; later coordinator stop exit5 means the service was already not loaded, not an extra successful stop.

Portable result: evidence/results/RES-STAGE-0.5-B00-NATIVE-V1/. Raw logs and partial trajectory/identity/XML remain code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/V3_0750_B00_DS38_s20261201 and its exclusive Linux capsule. Independent failure review: docs/audits/stage_0_5_b00_closure_20261027/b00_failure_acceptance.json. Verified failure evidence does not mean successful execution/measurement.

## Specific scientific conflict

Documented Intent: preserve v6 DS38 scope/i0007/network/B00 and stop on native error, while allowing legitimate pending.
Actual Implementation: the bound native run emits the exact i0007 slow-lane Error on its first step; the existing stop rule terminates.
Evidence and Affected Files: portable scientific_conflict.json binds route/network/proposal/controller/raw console hashes and exact source locations.
Conflict: a speed/position/lane/network change or suppressing the existing Error stop changes frozen scientific input or execution semantics. This is not an ordinary pending-only outcome.
Status: Awaiting Researcher Decision, only for that specific input/rule conflict. No generic new engineering audit is required. A later changed scientific candidate must have a new decision and binding, not reuse this consumed run/envelope/output.

## Export and context consistency

The exporter now registers the three formerly omitted manual historical results and this new result; old snapshots are unchanged. Candidate helper receipt-path typo occurred before proposal/authorization/reserve; partial artifacts and logs remain, only output_contract_v2.json is bound by the final proposal. AI_CONTEXT00/03/04/05/06/07/08, registry, project/research/stage/results indexes are synchronized. Scientific background/architecture/Gate/thresholds and historical Not Accepted stay unchanged.

## Final software and evidence verification

Final source plus exporter no-data regression:1361 passed/16 skipped/7 native deselected,0 failures/errors,336.66s; audit denied=[]/SUMO_launches=0. Compileall exit0. Strict docs/evidence verification and independent candidate/raw artifact/SHA list checks pass. Proof: docs/audits/stage_0_5_b00_closure_20261027/post_execution_validation.json. A generated new portable checksum list initially contained a self-entry; that pre-seal list is retained in portable_checksum_preseal_failure.txt and corrected before final commit. No historical snapshot or original run file was changed.
