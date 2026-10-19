"""Independent C/D engineering contract; historical B1.2 modules stay frozen.

All graph frames are processed at .05s; output snapshots remain 1s. Path IDs
are usable only on the independently checked B1.2 coordinate support. No new
scientific thresholds or inference of hidden velocity from displacement.
"""
from __future__ import annotations
from .stage_0_5_b12_observation import QUEUE_CONFIG

VERSION='cd-integration-observation-v1'


def movement(before,after):
    if before['edge_id']!=after['edge_id']:return 'edge_transition'
    return 'lane_change' if before['lane_id']!=after['lane_id'] else 'same_lane'


def entry_evidence(rows,pending,definitions,types):
    """Sufficient geometric obstruction, NOT a full SUMO insertion oracle.

    DepartPos=base places the new front at length+POSITION_EPS. Comparing the
    nearest physical rear with length+minGap is conservative: some additional
    .1m / speed-safety failures remain Unknown. No speed safety is inferred.
    """
    result={}
    for path in sorted({definitions[v]['assigned_lane'] for v in pending}):
        ids=sorted(v for v in pending if definitions[v]['assigned_lane']==path)
        rears=[r['position_m']-r['length_m'] for r in rows if r['lane_id']=='main_0_'+path]
        rear=min(rears) if rears else None
        requirements={v:float(types[definitions[v]['type']]['length'])+float(types[definitions[v]['type']]['minGap']) for v in ids}
        # Report support only when EVERY assigned pending vehicle is obstructed
        # by the conservative physical test, not just the longest vehicle.
        result[path]=dict(pending_ids=ids,nearest_rear_m=rear,required_front_space_by_vehicle_m=requirements,
                          blocked=rear is not None and all(rear<x for x in requirements.values()),
                          full_insertion_safety_verified=False)
    return result


class QueueContinuity:
    def __init__(self,step=.05):
        self.step=step;self.previous=None;self.tracks=[];self.member_paths={}
        self.breaks=0;self.lane_resets=0;self.extension=False;self.frames=0

    def update(self,o):
        self.frames+=1;now=o['time_s'];valid=o['observation_valid'] and o['support_complete']
        dt=now-self.previous['time_s'] if self.previous else None
        gap=self.previous is not None and (abs(dt-self.step)>1e-8 or not self.previous['observation_valid'] or not self.previous['support_complete'])
        if gap or not valid:
            self.tracks=[];self.member_paths={};self.breaks+=1
        paths={v:c['path'] for c in o['components'] for v in c['members']}
        changed={v for v,p in paths.items() if v in self.member_paths and self.member_paths[v]!=p}
        self.lane_resets+=len(changed);tracks=[];extension=False
        if valid:
            for c in o['components']:
                candidates=[t for t in self.tracks if t['component']['path']==c['path'] and
                            len(set(t['component']['members'])&set(c['members']))>=QUEUE_CONFIG['minimum_queue_vehicles']]
                prior=max(candidates,key=lambda t:len(set(t['component']['members'])&set(c['members']))) if candidates else None
                if changed&set(c['members']):prior=None
                entry=o.get('entry_by_path',{}).get(c['path'],{})
                obstructed=bool(entry.get('pending_ids')) and entry.get('blocked') is True
                anchored=c['downstream_anchored'] and o['downstream_context'] is True
                both=c['inlet_adjacent'] is True and obstructed and anchored
                t=dict(component=c,duration_s=prior['duration_s']+dt if prior else 0.,
                       inlet_duration_s=prior['inlet_duration_s']+dt if prior and prior['component']['inlet_adjacent'] is True and c['inlet_adjacent'] is True else 0.,
                       coupled_duration_s=prior['coupled_duration_s']+dt if prior and prior['coupled'] and both else 0.,coupled=both)
                if prior:
                    a=prior['component']['upstream_interval_m'];b=c['upstream_interval_m']
                    extension|=a[0] is not None and b[1] is not None and b[1]<a[0]
                tracks.append(t)
        self.tracks=tracks;self.member_paths=paths if valid else {};self.previous=o
        self.extension|=extension
        supported=sorted({t['component']['path'] for t in tracks if t['coupled'] and t['coupled_duration_s']+1e-8>=QUEUE_CONFIG['duration_s']})
        inlet=any(c['inlet_adjacent'] is True for c in o['components'])
        insufficient=not valid or any(c['inlet_adjacent'] is None for c in o['components']) or (bool(o['components']) and o['downstream_context'] is not True)
        state='Evidence Insufficient' if insufficient else 'Entry Spillback Supported' if supported else 'Inlet-Adjacent Queue Observed' if inlet else 'No On-Road Queue' if not o['components'] else 'Upstream Queue Extension Observed' if extension else 'On-Road Queue Observed'
        return dict(time_s=now,state=state,onroad_queue_observed=bool(o['components']) if valid else None,
                    inlet_adjacent_queue_observed=inlet if valid else None,entry_spillback_supported=bool(supported) if valid else None,
                    supported_entry_paths=supported,upstream_extension_observed=self.extension,current_upstream_extension=extension,
                    continuous_inlet_duration_s=max((t['inlet_duration_s'] for t in tracks),default=0.),
                    continuous_coupled_entry_duration_s=max((t['coupled_duration_s'] for t in tracks),default=0.),
                    longest_component_duration_s=max((t['duration_s'] for t in tracks),default=0.),
                    temporal_breaks=self.breaks,lane_change_member_resets=self.lane_resets,processed_frames=self.frames,
                    all_paths_queued=o['all_paths_queued'],qualification_status='engineering_candidate',
                    scientific_traffic_validity='Not Established',scientific_claim_eligible=False)


