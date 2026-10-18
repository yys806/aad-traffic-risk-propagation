"""AAD-0.5.4-A+ targeted diagnostics; no calibration or scientific Gate decisions.

Raw access is restricted to two allowlisted members of a previously fingerprinted
public archive. The shared guard is used before extraction and before parsing.
No sealed state, formal event definition, or historical result is modified.
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import platform
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from .ngsim_risk_calibration import _NGSIM_TXT_COLUMNS
from .stage_0_5_calibration_readiness import (
    CALIBRATION_GROUPS, STATE_SOURCES, load_calibration_states,
    verify_against_real_reference_manifest, _sha256_file, _write_json, _utc_now,
)
from .stage_0_5_sumo import (
    CALIBRATION_VALIDATION_POLICY, CalibrationValidationGuard, Stage05AccessDenied,
)

RESULT_ID = "RES-STAGE-0.5-CALIBRATION-GAPS-V1"
ARCHIVE_PATH = "dataset/NGSIM/US-101-LosAngeles-CA.zip"
# Historical Stage 0.2 task1.5 audit input_sha256, independently verified on access.
ARCHIVE_SHA256 = "830442bb08f1f7a20a686b5879b4b82bfb7c47e526d48908db666fccc7e811dc"
INNER = "us-101-vehicle-trajectory-data.zip"
RAW_MEMBERS = {
    "us101__0750_0805": "vehicle-trajectory-data/0750am-0805am/trajectories-0750am-0805am.txt",
    "us101__0805_0820": "vehicle-trajectory-data/0805am-0820am/trajectories-0805am-0820am.txt",
}
MAINLINE = ["1", "2", "3", "4", "5"]
DT = .1
LOCAL_M = (150., 350.)


def bind_raw_policy(group: str, digest: str) -> dict:
    """Extend roles only for an exact approved raw member (never arbitrary sources)."""
    if group not in RAW_MEMBERS:
        raise Stage05AccessDenied(f"raw source outside approved calibration scope: {group}")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise Stage05AccessDenied("raw binding requires SHA-256")
    policy = copy.deepcopy(CALIBRATION_VALIDATION_POLICY)
    source = group + "::raw"
    policy["calibration"] = list(policy["calibration"]) + [source]
    policy["source_bindings"][source] = digest
    return policy


def controlled_join(states: pd.DataFrame, raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Source/row bijection plus time, frame, ID and coordinate validation.

    Ambiguous or conflicting records retain their state row but have no inferred
    class/length. No Vehicle_ID-only merge is permitted.
    """
    keys = ["source_member", "original_row_number"]
    dup_raw = raw.duplicated(keys, keep=False)
    dup_state = states.duplicated(keys, keep=False)
    unique = raw.loc[~dup_raw, keys + ["Vehicle_ID", "Frame_ID", "Global_Time",
        "Local_Y", "v_Class", "v_Length"]]
    joined = states.merge(unique, on=keys, how="left", validate="many_to_one", sort=False)
    found = joined.Vehicle_ID.notna()
    consistent = (found & ~dup_state.to_numpy()
        & pd.to_numeric(joined.original_vehicle_id).eq(joined.Vehicle_ID)
        & joined.frame_id.eq(joined.Frame_ID)
        & joined.global_time_ms.eq(joined.Global_Time)
        & np.isclose(joined.y_m, joined.Local_Y * .3048, rtol=0, atol=1e-7))
    joined.loc[~consistent, ["v_Class", "v_Length"]] = np.nan
    joined["raw_match_status"] = np.where(consistent, "Verified", "Unresolved")
    return joined, dict(state_rows=len(states), raw_rows=len(raw), matched_rows=int(consistent.sum()),
        unmatched_rows=int((~found).sum()), conflict_rows=int((found & ~consistent).sum()),
        unresolved_rows=int((~consistent).sum()), match_rate=float(consistent.mean()),
        duplicate_raw_keys=int(dup_raw.sum()), duplicate_state_keys=int(dup_state.sum()),
        raw_unused_rows=int((~raw.original_row_number.isin(states.original_row_number)).sum()),
        validation_keys=keys + ["original_vehicle_id", "global_time_ms", "frame_id", "y_m"])


