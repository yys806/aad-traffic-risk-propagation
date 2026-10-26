# Smoke 3 continuation r2

The researcher explicitly continued the same exact authorization on 2026-10-26.
The earlier auxiliary precheck exception did not invoke launch or consume the
single native attempt. Original `../result.json`, `../SHA256SUMS` and original
audit tools remain byte-identical historical evidence. Corrected versions live
in this new directory, rather than invalidating that historical checksum list.

`audit_tools/preflight_git.py` requires `--repo-root`, `--clone`, `--output-dir`.
It exclusively creates new task output/clone paths. `preflight_linux.py` requires
`--repo-root` and the same explicit `--output-dir`, consumes that fresh Git
record, and exclusively creates distinct Linux command logs and result records.
Neither script rejects the historical audit directory merely for existing.

Optional sysctl paths are metadata only. Live user namespace creation has a
5-second timeout and explicit UID/namespace checks. Live bound Landlock/seccomp
restriction and denial checks run in a harmless child; a separate harmless
systemd unit verifies actual cgroup resource readback. These are not SUMO or
TraCI processes. Existing fixed probes are verified as historical observations,
separately from these current checks. The bound production preflight rehashes
all runtime/policy/readonly/executable bindings and checks fresh resources.

Actual launch records, production receipts, broker output, matching processes,
and the exact production systemd unit prevent reuse. Raw bytes, command exit
codes and log hashes are saved before ASCII-safe display. Unexpected auxiliary
defects are labeled `HELPER_ERROR`; genuine binding/capability/resource failures
remain blocking. Production source, r5, proposal, policy, runtime and inputs
are not changed by these repairs. This continuation still permits only one
actual native launch, with no retry after that launch.
