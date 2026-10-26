# V4 smoke 3 continuation: SMOKE PASS

**SMOKE PASS**, for engineering integration only. The single authorized native
attempt was executed once through the original r5 broker/controller/launch
chain. No B00 research input or trajectory was executed. Candidate-v5, all four
false flags, scientific definitions, Gate, δ/h/B, Stage 1.1 and the historical
`Not Accepted` incident remain unchanged. B00 remains `BLOCKED_ENGINEERING`;
this smoke does not grant research admission or B00 authorization.

## Exact scope and authorization

- Task: `AAD-0.5-LINUX-INTEGRATION-V4-SMOKE`.
- Run: `SMOKE_V4_20261026_3`.
- Fixed staging: `/home/shen/AAD/code/tmp/stage05_v4_20261026_r5`.
- Proposal SHA: `a5f419029a7dc3ddc527d9b7e7e824c9f0f3779f4f3e17e769d87d472ca4a550`.
- Runtime manifest SHA: `3afa1fdb8eac97acf875d1a816eac168bfd39d3318414e316c85b4136d0a4abc`.
- Production source closure SHA: `b1598d279e2665c1c902bae827022440a34f668377fc0544b30fbcf84f8015c2`.
- New authorized envelope SHA: `a9ce5a370957387690adfcfc953e7d20d5a877d3d73e628418bd73b816b1271d`.

The new envelope is at
`docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/authorized-execution/authorized_envelope.json`.
Its decision record cites the researcher's explicit 2026-10-26 authorization and
continuation of the same unconsumed exact task. The original r5 false envelope
SHA remains `6b37149d000f28258ee22bb499d7db7ee0e7a1255d4195c4bb7658f5aae8a463`.
No staging, proposal, input, production source, runtime or policy was regenerated.

## Auxiliary repairs and current prelaunch evidence

Original `smoke-20261026-3/result.json`, `SHA256SUMS` and audit tools are preserved
byte for byte. Corrected active helpers are in `continuation-r2/audit_tools/`:
optional sysctls are metadata, existing historical audit directories are allowed,
actual attempt/receipt/unit/process records prevent reuse, output paths are
explicit and exclusive, and raw stdout/stderr are saved before ASCII-safe output.

Auxiliary repairs were tested and pushed before native launch: `c12950e` (177
tests) and `09918d16bc06fc1d72e8322da21e048aa1548317` (180 tests). An additional
overstrict auxiliary assertion in the first corrected live precheck required
current WSL outer mnt/pid IDs to equal historical policy IDs. Policy SHA did not
change. Its r2 logs and old helper version are preserved and explicitly classified
as a helper defect. The final check verifies actual fresh user/mnt/pid/net/ipc
namespace separation from both current outer IDs and policy-recorded IDs.

`continuation-r2/prelaunch-r3/` contains fresh Git checks (19 commands, 180 tests)
and Linux checks (6 commands), with actual exit codes and raw log hashes. Current
user namespace creation, Landlock ABI3 restriction/denied reads, seccomp filtering,
systemd user manager and controlled cgroup resource readback passed using harmless
Python only. These live results are separate from the fixed six-group historical
probe record. No production unit or matching native process existed before launch.

The bound production preflight rehashed all **8031 runtime files**, the 12
production sources and exact input/policy/executable bindings. Live precheck
resources in bytes: available memory 13,803,880,448; C free 120,701,960,192;
D free 278,572,023,808; WSL/archive free 14,665,596,928. Existing startup floors
were met. The actual launch entry repeated its own live preflight before starting
the confined version process. No threshold was changed or historical data cleaned.

## Actual native result

| Check | Verified result |
|---|---|
| Launch / version process / simulation process / real TraCI connection | 1 / 1 / 1 / 1 |
| Native version | Exact release line `Eclipse SUMO sumo 1.26.0` |
| TraCI | `[22, "SUMO 1.26.0"]` |
| Simulation / control steps | 60 / 60, 3 s at 0.05 s |
| Speed schedule | 20 steps at 10, 20 at 5, 20 at 10 m/s |
| Control timestamps, native clock, target and readback | All 60 steps passed independent verification |
| FCD | Valid XML, 30 timestep elements |
| summary | Valid XML, 60 step elements |
| tripinfo | Valid XML, 1 tripinfo element (unfinished-output contract) |
| Production coordinator acceptance | Pass, `engineering_acceptance.json` generated |
| Separate original `verify_receipt` on collected archive | Pass |
| Automatic native retry / new B00 trajectories | 0 / 0 |

Controller and SUMO shared all five isolated namespaces. Both had
`NoNewPrivs=1`, `Seccomp=2`, zero effective capabilities and only `lo` visible.
Cgroup limits were memory 1 GiB, swap 0, pids 32 and CPU quota one core. All 66
resource samples passed: peak process-tree RSS **100,130,816 bytes**; final
sample wall time **1.227888848 s**; maximum sample interval **0.345776584 s**.
Sealed output bytes: **1,619,609**, below 16 MiB. Version/broker/coordinator
timeouts remained 10/30/60 s. Payload and controller exited 0, descendants were
reaped and remaining PID list was empty. A separate post-execution observation
found no matching process and the exact production unit `not-found/inactive`.

## Evidence and hashes

Actual execution evidence is in
`docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/authorized-execution/`.
It contains the exact new envelope, one launch invocation, the exclusive native
launch record, raw broker/coordinator logs, complete native archive, XML outputs,
OS/controller receipts and both acceptance records. All collected file bytes
were checked against their collection hashes; no simulator was rerun for analysis.

| File | SHA-256 |
|---|---|
| `result.json` | `ae4ce45d42b37b4b42598987c9bae22c50f69641b80ee49c5c5d2449f2df0c64` |
| `capsule/engineering_acceptance.json` | `a3276183a38b6bfd03e5c5e0eb67a61b86a8f193d4d5d541bea208ed669dd88b` |
| `independent_receipt_acceptance.json` | `e295f312bfa2c75258db162ee42bbeb0b1d01373060fdc641097b8c6e1784894` |
| `capsule/archive/isolation_runtime.json` | `9c4251d748ec613214682195ce27ee6235d945fd4b25e0e86a249508414a5c5f` |
| `capsule/archive/controller_receipt.json` | `316dcb625a55a7919a54e88e7986a7477f2972383e2d0a30d0ad94f32daf7606` |

The continuation and execution have separate full manifests/checksum lists; the
old failure's checksum list remains unchanged. Postcommit software/evidence/
receipt checks are executed on a new pure-Git checkout of the final commit and
recorded with their actual tested SHA and command/log hashes, separately from
the precommit helper validations. The prior 1275-test full run is not rerun or
misrepresented as a current full run.

Context Consistency Check: 00/02/03/04/05/07/08 reflect auxiliary repairs and
engineering-only native evidence. Research background/approved decisions
(01/06) are unchanged. No scientific inference follows from this smoke.
