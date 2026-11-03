"""Thin P7 producer adapter. The sole event schema is controller_evidence v1."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .controller_evidence import ADOPTION_BOUNDARY_STATUS, ADOPTION_BOUNDARY_VERSION, EvidenceJournal, EventContext, SPECS, TimeEvidence
from .message_driven_longitudinal_controller import RunAssignment, byte_hash, canonical_bytes


class P7EvidenceAdapter:
    def __init__(self, root: Path, run_id: str, assignment: RunAssignment):
        self.root, self.run_id, self.assignment = root, run_id, assignment
        root.mkdir(parents=True, exist_ok=False)
        self.journal = EvidenceJournal(adoption_boundary_version=ADOPTION_BOUNDARY_VERSION,
                                      adoption_boundary_status=ADOPTION_BOUNDARY_STATUS)
        self.sequence = 0
        self.counter: dict[str, int] = {}
        self.artifacts: dict[str, str] = {}
        self.producer_log = (root / "producer_events.jsonl").open("x", encoding="utf-8", newline="\n")

    def identity(self, kind: str) -> str:
        self.counter[kind] = self.counter.get(kind, 0) + 1
        return f"{self.run_id}:{kind}:{self.counter[kind]}"

    def time(self, now: float, step: int, phase: str) -> TimeEvidence:
        self.sequence += 1
        return TimeEvidence(native_timestamp=now, clock_id=self.run_id + ":SUMO",
                            simulation_step=step, phase=phase, sequence=self.sequence,
                            time_lower=now, time_upper=now, reference_clock_id=self.run_id + ":SUMO",
                            clock_mapping_version="SUMO_NATIVE_IDENTITY_NO_WALL_CLOCK_CLAIM_v1",
                            observed_at=now, available_at=now)

    def blob(self, relative: str, value: Any, *, raw: bool = False) -> tuple[str, str]:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        content = value if raw else canonical_bytes(value)
        if not isinstance(content, bytes):
            raise TypeError("raw artifact must be bytes")
        with path.open("xb") as stream:
            stream.write(content)
        digest = byte_hash(content)
        self.artifacts[relative] = digest
        return relative, digest

    def emit(self, kind: str, producer: str, vehicle: str, incarnation: str,
             now: float, step: int, phase: str, evidence_ref: str, *,
             source: str | None = None, message: str | None = None,
             event_time: TimeEvidence | None = None, **data) -> str:
        context = EventContext(record_id=self.identity("record"), run_id=self.run_id,
            pair_id="P7-T2-engineering-three-condition", cell_id=self.run_id,
            producer_id=producer, producer_role=SPECS[kind]["role"], evidence_ref=evidence_ref,
            fixture_only=True, vehicle_id=vehicle, vehicle_incarnation_id=incarnation,
            source_event_id=source, message_id=message, **asdict(self.assignment))
        stamp = event_time or self.time(now, step, phase)
        self.journal.append(kind, context, stamp, **data)
        self.producer_log.write(json.dumps({"record_id": context.record_id, "producer": producer,
            "kind": kind, "time": asdict(stamp), "evidence_ref": evidence_ref}, ensure_ascii=False) + "\n")
        self.producer_log.flush()
        return context.record_id

    def finalize(self) -> dict:
        self.producer_log.close()
        audit = self.journal.validate()
        self.journal.write(self.root / "controller_evidence.json")
        compact = {k: v for k, v in audit.items() if k != "timeline"}
        self.blob("association_validation.json", compact)
        self.artifacts["controller_evidence.json"] = byte_hash((self.root / "controller_evidence.json").read_bytes())
        self.artifacts["producer_events.jsonl"] = byte_hash((self.root / "producer_events.jsonl").read_bytes())
        self.blob("artifact_manifest.json", {"schema_version": "aad.p7.artifact-manifest.v1",
                    "run_id": self.run_id, "files": self.artifacts.copy()})
        return compact