def journey_audit(definitions,first_lanes,events,exits,require_all=True):
    by_exit={x['vehicle_id']:x for x in exits};vehicles={}
    for vid,d in definitions.items():
        mandatory=d['assigned_lane']=='2'
        merged=any(e['vehicle_id']==vid and e['edge'] in ['main_0','main_1'] and
                   e['from_lane']==e['edge']+'_2' and e['to_lane'] in [e['edge']+'_0',e['edge']+'_1'] for e in events)
        departed=vid in first_lanes;arrived=vid in by_exit
        vehicles[vid]=dict(mandatory=mandatory,actual_departure_lane=first_lanes.get(vid),
            entered_assigned_lane=departed and first_lanes[vid]=='main_0_'+d['assigned_lane'],actual_required_merge=merged if mandatory else None,
            arrived=arrived,downstream_exit=arrived and by_exit[vid]['last_edge']=='main_2')
    eligible=[v for v in vehicles.values() if v['arrived'] or require_all]
    verified=bool(eligible) and all(v['entered_assigned_lane'] and v['downstream_exit'] and (not v['mandatory'] or v['actual_required_merge']) for v in eligible)
    return dict(verified=verified,all_planned_exit_required=require_all,vehicles=vehicles,mandatory_planned=sum(x['mandatory'] for x in vehicles.values()),
                mandatory_arrived=sum(x['mandatory'] and x['arrived'] for x in vehicles.values()),
                mandatory_actual_merges=sum(x['mandatory'] and x['actual_required_merge'] for x in vehicles.values()))


def validate_summary(value):
    if not isinstance(value,dict):return 'missing_worker_summary'
    for k in ['global_blockers','scenario_blockers','engineering_blockers','evidence_insufficient']:
        if not isinstance(value.get(k),list):return 'unclassified_worker_severity'
    if set(value['engineering_blockers'])!=set(value['global_blockers']+value['scenario_blockers']):return 'inconsistent_worker_severity'
    if value.get('status') not in ['completed_valid','completed_with_diagnostic_warning','completed_with_engineering_blocker']:return 'unknown_worker_status'
    if bool(value['engineering_blockers'])!=(value['status']=='completed_with_engineering_blocker'):return 'worker_status_severity_mismatch'
    return value['global_blockers'] or None
