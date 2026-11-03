"""Actual one-hop receive, input gate, policy and TraCI command boundaries."""
from __future__ import annotations

from dataclasses import asdict, replace
from typing import Callable

from .controller_evidence import ADOPTION_BOUNDARY_STATUS, ADOPTION_BOUNDARY_VERSION
from .message_driven_longitudinal_controller import (
    INPUT_SCHEMA, PARAMETER_STATUS, PAYLOAD_SCHEMA, LocalState, Message, PolicyConfig,
    PolicyInput, RiskPayload, RunAssignment, longitudinal_policy, validate_message,
)
from .p7_evidence_adapter import P7EvidenceAdapter


class InProcessSingleHop:
    """SUMO-model communication; no wireless, delay or channel realism claim."""
    def __init__(self, adapter: P7EvidenceAdapter):
        self.a = adapter

    def send(self, message: Message, receiver: MessageController, state: LocalState,
             *, send_status: str = "SENT", delivery_status: str = "RECEIVED") -> str | None:
        a = self.a
        if send_status not in ("SENT", "FAILED", "UNKNOWN") or delivery_status not in ("RECEIVED", "CONFIRMED_FAILURE", "UNKNOWN"):
            raise ValueError("unsupported transport outcome")
        attempt = a.identity("attempt")
        a.emit("send", "p7.inprocess.send", message.sender_id, "synthetic-source-life-1",
            state.simulation_time_s, state.simulation_step, "SEND", "payloads/" + message.message_id.rsplit(":", 1)[-1] + ".json",
            source=message.source_event_id, message=message.message_id, attempt_id=attempt,
            send_status=send_status, transport_ref="IN_PROCESS_SINGLE_HOP_NOT_WIRELESS_v1")
        if send_status != "SENT":
            return None
        return receiver.receive(message, attempt, state, delivery_status=delivery_status)


