"""Candidate queue observations and qualifications; not a scientific Gate."""
from __future__ import annotations
from collections import defaultdict
import math

METHODS=("legacy_grid","grid_candidate","vehicle_graph")


def observe_queue(frame,config,method="vehicle_graph"):
    if method not in METHODS:raise ValueError("unknown queue method")
    rows=frame["vehicles"];lo,hi=frame["observed_range_m"];length=frame["road_length_m"]
    errors=[]
    if not frame.get("positions_verified") or not frame.get("coordinate_frame"):errors.append("unverified_coordinate_frame")
    if len({r["vehicle_id"] for r in rows})!=len(rows):errors.append("duplicate_vehicle_identity")
    if len({r.get("incarnation_id") for r in rows})!=len(rows):errors.append("duplicate_incarnation")
    if not 0<=lo<hi<=length:errors.append("invalid_observation_domain")
    if not frame.get("supported_lanes") or frame.get("supported_lane_count")!=len(frame["supported_lanes"]):errors.append("undefined_lane_support")
    for r in rows:
        if any(not isinstance(r.get(k),(float,int)) or not math.isfinite(r[k]) for k in ["position_m","speed_mps","length_m"]):errors.append("nonfinite_vehicle_state");continue
        if not lo<=r["position_m"]<hi or r["length_m"]<=0 or r["speed_mps"]<0 or not r.get("lane_id"):errors.append("invalid_vehicle_state_or_support")
        if r.get("lane_id") not in frame.get("supported_lanes",[]):errors.append("vehicle_outside_lane_support")
    if frame["inserted_total"]-frame["exited_total"]!=frame["present"] or frame["present"]!=len(rows):errors.append("vehicle_conservation")
    if frame["scheduled_due"]-frame["inserted_total"]!=frame["pending"]:errors.append("external_demand_accounting")
    slow=[r for r in rows if r["speed_mps"]<config["speed_low_mps"]]
    result=dict(method=method,time_s=frame["time_s"],observation_valid=not errors,quality_errors=errors,
        coordinate_frame=frame["coordinate_frame"],observed_range_m=[lo,hi],full_road_observed=lo==0 and hi==length,
        low_vehicles=len(slow),stopped_vehicles=sum(r["speed_mps"]<config["stopped_speed_mps"] for r in rows),
        local_density_veh_km_lane=len(rows)/((hi-lo)/1000*frame["supported_lane_count"]) if hi>lo and frame.get("supported_lane_count",0)>0 else None,
        present=frame["present"],pending=frame["pending"],inserted_total=frame["inserted_total"],exited_total=frame["exited_total"],
        physical_entry_space_observed=frame["physical_entry_space_observed"],arrival_manifest_valid=frame["arrival_manifest_valid"],
        downstream_service_context=frame["downstream_service_context"],components=[],grid_cells=[],
        low_speed_observation_is_not_automatically_queue=True)
    if errors:return result
    minimum=config["minimum_queue_vehicles"];G=config["max_net_gap_m"];cell=config["grid_m"]
    components=[]
    if method=="vehicle_graph":
        lanes=defaultdict(list)
        for r in rows:lanes[r["lane_id"]].append(r)
        for lane,values in sorted(lanes.items()):
            group=[];previous=None
            for r in sorted(values,key=lambda v:v["position_m"]):
                low=r["speed_mps"]<config["speed_low_mps"]
                connected=bool(group) and low and previous is not None and previous["speed_mps"]<config["speed_low_mps"] and previous["edge_id"]==r["edge_id"] and 0<=r["position_m"]-r["length_m"]-previous["position_m"]<=G
                if not connected:
                    if len(group)>=minimum:components.append((lane,group,None))
                    group=[]
                if low:group.append(r)
                previous=r
            if len(group)>=minimum:components.append((lane,group,None))
    else:
        cells=defaultdict(list)
        for r in rows:cells[("pooled" if method=="legacy_grid" else r["lane_id"],int(r["position_m"]//cell))].append(r)
        active={}
        for (lane,index),values in cells.items():
            low=[r for r in values if r["speed_mps"]<config["speed_low_mps"]]
            good=len(low)>=2 if method=="legacy_grid" else bool(low) and len(low)/len(values)>=config["cell_low_fraction"]
            result["grid_cells"].append(dict(lane=lane,index=index,vehicles=len(values),low=len(low),low_share=len(low)/len(values),active=good))
            if good:active[(lane,index)]=low
        if method=="legacy_grid":
            i=int((length-1e-9)//cell);group=[];indices=[]
            while ("pooled",i) in active:group=active[("pooled",i)]+group;indices.insert(0,i);i-=1
            if group:components.append(("pooled",group,indices))
        else:
            for lane in sorted({k[0] for k in active}):
                group=[];indices=[];previous=None
                for index in sorted(k[1] for k in active if k[0]==lane):
                    if previous is not None and index!=previous+1:
                        if len(group)>=minimum:components.append((lane,group,indices))
                        group=[];indices=[]
                    group+=active[(lane,index)];indices.append(index);previous=index
                if len(group)>=minimum:components.append((lane,group,indices))
    for lane,group,indices in components:
        rear=min(r["position_m"]-r["length_m"] for r in group);front=max(r["position_m"] for r in group)
        censored=not result["full_road_observed"]
        if censored:boundary=None;interval=[None,None]
        elif method=="legacy_grid":boundary=indices[0]*cell;interval=[boundary,boundary]
        elif method=="grid_candidate":
            interval=[max(lo,indices[0]*cell-max(r["length_m"] for r in group)),min(hi,(indices[0]+1)*cell-min(r["length_m"] for r in group))]
            boundary=None # grid support interval, not a measured point front
        else:boundary=rear;interval=[rear-config["position_uncertainty_m"],rear+config["position_uncertainty_m"]]
        if censored:inlet=None
        elif method=="legacy_grid":inlet=boundary<=config["inlet_zone_m"]
        elif interval[1]<config["inlet_zone_m"]:inlet=True
        elif interval[0]>=config["inlet_zone_m"]:inlet=False
        else:inlet=None
        result["components"].append(dict(lane=lane,members=sorted(r["incarnation_id"] for r in group),vehicles=len(group),
            upstream_boundary_m=boundary,upstream_interval_m=interval,front_left_censored=censored,
            downstream_m=front,downstream_anchored=front>=length-config["anchor_zone_m"],
            inlet_adjacent=inlet,spatial_resolution_limited=method!="vehicle_graph"))
    return result


def qualify_series(observations,config):
    """No imputation across a missing snapshot, lane change, or release gap."""
    if not observations:raise ValueError("observations required")
    history=[];tracks=[];previous=None;breaks=0;extension=False
    for o in observations:
        dt=None if previous is None else o["time_s"]-previous["time_s"]
        gap=previous is not None and (dt<=0 or abs(dt-config["snapshot_step_s"])>1e-9 or not previous["observation_valid"] or o["coordinate_frame"]!=previous["coordinate_frame"])
        if gap:tracks=[];breaks+=1
        new=[]
        for c in o["components"]:
            matches=[t for t in tracks if t["component"]["lane"]==c["lane"] and set(c["members"])&set(t["component"]["members"])]
            prior=max(matches,key=lambda t:len(set(t["component"]["members"])&set(c["members"]))) if matches else None
            duration=(prior["duration_s"]+dt) if prior is not None and dt is not None else 0.
            inlet_duration=(prior["inlet_duration_s"]+dt) if prior is not None and c["inlet_adjacent"] is True and prior["component"]["inlet_adjacent"] is True else 0.
            if prior:
                old=prior["component"]["upstream_interval_m"];current=c["upstream_interval_m"]
                if old[0] is not None and current[1] is not None and current[1]<old[0]:extension=True
            new.append(dict(component=c,duration_s=duration,inlet_duration_s=inlet_duration))
        tracks=new;previous=o
        full=o["full_road_observed"] and o["observation_valid"]
        inlet=any(c["inlet_adjacent"] is True for c in o["components"]) if full else None
        persistent=[t for t in tracks if t["component"]["downstream_anchored"] and t["inlet_duration_s"]>=config["duration_s"]]
        cause=o["physical_entry_space_observed"] and o["arrival_manifest_valid"] and o["downstream_service_context"]
        supported=bool(persistent) and o["pending"]>0 and cause if full else None
        if not full or (o["components"] and not o["downstream_service_context"]):state="Evidence Insufficient"
        elif supported:state="Entry Spillback Supported"
        elif inlet:state="Inlet-Adjacent Queue Observed"
        elif not o["components"]:state="No On-Road Queue"
        elif extension:state="Upstream Queue Extension Observed"
        elif o["components"]:state="On-Road Queue Observed"
        else:state="No On-Road Queue"
        history.append(dict(time_s=o["time_s"],state=state,inlet_adjacent_queue_observed=inlet,
            entry_spillback_supported=supported,continuous_inlet_duration_s=max([t["inlet_duration_s"] for t in tracks] or [0.])))
    last=observations[-1]
    qualified_queue=bool(last["components"]) if last["observation_valid"] else None
    if qualified_queue and not last["downstream_service_context"]:qualified_queue=None
    return dict(history[-1],method=last["method"],onroad_queue_observed=qualified_queue,
        onroad_spatial_cluster_observed=bool(last["components"]),queue_cause_status="service context supplied; unique causation not proven" if last["downstream_service_context"] else "Unresolved",
        upstream_extension_observed=extension,external_pending=last["pending"],temporal_breaks=breaks,
        entry_cause_status="Observed physical entry-space constraint" if last["physical_entry_space_observed"] else "Unresolved",
        observation_history=history,qualification_status="Candidate; no scientific approval",scientific_claim_eligible=False,
        limitations=["Slow connected vehicles are an observed candidate queue, not proof of a unique downstream cause",
            "No joining across unverified edge/path coordinates or different lanes; lane changes reset continuity",
            "No smoothing through release/missing frames; sparse/noisy fronts can remain unresolved",
            "Pending alone cannot identify insertion cause; physical entry-space evidence must be supplied independently"])
