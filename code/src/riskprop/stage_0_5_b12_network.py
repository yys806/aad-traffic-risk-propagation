"""B1.2 checked path coordinates include explicit internal junction lanes."""
from __future__ import annotations
import math
import xml.etree.ElementTree as ET


def coordinate_support(path):
    net=ET.parse(path).getroot()
    lanes={l.attrib["id"]:dict(l.attrib,edge=e.attrib["id"]) for e in net.findall("edge") for l in e.findall("lane")}
    connections=[dict(c.attrib) for c in net.findall("connection")]
    mapped={};lengths={};checks=[];errors=[];geometry=[]
    def xy(lane):return [tuple(map(float,p.split(","))) for p in lanes[lane]["shape"].split()]
    def link_chain(source,destination):
        matches=[c for c in connections if c["from"]==source.rsplit("_",1)[0] and c["fromLane"]==source.rsplit("_",1)[1] and c["to"]==destination.rsplit("_",1)[0] and c["toLane"]==destination.rsplit("_",1)[1]]
        if len(matches)!=1:raise ValueError("nonunique corridor connection")
        c=matches[0];via=c.get("via");chain=[];seen=set()
        while via:
            if via in seen or via not in lanes:raise ValueError("unknown internal path")
            seen.add(via);chain.append(via)
            ll=lanes[via];nexts=[k for k in connections if k["from"]==ll["edge"] and k["fromLane"]==ll["index"] and k["to"]==c["to"] and k["toLane"]==c["toLane"]]
            if len(nexts)!=1:raise ValueError("internal connection not unique")
            via=nexts[0].get("via")
        return chain
    for i in range(3):
        pid=str(i);a=f"main_0_{i}";b=f"main_1_{i}"
        try:
            chain=[a,*link_chain(a,b),b];offset=0.
            for lane in chain:
                if lane in mapped:raise ValueError("shared path lane is ambiguous")
                length=float(lanes[lane]["length"])
                points=xy(lane);arc=sum(math.dist(p,q) for p,q in zip(points,points[1:]))
                geometry.append(dict(lane=lane,declared_length_m=length,polyline_length_m=arc,
                                     absolute_difference_m=abs(arc-length),shape=lanes[lane]["shape"]))
                if length<=0 or any(q[0]<p[0]-1e-8 for p,q in zip(points,points[1:])):raise ValueError("nonlongitudinal corridor")
                mapped[lane]=dict(path=pid,offset_m=offset,length_m=length,edge=lanes[lane]["edge"])
                offset+=length
            continuity=[math.dist(xy(x)[-1],xy(y)[0]) for x,y in zip(chain,chain[1:])]
            if any(v>1e-8 for v in continuity):raise ValueError("path endpoint gap")
            lengths[pid]=offset;checks.append(dict(path=pid,lanes=chain,length_m=offset,junction_included=True,endpoint_gaps_m=continuity))
        except ValueError as exc:errors.append(dict(path=pid,reason=str(exc)))
    down={str(i):[c for c in connections if c["from"]=="main_1" and c["fromLane"]==str(i) and c["to"]=="main_2"] for i in range(3)}
    count2=sum(l["edge"]=="main_2" for l in lanes.values())
    d_ok=count2 in (2,3) and all(down[str(i)] for i in range(count2))
    if count2==2:d_ok=d_ok and not down["2"]
    if not d_ok:errors.append(dict(reason="downstream_connectivity"))
    # Logical simulation coordinate is defined by loaded lane lengths, not a
    # claim about the real road. Geometry rounding discrepancies are reported.
    return dict(lanes=mapped,path_lengths=lengths,path_checks=checks,geometry_checks=geometry,
                coordinate_verified=not errors,cross_edge_verified=not errors,
                engineering_position_uncertainty_m=0.,real_world_position_uncertainty_m="Unknown",
                precision_basis="Logical route distance in loaded SUMO lane-length units; no sensor precision claim; runtime cross-check required before main admission",
                geometry_length_disagreement_max_m=max([g["absolute_difference_m"] for g in geometry] or [0.]),
                unknown_paths=[e.get("path","downstream") for e in errors],errors=errors,
                main2_lanes=count2,mandatory_lane_change_from=["main_1_2"] if count2==2 else [],
                downstream_connections=down,all_lane_lengths={k:float(v["length"]) for k,v in lanes.items()},
                all_lane_edges={k:v["edge"] for k,v in lanes.items()},
                comparison_rule="Only the same checked lane path; no joining between lateral paths; main_2 outside upstream queue domain")
