# Stage 0.5 V4 r5 preparation

Status: **PREPARED / AWAITING_EXPLICIT_AUTHORIZATION**. Research admission remains
**BLOCKED_ENGINEERING**. No smoke has run in this task; no production receipt has
been accepted. No B00, SUMO version process, SUMO simulation, real TraCI connection
or new research trajectory was executed. Six harmless Python OS probe groups ran.

## Exact new artifacts

All Linux paths below are in the sole authorized workspace `/home/shen/AAD`.
Windows access to the staging is
`\\wsl.localhost\Ubuntu\home\shen\AAD\code\tmp\stage05_v4_20261026_r5`.
The independent preparation collection is
`docs/audits/stage_0_5_linux_native_v4/prepared-20261026-r5/`.

| Artifact | Exact Linux path or SHA-256 |
|---|---|
| Staging | `/home/shen/AAD/code/tmp/stage05_v4_20261026_r5` |
| Controller/broker source closure (canonical filename/hash map) | `b1598d279e2665c1c902bae827022440a34f668377fc0544b30fbcf84f8015c2` |
| Strict parser source SHA | `22ed677334290729038b8c30049637fb90af301760e9ee33a1aa7073e2cf26db` |
| Runtime manifest | `/home/shen/AAD/code/tmp/stage05_v4_20261026_r5/runtime_manifest.json` |
| Runtime manifest SHA | `3afa1fdb8eac97acf875d1a816eac168bfd39d3318414e316c85b4136d0a4abc` |
| Smoke proposal | `/home/shen/AAD/code/tmp/stage05_v4_20261026_r5/smoke_proposal.json` |
| Proposal SHA | `a5f419029a7dc3ddc527d9b7e7e824c9f0f3779f4f3e17e769d87d472ca4a550` |
| Unapproved envelope | `/home/shen/AAD/code/tmp/stage05_v4_20261026_r5/smoke_envelope.json` |
| Envelope SHA | `6b37149d000f28258ee22bb499d7db7ee0e7a1255d4195c4bb7658f5aae8a463` |

Source baseline is `7c5a5d4754e79aab9eeda7f5e7395438c5b41ef4`, plus the explicitly
recorded uncommitted engineering fixes. `staging_record.json` lists every source
SHA. `preparation_verification.json` records the actual Linux environment,
resource sample, source checks, runtime and probe bindings. The runtime manifest
was regenerated using static ELF inspection and every file was rehashed. Its SHA
equals the prior runtime's SHA because those runtime bytes are unchanged; the
new controller/source/policy/probe bindings are independent of r4.

## Synthetic input and isolation contract

Run ID: `SMOKE_V4_20261026_3`. Only the three files in `smoke_inputs/` are mounted
as inputs. The proposal's `runs[0].capsule_input_sha256`, the policy's
`inputs`/`file_sha256`, and the collection bind their exact bytes. The network has
one synthetic edge/lane (`synth_main`, `synth_main_0`, length 500 m), and one
noninitial synthetic vehicle (`synth_vehicle`, departure 0.05 s). Duration 3 s,
step 0.05 s, recorded FCD 0.1 s, seed 1, ballistic integration, one thread. The
lane limit schedule is 10 m/s on [0,1), 5 on [1,2), 10 on [2,3).

The policy is `smoke_capsule/policy.json`; its exact SHA is stored in the
proposal and the verification record. It binds all twelve current controller,
broker and support sources in a dedicated read-only source directory; Linux
SUMO 1.26.0, TraCI protocol 22 and tools; the entire Python/ELF runtime closure;
and the new r5 capability record. Namespace/Landlock/seccomp/cgroup restrictions,
read-only inputs, isolated loopback and executable allowlist remain enforced.
The dedicated scratch/archive paths are `smoke_capsule/scratch` and
`smoke_capsule/archive` inside r5. Neither exists after preparation; no
`launch_attempt.json`, production receipt or acceptance artifact exists.

| Binding | SHA-256 |
|---|---|
| `smoke_inputs/network.net.xml` | `686042b018591e728bfd31a194d301b18233b9027b47f9bb276c4c641a039d5f` |
| `smoke_inputs/routes.rou.xml` | `7ab787025b44a82fa7d4bc7b0f0b958631b094de81ba5f8f82800dee3867ef37` |
| `smoke_inputs/run.sumocfg` | `f96cae379fd8557affcdfe6f108e61f3281e0ac87539a7e65c9b5095c9276930` |
| `smoke_capsule/policy.json` | `1762cb24ac631bf211e418a99eb2289a483d5a8df900d0391d24fc3f6b911507` |
| `probe_results/record.json` | `c38b6b32d54cf2b3f28852dab84ceef5811b3481418356d035e2f34234ba5513` |

If later separately authorized, the maximum is one attempt: one version process
and one synthetic SUMO simulation process, one real TraCI connection, one worker,
zero task retries. Process-tree RSS cap 1 GiB; output cap 16 MiB; TasksMax 32;
CPU quota one core; version timeout 10 s; broker wall limit 30 s; coordinator
timeout 60 s; resource supervision every 0.5 s. Startup floors: C 5 GiB, D 14 GiB,
available memory 4 GiB, WSL/archive output allocation plus 1 GiB. Runtime checks
must be repeated at any future authorized launch. Failure retains evidence and
stops; exclusive creation of the attempt record prevents reuse.

