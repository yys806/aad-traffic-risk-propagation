"""Independent B1.1 queue truth. No historical traffic states are consumed."""
from copy import deepcopy

QUEUE_CONFIG=dict(version="b11-queue-candidate-v1",status="Candidate; synthetic demonstration only",
    speed_low_mps=5.,stopped_speed_mps=.1,grid_m=50.,cell_low_fraction=.5,
    minimum_queue_vehicles=2,max_net_gap_m=10.,inlet_zone_m=50.,anchor_zone_m=50.,
    duration_s=2.,snapshot_step_s=1.,position_uncertainty_m=.01,
    empty_cell_bridging=False,time_gap_smoothing=False,cross_lane_merging=False,
    threshold_scientific_approval=False,
    basis=dict(speed="inherited B1 descriptive5m/s, not a scientific congestion threshold",
        grid="legacy50m retained for comparison, not selected on C",
        count="at least two vehicles to observe a spatial following relation",
        gap="10m=two synthetic5m vehicle lengths; no empirical queue-gap identification",
        duration="two1s intervals/three snapshots; test-scale candidate, not a traffic persistence claim",
        inlet="same physical first50m support as B1; inclusion now uses observed bodies and uncertainty",
        uncertainty="0.01m synthetic coordinate assumption; future mapping precision must be verified"))


def vehicle(vid,x,speed=1.,lane="e_0"):
    return dict(vehicle_id=vid,incarnation_id="synthetic|"+vid,position_m=float(x),speed_mps=float(speed),
        lane_id=lane,edge_id="e",length_m=5.)


def snapshot(t,positions,*,pending=0,coverage=(0.,200.),physical_entry=False,vehicles=None,supported_lanes=None):
    rows=vehicles if vehicles is not None else [vehicle(f"x{x}",x) for x in positions]
    lanes=supported_lanes or ["e_0"]
    return dict(time_s=float(t),road_length_m=200.,observed_range_m=list(coverage),coordinate_frame="single_edge:e",supported_lane_count=len(lanes),supported_lanes=lanes,
        positions_verified=True,downstream_service_context=True,arrival_manifest_valid=True,
        pending=pending,inserted_total=len(rows),exited_total=0,present=len(rows),scheduled_due=len(rows)+pending,
        physical_entry_space_observed=physical_entry,vehicles=rows)


def repeated(positions,**kwargs):return [snapshot(t,positions,**kwargs) for t in [0,1,2]]


def synthetic_queue_cases():
    long=list(range(10,191,15));sparse=list(range(45,196,15))
    cases=[
        dict(id="01_free_flow",frames=repeated([],vehicles=[vehicle("f",100,20)]),truth=dict(queue=False,inlet=False,spillback=False,components=0)),
        dict(id="02_external_only",frames=repeated([],vehicles=[vehicle("f",100,20)],pending=10),truth=dict(queue=False,inlet=False,spillback=False,components=0)),
        dict(id="03_downstream_local_queue",frames=repeated([175,185,195]),truth=dict(queue=True,inlet=False,spillback=False,components=1)),
        dict(id="04_upstream_extension",frames=[snapshot(t,positions) for t,positions in enumerate([[185,195],[170,185,195],[155,170,185,195]])],truth=dict(queue=True,inlet=False,spillback=False,extension=True,components=1)),
        dict(id="05_queue_reaches_inlet",frames=repeated(long,pending=10,physical_entry=True),truth=dict(queue=True,inlet=True,spillback=True,components=1)),
        dict(id="06_sparse_front",frames=repeated(sparse,pending=10,physical_entry=True),truth=dict(queue=True,inlet=True,spillback=True,front_m=40.,components=1)),
        dict(id="07_periodic_release",frames=[snapshot(t,long,pending=10,physical_entry=True,vehicles=[vehicle(f"x{x}",x,8 if t==2 else 1) for x in long]) for t in range(5)],truth=dict(queue=True,inlet=True,spillback=False,components=1,continuous_support=False)),
        dict(id="08_disconnected_groups",frames=repeated([20,30,180,190],pending=10,physical_entry=True),truth=dict(queue=True,inlet=True,spillback=False,components=2)),
        dict(id="09_two_lanes_isolated",frames=repeated([],vehicles=[vehicle("a",185,1,"e_0"),vehicle("b",195,1,"e_1")],supported_lanes=["e_0","e_1"]),truth=dict(queue=False,inlet=False,spillback=False,components=0)),
        dict(id="10_partial_observation",frames=repeated([115,130,145,160,175,190],coverage=(100.,200.),pending=10),truth=dict(queue=True,inlet=None,spillback=None,components=1,front_censored=True)),
        dict(id="11_same_cell_disconnected",frames=repeated([155,161,185,191]),truth=dict(queue=True,inlet=False,spillback=False,components=2)),
        dict(id="12_isolated_slow",frames=repeated([195]),truth=dict(queue=False,inlet=False,spillback=False,components=0)),
        dict(id="13_lane_change_no_temporal_bridge",frames=[snapshot(t,[],pending=10,physical_entry=True,
            vehicles=[vehicle(f"x{x}",x,1,"e_1" if t==1 else "e_0") for x in long],supported_lanes=["e_0","e_1"]) for t in range(3)],
            truth=dict(queue=True,inlet=True,spillback=False,components=1,continuous_support=False)),
    ]
    unknown=repeated([175,185,195])
    for f in unknown:f["downstream_service_context"]=False
    cases.append(dict(id="14_slow_cluster_unknown_cause",frames=unknown,
        truth=dict(queue=True,inlet=False,spillback=False,components=1,causal_queue=None)))
    for c in cases:c["truth_basis"]="designed vehicle adjacency/physical support and explicit input cause; no C result or fitted threshold"
    return deepcopy(cases)
