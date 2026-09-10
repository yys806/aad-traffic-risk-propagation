"""Human-audit package for candidate pNEUMA road and leader assignments."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from riskprop.calibration import sha256_file
from riskprop.legacy.pneuma_mapmatch import load_osm_segments


def _blind_id(seed: int, vehicle_id: object, time_s: object) -> str:
    value = f"{seed}|{vehicle_id}|{float(time_s):.6f}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()[:16]


def write_pneuma_manual_qa_pack(
    *,
    mapmatch_dir: str | Path,
    output_dir: str | Path,
    osm_path: str | Path | None = None,
    total: int = 300,
    seed: int = 20260907,
    pilot_per_stratum: int = 12,
) -> Path:
    """Create a balanced round-1 review sheet without promoting candidates to truth."""

    if total < 4 or total % 4:
        raise ValueError("total must be a positive multiple of four")
    if pilot_per_stratum < 0 or pilot_per_stratum > total // 4:
        raise ValueError("pilot_per_stratum must be between zero and the per-stratum sample size")
    mapmatch_dir = Path(mapmatch_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    states = pd.read_parquet(mapmatch_dir / "map_matched_states.parquet")
    leaders = pd.read_parquet(mapmatch_dir / "candidate_leaders.parquet")
    leader_fields = leaders[
        ["vehicle_id", "time_s", "leader_id", "front_to_front_m", "leader_status"]
    ].copy()
    candidates = states.rename(columns={"id": "vehicle_id"}).merge(
        leader_fields, on=["vehicle_id", "time_s"], how="left", validate="one_to_one"
    )
    candidates["sampling_stratum"] = candidates["map_match_status"].astype(str)
    candidates.loc[
        candidates["map_match_status"].eq("candidate") & candidates["leader_id"].notna(),
        "sampling_stratum",
    ] = "candidate_with_leader"
    strata = (
        "candidate_with_leader",
        "direction_mismatch",
        "heading_unobservable",
        "outside_map_tolerance",
    )
    per_stratum = total // len(strata)
    sampled = []
    for offset, stratum in enumerate(strata):
        subset = candidates.loc[candidates["sampling_stratum"].eq(stratum)]
        if len(subset) < per_stratum:
            raise ValueError(f"pNEUMA QA stratum {stratum} has {len(subset)} rows; need {per_stratum}")
        sampled.append(subset.sample(per_stratum, random_state=seed + offset))
    sample = pd.concat(sampled, ignore_index=True)
    sample["blind_id"] = [
        _blind_id(seed, vehicle_id, time_s)
        for vehicle_id, time_s in zip(sample["vehicle_id"], sample["time_s"], strict=True)
    ]
    sample = sample.sort_values("blind_id").reset_index(drop=True)
    sample["pilot_batch"] = False
    for stratum in strata:
        pilot_index = sample.index[sample["sampling_stratum"].eq(stratum)][:pilot_per_stratum]
        sample.loc[pilot_index, "pilot_batch"] = True
    sample = sample.sort_values(["pilot_batch", "blind_id"], ascending=[False, True]).reset_index(drop=True)
    sample["review_order"] = sample.index + 1

    review_columns = [
        "review_order",
        "pilot_batch",
        "blind_id",
        "vehicle_id",
        "time_s",
        "latitude",
        "longitude",
        "speed_mps",
        "road_id",
        "travel_direction",
        "road_position_m",
        "map_match_distance_m",
        "leader_id",
        "front_to_front_m",
    ]
    review = sample.loc[:, review_columns].copy()
    review["reviewed_road_match"] = ""
    review["reviewed_travel_direction"] = ""
    review["reviewed_leader_match"] = ""
    review["reviewer_uncertain"] = ""
    review["reviewer_notes"] = ""
    key = sample.rename(
        columns={
            "map_match_status": "system_map_match_status",
            "leader_status": "system_leader_status",
        }
    )
    key_columns = [
        "review_order",
        "pilot_batch",
        "blind_id",
        "vehicle_id",
        "time_s",
        "sampling_stratum",
        "system_map_match_status",
        "system_leader_status",
    ]
    review.to_csv(output_dir / "map_leader_review_round1.csv", index=False, encoding="utf-8-sig")
    key.loc[:, key_columns].to_csv(
        output_dir / "sealed_sampling_key.csv", index=False, encoding="utf-8-sig"
    )
    if osm_path is not None:
        _write_review_map(
            output_dir / "review_map.html",
            sample=sample,
            states=states,
            osm_path=Path(osm_path),
        )
    instructions = f"""# pNEUMA 道路与前车关系人工审计（第 1 轮）

