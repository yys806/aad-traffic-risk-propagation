"""B1.2 engineering observations. No scientific traffic or risk threshold changes.

Independent version: the B1.1 full-frame synthetic queue contract is unchanged.
No displacement is used to infer a signed speed. Unknowns are never zero-filled.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import math

from .stage_0_5_stopping_observability import (
    reconstruct_signed_vnext, step_is_action, expected_displacement,
)

VERSION = "b12-integration-v1"
QUEUE_CONFIG = dict(status="engineering_candidate_for_B1_2", speed_low_mps=5.,
                    stopped_speed_mps=.1, minimum_queue_vehicles=2, max_net_gap_m=10.,
                    grid_m=50., cell_low_fraction=.5, inlet_zone_m=50., anchor_zone_m=50.,
                    duration_s=2., snapshot_step_s=1., position_uncertainty_m="Unknown")
CLASSIFICATIONS = ("Exact Observable", "Exact Reconstructable Under Verified Conditions",
                   "Bounded Consistency Only", "Not Evaluable")


def audit_transition(before, after, h=.05, action_step=.1):
    r=dict(classification="Not Evaluable", candidate=None, residual_m=None,
           actual_dx_m=None, expected_dx_m=None, bounds_m=None, passed=None,
           blocker=None, reason=None, is_action=None)
    def reject(reason, blocker=True):
        r.update(reason=reason, blocker=reason if blocker else None)
        return r
    if any(not before.get(k) or before.get(k)!=after.get(k)
           for k in ("run_id","vehicle_id","incarnation_id")):
        return reject("identity_discontinuity")
    if any(s.get("traci_vehicle_control") is not False for s in (before,after)):
        return reject("vehicle_control_unconfirmed")
    if any(s.get("numerical_config_verified") is not True for s in (before,after)):
        return reject("numerical_configuration_unconfirmed")
    for s in (before,after):
        if any(type(s.get(k)) not in (int,float) or not math.isfinite(s[k])
               for k in ("time_s","speed_mps","acceleration_mps2","position_m")):
            return reject("nonfinite_runtime_observation")
    if h<=0 or abs(after["time_s"]-before["time_s"]-h)>1e-8:
        return reject("internal_clock_inconsistent")
    action=step_is_action(after.get("last_action_time_s"),before["time_s"],h,action_step)
    r["is_action"]=action
    if type(action) is not bool:return reject("action_clock_unknown")
    v0=before["speed_mps"];v1=after["speed_mps"]
    reconstruction=reconstruct_signed_vnext(v0,before["acceleration_mps2"],h,is_action=action,v1=v1)
    if reconstruction["classification"]=="Not Evaluable":return reject(reconstruction["reason"])
    u=reconstruction["candidate"]
    if u is not None and abs(max(u,0.)-v1)>1e-9:
        return reject("candidate_terminal_speed_inconsistent")
    if any(not before.get(k) or not after.get(k) for k in ("edge_id","lane_id")):
        return reject("coordinate_identity_missing")
    if before["edge_id"]!=after["edge_id"]:
        return reject("legal_edge_transition",False)
    if before["lane_id"]!=after["lane_id"]:
        return reject("legal_lane_change",False)
    dx=after["position_m"]-before["position_m"]
    r.update(classification=reconstruction["classification"],candidate=u,
             actual_dx_m=dx,reason=reconstruction["reason"])
    if u is None and v0==v1==0:
        # Zero displacement is independently identifiable even when u is hidden.
        r.update(classification="Exact Observable",reason="stationary_zero_displacement")
        expected=0.
    elif u is None:
        upper=.5*v0*h;violation=max(0.,-dx,dx-upper)
        r.update(bounds_m=[0.,upper],bound_violation_m=violation,passed=violation<=1e-6)
        if not r["passed"]:r["blocker"]="bounded_range_violation"
        return r
    else:expected=expected_displacement(v0,u,h)
    r.update(expected_dx_m=expected,residual_m=dx-expected,passed=abs(dx-expected)<=1e-6)
    if not r["passed"]:r["blocker"]="exact_displacement_violation"
    return r


class NumericalCoverage:
    """Screen ALL adjacent internal steps; retain bounded examples and maxima."""
    def __init__(self):
        self.counts=Counter();self.reasons=Counter();self.locations=defaultdict(dict)
        self.max_abs_residual=None;self.exact_passed=0;self.blockers=Counter()
        self.examples={};self.worst=None;self.nonaction_negative=0;self.action_counts=Counter()

    def add(self,before,after):
        r=audit_transition(before,after);c=r["classification"];self.counts[c]+=1
        self.reasons[r["reason"]]+=1;self.action_counts[str(r["is_action"])]+=1
        self.nonaction_negative+=r["candidate"] is not None and r["candidate"]<0
        if r["residual_m"] is not None:
            value=abs(r["residual_m"])
            if self.max_abs_residual is None or value>self.max_abs_residual:
                self.max_abs_residual=value;self.worst=dict(before=before,after=after,**r)
            self.exact_passed+=r["passed"] is True
        if r["blocker"]:self.blockers[r["blocker"]]+=1
        if r["reason"] not in self.examples:
            self.examples[r["reason"]]=dict(before=before,after=after,**r)
        if c=="Not Evaluable":
            key=f'{r["reason"]}|{before["edge_id"]}|{before["lane_id"]}'
            loc=self.locations[key]
            if not loc:loc.update(count=0,first_s=after["time_s"],last_s=after["time_s"],vehicle_step_s=0.)
            loc["count"]+=1;loc["last_s"]=after["time_s"];loc["vehicle_step_s"]+=.05
        return r

    def summary(self):
        n=sum(self.counts.values());exact=sum(self.counts[c] for c in CLASSIFICATIONS[:2])
        return dict(version=VERSION,all_adjacent_edges=n,
                    classifications={c:dict(count=self.counts[c],fraction=self.counts[c]/n if n else None) for c in CLASSIFICATIONS},
                    exact_checked=exact,exact_passed=self.exact_passed,
                    exact_pass_fraction=self.exact_passed/exact if exact else None,
                    max_abs_residual_m=self.max_abs_residual,nonaction_negative_candidates=self.nonaction_negative,
                    action_counts=dict(self.action_counts),reasons=dict(self.reasons),
                    not_evaluable_locations=dict(self.locations),blockers=dict(self.blockers),
                    examples=self.examples,worst_exact_edge=self.worst,tolerance_m=1e-6,
                    fresh_departures_and_arrivals="No invented transition outside jointly observed endpoints",
                    unknown_fraction_threshold=None)


class ScopedAccounting:
    """Full-network identity conservation plus independent local membership flux.

    Local flux is measured from consecutive identity sets, with entry/exit causes
    separately described. It is NOT inferred from global insertions/arrivals.
    """
    def __init__(self,local_space=None):
        self.space=local_space or dict(edge="main_1",start_m=50.,end_m=250.,lanes=3,lane_km=.6)
        self.departed=set();self.arrived=set();self.previous={};self.local=set()
        self.local_in=0;self.local_out=0;self.local_vehicle_s=0.;self.last_time=None

    def update(self,rows,new,gone,due,time_s):
        if set(new)&self.departed or set(gone)&self.arrived:raise ValueError("reused_vehicle_identity")
        self.departed.update(new);self.arrived.update(gone)
        if self.departed-self.arrived!=set(rows):raise ValueError("global_identity_conservation")
        if due<len(self.departed):raise ValueError("demand_clock_accounting")
        edge=self.space["edge"];lo=self.space["start_m"];hi=self.space["end_m"]
        local={v for v,r in rows.items() if r["edge_id"]==edge and lo<=r["position_m"]<hi}
        entered=local-self.local;exited=self.local-local
        causes_in=Counter();causes_out=Counter()
        for vid in entered:
            old=self.previous.get(vid);now=rows[vid]
            cause="lower_spatial_boundary" if old and old["edge_id"]==edge and old["position_m"]<lo<=now["position_m"] else "birth_or_edge_boundary"
            causes_in[cause]+=1
        for vid in exited:
            now=rows.get(vid)
            causes_out["upper_spatial_boundary" if now and now["edge_id"]==edge and now["position_m"]>=hi else "arrival_or_edge_boundary"]+=1
        dt=0. if self.last_time is None else time_s-self.last_time
        if dt<0 or (self.last_time is not None and abs(dt-.05)>1e-8):raise ValueError("accounting_clock")
        self.local_in+=len(entered);self.local_out+=len(exited);self.local_vehicle_s+=len(local)*dt
        residual=len(self.local)+len(entered)-len(exited)-len(local)
        self.local=local;self.previous=rows;self.last_time=time_s
        return dict(time_s=time_s,global_present=len(rows),global_inserted=len(self.departed),global_exited=len(self.arrived),
                    global_conservation_residual=len(self.departed)-len(self.arrived)-len(rows),
                    edge_counts=dict(Counter(r["edge_id"] for r in rows.values())),
                    local_present=len(local),local_entered=len(entered),local_exited=len(exited),
                    local_entered_causes=dict(causes_in),local_exited_causes=dict(causes_out),
                    local_set_balance_residual=residual,local_density_veh_km_lane=len(local)/self.space["lane_km"],
                    local_cumulative_entered=self.local_in,local_cumulative_exited=self.local_out,
                    local_vehicle_s_internal_right_endpoint=self.local_vehicle_s,local_lane_km=self.space["lane_km"],
                    scheduled_due=due,external_pending=due-len(self.departed))


def queue_snapshot(rows,time_s,support,config,*,pending,physical_entry_space,downstream_context):
    """Lane/path-separated spatial graph on independently verified support.

    Cross-edge links are possible only when the support explicitly maps them to
    the SAME checked path, including internal junction lengths. Unknown rear
    precision cannot be used for an inlet threshold decision.
    """
    errors=[];paths=defaultdict(list);members={};unknown=[]
    if not support["coordinate_verified"]:errors.append("coordinate_support_unverified")
    for r in rows:
        lane=support["lanes"].get(r["lane_id"])
        if lane is None:
            unknown.append(r["lane_id"]);continue
        if r["incarnation_id"] in members:errors.append("duplicate_incarnation")
        x=lane["offset_m"]+r["position_m"]
        row=dict(r,path=lane["path"],coordinate_m=x,rear_m=x-r["length_m"])
        paths[lane["path"]].append(row);members[r["incarnation_id"]]=r["lane_id"]
    components=[];grid=[];uncertainty=support["engineering_position_uncertainty_m"]
    for path,values in paths.items():
        ordered=sorted(values,key=lambda r:r["coordinate_m"]);group=[];previous=None;gaps=[]
        def finish():
            if len(group)<config["minimum_queue_vehicles"]:return
            rear=min(r["rear_m"] for r in group);front=max(r["coordinate_m"] for r in group)
            interval=[rear-uncertainty,rear+uncertainty] if isinstance(uncertainty,(int,float)) else [None,None]
            inlet=(interval[1]<config["inlet_zone_m"] if interval[1] is not None else None)
            if interval[0] is not None and interval[0]<=config["inlet_zone_m"]<=interval[1]:inlet=None
            components.append(dict(path=path,members=[r["incarnation_id"] for r in group],
                upstream_boundary_m=rear,upstream_interval_m=interval,downstream_m=front,
                inlet_adjacent=inlet,downstream_anchored=front>=support["path_lengths"][path]-config["anchor_zone_m"],
                vehicles=len(group),max_net_gap_m=max(gaps) if gaps else None,
                member_lanes={r["incarnation_id"]:r["lane_id"] for r in group}))
        for row in ordered:
            slow=row["speed_mps"]<config["speed_low_mps"]
            gap=row["rear_m"]-previous["coordinate_m"] if previous else None
            same_edge=previous and previous["edge_id"]==row["edge_id"]
            connect=bool(group) and slow and previous["speed_mps"]<config["speed_low_mps"] and 0<=gap<=config["max_net_gap_m"] and (same_edge or support["cross_edge_verified"])
            if not connect:finish();group=[];gaps=[]
            if slow:
                if connect:gaps.append(gap)
                group.append(row)
            previous=row
        finish()
        cells=defaultdict(list)
        for r in ordered:cells[int(r["coordinate_m"]//config["grid_m"])].append(r)
        for i,rr in cells.items():
            low=sum(r["speed_mps"]<config["speed_low_mps"] for r in rr)
            grid.append(dict(path=path,cell=i,vehicles=len(rr),slow=low,low_share=low/len(rr),
                             candidate_active=low/len(rr)>=config["cell_low_fraction"]))
    queued=sorted({c["path"] for c in components})
    return dict(time_s=time_s,observation_valid=not errors,errors=errors,components=components,
                grid=grid,queued_paths=queued,all_paths_queued=set(queued)==set(support["path_lengths"]),
                member_lanes=members,pending=pending,physical_entry_space_observed=physical_entry_space,
                downstream_context=downstream_context,unknown_lanes=sorted(set(unknown)),
                support_complete=not support.get("unknown_paths"),
                scope="main_0 + verified junction + main_1, per path; downstream main_2 outside queue domain",
                low_vehicles=sum(r["speed_mps"]<config["speed_low_mps"] for rr in paths.values() for r in rr),
                stopped_vehicles=sum(r["speed_mps"]<config["stopped_speed_mps"] for rr in paths.values() for r in rr))


class QueueTracker:
    def __init__(self,config):
        self.config=config;self.previous=None;self.tracks=[];self.breaks=0;self.lane_resets=0;self.extension=False

    def update(self,o):
        dt=o["time_s"]-self.previous["time_s"] if self.previous else None
        if self.previous and (abs(dt-self.config["snapshot_step_s"])>1e-8 or not self.previous["observation_valid"]):
            self.tracks=[];self.breaks+=1
        old_lanes=self.previous["member_lanes"] if self.previous else {}
        changed={v for v,lane in o["member_lanes"].items() if v in old_lanes and lane!=old_lanes[v]}
        self.lane_resets+=len(changed)
        tracks=[];current_extension=False
        for c in o["components"]:
            matches=[t for t in self.tracks if t["component"]["path"]==c["path"] and
                     ((set(t["component"]["members"])&set(c["members"]))-changed)]
            prior=max(matches,key=lambda t:len(set(t["component"]["members"])&set(c["members"]))) if matches else None
            # A component containing ANY changed member is conservatively reset.
            if set(c["members"])&changed:prior=None
            duration=prior["duration_s"]+dt if prior else 0.
            inlet_duration=prior["inlet_duration_s"]+dt if prior and c["inlet_adjacent"] is True and prior["component"]["inlet_adjacent"] is True else 0.
            if prior:
                old=prior["component"]["upstream_interval_m"];new=c["upstream_interval_m"]
                current_extension|=old[0] is not None and new[1] is not None and new[1]<old[0]
            tracks.append(dict(component=c,duration_s=duration,inlet_duration_s=inlet_duration))
        self.extension|=current_extension;self.tracks=tracks;self.previous=o
        valid=o["observation_valid"] and o["support_complete"]
        inlet=any(c["inlet_adjacent"] is True for c in o["components"])
        persistent=any(t["inlet_duration_s"]>=self.config["duration_s"] and t["component"]["downstream_anchored"] for t in tracks)
        supported=valid and persistent and o["pending"]>0 and o["physical_entry_space_observed"] is True and o["downstream_context"] is True
        insufficient=not valid or (o["components"] and o["downstream_context"] is not True) or any(c["inlet_adjacent"] is None for c in o["components"])
        state="Evidence Insufficient" if insufficient else "Entry Spillback Supported" if supported else "Inlet-Adjacent Queue Observed" if inlet else "No On-Road Queue" if not o["components"] else "Upstream Queue Extension Observed" if current_extension else "On-Road Queue Observed"
        return dict(time_s=o["time_s"],state=state,onroad_queue_observed=bool(o["components"]) if valid else None,
                    inlet_adjacent_queue_observed=inlet if valid else None,entry_spillback_supported=supported if valid else None,
                    upstream_extension_observed=self.extension,current_upstream_extension=current_extension,
                    continuous_inlet_duration_s=max([t["inlet_duration_s"] for t in tracks] or [0.]),
                    longest_component_duration_s=max([t["duration_s"] for t in tracks] or [0.]),
                    temporal_breaks=self.breaks,lane_change_member_resets=self.lane_resets,
                    all_paths_queued=o["all_paths_queued"],qualification_status="engineering_candidate_for_B1_2",
                    scientific_traffic_validity="Not Established",scientific_claim_eligible=False)
