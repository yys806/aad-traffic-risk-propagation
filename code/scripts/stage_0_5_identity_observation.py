"""Versioned identity evidence; no simulator import or launcher.

Events are observed after a completed simulation step. Their observation time is
not substituted for actual insertion time. None means API evidence unavailable;
[] means the API was available and reported an empty set.
"""
from __future__ import annotations
from collections import Counter
from copy import copy, deepcopy
import math
import re
import hashlib
import xml.etree.ElementTree as ET

VERSION = "aad.identity-observation.v1"
API = {
    "loaded": "simulation.getLoadedIDList", "departed": "simulation.getDepartedIDList",
    "arrived": "simulation.getArrivedIDList", "pending": "simulation.getPendingVehicles",
    "active": "vehicle.getIDList", "teleport_start": "simulation.getStartingTeleportIDList",
    "teleport_end": "simulation.getEndingTeleportIDList",
}


class IdentityContractError(ValueError):
    pass


def check(condition, reason):
    if not condition:
        raise IdentityContractError(reason)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


class IdentityObserver:
    def __init__(self, declarations, *, step_s=0.05):
        rows = list(declarations)
        check(finite(step_s) and step_s > 0, "invalid_internal_step")
        check(all(isinstance(r.get("id"), str) and r["id"] and finite(r.get("depart_s")) and r["depart_s"] >= 0 for r in rows), "invalid_declaration")
        check(len({r["id"] for r in rows}) == len(rows), "duplicate_declared_identity")
        self.step = float(step_s)
        self.rows = {r["id"]: dict(declaration=deepcopy(r), state="Unknown", loaded_at=None,
                     departed_event_observed_at=None, actual_departure_s=None, depart_delay_s=None,
                     actual_insertion_speed_mps=None, post_step_departure_speed_mps=None,
                     actual_depart_lane=None, actual_depart_position_m=None, tripinfo=None,
                     arrived_at=None, discarded_at=None, teleporting=False,
                     first_FCD_s=None, last_FCD_s=None, last_native_active_s=None,
                     right_censored=None, unavailable_evidence=[]) for r in rows}
        self.time = None
        self.frames = []
        self.coverage = Counter()
        self.rejected_frames = []

    def _ids(self, values, kind):
        if values is None:
            return None
        check(isinstance(values, (list, tuple, set)), "invalid_identity_list:" + kind)
        check(all(isinstance(v, str) and v in self.rows for v in values), "unknown_identity:" + kind)
        check(len(values) == len(set(values)), "duplicate_event_identity:" + kind)
        return set(values)

    def ingest(self, frame):
        # Validate on a copy: rejected frames never partially mutate evidence.
        candidate = copy(self)
        candidate.rows = {ident: dict(row, unavailable_evidence=list(row["unavailable_evidence"])) for ident, row in self.rows.items()}
        candidate.coverage = self.coverage.copy()
        candidate.frames = list(self.frames)
        try:
            candidate._ingest(frame)
        except Exception as error:
            self.rejected_frames.append(dict(frame=deepcopy(frame), error=type(error).__name__ + ":" + str(error)))
            raise
        self.__dict__.update(candidate.__dict__)

    def _ingest(self, frame):
        now = frame.get("time_s")
        check(finite(now) and now >= 0, "invalid_clock")
        if self.time is None:
            check(abs(now) < 1e-9, "initial_snapshot_at_zero_required")
        else:
            check(abs(now - self.time - self.step) < 1e-8, "clock_gap_or_duplicate")
        check(frame.get("phase") == ("initial_snapshot" if self.time is None else "after_simulationStep"), "observation_phase")
        groups = {key: self._ids(frame.get(key), key) for key in API}
        discarded = frame.get("discarded")
        if discarded is not None:
            check(isinstance(discarded, list) and all(isinstance(x, dict) and x.get("source") in
                  {"SUMO.native_discard_log_identity", "synthetic_explicit_discard"} and
                  re.fullmatch(r"[0-9a-f]{64}", x.get("evidence_sha256", "")) for x in discarded), "discard_identity_evidence_required")
        groups["discarded"] = self._ids([x["id"] for x in discarded], "discarded") if discarded is not None else None
        # A native controller can opt into a hard per-step collision contract.
        # Synthetic replay fixtures intentionally omit this marker because they
        # are data-only tests; native frames must distinguish an observed zero
        # from a missing/invalid getter result.
        if frame.get("collision_observation_required") is True and self.time is not None:
            check(frame.get("collision_observation_status") == "available",
                  "collision_observation_missing")
            count = frame.get("collision_count")
            check(type(count) is int and count >= 0, "collision_observation_invalid")
            self.coverage["collision_required_available"] += 1
        on_road = self._ids(frame.get("on_road"), "on_road")
        if on_road is not None and groups["active"] is not None:
            check(on_road <= groups["active"], "on_road_not_in_visible_ID_set")
        for kind, ids in groups.items():
            prefix = "_initial" if self.time is None else ""
            self.coverage[kind + prefix + ("_available" if ids is not None else "_unavailable")] += 1
        for left, right in [("pending", "active"), ("pending", "arrived"), ("pending", "discarded"),
                            ("active", "arrived"), ("active", "discarded"), ("arrived", "discarded")]:
            check(not ((groups[left] or set()) & (groups[right] or set())), "contradictory_sets:" + left + ":" + right)
        for kind in ["loaded", "departed", "teleport_start", "teleport_end", "arrived", "discarded"]:
            for ident in sorted(groups[kind] or []):
                row = self.rows[ident]
                check(row["arrived_at"] is None and row["discarded_at"] is None, "event_after_terminal:" + ident)
                if kind == "loaded":
                    check(row["loaded_at"] is None, "duplicate_loaded:" + ident)
                    check(row["departed_event_observed_at"] is None, "loaded_after_departure:" + ident)
                    row["loaded_at"] = now
                elif kind == "departed":
                    check(row["departed_event_observed_at"] is None, "duplicate_departed:" + ident)
                    check(row["declaration"]["depart_s"] <= now + 1e-9, "departure_before_declaration:" + ident)
                    row["departed_event_observed_at"] = now
                elif kind == "teleport_start":
                    check(not row["teleporting"], "duplicate_teleport_start:" + ident)
                    check(row["departed_event_observed_at"] is not None or self.coverage["departed_unavailable"] > 0, "teleport_before_departure:" + ident)
                    row["teleporting"] = True
                elif kind == "teleport_end":
                    check(row["teleporting"] or self.coverage["teleport_start_unavailable"] > 0, "teleport_end_without_start:" + ident)
                    row["teleporting"] = False
                elif kind == "arrived":
                    check(row["departed_event_observed_at"] is not None or self.coverage["departed_unavailable"] > 0, "arrival_before_departure:" + ident)
                    row["arrived_at"] = now
                    row["teleporting"] = False
                else:
                    row["discarded_at"] = now
        native = frame.get("native_departures", {})
        check(isinstance(native, dict) and set(native) <= set(self.rows), "unknown_native_departure_identity")
        for ident, item in native.items():
            row = self.rows[ident]
            actual, delay = item.get("actual_departure_s"), item.get("depart_delay_s")
            if actual is not None:
                check(finite(actual) and row["declaration"]["depart_s"] - 1e-8 <= actual <= now + 1e-8, "invalid_native_departure_time")
                check(row["actual_departure_s"] is None or abs(row["actual_departure_s"] - actual) < 1e-8, "native_departure_changed")
                check(row["first_FCD_s"] is None or row["first_FCD_s"] + 1e-8 >= actual, "FCD_before_actual_departure")
                row["actual_departure_s"] = actual
            if delay is not None:
                check(finite(delay) and delay >= 0, "invalid_departure_delay")
                if actual is not None:
                    check(abs(actual - row["declaration"]["depart_s"] - delay) < 1e-7, "departure_delay_mismatch")
                row["depart_delay_s"] = delay
            if item.get("post_step_speed_mps") is not None:
                check(finite(item["post_step_speed_mps"]) and item["post_step_speed_mps"] >= 0, "invalid_post_step_speed")
                row["post_step_departure_speed_mps"] = item["post_step_speed_mps"]
            row["post_step_departure_lane"] = item.get("post_step_lane")
            row["post_step_departure_position_m"] = item.get("post_step_position_m")
        for ident, row in self.rows.items():
            if row["arrived_at"] is not None or row["discarded_at"] is not None:
                check(ident not in (groups["active"] or set()) and ident not in (groups["pending"] or set()), "terminal_identity_reappeared:" + ident)
            row["on_road_observed"] = (ident in on_road) if on_road is not None else None
            if row["arrived_at"] is not None:
                row["state"] = "arrived_native"
            elif row["discarded_at"] is not None:
                row["state"] = "discarded_explicit_evidence"
            elif ident in (groups["active"] or set()):
                check(not row["teleporting"], "active_while_teleporting:" + ident)
                row["state"] = "active_native"
                row["last_native_active_s"] = now
                if row["departed_event_observed_at"] is None and row["actual_departure_s"] is None:
                    if "active_without_departure_evidence" not in row["unavailable_evidence"]:
                        row["unavailable_evidence"].append("active_without_departure_evidence")
            elif ident in (groups["pending"] or set()):
                check(row["departed_event_observed_at"] is None and row["actual_departure_s"] is None, "pending_after_departure:" + ident)
                row["state"] = "pending_native"
            elif row["teleporting"]:
                row["state"] = "teleporting_native"
            else:
                row["state"] = "not_yet_scheduled" if row["declaration"]["depart_s"] > now else "Unknown"
                if row["last_native_active_s"] is not None and "disappeared_without_terminal_evidence" not in row["unavailable_evidence"]:
                    row["unavailable_evidence"].append("disappeared_without_terminal_evidence")
        self.frames.append(dict(deepcopy(frame), evidence_window_s=[self.time, now], sources=dict(API),
                                event_timestamp_semantics="observed after step; exact departure only from vehicle.getDeparture"))
        self.time = float(now)

    def observe_fcd(self, ident, time_s):
        check(ident in self.rows and finite(time_s) and time_s >= 0, "invalid_FCD_identity_or_clock")
        check(abs(time_s / 0.1 - round(time_s / 0.1)) < 1e-7, "FCD_clock_not_on_100ms_grid")
        check(self.time is None or time_s <= self.time + 1e-8, "FCD_beyond_native_observation")
        row = self.rows[ident]
        check(row["last_FCD_s"] is None or time_s > row["last_FCD_s"] + 1e-9, "duplicate_or_reversed_FCD")
        check(row["actual_departure_s"] is None or time_s + 1e-8 >= row["actual_departure_s"], "FCD_before_actual_departure")
        if row["first_FCD_s"] is None:
            row["first_FCD_s"] = float(time_s)
        row["last_FCD_s"] = float(time_s)

    def observe_tripinfo(self, data):
        """Bound unfinished/undeparted output; never infer discard from absence."""
        check(b"<!DOCTYPE" not in data.upper() and b"<!ENTITY" not in data.upper(), "unsafe_tripinfo_XML")
        root = ET.fromstring(data)
        check(root.tag == "tripinfos", "invalid_tripinfo_root")
        updates, seen = {}, set()
        for item in root.findall("tripinfo"):
            ident = item.get("id")
            check(ident in self.rows and ident not in seen, "unknown_or_duplicate_tripinfo_identity")
            seen.add(ident)
            row = deepcopy(self.rows[ident])
            depart, arrival = float(item.get("depart")), float(item.get("arrival"))
            check(finite(depart) and finite(arrival), "invalid_tripinfo_clock")
            if depart >= 0:
                delay, speed, position = (float(item.get(k)) for k in ["departDelay", "departSpeed", "departPos"])
                check(all(finite(v) and v >= 0 for v in [delay, speed, position]), "invalid_tripinfo_departure")
                check(abs(depart - row["declaration"]["depart_s"] - delay) < 1e-7, "tripinfo_delay_mismatch")
                check(self.time is not None and depart <= self.time + 1e-8, "tripinfo_departure_beyond_observation")
                check(row["actual_departure_s"] is None or abs(row["actual_departure_s"] - depart) < 1e-7, "tripinfo_departure_mismatch")
                check(row["departed_event_observed_at"] is None or
                      -1e-8 <= row["departed_event_observed_at"] - depart <= self.step + 1e-7, "tripinfo_departed_event_clock")
                check(bool(item.get("departLane")), "tripinfo_depart_lane_missing")
                check(row["first_FCD_s"] is None or row["first_FCD_s"] >= depart - 1e-8, "FCD_before_tripinfo_departure")
                row.update(actual_departure_s=depart, depart_delay_s=delay, actual_insertion_speed_mps=speed,
                           actual_depart_lane=item.get("departLane"), actual_depart_position_m=position)
            else:
                check(row["actual_departure_s"] is None and row["departed_event_observed_at"] is None, "tripinfo_undeparted_conflict")
            if arrival >= 0:
                check(row["arrived_at"] is not None and -1e-8 <= row["arrived_at"] - arrival <= self.step + 1e-7, "tripinfo_arrival_without_matching_event")
            else:
                check(row["arrived_at"] is None, "tripinfo_unfinished_conflict")
            row["tripinfo"] = dict(attributes=dict(item.attrib), source="SUMO.tripinfo-output", sha256=hashlib.sha256(data).hexdigest(),
                                    unfinished=arrival < 0, undeparted=depart < 0)
            updates[ident] = row
        self.rows.update(updates)
        return dict(observed=len(seen), absent=sorted(set(self.rows) - seen), absence_semantics="Unknown, not discarded")

    def finish(self, *, interrupted=False):
        rows = deepcopy(self.rows)
        for row in rows.values():
            terminal = row["arrived_at"] is not None or row["discarded_at"] is not None
            row["right_censored"] = not terminal
            row["native_insertion_status"] = ("observed_actual_departure" if row["actual_departure_s"] is not None else
                                              ("observed_departed_event" if row["departed_event_observed_at"] is not None else "Unknown"))
            row["FCD_observation_status"] = "observed" if row["first_FCD_s"] is not None else "not_observed"
            row["end_reason"] = "simulation_interrupted" if interrupted else "finite_observation_end"
        complete = not self.rejected_frames and self.time is not None and all(not r["unavailable_evidence"] and r["state"] != "Unknown" for r in rows.values()
                       if self.time is not None and r["declaration"]["depart_s"] <= self.time)
        # Only completed-step gaps count here; *_initial_unavailable is separate.
        complete &= all(self.coverage[k + "_unavailable"] == 0 for k in
                        ["loaded", "departed", "arrived", "pending", "active", "teleport_start", "teleport_end"])
        if self.coverage["collision_required_available"]:
            complete &= self.coverage["loaded_initial_unavailable"] == 0
        exact_departure_clock = complete and all(r["actual_departure_s"] is not None for r in rows.values()
                                                 if r["departed_event_observed_at"] is not None)
        return dict(version=VERSION, last_native_observation_s=self.time, observations=len(self.frames),
                    rejected_observations=deepcopy(self.rejected_frames),
                    collision_coverage_complete=bool(not interrupted and not self.rejected_frames and self.time is not None and
                        self.coverage["collision_required_available"] == round(self.time / self.step) and self.time > 0),
                    declared_count=len(rows), states=dict(Counter(r["state"] for r in rows.values())),
                    identity_accounting_complete=bool(complete),
                    native_departure_clock_complete=bool(exact_departure_clock),
                    API_coverage=dict(self.coverage), vehicles=rows,
                    limits=["FCD absence is not pending/discard", "No native discard ID getter verified",
                            "Missing native active/arrival evidence leaves state Unknown", "Not a scientific initialization acceptance"])