本表只核验地图匹配和候选前车关系，不核验“消息效应”，也不产生 TTC 结论。

请先完成页面中标记为“平衡试标”的 {pilot_per_stratum * len(strata)} 条，不必一开始就标完全部 {total} 条。页面同时显示被审计车辆和候选前车前后约 1 秒轨迹、行驶箭头、候选道路方向及周围车辆。

三个问题依次判断：道路是否匹配正确、车辆行驶方向是否与道路方向一致、蓝色候选车辆是否确实是红色车辆同一路径上紧邻的前车。填写 `yes`、`no` 或 `uncertain`；该问题没有候选对象时填 `not_applicable`。证据不足时必须填 `reviewer_uncertain=yes`，不得猜测。

页面会在本机浏览器中自动保存进度。完成试标后点击“导出标签 CSV”，保留导出的 `pneuma_map_leader_round1_completed.csv`。`sealed_sampling_key.csv` 用于最终核对抽样层，在完成本轮前不要打开。
"""
    (output_dir / "审计说明.md").write_text(instructions, encoding="utf-8")
    audit = {
        "schema_version": "e15a.pneuma-manual-qa.v2",
        "experiment_id": "E15-A",
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "seed": seed,
        "sample_count": int(len(review)),
        "pilot_count": int(review["pilot_batch"].sum()),
        "strata": {str(key): int(value) for key, value in sample["sampling_stratum"].value_counts().items()},
        "context": {"track_window_s": 1.0, "nearby_radius_m": 50.0},
        "ttc_generated": False,
        "leader_relations_validated": False,
        "gate_status": "pending_human_round1",
        "scientific_claim_eligible": False,
    }
    (output_dir / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _seal(output_dir, "e15a.pneuma-manual-qa-manifest.v2")
    return output_dir


def _optional_float(value: object) -> float | None:
    return None if pd.isna(value) else float(value)


def _optional_int(value: object) -> int | None:
    return None if pd.isna(value) else int(value)


def _optional_text(value: object) -> str | None:
    return None if pd.isna(value) else str(value)


def _track_points(
    frame: pd.DataFrame, *, center_time_s: float, window_s: float = 1.0, max_points: int = 51
) -> list[dict[str, float]]:
    track = frame.loc[
        frame["time_s"].between(center_time_s - window_s, center_time_s + window_s),
        ["time_s", "map_x_m", "map_y_m"],
    ].dropna()
    track = track.sort_values("time_s")
    if len(track) > max_points:
        positions = [round(i * (len(track) - 1) / (max_points - 1)) for i in range(max_points)]
        track = track.iloc[positions]
    return [
        {"time_s": float(row.time_s), "x_m": float(row.map_x_m), "y_m": float(row.map_y_m)}
        for row in track.itertuples(index=False)
    ]


def _nearest_display_segment(
    segments: pd.DataFrame,
    *,
    x_m: float,
    y_m: float,
    ego_track: list[dict[str, float]],
    accepted_road_id: str | None,
    accepted_segment_index: int | None,
) -> dict[str, object] | None:
    choices = segments
    if accepted_road_id is not None:
        accepted = segments.loc[segments["road_id"].astype(str).eq(accepted_road_id)]
        if accepted_segment_index is not None:
            exact = accepted.loc[accepted["segment_index"].eq(accepted_segment_index)]
            if not exact.empty:
                accepted = exact
        if not accepted.empty:
            choices = accepted
    best: tuple[float, object] | None = None
    for segment in choices.itertuples(index=False):
        sx = float(segment.x2_m - segment.x1_m)
        sy = float(segment.y2_m - segment.y1_m)
        denominator = sx * sx + sy * sy
        if denominator <= 0:
            continue
        projection = max(
            0.0,
            min(1.0, ((x_m - segment.x1_m) * sx + (y_m - segment.y1_m) * sy) / denominator),
        )
        projected_x = float(segment.x1_m) + projection * sx
        projected_y = float(segment.y1_m) + projection * sy
        distance = math.hypot(x_m - projected_x, y_m - projected_y)
        if best is None or distance < best[0]:
            best = (distance, segment)
    if best is None:
        return None
    distance, segment = best
    direction: int | None = None
    if len(ego_track) >= 2:
        motion_x = ego_track[-1]["x_m"] - ego_track[0]["x_m"]
        motion_y = ego_track[-1]["y_m"] - ego_track[0]["y_m"]
        segment_x = float(segment.x2_m - segment.x1_m)
        segment_y = float(segment.y2_m - segment.y1_m)
        if math.hypot(motion_x, motion_y) > 1e-6:
            direction = 1 if motion_x * segment_x + motion_y * segment_y >= 0 else -1
    return {
        "road_id": str(segment.road_id),
        "segment_index": int(segment.segment_index),
        "distance_m": float(distance),
        "direction": direction,
    }


def _write_review_map(
    output_path: Path, *, sample: pd.DataFrame, states: pd.DataFrame, osm_path: Path
) -> None:
    """Write a self-contained local SVG reviewer; no web tiles or external scripts."""

    segments = load_osm_segments(osm_path)
    state_columns = ["id", "time_s", "map_x_m", "map_y_m", "speed_mps"]
    state_view = states.loc[:, state_columns].drop_duplicates(["id", "time_s"], keep=False)
    sample_ids = set(sample["vehicle_id"].dropna().astype(str))
    sample_ids.update(sample["leader_id"].dropna().astype(str))
    track_groups = {
        str(vehicle_id): frame
        for vehicle_id, frame in state_view.loc[state_view["id"].astype(str).isin(sample_ids)].groupby("id")
    }
    time_groups = {float(time_s): frame for time_s, frame in state_view.groupby("time_s")}

    cases: list[dict[str, object]] = []
    for row in sample.itertuples(index=False):
        vehicle_id = str(row.vehicle_id)
        time_s = float(row.time_s)
        leader_id = _optional_text(row.leader_id)
        ego_track = _track_points(track_groups.get(vehicle_id, state_view.iloc[0:0]), center_time_s=time_s)
        accepted_road_id = _optional_text(row.road_id)
        display_segment = _nearest_display_segment(
            segments,
            x_m=float(row.map_x_m),
            y_m=float(row.map_y_m),
            ego_track=ego_track,
            accepted_road_id=accepted_road_id,
            accepted_segment_index=_optional_int(getattr(row, "segment_index", None)),
        )
        leader_track = _track_points(
            track_groups.get(leader_id, state_view.iloc[0:0]), center_time_s=time_s
        ) if leader_id is not None else []
        current = time_groups.get(time_s, state_view.iloc[0:0]).copy()
        if not current.empty:
            dx = current["map_x_m"] - float(row.map_x_m)
            dy = current["map_y_m"] - float(row.map_y_m)
            current = current.loc[(dx * dx + dy * dy <= 50.0**2)]
            current = current.loc[~current["id"].astype(str).isin({vehicle_id, leader_id})].head(80)
        nearby = [
            {
                "vehicle_id": str(item.id),
                "x_m": float(item.map_x_m),
                "y_m": float(item.map_y_m),
                "speed_mps": _optional_float(item.speed_mps),
            }
            for item in current.itertuples(index=False)
        ]
        cases.append(
            {
                "review_order": int(row.review_order),
                "pilot_batch": bool(row.pilot_batch),
                "blind_id": str(row.blind_id),
                "vehicle_id": vehicle_id,
                "time_s": time_s,
                "speed_mps": _optional_float(row.speed_mps),
                "map_x_m": float(row.map_x_m),
                "map_y_m": float(row.map_y_m),
                "road_id": accepted_road_id,
                "travel_direction": _optional_int(row.travel_direction),
                "map_match_distance_m": _optional_float(row.map_match_distance_m),
                "display_road_id": None if display_segment is None else display_segment["road_id"],
                "display_road_distance_m": None if display_segment is None else display_segment["distance_m"],
                "display_direction": None if display_segment is None else display_segment["direction"],
                "leader_id": leader_id,
                "front_to_front_m": _optional_float(row.front_to_front_m),
                "has_candidate_road": display_segment is not None,
                "has_candidate_leader": leader_id is not None,
                "ego_track": ego_track,
                "leader_track": leader_track,
                "nearby_vehicles": nearby,
            }
        )
    road_rows = [
        {
            "road_id": str(row.road_id),
            "x1_m": float(row.x1_m),
            "y1_m": float(row.y1_m),
            "x2_m": float(row.x2_m),
            "y2_m": float(row.y2_m),
            "highway": str(row.highway),
            "oneway": int(row.oneway),
        }
        for row in segments.itertuples(index=False)
    ]
    pack_id = hashlib.sha256(
        "|".join(case["blind_id"] for case in cases).encode("utf-8")
    ).hexdigest()[:12]
    data = json.dumps({"cases": cases, "roads": road_rows}, ensure_ascii=False, allow_nan=False)
    data = data.replace("</", "<\\/")
    html = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>pNEUMA 离线审计图</title>
<style>
body{font-family:system-ui,"Microsoft YaHei",sans-serif;margin:18px;color:#18212b;line-height:1.45}h1{margin-bottom:4px}header{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:12px 0}button,select,input,textarea{font:inherit}button{padding:6px 10px}#case{max-width:300px}#map{width:100%;height:560px;border:1px solid #aab3bd;background:#fafafa}.road{stroke:#bbc2ca;stroke-width:2}.candidate{stroke:#111;stroke-width:5}.ego-track{fill:none;stroke:#d33;stroke-width:3}.leader-track{fill:none;stroke:#1677ff;stroke-width:3}.ego{fill:#d33;stroke:white;stroke-width:2}.leader{fill:#1677ff;stroke:white;stroke-width:2}.nearby{fill:#818a94;opacity:.8}.scale{stroke:#111;stroke-width:3}.panel{display:grid;grid-template-columns:repeat(3,minmax(210px,1fr));gap:12px;margin-top:12px}.field{padding:12px;border:1px solid #d8dde3;border-radius:7px}.hint{color:#56616d;font-size:.92rem}.pilot{color:#8b3d00;font-weight:700}.progress{font-weight:650}textarea{width:100%;min-height:70px;box-sizing:border-box}@media(max-width:800px){.panel{grid-template-columns:1fr}}
</style></head>
<body><h1>pNEUMA 道路、方向与前车审计</h1>
<p>这是测量工具，不是消息效应实验。红色为被审计车辆，蓝色为候选前车；彩色线段显示前后轨迹和行驶箭头，灰点为同一时刻 50 m 内的周围车辆。黑线优先显示系统已匹配道路；系统未接受道路时显示距离最近的道路，供你判断拒绝是否合理。页面不计算 TTC。</p>
<header><button id="prev">上一条</button><select id="case"></select><button id="next">下一条</button><button id="unfinished">下一条未完成</button><label><input id="pilotOnly" type="checkbox" checked> 只看平衡试标批次</label><button id="export">导出标签 CSV</button></header>
<p><span id="progress" class="progress"></span> <span id="summary"></span></p>
<svg id="map" viewBox="0 0 800 560"><defs><marker id="redArrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#d33"/></marker><marker id="blueArrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#1677ff"/></marker><marker id="blackArrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="#111"/></marker></defs></svg>
<div class="panel">
 <div class="field"><b>1. 道路是否正确？</b><p class="hint">黑线是否就是红车所在道路。</p><select id="road"><option></option><option>yes</option><option>no</option><option>uncertain</option><option>not_applicable</option></select></div>
 <div class="field"><b>2. 行驶方向是否正确？</b><p class="hint">红色轨迹箭头是否与系统给出的候选道路方向一致。</p><select id="direction"><option></option><option>yes</option><option>no</option><option>uncertain</option><option>not_applicable</option></select></div>
 <div class="field"><b>3. 候选前车是否正确？</b><p class="hint">蓝车是否在同一路径上、位于红车前方，且两车之间没有更近车辆。</p><select id="leader"><option></option><option>yes</option><option>no</option><option>uncertain</option><option>not_applicable</option></select></div>
</div>
<p>整体证据是否不足？ <select id="uncertain"><option></option><option>yes</option><option>no</option></select></p><p><textarea id="notes" placeholder="可选：写下看不清、匹配错误或特殊情况"></textarea></p>
<script>const DATA=__DATA__;const STORAGE_KEY='pneumaQaLabels_v2___PACK_ID__';const labels=JSON.parse(localStorage.getItem(STORAGE_KEY)||'{}');let index=0;const $=id=>document.getElementById(id);const NS='http://www.w3.org/2000/svg';
function val(v){return v===null||v===undefined?'':v}function complete(c){const l=labels[c.blind_id]||{};return Boolean(l.road&&l.direction&&l.leader&&l.uncertain)}
function visibleIndices(){const only=$('pilotOnly').checked;return DATA.cases.map((c,i)=>[c,i]).filter(([c])=>!only||c.pilot_batch).map(([,i])=>i)}
function rebuildCases(){const visible=new Set(visibleIndices());$('case').innerHTML='';DATA.cases.forEach((c,i)=>{if(!visible.has(i))return;const o=document.createElement('option');o.value=i;o.textContent=`${c.review_order}/${DATA.cases.length} ${c.pilot_batch?'[平衡试标] ':''}${c.blind_id}`;$('case').appendChild(o)});if(!visible.has(index))index=visibleIndices()[0]??0}
function save(){const c=DATA.cases[index];labels[c.blind_id]={road:$('road').value,direction:$('direction').value,leader:$('leader').value,uncertain:$('uncertain').value,notes:$('notes').value};localStorage.setItem(STORAGE_KEY,JSON.stringify(labels));updateProgress()}
function add(tag,attrs,parent){const e=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);parent.appendChild(e);return e}
function polyline(svg,points,cls,marker){if(points.length<2)return;add('polyline',{points:points.map(p=>`${p.x},${p.y}`).join(' '),class:cls,'marker-end':`url(#${marker})`},svg)}
function updateProgress(){const pilot=DATA.cases.filter(c=>c.pilot_batch),pd=pilot.filter(complete).length,all=DATA.cases.filter(complete).length;$('progress').textContent=`试标进度 ${pd}/${pilot.length}；全部进度 ${all}/${DATA.cases.length}`}
function render(){const c=DATA.cases[index],svg=$('map');svg.querySelectorAll(':scope > :not(defs)').forEach(e=>e.remove());$('case').value=index;const tag=c.pilot_batch?'平衡试标':'正式复核';$('summary').innerHTML=`<span class="${c.pilot_batch?'pilot':''}">${tag}</span>；编号 ${c.blind_id}；t=${c.time_s}s；速度=${val(c.speed_mps)} m/s；显示道路=${val(c.display_road_id)}；道路距离=${val(c.display_road_distance_m)} m；候选前车=${val(c.leader_id)}；前向距离=${val(c.front_to_front_m)} m`;
 const cx=c.map_x_m,cy=c.map_y_m,R=Math.max(80,Math.min(300,(c.display_road_distance_m||0)*1.25+20)),scale=250/R,tx=x=>400+(x-cx)*scale,ty=y=>280-(y-cy)*scale;
 for(const r of DATA.roads){if(Math.max(r.x1_m,r.x2_m)<cx-R||Math.min(r.x1_m,r.x2_m)>cx+R||Math.max(r.y1_m,r.y2_m)<cy-R||Math.min(r.y1_m,r.y2_m)>cy+R)continue;const candidate=String(r.road_id)===String(c.display_road_id),reverse=candidate&&Number(c.display_direction)===-1,attrs={x1:tx(reverse?r.x2_m:r.x1_m),y1:ty(reverse?r.y2_m:r.y1_m),x2:tx(reverse?r.x1_m:r.x2_m),y2:ty(reverse?r.y1_m:r.y2_m),class:candidate?'candidate':'road'};if(candidate&&c.display_direction!==null)attrs['marker-end']='url(#blackArrow)';add('line',attrs,svg)}
 for(const n of c.nearby_vehicles)add('circle',{cx:tx(n.x_m),cy:ty(n.y_m),r:4,class:'nearby'},svg);
 polyline(svg,c.ego_track.map(p=>({x:tx(p.x_m),y:ty(p.y_m)})),'ego-track','redArrow');polyline(svg,c.leader_track.map(p=>({x:tx(p.x_m),y:ty(p.y_m)})),'leader-track','blueArrow');add('circle',{cx:400,cy:280,r:8,class:'ego'},svg);
 const lp=c.leader_track.find(p=>Math.abs(p.time_s-c.time_s)<1e-6);if(lp)add('circle',{cx:tx(lp.x_m),cy:ty(lp.y_m),r:8,class:'leader'},svg);add('line',{x1:60,y1:520,x2:60+20*scale,y2:520,class:'scale'},svg);const st=add('text',{x:60,y:510},svg);st.textContent='20 m';
 const l=labels[c.blind_id]||{};$('road').value=l.road||'';$('direction').value=l.direction||'';$('leader').value=l.leader||'';$('uncertain').value=l.uncertain||'';$('notes').value=l.notes||'';
 $('direction').disabled=!c.has_candidate_road||c.display_direction===null;$('leader').disabled=!c.has_candidate_leader;if(!c.has_candidate_road)$('road').value=$('road').value||'not_applicable';if(!c.has_candidate_road||c.display_direction===null)$('direction').value='not_applicable';if(!c.has_candidate_leader)$('leader').value='not_applicable';updateProgress()}
function move(delta){save();const visible=visibleIndices(),at=visible.indexOf(index);index=visible[(at+delta+visible.length)%visible.length];render()}
for(const id of ['road','direction','leader','uncertain','notes'])$(id).addEventListener('change',save);$('prev').onclick=()=>move(-1);$('next').onclick=()=>move(1);$('case').onchange=e=>{save();index=Number(e.target.value);render()};$('pilotOnly').onchange=()=>{save();rebuildCases();render()};$('unfinished').onclick=()=>{save();const visible=visibleIndices(),start=visible.indexOf(index);for(let k=1;k<=visible.length;k++){const candidate=visible[(start+k)%visible.length];if(!complete(DATA.cases[candidate])){index=candidate;render();break}}};
$('export').onclick=()=>{save();const head=['blind_id','reviewed_road_match','reviewed_travel_direction','reviewed_leader_match','reviewer_uncertain','reviewer_notes'];const esc=v=>'"'+String(v??'').replaceAll('"','""')+'"';const rows=DATA.cases.map(c=>{const l=labels[c.blind_id]||{};return[c.blind_id,l.road,l.direction,l.leader,l.uncertain,l.notes].map(esc).join(',')});const blob=new Blob(['\ufeff'+head.join(',')+'\\n'+rows.join('\\n')],{type:'text/csv;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='pneuma_map_leader_round1_completed.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};rebuildCases();render();</script></body></html>"""
    html = html.replace("__DATA__", data).replace("__PACK_ID__", pack_id)
    output_path.write_text(html, encoding="utf-8")


def _seal(output_dir: Path, schema_version: str) -> None:
    files = sorted(path for path in output_dir.iterdir() if path.is_file())
    manifest = {
        "schema_version": schema_version,
        "files": [
            {"path": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in files
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    files.append(manifest_path)
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(f"{sha256_file(path)}  {path.name}" for path in files) + "\n",
        encoding="utf-8",
        newline="\n",
    )