class MessageController:
    def __init__(self, adapter: P7EvidenceAdapter, assignment: RunAssignment, config: dict,
                 state: LocalState, controller_code_hash: str, policy_config_hash: str,
                 policy: Callable = longitudinal_policy):
        self.a, self._assignment = adapter, assignment
        self.policy_config = PolicyConfig.from_dict(config)
        self.policy = policy
        self.vehicle, self.incarnation = state.vehicle_id, state.vehicle_incarnation_id
        self.original_max = state.original_max_speed_mps
        self.active_reference: float | None = None
        self.active_command: str | None = None
        self.command_tenures: list[dict] = []
        self.inbox: dict[str, tuple[Message, str]] = {}
        self.closed = False
        self.controller_id = adapter.identity("controller")
        adapter.emit("controller", "p7.controller.initialize", self.vehicle, self.incarnation,
            state.simulation_time_s, state.simulation_step, "INITIALIZE", "controller_config.json",
            controller_id="P7-message-longitudinal", controller_instance_id=self.controller_id,
            controller_version="aad.p7.controller.v1", controller_code_hash=controller_code_hash,
            policy_version=self.policy_config.policy_version, policy_config_hash=policy_config_hash,
            controlled_vehicle_id=self.vehicle)

    @property
    def assignment(self) -> RunAssignment:
        return self._assignment

    def receive(self, message: Message, attempt: str, state: LocalState, *, delivery_status="RECEIVED") -> str:
        if self.closed or (state.vehicle_id, state.vehicle_incarnation_id) != (self.vehicle, self.incarnation):
            raise ValueError("RECEIVER_LIFECYCLE_MISMATCH")
        delivery = self.a.identity("delivery")
        ref, _ = self.a.blob("deliveries/" + delivery.rsplit(":", 1)[-1] + ".json",
            {"attempt_id": attempt, "delivery_id": delivery, "receiver": self.vehicle,
             "message_id": message.message_id, "payload_hash": message.payload_hash, "status": delivery_status})
        self.a.emit("delivery", "p7.receiver.receive", self.vehicle, self.incarnation, state.simulation_time_s,
            state.simulation_step, "RECEIVE", ref, source=message.source_event_id, message=message.message_id,
            delivery_id=delivery, attempt_id=attempt, delivery_status=delivery_status)
        if delivery_status == "RECEIVED":
            if message.message_id in self.inbox and self.inbox[message.message_id][0].payload_hash != message.payload_hash:
                raise ValueError("CONFLICTING_PAYLOAD_HASH")
            self.inbox[message.message_id] = message, delivery
        return delivery

    def decide(self, state: LocalState, assignment: RunAssignment, vehicle_api) -> dict:
        self._assignment.assert_matches(assignment)
        self._assignment.assert_matches(self.a.assignment)
        if self.closed or (state.vehicle_id, state.vehicle_incarnation_id) != (self.vehicle, self.incarnation):
            raise ValueError("CONTROLLER_LIFECYCLE_MISMATCH")
        a, now, step = self.a, state.simulation_time_s, state.simulation_step
        gates, included = [], []
        decision = a.identity("decision")
        for message, delivery in self.inbox.values():
            result = validate_message(message, state)
            validation = a.identity("validation")
            suffix = validation.rsplit(":", 1)[-1]
            ref, _ = a.blob(f"validations/{suffix}.json", {"message_id": message.message_id,
                "delivery_id": delivery, "status": result.status, "reason": result.reason, "local_state": asdict(state)})
            a.emit("validation", "p7.validator.validate_message", self.vehicle, self.incarnation, now, step,
                "VALIDATE", ref, source=message.source_event_id, message=message.message_id, validation_id=validation,
                delivery_id=delivery, validator_id="p7-risk-payload-validator", validator_version=PAYLOAD_SCHEMA,
                validation_status=result.status, reason=result.reason)
            receipt = a.identity("receipt")
            available = result.status == "VALID"
            # Record actual received boundary before the subsequent availability stamp.
            received_time = a.time(now, step, "INPUT_RECEIVED")
            available_time = a.time(now, step, "AVAILABLE") if available else None
            a.emit("input", "p7.controller.input_boundary", self.vehicle, self.incarnation, now, step,
                "INPUT_BOUNDARY", ref, source=message.source_event_id, message=message.message_id,
                receipt_id=receipt, message_id=message.message_id, payload_hash=message.payload_hash,
                validation_id=validation, controller_instance_id=self.controller_id,
                available_time=available_time, input_schema_version=INPUT_SCHEMA, input_snapshot_ref=ref,
                input_status="AVAILABLE" if available else "RECEIVED", event_time=received_time)
            allowed = available and assignment.adoption_mode == "ENABLED"
            if allowed:
                included.append((message.message_id, result.payload))
            gates.append((message, receipt, "POLICY_INPUT_INCLUDED" if allowed else "REJECTED",
                          "ACTUAL_POLICY_INPUT" if allowed else "ADOPTION_DISABLED" if available else result.reason))
        policy_input = PolicyInput(state, tuple(included))
        suffix = decision.rsplit(":", 1)[-1]
        snapshot_ref, snapshot_hash = a.blob(f"inputs/{suffix}.json", policy_input.snapshot())
        refs = []
        for message, receipt, status, reason in gates:
            consumption = a.identity("consumption")
            a.emit("consumption", "p7.policy.actual_input_gate", self.vehicle, self.incarnation, now, step,
                "POLICY_CALL_INPUT", snapshot_ref, source=message.source_event_id, message=message.message_id,
                consumption_receipt_id=consumption, input_receipt_id=receipt, message_id=message.message_id,
                payload_hash=message.payload_hash, controller_instance_id=self.controller_id, decision_id=decision,
                policy_version=self.policy_config.policy_version, input_snapshot_hash=snapshot_hash,
                consumption_status=status, reason=reason, adoption_boundary_version=ADOPTION_BOUNDARY_VERSION,
                adoption_boundary_status=ADOPTION_BOUNDARY_STATUS)
            if status == "POLICY_INPUT_INCLUDED":
                refs.append({"message_id": message.message_id, "consumption_receipt_id": consumption})
        try:
            output = self.policy(policy_input, self.policy_config)
            target = output.target_speed_reference_mps
            changed = target != self.active_reference
            result = {**asdict(output), "decision_id": decision, "input_snapshot_ref": snapshot_ref,
                      "input_snapshot_hash": snapshot_hash, "new_command_needed": changed}
            outref, _ = a.blob(f"decisions/{suffix}.json", result)
        except Exception as exc:
            outref, _ = a.blob(f"decisions/{suffix}.json", {"decision_id": decision, "failure": repr(exc)})
            a.emit("decision", "p7.policy.output", self.vehicle, self.incarnation, now, step, "POLICY_FAILED",
                outref, decision_id=decision, controller_instance_id=self.controller_id, policy_version=self.policy_config.policy_version,
                input_snapshot_hash=snapshot_hash, consumed_message_refs=refs, decision_status="FAILED",
                decision_output_ref=outref, control_intent="FAILED", no_change_reason=repr(exc), command_disposition="NONE")
            raise
        a.emit("decision", "p7.policy.output", self.vehicle, self.incarnation, now, step, "DECISION", outref,
            decision_id=decision, controller_instance_id=self.controller_id, policy_version=self.policy_config.policy_version,
            input_snapshot_hash=snapshot_hash, consumed_message_refs=refs, decision_status="DECIDED" if changed else "UNCHANGED",
            decision_output_ref=outref, control_intent=output.control_intent, no_change_reason=None if changed else "SAME_REFERENCE_NO_NEW_COMMAND",
            command_disposition="EXPECTED" if changed else "NONE")
        if changed:
            self._issue(decision, target, state, vehicle_api)
        return result

    def _issue(self, decision: str, target: float | None, state: LocalState, vehicle_api):
        a, now, step = self.a, state.simulation_time_s, state.simulation_step
        command = a.identity("command")
        value = self.original_max if target is None else target
        issue_time = a.time(now, step, "API_ISSUE")
        raw = {"command_id": command, "decision_id": decision, "api": "traci.vehicle.setMaxSpeed",
            "vehicle_id": self.vehicle, "value_mps": value, "release_original_limit": target is None,
            "replaces_command_id": self.active_command, "issue_time": asdict(issue_time)}
        failure, ack, status = None, None, "ACKNOWLEDGED"
        try:
            vehicle_api.setMaxSpeed(self.vehicle, value)
            raw["getter_max_speed_mps"] = vehicle_api.getMaxSpeed(self.vehicle)
            if raw["getter_max_speed_mps"] != value:
                raise RuntimeError("MAX_SPEED_READBACK_MISMATCH")
            ack = a.time(now, step, "API_RETURN")
        except Exception as exc:
            failure, status = repr(exc), "UNKNOWN"
        raw.update(status=status, failure=failure, ack_time=asdict(ack) if ack else None)
        ref, _ = a.blob("commands/" + command.rsplit(":", 1)[-1] + ".json", raw)
        a.emit("command", "p7.traci.setMaxSpeed_boundary", self.vehicle, self.incarnation, now, step,
            "COMMAND_CALL_RETURN", ref, command_id=command, decision_id=decision, controller_instance_id=self.controller_id,
            target_vehicle_id=self.vehicle, command_type="RESTORE_NATIVE_MAX_SPEED" if target is None else "SET_MAX_SPEED_REFERENCE",
            command_value=value, command_unit="m/s", valid_from=issue_time, valid_until=None, command_status=status,
            execution_interface_ref=ref, ack_time=ack, failure_reason=failure,
            execution_disposition="EXPECTED" if not failure else "UNKNOWN", event_time=issue_time)
        if failure:
            raise RuntimeError("COMMAND_CALL_FAILED: " + failure)
        if self.command_tenures:
            self.command_tenures[-1].update(superseded_by=command, tenure_end_s=now)
        self.command_tenures.append({"command_id": command, "tenure_start_s": now,
                                    "tenure_end_s": None, "superseded_by": None})
        self.active_reference, self.active_command = target, command

    def observe(self, row: dict, readback_ref: str) -> str:
        a, now, step = self.a, row["simulation_time_s"], row["simulation_step"]
        refs = []
        if self.active_command:
            execution = a.identity("execution")
            execution_time = a.time(now, step, "POST_STEP_READBACK")
            a.emit("execution", "p7.post_step.actual_state_reader", self.vehicle, self.incarnation, now, step,
                "POST_STEP_READBACK", readback_ref, execution_id=execution, command_id=self.active_command,
                target_vehicle_id=self.vehicle, execution_end=a.time(now, step, "READBACK_COMPLETE"),
                execution_status="EXECUTED" if row["readback_status"] == "OBSERVED" else
                    "VEHICLE_EXITED" if row["vehicle_existence"] is False else "UNOBSERVABLE",
                actual_acceleration=row.get("acceleration_mps2"), actual_speed=row.get("speed_mps"),
                actual_position=row.get("lane_position_m"), state_readback_ref=readback_ref,
                execution_reason="NATIVE_STATE_DURING_COMMAND_TENURE_NOT_CAUSAL_ATTRIBUTION",
                safety_intervention_refs=[], event_time=execution_time)
            refs.append(execution)
        action = a.identity("action")
        a.emit("action_observation", "p7.p4.continuous_action_observer", self.vehicle, self.incarnation, now, step,
            "ACTION_OBSERVATION", readback_ref, action_observation_id=action, execution_refs=refs, comparison_ref=None,
            action_change_status="UNKNOWN", observation_ref=readback_ref)
        if row["vehicle_existence"] is False:
            self.closed = True
            if self.command_tenures:
                self.command_tenures[-1].update(tenure_end_s=now, vehicle_exited=True)
        return action

    def risk_attachment(self, action_refs: list[str], now: float, step: int, measurement: dict) -> str:
        ref, _ = self.a.blob("risk_observation.json", measurement)
        risk = self.a.identity("risk")
        self.a.emit("risk_observation", "p7.p4.existing_risk_reference_adapter", self.vehicle, self.incarnation,
            now, step, "RISK_REFERENCE", ref, risk_observation_id=risk, action_observation_refs=action_refs,
            measurement_version=measurement["measurement_version"], observation_ref=ref, risk_status="UNKNOWN")
        return risk

    def censor(self, now: float, step: int, reason: str) -> None:
        """Observed run termination does not imply future execution or non-execution."""
        ref, _ = self.a.blob("termination.json", {"time_s": now, "step": step, "reason": reason})
        if self.active_command:
            self.a.emit("execution", "p7.post_step.actual_state_reader", self.vehicle, self.incarnation,
                now, step, "RIGHT_CENSORED", ref, execution_id=self.a.identity("execution"),
                command_id=self.active_command, target_vehicle_id=self.vehicle, execution_end=None,
                execution_status="RIGHT_CENSORED", actual_acceleration=None, actual_speed=None, actual_position=None,
                state_readback_ref=None, execution_reason=reason, safety_intervention_refs=[])
        if self.command_tenures:
            self.command_tenures[-1]["termination_status"] = "RIGHT_CENSORED"
        self.closed = True


