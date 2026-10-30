# AAD Round2 research decisions — 2026-10-30

Status: Agreed. Authority: the researcher's `AAD Round2 Closure & Conditional Research Validation Campaign` instruction dated 2026-10-30. This decision record supersedes earlier pending A/B/C and acquisition-authorization descriptions only prospectively; historical reports and machine evidence remain unchanged. Baseline main independently verified through the GitHub read-only API: `80abab044063803219f6ceadfeb3562c3939aaa1`.

## 1. Original Round2 candidate is closed

The single-factor minGap=1.0 source-mechanism candidate is CLOSED_FAILED_ORIGINAL_SOURCE_CONDITION. Its one completed seed 20261201 run, Rule A PASS, source Formal P2=0 and one target-only diagnostic event remain preserved. No independent-seed confirmation and no change to source, target, cohort, windows, TTC, duration or disturbance intensity is allowed to rescue this branch. Future minGap=1.0 use is restricted to a separately gated fixed-leader paired control experiment; it is not confirmation of this branch.

## 2. General Formal P2 uses C; D1 remains independent

C qualifies events by follower/leader pair identity and temporal continuity. Same native lane for all event members is not required. Lane-ID changes alone do not prove physical connectivity. Explicit identity_break, observation_gap, leader identity and clock continuity retain their existing force. TTC threshold, duration and cadence are unchanged. D1 retains its same-native-lane local diagnostic denominator. Formal P2 and D1 event counts and exposures must be labelled separately and never pooled. A is retained only as a conservative sensitivity option.

## 3. Physical-path eligibility uses B witnesses

B is independent of C event qualification. A physical-path claim requires traceable follower and leader identities, time-indexed lane/edge connectivity, continuous follower–leader interaction evidence, a documented physical basis for the road connection, and verifiable temporal order of the transition. A topology edge, lane-ID change, boolean road-connection flag, event onset or local confirmation time alone cannot establish the vehicle's observed path or physical arrival. Any missing component yields Unknown, not unreachable or safe. No unobserved path is interpolated.

## 4. Scientific equivalence is not accepted

`formal_equivalence_accepted` remains false. Engineering interface agreement, descriptive comparability and unresolved physical/data support are reported independently. Passing synthetic tests cannot establish simulator–NGSIM scientific or physical equivalence. No Gate, Stage 0.6 δ/h/B freeze, Protocol Lock or Stage I promotion is authorized.

## 5. Official inquiry is authorized; acquisition is conditional

The existing Task7.2 English inquiry to data.itsjpo@dot.gov is approved for dispatch without expanded commitments. Actual send status requires a real receipt. Raw acquisition is limited to camera7/8 in 0750–0805 and 0805–0820: four named AVI members only. G-V1 license, G-V2 trusted clocks/PTS/time base/offset/drift, G-V3 source/lane coverage and G-V4 resource/checksum checks must all pass first. Publication, derived imagery, redistribution and human-review access permissions are separate fields. Fees, agreements or institutional authorization require a new researcher decision. No complete ZIP, third window, extra camera or processed-video acquisition is authorized.

## 6. Human review is conditional and capped

After license/time/space gates and acquired-file integrity checks pass, preregister before watching: at most 24 risk events (4 extreme/4 intermediate/4 representative per window, severity by minimum TTC) plus 12 unique-follower nonrisk controls (at most 6/window). Use seed 20261030, deterministic sorting, explicit strata/identity/context/shortage/exclusion rules, blind Review IDs, local-only identity maps and normally ±5 s clips. Actual visual judgments belong to human reviewers. Preserve Unknown; uncalibrated visual estimates are not precise gap/TTC/DRAC truth.

## 7. Fixed-leader mechanism direction is conditionally approved

Only after independently permitted, physically verified stable leader/follower segments, trustworthy leader identity/time and motion extraction, fair initial matching, engineering feasibility and resources are established may fixed-leader trials run. Arm A is actual B00; Arm B is actual Round2 minGap=1.0; only minGap differs. Inputs, follower initial conditions, road/lane, time/cadence, measurement, paired seeds and metrics are identical. A new exact seed/repetition matrix still needs researcher approval if none is already approved for this experiment. Existing historical replay seeds do not transfer that approval.

The instruction announces eight decisions but numbers Decision 1 through Decision 7; its cross-reference to “Decision 8” identifies this independently gated two-arm minGap control by content. No missing eighth research choice is invented.

## 8. Scope and evidence protection

No new ungated SUMO/TraCI, original-candidate confirmation, parameter search, third window, locked holdout, auxiliary pooling, Task6 vehicle-clustering extension or additional literature work. No changes to AGENTS.md, historical outputs, upstream DRIFT or private OB materials. Implementation facts and bounded tests are recorded in the comparability matrix; conditional no-go and readiness reports record remaining blockers. These decisions are approved research scope, not evidence that a mechanism or AAD hypothesis is true.