def distribution(values: pd.Series) -> dict:
    x = pd.to_numeric(values, errors="coerce")
    x = x[np.isfinite(x)]
    return dict(n=len(x), mean=float(x.mean()) if len(x) else None,
        sd=float(x.std()) if len(x)>1 else None,
        quantiles={str(q): float(x.quantile(q)) for q in [0,.01,.05,.1,.5,.9,.95,.99,1]} if len(x) else {})


def fleet_summary(joined: pd.DataFrame) -> dict:
    grouped = joined.groupby("trajectory_id", sort=True)
    tracks = grouped.agg(class_code=("v_Class","first"), length_ft=("v_Length","first"),
        class_n=("v_Class","nunique"), length_n=("v_Length","nunique"), rows=("time_s","size"),
        start=("time_s","min"), end=("time_s","max"), identity_uncertain=("identity_uncertain","any"))
    unresolved = grouped.raw_match_status.apply(lambda x: x.ne("Verified").any())
    tracks["eligible"] = (tracks.class_n.eq(1) & tracks.length_n.eq(1) &
        tracks.class_code.isin([1,2,3]) & tracks.length_ft.gt(0) &
        ~tracks.identity_uncertain & ~unresolved & (tracks.end-tracks.start).ge(.2))
    tracks["length_m"] = tracks.length_ft * .3048
    result = dict(unit="source-scoped trajectory/vehicle; one vote per trajectory", vehicles=len(tracks),
        reliable_trajectories=int(tracks.eligible.sum()), class_conflict_trajectories=int(tracks.class_n.gt(1).sum()),
        length_conflict_trajectories=int(tracks.length_n.gt(1).sum()),
        identity_uncertain_trajectories=int(tracks.identity_uncertain.sum()),
        unresolved_trajectories=int(unresolved.sum()),
        missing_or_invalid_class_rows=int((~joined.v_Class.isin([1,2,3])).sum()),
        missing_or_nonpositive_length_rows=int((joined.v_Length.isna() | joined.v_Length.le(0)).sum()),
        all_vehicle_length_m=distribution(tracks.loc[tracks.eligible,"length_m"]), classes=[])
    for code,label in [(1,"motorcycle"),(2,"auto"),(3,"truck")]:
        s=tracks[tracks.class_code.eq(code)]
        good=s[s.eligible]
        result["classes"].append(dict(code=code,official_label=label, vehicles=len(s),
            share=len(s)/len(tracks), reliable_trajectories=len(good),
            length_m=distribution(good.length_m), duration_s=distribution(good.end-good.start),
            candidate_vClass={1:"motorcycle",2:"passenger",3:"truck"}[code],
            mapping_status="Proposal", physical_length_truth="Unverified; annotation only"))
    return result