def generate_synthetic_message(adapter: P7EvidenceAdapter, state: LocalState, config: dict) -> Message:
    # The synthetic input is identical across conditions; run identity is contextual.
    source, mid = "p7-engineering-source-1", "p7-engineering-message-1"
    now, step = state.simulation_time_s, state.simulation_step
    sender = "p7_synthetic_source"
    source_ref, _ = adapter.blob("synthetic_source.json", {"source_event_id": source,
        "observed_generation_time_s": now, "fixture_only": True, "qualification_status": "UNKNOWN",
        "formal_qualified": False, "scientific_claim_eligible": False})
    adapter.emit("source", "p7.synthetic_event_generator", sender, "synthetic-source-life-1", now, step,
        "SOURCE_GENERATION", source_ref, source=source, source_type="UNKNOWN", qualification_status="UNKNOWN", confirmation_ref=source_ref)
    p = RiskPayload(PAYLOAD_SCHEMA, PARAMETER_STATUS, source, "SYNTHETIC_REMOTE_RISK",
        config["message_risk_level"], config["engineering_applicable_edge"],
        *config["engineering_applicable_lane_position_m"], (state.vehicle_id,), now, now, config["message_valid_until_s"])
    raw = p.to_bytes()
    ref, digest = adapter.blob("payloads/" + mid.rsplit(":", 1)[-1] + ".json", raw, raw=True)
    declared_expiry = replace(adapter.time(p.valid_until, step, "DECLARED_VALIDITY_END"),
                              observed_at=now, available_at=now,
                              reason="ENGINEERING_CONFIGURATION_TIMESTAMP_KNOWN_AT_GENERATION_NOT_FUTURE_OBSERVATION")
    adapter.emit("message", "p7.risk_message_generator", sender, "synthetic-source-life-1", now, step,
        "MESSAGE_GENERATION", ref, source=source, message=mid, sender_id=sender, payload_hash=digest, payload_type=PAYLOAD_SCHEMA,
        payload_ref=ref, message_kind="SOURCE", valid_from=adapter.time(now, step, "VALID_FROM"),
        valid_until=declared_expiry,
        validity_rule_ref="controller_config.json#ENGINEERING_CANDIDATE_NOT_FORMAL")
    return Message(mid, sender, state.vehicle_id, source, raw, digest)