def collect_snapshot(connection, *, initial=False):
    """Read-only getters on an already connected object; never starts/connects SUMO."""
    frame = dict(time_s=connection.simulation.getTime(), phase="initial_snapshot" if initial else "after_simulationStep",
                 discarded=None, native_departures={}, unavailable={})
    for key, source in API.items():
        if initial and key not in {"loaded", "active", "pending"}:
            frame[key] = None
            frame["unavailable"][key] = "No completed step in initial snapshot; event interval is undefined"
            continue
        domain, method = source.split(".")
        try:
            frame[key] = list(getattr(getattr(connection, domain), method)())
        except Exception as error:
            frame[key] = None
            frame["unavailable"][key] = type(error).__name__ + ":" + str(error)
    for ident in frame["departed"] or []:
        item = {"actual_departure_s": None, "depart_delay_s": None, "post_step_speed_mps": None}
        for field, method in [("actual_departure_s", "getDeparture"), ("depart_delay_s", "getDepartDelay"), ("post_step_speed_mps", "getSpeed")]:
            try:
                value = float(getattr(connection.vehicle, method)(ident))
                if not math.isfinite(value) or value < 0:
                    raise ValueError("native_invalid_sentinel")
                item[field] = value
            except Exception as error:
                frame["unavailable"][ident + ":" + method] = type(error).__name__ + ":" + str(error)
        for field, method in [("post_step_lane", "getLaneID"), ("post_step_position_m", "getLanePosition")]:
            try:
                item[field] = getattr(connection.vehicle, method)(ident)
            except Exception as error:
                item[field] = None
                frame["unavailable"][ident + ":" + method] = type(error).__name__ + ":" + str(error)
        frame["native_departures"][ident] = item
    frame["on_road"] = None
    if frame["active"] is not None:
        try:
            frame["on_road"] = [ident for ident in frame["active"] if connection.vehicle.getLaneID(ident)]
        except Exception as error:
            frame["unavailable"]["on_road"] = type(error).__name__ + ":" + str(error)
    frame["collision_observation_required"] = not initial
    frame["collision_count_semantics"] = "colliding_vehicle_count_current_step; not collision_event_count"
    try:
        value = connection.simulation.getCollidingVehiclesNumber()
        # TraCI returns an integer vehicle count.  Do not coerce None, bool,
        # floats, strings, or negative sentinels into a plausible zero.
        if type(value) is not int or value < 0:
            raise ValueError("invalid_collision_vehicle_count:" + repr(value))
        frame["collision_count"] = value
        frame["collision_observation_status"] = "available"
    except Exception as error:
        frame["collision_count"] = None
        frame["collision_observation_status"] = "invalid" if isinstance(error, ValueError) and str(error).startswith("invalid_collision_vehicle_count") else "unavailable"
        frame["unavailable"]["collision_count"] = type(error).__name__ + ":" + str(error)
    return frame