`engineering_authorized=false`. The real envelope verifier currently refuses
this envelope with `engineering_smoke_authorization_missing`. No authorization
from `SMOKE_V4_20261026_2` is transferred. New exact human authorization of this
proposal SHA is required; this preparation is not authorization.

## Strict version validation and admission candidate

`sumo_version_output_matches()` now matches a complete LF/CRLF-delimited line
of exactly `Eclipse SUMO sumo 1.26.0` or
`Eclipse SUMO sumo Version 1.26.0`. Prefix fragments, suffixes (`.1`, `-dev`,
`+custom`, `rc1`), inline annotations and extra versions are rejected. The same
function protects controller preflight and independent receipt verification.
Synthetic controller tests forbid socket creation and native start after a
wrong version response.

New `candidate-v5/` uses `aad.native-admission.v4`, a Linux environment, pinned
runtime, exact Linux policy and the current source closure. Its previous proposal
is immutable candidate-v4. The B00 input bytes, seed 20261201, run ID
`V3_0750_B00_DS38_s20261201`, 420 s duration, [120,390) evaluation, initialization,
factor definitions, supply targets and schedule are preserved. Only environment
bindings and additional engineering fields are added. The three B00 inputs are
staged in `research_inputs/`; `research_capsule/policy.json` is prepared with
`accepted_build=false`. No research launch envelope is created.

Candidate-v5 proposal SHA is
`e4b4dcf9e559b56be0ac50c143e3e327c336927f02d9c90c63f5c0463e93442f`;
its Linux copy is `/home/shen/AAD/code/tmp/stage05_v4_20261026_r5/research_proposal.json`.
The independent field comparison is `offline_binding_verification.json` in the
new audit. The complete path/hash/resource bindings are in
`preparation_summary.json` in that same audit.

The actual `technical_preflight_v4(..., inspect_runtime=False)` must reach
`integration_not_accepted`, rather than schema, environment, source, budget or
input-binding errors. Its `technical_errors` and `authorization_pending` are
separate. Production acceptance, exact current smoke receipt and later live
research runtime/resource checks remain required. `READY_FOR_RESEARCHER_APPROVAL`
is covered by a synthetic status test and means engineering passed while human
approval is pending; it is not the state of this real candidate.

All four flags remain false (`execution_allowed`, `researcher_confirmed`,
`protocol_frozen`, `accepted_for_new_task`), the bare-host native hard lock stays
true, the historical incident remains `Not Accepted`, and Gate, δ/h/B and
Stage 1.1 are unchanged. r3/r4 staging, historical failures and candidate-v4 are
retained without modification. Scientific interpretation is outside this task.

## Offline validation and reproducibility

The final machine record is
`docs/audits/stage_0_5_linux_native_v4/prepared-20261026-r5/validation_record.json`.
It retains the initial temporary-directory setup failure, the five failing
synthetic fixture tests before correction, and the initial isolated-import
preparation failure. None launched SUMO. Final V4 tests: 122 passed.

Final exact-byte related regression: 288 passed / 1 skipped. Full software:
1275 passed / 15 skipped / 7 native tests excluded. Both parent audits recorded
zero denied resource reads and zero SUMO launch attempts. All 38 bound source
files match the no-data clone byte for byte; compileall passed. Existing pandas
FutureWarnings remain recorded in the full log.

All broader software checks run in the separate data-free Git clone
`code/tmp/v4_finalize_validate_20261026_r1`, with the reviewed audit harness,
exact source overlay, fixed seven-native-test exclusion and private temp paths.
Full/targeted counts, audit paths and environment are recorded there and in the
machine record. Skips are not passes. Linux preparation uses the existing pinned
interpreter under `code/runtime/stage_0_5_sumo126_v4_r2`, never system SUMO 1.18.

The initial 1275-pass full run and 288-pass targeted run used nine clone files
with CRLF-only checkout differences. Their normalized contents were identical;
the original logs are retained. Explicit Git EOL rules and exact source overlay
correct the byte binding, and the final recorded suites use those exact bytes.

The required generic `export_project_evidence.py --repo-root .` command succeeded
but regenerated the common manifest without three independently registered
historical extensions (depart-speed candidate, interaction-research V2 and V2
admission engineering). No result file changed. Its generated manifest was kept
under task-local `code/tmp/`; the common manifest was restored to its original
HEAD bytes, then `--verify` passed. The general exporter's coverage issue is
recorded, not repaired in this preparation task. New r5/candidate-v5 evidence has
its own collection/manifest and is registered directly in PROJECT_REGISTRY.

Reproduction of preparation uses the existing V4 `stage` then six-probe then
`smoke` entries, and `prepare_stage_0_5_admission_v4.py linux-policy` / `candidate`.
Every destination must be new; replay requires a new stage/run ID and fresh
binding. Do not rerun these commands against r5. The recorded commands and
parameters describe preparation, not authority to execute a smoke.

Context Consistency Check: updated current state, architecture, data flow,
module map, experiment preparation, known issues and changelog; scientific
background and approved decisions do not change.