def clock_audit(raw: pd.DataFrame, states: pd.DataFrame, group: str) -> dict:
    lo,hi=int(raw.Global_Time.min()),int(raw.Global_Time.max())
    anchors=raw.Global_Time-100*raw.Frame_ID
    offset=states.global_time_ms/1000-states.time_s
    nominal = {CALIBRATION_GROUPS[0]:("2005-06-15 07:50:00","2005-06-15 08:05:00"),
        CALIBRATION_GROUPS[1]:("2005-06-15 08:05:00","2005-06-15 08:20:00")}[group]
    nlo,nhi=[int(pd.Timestamp(t,tz="America/Los_Angeles").timestamp()*1000) for t in nominal]
    per = raw.groupby("Vehicle_ID").agg(start=("Global_Time","min"),end=("Global_Time","max"))
    ordered=raw.sort_values(["Vehicle_ID","Global_Time","Frame_ID"])
    d=ordered.groupby("Vehicle_ID").Global_Time.diff()
    return dict(raw_global_time_ms=[lo,hi], raw_span_s=(hi-lo)/1000,
        standardized_span_s=float(states.time_s.max()-states.time_s.min()),
        raw_pacific_time=[pd.to_datetime(x,unit="ms",utc=True).tz_convert("America/Los_Angeles").isoformat() for x in [lo,hi]],
        nominal_global_time_ms=[nlo,nhi], nominal_span_s=900,
        rows_before_nominal=int(raw.Global_Time.lt(nlo).sum()), rows_after_nominal=int(raw.Global_Time.ge(nhi).sum()),
        trajectory_starts_before_nominal=int(per.start.lt(nlo).sum()),
        trajectory_ends_after_nominal=int(per.end.ge(nhi).sum()),
        diagnostic_clock_anchors_ms=[int(x) for x in sorted(anchors.unique())],
        frame_range=[int(raw.Frame_ID.min()),int(raw.Frame_ID.max())],
        observed_timestamps=int(raw.Global_Time.nunique()),
        missing_global_grid_frames=int((hi-lo)//100+1-raw.Global_Time.nunique()),
        duplicate_vehicle_times=int(raw.duplicated(["Vehicle_ID","Global_Time"],keep=False).sum()),
        non_100ms_vehicle_increments=int((d.notna() & d.ne(100)).sum()),
        time_normalization_offset_s_range=[float(offset.min()),float(offset.max())],
        source_members=sorted(states.source_member.unique().tolist()),
        measurement_error_demonstrated=False,
        boundary_selection_warning="official metadata records complete trajectories; boundary occupancy is not proven a census")


def crossing_counts(states: pd.DataFrame, planes=(150.,300.,450.), duration_s=None) -> list[dict]:
    ordered=states.sort_values(["trajectory_id","time_s"])
    prev=ordered.shift()
    adjacent=(ordered.trajectory_id.eq(prev.trajectory_id) &
        (ordered.time_s-prev.time_s-.1).abs().lt(1e-7) & ordered.frame_id.sub(prev.frame_id).eq(1))
    if "identity_uncertain" in ordered:
        adjacent &= ~ordered.identity_uncertain & ~prev.identity_uncertain.fillna(True)
    duration=float(states.time_s.max()-states.time_s.min()) if duration_s is None else duration_s
    result=[]
    for plane in planes:
        forward=adjacent & prev.y_m.lt(plane) & ordered.y_m.ge(plane)
        backward=adjacent & prev.y_m.ge(plane) & ordered.y_m.lt(plane)
        lanes=ordered.loc[forward].lane_id.astype(str).value_counts().sort_index().to_dict()
        main=sum(int(lanes.get(k,0)) for k in MAINLINE)
        result.append(dict(plane_m=plane,forward_crossings=int(forward.sum()),
            backward_crossings=int(backward.sum()),lane_counts={str(k):int(v) for k,v in lanes.items()},
            mainline_crossings=main, mainline_veh_h=main*3600/duration,
            mainline_veh_h_lane=main*3600/duration/5,
            all_lane_veh_h=float(forward.sum())*3600/duration, duration_s=duration,
            lane_assignment="downstream endpoint; lane-changing edges separately flagged",
            crossing_lane_change_edges=int((forward & ordered.lane_id.ne(prev.lane_id)).sum())))
    return result


def reliable_local_edges(states: pd.DataFrame) -> pd.DataFrame:
    """Following exposure only, full-source continuity before spatial restriction.

    Both follower endpoints inside the local mainline support and one 60 s slice.
    Events are intentionally not reassigned or re-extracted for this new domain.
    """
    o=states.sort_values(["trajectory_id","global_time_ms","frame_id"]).reset_index(drop=True)
    p=o.shift()
    mask=pd.Series(True,index=o.index)
    for key in ["trajectory_id","leader_trajectory_id","source_member","source_period","diagnostic_clock_anchor_ms"]:
        mask &= o[key].notna() & p[key].notna() & o[key].eq(p[key]).fillna(False)
    mask &= o.global_time_ms.diff().eq(100) & o.frame_id.diff().eq(1) & (o.time_s.diff()-.1).abs().lt(1e-8)
    reliable=o.leader_matched & ~o.identity_uncertain & ~o.leader_identity_uncertain
    mask &= reliable & reliable.shift(fill_value=False) & ~o.identity_break & ~o.observation_gap
    local=o.lane_id.isin(MAINLINE) & o.y_m.ge(LOCAL_M[0]) & o.y_m.lt(LOCAL_M[1])
    mask &= local & local.shift(fill_value=False)
    # Edges touching a bin boundary are allocated by their left endpoint; the
    # interval [t-.1,t) lies entirely in that bin on this 100 ms grid.
    bins=np.floor(np.round(o.time_s-.1,6)/60).astype(int)
    evaluable=o.measurement_status.isin(["valid","not_applicable"])
    return pd.DataFrame(dict(slice_index=bins,following_s=mask.astype(float)*.1,
        evaluable_s=(mask & evaluable & evaluable.shift(fill_value=False)).astype(float)*.1))


def density_slices(states: pd.DataFrame, group="fixture", edges: pd.DataFrame | None=None) -> list[dict]:
    """Mainline local density in 200m*5 lane space, equal 100ms observed frames.

    Use [t_min,t_max); no extrapolated last frame. Missing global frames are
    absent coverage; an observed frame with no local vehicles contributes zero.
    """
    s=states.copy()
    end=float(s.time_s.max())
    start=float(s.time_s.min())
    time_grid=np.sort(s.loc[s.time_s.lt(end),"time_s"].unique())
    local=s[s.lane_id.isin(MAINLINE) & s.y_m.ge(150) & s.y_m.lt(350) & s.time_s.lt(end)]
    counts=local.groupby("time_s").trajectory_id.nunique().reindex(time_grid,fill_value=0)
    result=[]
    for a in np.arange(start,end,60):
        b=min(a+60,end)
        ticks=counts[(counts.index>=a)&(counts.index<b)]
        c=local[local.time_s.ge(a)&local.time_s.lt(b)]
        covered=len(ticks)*.1
        row=dict(source_group=group,slice_start_s=float(a),slice_end_s=float(b),
            coverage_s=covered,span_s=float(b-a),coverage_fraction=covered/(b-a),
            eligible=bool(covered>=45-1e-7 and covered/(b-a)>=.95),
            density_veh_km_lane=float(ticks.sum()*.1/(covered*.2*5)) if covered else None,
            local_vehicle_seconds=len(c)*.1,mean_speed_mps=float(c.speed_mps.mean()) if len(c) else None,
            low_speed_share_below_5_mps=float(c.speed_mps.lt(5).mean()) if len(c) else None,
            p2_events=None,p2_rate=None,p2_status="Unresolved for restricted local domain; full event membership not reassigned")
        if edges is not None:
            e=edges[edges.slice_index.eq(int(a//60))]
            row.update(local_reliable_following_s=float(e.following_s.sum()),local_evaluable_following_s=float(e.evaluable_s.sum()))
        result.append(row)
    return result


def boundary_qualified_slices(rows: list[dict], states: pd.DataFrame) -> list[dict]:
    """Conservative candidate boundary sensitivity, defined before SUMO runs.

    Complete-trajectory selection does not guarantee a boundary census. Guard
    each end by the longest observed trajectory duration, without claiming that
    the unobserved duration tail is bounded by this empirical value.
    """
    extents=states.groupby("trajectory_id").time_s.agg(["min","max"])
    buffer=float((extents["max"]-extents["min"]).max())
    lo=float(states.time_s.min())+buffer
    hi=float(states.time_s.max())-buffer
    output=[]
    for row in rows:
        r=dict(row)
        r["coverage_eligible"]=r["eligible"]
        r["boundary_guard_s"]=buffer
        r["boundary_eligible"]=bool(r["slice_start_s"]>=lo and r["slice_end_s"]<=hi)
        r["eligible"]=bool(r["eligible"] and r["boundary_eligible"])
        r["exclusion_reason"]=(None if r["eligible"] else "partial_or_missing_coverage" if not r["coverage_eligible"] else "complete_trajectory_boundary_guard")
        output.append(r)
    return output


def pooled_strata(rows: list[dict]) -> dict:
    eligible=[r for r in rows if r["eligible"]]
    if not eligible:
        raise ValueError("no eligible calibration slices")
    limits=np.quantile([r["density_veh_km_lane"] for r in eligible],[1/3,2/3])
    output=[]
    for row in rows:
        r=dict(row)
        r["density_stratum"]=("Excluded" if not r["eligible"] else
            "Low-density" if r["density_veh_km_lane"]<=limits[0] else
            "Medium-density" if r["density_veh_km_lane"]<=limits[1] else "High-density")
        output.append(r)
    summaries=[]
    for group in sorted({r["source_group"] for r in output}):
        for label in ["Low-density","Medium-density","High-density"]:
            chunk=[r for r in output if r["source_group"]==group and r["density_stratum"]==label]
            if not chunk:
                continue
            def weighted(key,weight):
                if key not in chunk[0]: return None
                usable=[r for r in chunk if r.get(key) is not None and
                        np.isfinite(r[key]) and r.get(weight,0)>0]
                if not usable: return None
                return float(np.average([r[key] for r in usable],weights=[r[weight] for r in usable]))
            summaries.append(dict(source_group=group,density_stratum=label,slices=len(chunk),
                coverage_s=sum(r.get("coverage_s",0) for r in chunk),
                density_veh_km_lane=weighted("density_veh_km_lane","coverage_s") if "coverage_s" in chunk[0] else None,
                mean_speed_mps=weighted("mean_speed_mps","local_vehicle_seconds"),
                low_speed_share_below_5_mps=weighted("low_speed_share_below_5_mps","local_vehicle_seconds"),
                following_exposure_s=sum(r.get("local_reliable_following_s",0) for r in chunk),
                evaluable_following_exposure_s=sum(r.get("local_evaluable_following_s",0) for r in chunk),
                p2_events=None,p2_rate=None))
    return dict(status="Proposal",thresholds_veh_km_lane=limits.tolist(),
        slice_s=60,minimum_coverage_s=45,minimum_coverage_fraction=.95,
        pooling_weight="equal eligible time slice; windows contribute their actual eligible slices, no state-row weights",
        space="150<=Local_Y_m<350, lane 1..5; length 0.2km*5 lanes",
        extremes="all finite qualified slices retained; no winsorization or SUMO-dependent selection",
        slices=output,summary=summaries)


def local_metrics(states: pd.DataFrame, seed=20261018) -> dict:
    """Trajectory cluster ratio bootstrap, same full local data, no iid rows.

    CIs quantify sampling under this empirical trajectory population; shared
    traffic-wave dependence and annotation error are not fully covered.
    """
    local=states[states.lane_id.isin(MAINLINE)&states.y_m.ge(150)&states.y_m.lt(350)]
    matched=local.leader_matched & ~local.identity_uncertain & ~local.leader_identity_uncertain
    result={}
    rng=np.random.default_rng(seed)
    for key,mask in [("speed_mps",pd.Series(True,index=local.index)),
        ("acceleration_mps2",pd.Series(True,index=local.index)),
        ("net_gap_m",matched & local.net_gap_m.gt(0)),("closing_speed_mps",matched)]:
        x=local.loc[mask,["trajectory_id",key]].copy()
        x=x[np.isfinite(x[key])]
        aggregate=x.groupby("trajectory_id")[key].agg(["sum","count"])
        draws=rng.integers(0,len(aggregate),size=(2000,len(aggregate)))
        vals=aggregate["sum"].to_numpy()[draws].sum(axis=1)/aggregate["count"].to_numpy()[draws].sum(axis=1)
        result[key]=dict(distribution=distribution(x[key]),mean_cluster_ci95=np.quantile(vals,[.025,.975]).tolist(),
            clusters=len(aggregate),resamples=2000,seed=seed,model_tolerance="Tolerance Not Yet Justified")
    return result


def seal_package(out: Path) -> None:
    files=sorted(p for p in out.iterdir() if p.is_file() and p.name not in ["manifest.json","SHA256SUMS"])
    _write_json(out/"manifest.json",dict(result_id=RESULT_ID,files=[dict(path=p.name,bytes=p.stat().st_size,sha256=_sha256_file(p)) for p in files]))
    files.append(out/"manifest.json")
    (out/"SHA256SUMS").write_text("".join(f"{_sha256_file(p)}  {p.name}\n" for p in files),encoding="utf-8",newline="\n")


def run_diagnostics(root: Path, out: Path) -> None:
    if out.exists():
        raise ValueError(f"refusing to overwrite supplement: {out}")
    out.mkdir(parents=True)
    guard=CalibrationValidationGuard()
    binding=verify_against_real_reference_manifest(root)
    _write_json(out/"config.json",dict(result_id=RESULT_ID,status="Proposal",scope=list(CALIBRATION_GROUPS),
        density_space_m=LOCAL_M,density_lanes=MAINLINE,slice_s=60,minimum_coverage_s=45,
        minimum_coverage_fraction=.95,bootstrap_resamples=2000,bootstrap_seed=20261018,
        scientific_tolerances_frozen=False,benchmark_mode="engineering_benchmark_only"))
    # Register the whole archive binding before opening its ZIP directory. No
    # validation member is opened, parsed or independently hashed.
    archive_policy=bind_raw_policy(CALIBRATION_GROUPS[0],ARCHIVE_SHA256)
    archive_policy["calibration"].append(CALIBRATION_GROUPS[1]+"::raw")
    archive_policy["source_bindings"][CALIBRATION_GROUPS[1]+"::raw"]=ARCHIVE_SHA256
    ag=CalibrationValidationGuard(archive_policy)
    ag.require_source_read(root/ARCHIVE_PATH,role="calibration",source=CALIBRATION_GROUPS[0]+"::raw")
    manifest=dict(archive=dict(path=ARCHIVE_PATH,sha256=ARCHIVE_SHA256,
        source="FHWA NGSIM US-101 public archive, existing local copy",inner_zip_member=INNER),
        allowed_members=RAW_MEMBERS,forbidden_member_content_read=False,members=[],
        metadata=dict(path="dataset/NGSIM/1- US 101 Metadata Documentation.pdf",
            sha256=_sha256_file(root/"dataset/NGSIM/1- US 101 Metadata Documentation.pdf"),pages=[11,12],
            class_codes={1:"motorcycle",2:"auto",3:"truck"},length_unit="feet; 0.3048 m/ft",
            missing_value_rule="class/length sentinel not specified in official dictionary; unrecognized/nonfinite/nonpositive values flagged, never imputed"))
    _write_json(out/"source_manifest.json",manifest)
    frames,reads=load_calibration_states(root,guard)
    all_slices=[]
    unguarded_slices=[]
    summaries={}
    id_sets={}
    with zipfile.ZipFile(root/ARCHIVE_PATH) as outer:
        with zipfile.ZipFile(io.BytesIO(outer.read(INNER))) as inner:
            for group,member in RAW_MEMBERS.items():
                # Source membership checked before opening the exact raw member.
                ag.require(role="calibration",sources=[group+"::raw"],purpose=f"extract allowlisted member {member}")
                data=inner.read(member)
                digest=hashlib.sha256(data).hexdigest()
                manifest["members"].append(dict(source_group=group,member=member,sha256=digest,bytes=len(data),role="calibration"))
                _write_json(out/"source_manifest.json",manifest)  # before numeric parsing
                # Guard verifies frozen bytes through a local, isolated snapshot.
                (out/"raw").mkdir(exist_ok=True)
                snapshot=out/"raw"/(group+".raw.txt")
                snapshot.write_bytes(data)
                rg=CalibrationValidationGuard(bind_raw_policy(group,digest))
                rg.require_source_read(snapshot,role="calibration",source=group+"::raw",purpose="class/length/time audit")
                raw=pd.read_csv(io.BytesIO(data),sep=r"\s+",header=None,names=list(_NGSIM_TXT_COLUMNS))
                if raw.shape[1]!=18 or not isinstance(raw.index,pd.RangeIndex) or raw.isna().any().any():
                    raise ValueError("raw TXT does not satisfy 18 finite fields")
                raw["source_member"]=member
                raw["original_row_number"]=np.arange(1,len(raw)+1)
                states=frames[group]
                joined,join=controlled_join(states,raw)
                clock=clock_audit(raw,states,group)
                edges=reliable_local_edges(states)
                slices=density_slices(states,group,edges)
                unguarded_slices.extend(slices)
                guarded=boundary_qualified_slices(slices,states)
                all_slices.extend(guarded)
                interior_mask=pd.Series(False,index=states.index)
                for row in guarded:
                    if row["eligible"]:
                        interior_mask |= states.time_s.ge(row["slice_start_s"]) & states.time_s.lt(row["slice_end_s"])
                interior=states[interior_mask]
                interior_coverage=sum(r["coverage_s"] for r in guarded if r["eligible"])
                lane=[]
                for k,c in states.groupby("lane_id"):
                    lane.append(dict(lane=str(k),min_y_m=float(c.y_m.min()),max_y_m=float(c.y_m.max()),
                        vehicles=int(c.trajectory_id.nunique()),state_rows=len(c),mean_speed_mps=float(c.speed_mps.mean())))
                ordered=states.sort_values(["trajectory_id","time_s"])
                changes=ordered.groupby("trajectory_id").lane_id.nunique().gt(1)
                summaries[group]=dict(join=join,fleet=fleet_summary(joined),clock=clock,lanes=lane,
                    crossings=crossing_counts(states),local_metrics=local_metrics(states),
                    interior_crossings=crossing_counts(interior,duration_s=interior_coverage),
                    interior_local_metrics=local_metrics(interior),interior_coverage_s=interior_coverage,
                    lane_change_trajectories=int(changes.sum()),lane_change_share=float(changes.mean()))
                id_sets[group]=set(raw.Vehicle_ID)
                # Raw snapshots stay local for provenance; excluded from portable evidence.
                guard.decisions.extend(rg.decisions)
                print(group, json.dumps(dict(join=join,clock=clock,fleet=summaries[group]["fleet"]),ensure_ascii=True),flush=True)
                del raw,joined,data
    strata=pooled_strata(all_slices)
    strata["boundary_policy"]="Proposal: exclude slices within max observed trajectory duration of either source boundary; residual unobserved-cohort bias remains Unverified"
    _write_json(out/"diagnostics.json",dict(windows=summaries,
        cross_window_id_string_overlap=len(set.intersection(*id_sets.values())),
        cross_window_physical_identity="Unresolved; members/time scope kept distinct"))
    _write_json(out/"unified_strata.json",strata)
    _write_json(out/"boundary_sensitivity.json",pooled_strata(unguarded_slices))
    guard.decisions.extend(ag.decisions)
    _write_json(out/"access_audit.json",guard.audit())
    _write_json(out/"audit.json",dict(result_id=RESULT_ID,engineering_only=True,scientific_claim_eligible=False,
        source_binding_check=binding,state_reads=reads,validation_window_read=False,validation_window_rows_materialised=0,
        locked_holdout_accessed=False,parameters_approved=[],tolerances_frozen=False,formal_calibration_run=False,
        gate="pending_simulation_sample",protocol_lock_created=False,ready_to_start_stage_0_5_4b=False,
        all_raw_state_rows_verified=all(s["join"]["unresolved_rows"]==0 for s in summaries.values())))
    _write_json(out/"provenance.json",dict(result_id=RESULT_ID,created_at_utc=_utc_now(),python=platform.python_version(),
        pandas=pd.__version__,numpy=np.__version__,git_head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),
        code_sha256={str(p.relative_to(root)).replace("\\","/"):_sha256_file(p) for p in [Path(__file__),
            root/"code/scripts/run_stage_0_5_calibration_gaps.py"]},
        source_manifest_sha256=_sha256_file(out/"source_manifest.json"),status="diagnostics complete; benchmark pending"))
    # Exclude raw snapshots from package-level manifest and portable evidence.
    seal_package(out)
