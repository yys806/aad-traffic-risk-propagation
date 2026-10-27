# Candidate-v6 engineering audit

Task AAD-0.5-B00-ADMISSION-V6. No simulator, TraCI connection or research execution.
Candidate-v6 status: READY_FOR_RESEARCHER_APPROVAL, not execution authorization.

independent_evidence_verification.json rechecks sealed raw files using the original verifier.
live/ contains exact commands, raw stdout/stderr and current runtime/resource/interface checks.
validation_record.json is explicitly PRECOMMIT and must not be cited as postcommit verification.
validation/ contains actual command records, full/targeted no-data process audits and skip reasons.
supplemental_DS38_static_verification.json compares only the registered original input bytes.
schema_difference_verification.json complements the immutable candidate's deep-difference record.
tooling/ contains audit-helper source snapshots, outside the production/scientific closure.

audit_manifest.json covers audit content, all candidate files, helper/tests and final report/context/registry.
SHA256SUMS covers this audit directory including audit_manifest.json, excluding itself.
The candidate manifest is externally hashed; no circular proposal/certificate/manifest digest.

Postcommit validation must run from a fresh no-data checkout of the actual committed tree.
Its machine receipt is task-local code/tmp/admission_v6_work_20261027_r3/postcommit/verification_receipt.json,
outside the committed evidence to avoid a commit containing its own SHA. The final response records
that verified SHA, command results and actual push result. No precommit result substitutes for it.

Historical candidate-v5, smoke failures, false envelope and successful raw archives remain unchanged.
Research flags, native lock, historical Not Accepted and scientific Gate/delta/h/B/Stage1.1 remain unchanged.
