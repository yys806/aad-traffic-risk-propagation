# Stage 0.5 Linux native V4 integration record

## Status

`BLOCKED_ENGINEERING`. This record covers one explicitly authorized synthetic
engineering smoke (`SMOKE_V4_20261026_2`) and the r4 Linux guard probes. It is
not a B00 experiment and does not change any scientific decision or Gate.

## Verified evidence

- The r4 six-group Linux probes passed all checks reconstructed by
  `stage_0_5_isolation_admission.py::probe_checks`: read/write boundaries,
  child inheritance, namespaces and security status, loopback-only networking,
  PID/CPU/memory/output/timeout limits, and failure retention. The exact
  allowlisted collection is
  `docs/audits/stage_0_5_linux_native_v4/collection-20261026-r3/`.
- The fixed Linux runtime manifest records SUMO 1.26.0, the project Python
  environment, TraCI source and dependency hashes. No system SUMO was used as
  a substitute.
- The production broker created a real capsule for the authorized synthetic
  run. Inputs were synthetic network/routes/config only, and the capsule
  emitted an OS receipt with isolated namespaces, read-only input mounts and
  no remaining child processes.

## Failure and repair

The synthetic run stopped in the controller's version preflight before opening
TraCI or launching the native SUMO simulation. The bound SUMO 1.26 binary
reported `Eclipse SUMO sumo 1.26.0`; the controller and receipt verifier
required the older `Version 1.26.0` spelling and returned `SUMO_release_mismatch`.
The failure is retained under `failure-r4/` and was not retried. The parser now
accepts both observed spellings while requiring an exact release token, with a
regression test. The r4 staging remains bound to the pre-repair bytes and is
therefore not an accepted production build.

## Counts and boundaries

- Synthetic SUMO version process: 1.
- Real TraCI connections: 0.
- New research trajectories: 0.
- No B00 input, historical C6 result, locked holdout, or third-window data was
  read or changed. No automatic retry occurred.
- `execution_allowed`, `researcher_confirmed`, `protocol_frozen`, and
  `accepted_for_new_task` remain `false`; `POLICY-A-VALIDATION-SCOPE-01`
  remains `Not Accepted`.

## Software verification

- `test_stage_0_5_native_capsule_v4.py`: 63 passed, 0 failed.
- Related Linux/isolation/admission/ledger/V2 tests: 150 passed, 1 skipped,
  0 failed.
- `compileall` and `git diff --check`: passed.
- The historical 1130-test result is reused only as unchanged-source context;
  it was not rerun in this task.

The next native smoke requires a new staging directory and a new explicit
single-run authorization because the authorized r4 attempt has been consumed
and its source binding predates the parser repair. Until that evidence exists,
the new package remains `BLOCKED_ENGINEERING`.

The blocked candidate package is
`evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v4/`; its proposal
SHA-256 is `59233a64c2ceaa06d52ef381e0964dade55d621b4a74e8b8b85c03ec2d1fe902`
and its manifest SHA-256 is
`27e776754317e7f1e174a324605d854a8961545c2810a39a8ecc84a75994fe93`.
