"""Auditable initial-speed amendment; no simulation, topology or DS38 changes."""
from __future__ import annotations
import hashlib
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from stage_0_5_input_fidelity import inventory, xml


def amend_initial_speeds(routes: bytes, network: bytes):
    _, vehicles, initial, types, paths = inventory(routes)
    net = xml(network)
    edges = {e.get('id'): e for e in net.findall('edge')}
    rows, changes = [], {}
    for ident, vehicle in initial.items():
        chain = paths[vehicle.get('route')].get('edges').split()
        lane = next(l for l in edges[chain[0]].findall('lane') if l.get('index') == vehicle.get('departLane'))
        remaining = float(lane.get('length')) - float(vehicle.get('departPos'))
        raw = vehicle.get('departSpeed')
        vtype = types[vehicle.get('type')]
        numeric = None if raw == 'max' else float(raw)
        if numeric is not None and (not math.isfinite(numeric) or numeric < 0):
            raise ValueError('invalid_depart_speed:' + ident)
        current_limit = float(lane.get('speed'))
        downstream = []
        if len(chain) > 1:
            target_lanes = {c.get('toLane') for c in net.findall('connection')
                            if c.get('from') == chain[0] and c.get('to') == chain[1]
                            and c.get('fromLane') == vehicle.get('departLane')}
            downstream = [float(l.get('speed')) for l in edges[chain[1]].findall('lane')
                          if l.get('index') in target_lanes]
        emergency = vtype.get('emergencyDecel')
        emergency = float(emergency) if emergency is not None else None
        lower_bound = None
        hard_downstream = False
        if numeric is not None and downstream and emergency is not None and emergency > 0:
            # Even maximum declared braking cannot remove excess kinetic speed
            # over the available distance. No reaction-time allowance is needed
            # to prove this lower-bound conflict; it is not an insertion oracle.
            lower_bound = max(0.0, (numeric**2 - max(downstream)**2) / (2 * emergency))
            hard_downstream = numeric > max(downstream) and remaining < lower_bound
        start_conflict = numeric is not None and numeric > current_limit
        reason = ('downstream_emergency_braking_distance_exceeds_remaining' if hard_downstream
                  else 'numeric_departure_exceeds_start_lane_limit' if start_conflict else None)
        new = raw
        if reason:
            new = str(float(min(current_limit, max(downstream)) if hard_downstream else current_limit))
            changes[ident] = new
        rows.append(dict(id=ident,old_depart_speed=raw,new_depart_speed=new,reason=reason,
                         start_lane=lane.get('id'),position_m=float(vehicle.get('departPos')),
                         remaining_start_lane_m=remaining,start_lane_limit_mps=current_limit,
                         reachable_downstream_limits_mps=downstream,emergency_decel_mps2=emergency,
                         minimum_braking_distance_m=lower_bound,
                         downstream_scope='immediate connected next edge; not a proof of all future insertion safety'))
    def replace(match):
        tag = match.group()
        node = ET.fromstring(tag if tag.endswith(b'/>') else tag[:-1] + b'/>')
        ident = node.get('id')
        if ident not in changes:
            return tag
        replacement = ('departSpeed="' + changes[ident] + '"').encode()
        changed, count = re.subn(rb'\bdepartSpeed\s*=\s*([\x22\x27])[^\x22\x27]+\1', replacement, tag)
        if count != 1:
            raise ValueError('exact_speed_attribute_required:' + ident)
        return changed
    after = re.sub(rb'<vehicle\b[^>]*>', replace, routes)
    _, revised, revised_initial, _, _ = inventory(after)
    assert list(vehicles) == list(revised) and set(initial) == set(revised_initial)
    for ident in vehicles:
        expected = dict(vehicles[ident].attrib)
        if ident in changes:
            expected['departSpeed'] = changes[ident]
        assert revised[ident].attrib == expected
    report = dict(total_count=len(vehicles),initial_count=len(initial),noninitial_count=len(vehicles)-len(initial),
                  changes=[r for r in rows if r['reason']],initial_audit=rows,
                  unchanged_max_speed_initial_ids=[i for i,v in initial.items() if v.get('departSpeed') == 'max'],
                  unchanged_noninitial_count=len(vehicles)-len(initial),
                  original_sha256=hashlib.sha256(routes).hexdigest(),amended_sha256=hashlib.sha256(after).hexdigest(),
                  authorization='Current user task AAD-WEEK-2026-10-27-TO-STAGE-I-V1: i0007 15.23->10.0 and equivalent initial-speed/downstream-limit hard conflicts',
                  rule='Only departSpeed bytes of proved initial conflicts; network/positions/lanes/types/departures/order and DS38 max set unchanged',
                  limitation='Necessary lower-bound compatibility check, not guaranteed dynamic insertion or scientific acceptance')
    return after, report
