"""Static input checks only. Never writes routes or infers insertion success."""
from __future__ import annotations
from collections import Counter
import hashlib
from pathlib import PurePosixPath, PureWindowsPath
import re
import xml.etree.ElementTree as ET


class InputContractError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise InputContractError(reason)


def xml(data):
    require(b"<!DOCTYPE" not in data.upper() and b"<!ENTITY" not in data.upper(), "XML_external_entity_forbidden")
    return ET.fromstring(data)


def unique(nodes, kind):
    ids = [n.get("id") for n in nodes]
    require(all(ids) and len(ids) == len(set(ids)), "duplicate_or_missing_" + kind)
    return dict(zip(ids, nodes))


def inventory(routes):
    root = xml(routes)
    vehicles = unique(root.findall("vehicle"), "vehicle_identity")
    types = unique(root.findall("vType"), "vType")
    paths = unique(root.findall("route"), "route")
    initial = {}
    for ident, vehicle in vehicles.items():
        require(vehicle.get("type") in types and vehicle.get("route") in paths, "unknown_type_or_route:" + ident)
        depart = float(vehicle.get("depart"))
        require(depart >= 0, "negative_departure")
        if ident.startswith("i"):
            require(depart == 0, "initial_departure_not_zero")
            require(all(vehicle.get(k) is not None for k in ["departLane", "departPos", "departSpeed"]), "missing_initial_attribute")
            initial[ident] = vehicle
        else:
            require(depart != 0, "unclassified_zero_departure")
    return root, vehicles, initial, types, paths


def config_references(config, *, expected_inputs=None):
    root = xml(config)
    refs = {}
    allowed = {"net-file", "route-files", "fcd-output", "summary-output", "tripinfo-output",
               "tripinfo-output.write-unfinished", "tripinfo-output.write-undeparted"}
    for node in root.iter():
        require(not any(k.lower() in ["href", "file"] for k in node.attrib), "nested_XML_file_reference")
        if ("file" in node.tag or "output" in node.tag) and "value" in node.attrib:
            require(node.tag in allowed and node.tag not in refs, "unregistered_or_duplicate_file_reference:" + node.tag)
            if node.tag.startswith("tripinfo-output.write-"):
                require(node.get("value") in {"true", "false"}, "invalid_output_boolean")
                continue
            value = node.get("value", "")
            posix, windows = PurePosixPath(value.replace("\\", "/")), PureWindowsPath(value)
            require(bool(value) and not posix.is_absolute() and not windows.is_absolute() and not windows.drive and
                    ".." not in posix.parts and ":" not in value and "," not in value, "XML_path_escape")
            refs[node.tag] = value.replace("\\", "/")
    require({"net-file", "route-files"} <= set(refs), "missing_input_reference")
    if expected_inputs is not None:
        require(all(refs.get(k) == v for k, v in expected_inputs.items()), "XML_reference_binding")
    return refs


def compare_initial_policy(before, after, *, target_ids):
    a, av, ai, _, _ = inventory(before)
    b, bv, bi, _, _ = inventory(after)
    targets = set(target_ids)
    require(targets <= set(ai), "target_is_not_initial")
    require(list(av) == list(bv) and set(ai) == set(bi), "identity_replacement_or_reordering")
    require(a.attrib == b.attrib and len(a) == len(b), "route_root_or_count_changed")
    changed = []
    for old, new in zip(a, b):
        expected = dict(old.attrib)
        if old.tag == "vehicle" and old.get("id") in targets:
            require(float(old.get("departSpeed")) == 10, "DS10_target_not_numeric10")
            expected["departSpeed"] = "max"
            changed.append(old.get("id"))
        require(old.tag == new.tag and new.attrib == expected and old.text == new.text and old.tail == new.tail and
                [ET.tostring(c) for c in old] == [ET.tostring(c) for c in new], "forbidden_input_change")
    require(set(changed) == targets, "target_omitted")
    # Derive expected bytes in memory; no candidate XML is created.
    def replace(match):
        tag = match.group()
        item = ET.fromstring(tag if tag.endswith(b"/>") else tag[:-1] + b"/>")
        if item.get("id") not in targets:
            return tag
        value, n = re.subn(rb'\bdepartSpeed\s*=\s*([\x22\x27])10(?:\.0*)?\1', b'departSpeed="max"', tag)
        require(n == 1, "unsupported_numeric10_encoding")
        return value
    expected = re.sub(rb"<vehicle\b[^>]*>", replace, before)
    require(after == expected, "unapproved_byte_change")
    return dict(initial_count=len(ai), total_count=len(av), changed_initial_count=len(changed),
                unchanged_noninitial_count=len(av) - len(ai), exact_allowed_bytes_only=True,
                baseline_sha256=hashlib.sha256(before).hexdigest(), candidate_sha256=hashlib.sha256(after).hexdigest(),
                actual_insertion="Unknown; static comparison only")


def audit_bundle(routes, network, config, *, pulse_edge="main_2", pulse_mps=5):
    _, vehicles, initial, types, paths = inventory(routes)
    net = xml(network)
    edges = {e.get("id"): e for e in net.findall("edge")}
    links = {(c.get("from"), c.get("to")) for c in net.findall("connection")}
    refs = config_references(config)
    rows = []
    for ident, vehicle in initial.items():
        chain = paths[vehicle.get("route")].get("edges", "").split()
        require(bool(chain) and all(e in edges for e in chain), "unknown_route_edge")
        require(all((a, b) in links for a, b in zip(chain, chain[1:])), "disconnected_route")
        edge = chain[0]
        lanes = {lane.get("index"): lane for lane in edges[edge].findall("lane")}
        require(vehicle.get("departLane") in lanes, "unknown_start_lane:" + ident)
        lane = lanes[vehicle.get("departLane")]
        position = float(vehicle.get("departPos"))
        require(0 <= position < float(lane.get("length")), "invalid_start_position:" + ident)
        vclass = types[vehicle.get("type")].get("vClass", "passenger")
        require(vclass not in lane.get("disallow", "").split() and
                (not lane.get("allow") or vclass in lane.get("allow").split()), "lane_permission")
        text = vehicle.get("departSpeed")
        numeric = None if text == "max" else float(text)
        require(numeric is None or numeric >= 0, "invalid_depart_speed")
        limit = float(lane.get("speed"))
        rows.append(dict(id=ident, edge=edge, lane=lane.get("id"), depart_s=float(vehicle.get("depart")),
                         depart_speed=text, start_lane_limit_mps=limit, remaining_start_edge_m=float(lane.get("length")) - position,
                         static_start_speed_exceeds_limit=numeric is not None and numeric > limit,
                         potential_dynamic_pulse_speed_conflict=edge == pulse_edge and numeric is not None and numeric > pulse_mps,
                         downstream_lane_limits_mps={e: sorted({float(x.get("speed")) for x in edges[e].findall("lane")}) for e in chain[1:]}))
    return dict(total_count=len(vehicles), initial_count=len(initial), noninitial_count=len(vehicles) - len(initial),
                initial_by_start_edge=dict(Counter(r["edge"] for r in rows)), numeric10_count=sum(r["depart_speed"] != "max" and float(r["depart_speed"]) == 10 for r in rows),
                potential_dynamic_pulse_conflicts=sum(r["potential_dynamic_pulse_speed_conflict"] for r in rows),
                static_start_speed_conflicts=sum(r["static_start_speed_exceeds_limit"] for r in rows),
                references=refs, rows=rows, actual_insertion="Unknown; no safety/dynamic insertion proof")
