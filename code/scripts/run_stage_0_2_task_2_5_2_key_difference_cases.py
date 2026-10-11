"""Task 2.5.2: center-event versus nearby-event difference cases."""
from __future__ import annotations
import argparse, hashlib, json
from datetime import UTC, datetime
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parents[2]
T15 = ROOT / "code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4"
T251 = ROOT / "code/outputs/formal/calibration/stage_0_2_task_2_5_1_20261011_r2"
RULES = ["P1_strict", "P2_middle", "P3_sensitive"]

def members(x):
    try:
        return set(map(int, json.loads(x)))
    except Exception:
        return set()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def select_cases(audit, edges, n=12):
    e = audit[audit.inclusion_status == "reliable"].copy()
    e["members_set"] = e.original_row_numbers.map(members)
    p12 = edges[(edges.rule_a == "P1_strict") & (edges.rule_b == "P2_middle")]
    p23 = edges[(edges.rule_a == "P2_middle") & (edges.rule_b == "P3_sensitive")]
    p2_matched = set(p12.event_id_b)
    p3_matched = set(p23.event_id_b)
    chosen = []
    def add(pool, label, count):
        pool = pool.sort_values(["source", "ttc_min_s", "event_start_s"])
        for src, group in pool.groupby("source", sort=True):
            if len([z for z in chosen if z["label"] == label]) >= count:
                break
            if not group.empty:
                chosen.append({"row": group.iloc[0], "label": label})
        for _, row in pool.iterrows():
            if len([z for z in chosen if z["label"] == label]) >= count:
                break
            chosen.append({"row": row, "label": label})
    add(e[(e.rule == "P2_middle") & ~e.event_id.isin(p2_matched)], "P2_without_P1", 3)
    add(e[(e.rule == "P3_sensitive") & ~e.event_id.isin(p3_matched)], "P3_without_P2", 3)
    # Largest observed confirmation spread among P1 events linked to both rules.
    p13 = edges[(edges.rule_a == "P1_strict") & (edges.rule_b == "P3_sensitive")]
    p2_by_p1 = p12.groupby("event_id_a").event_id_b.first().to_dict()
    p3_by_p1 = p13.groupby("event_id_a").event_id_b.first().to_dict()
    candidates = []
    for p1_id in sorted(set(p2_by_p1) & set(p3_by_p1)):
        a = e[(e.rule == "P1_strict") & (e.event_id == p1_id)]
        b = e[(e.rule == "P2_middle") & (e.event_id == p2_by_p1[p1_id])]
        c = e[(e.rule == "P3_sensitive") & (e.event_id == p3_by_p1[p1_id])]
        if len(a) and len(b) and len(c):
            spread = abs(float(a.iloc[0].event_confirm_s) - float(c.iloc[0].event_confirm_s))
            candidates.append((spread, a.iloc[0]))
    add(pd.DataFrame([r for _, r in sorted(candidates, key=lambda z: -z[0])[:30]]), "all_three_confirmation_spread", 6)
    out, seen = [], set()
    for z in chosen:
        r = z["row"]
        ms = sorted(r.members_set)
        center = ms[len(ms) // 2] if ms else int(r.original_row_number)
        key = (r.source, center)
        if key in seen:
            continue
        seen.add(key)
        out.append({"selection_class": z["label"], "center_rule": r.rule, "center_event_id": r.event_id,
                    "source": r.source, "trajectory_id": r.trajectory_id,
                    "leader_trajectory_id": r.leader_trajectory_id,
                    "center_original_row_number": center, "event_start_s": r.event_start_s,
                    "event_end_s": r.event_end_s, "center_event_confirm_s": r.event_confirm_s,
                    "ttc_min_s": r.ttc_min_s, "drac_max_mps2": r.drac_max_mps2,
                    "member_count": len(ms)})
        if len(out) >= n:
            break
    return pd.DataFrame(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True, type=Path)
    args = ap.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=False, exist_ok=False)
    audit = pd.read_csv(T251 / "event_confirmation_audit.csv")
    edges = pd.read_parquet(T251 / "event_overlap_edges.parquet")
    cases = select_cases(audit, edges)
    states = {p.stem.removeprefix("ngsim_"): pd.read_parquet(p) for p in sorted((T15 / "states").glob("*.parquet"))}
    reliable = {}
    for rule in RULES:
        d = audit[(audit.rule == rule) & (audit.inclusion_status == "reliable")].copy()
        d["members_set"] = d.original_row_numbers.map(members)
        reliable[rule] = d
    rows, pdf = [], PdfPages(out / "key_difference_casebook.pdf")
    for _, case in cases.iterrows():
        d = states[case.source]
        center = int(case.center_original_row_number)
        center_rows = d[d.original_row_number.astype(int) == center]
        if center_rows.empty:
            continue
        center_row = center_rows.iloc[0]
        t = float(center_row.time_s)
        pair = d[(d.trajectory_id.astype(str) == str(case.trajectory_id)) &
                 (d.leader_trajectory_id.astype(str) == str(case.leader_trajectory_id))]
        loc = pair[pair.time_s.between(t - 3, t + 3)].sort_values(["global_time_ms", "frame_id"])
        rec = case.to_dict()
        rec.update({"center_time_s": t, "center_match_count": len(center_rows),
                    "physical_truth_status": "Unverified", "center_event_membership_verified": True})
        for rule in RULES:
            same = reliable[rule]
            same = same[(same.source == case.source) & (same.trajectory_id == case.trajectory_id) &
                        (same.leader_trajectory_id == case.leader_trajectory_id)]
            center_events = same[same.members_set.map(lambda s: center in s)]
            nearby = same[(same.event_start_s <= t + 3) & (same.event_end_s >= t - 3)]
            rec[f"{rule}_center_triggered"] = bool(len(center_events))
            rec[f"{rule}_center_event_count"] = len(center_events)
            rec[f"{rule}_nearby_event_count"] = len(nearby)
            if len(center_events):
                z = center_events.iloc[0]
                for k, v in {"event_id": z.event_id, "confirm_s": z.event_confirm_s,
                             "onset_s": z.event_start_s, "exit_s": z.event_end_s,
                             "ttc_min_s": z.ttc_min_s, "members": len(z.members_set)}.items():
                    rec[f"{rule}_center_{k}"] = v
            else:
                for k, v in {"event_id": "", "confirm_s": np.nan, "onset_s": np.nan,
                             "exit_s": np.nan, "ttc_min_s": np.nan, "members": 0}.items():
                    rec[f"{rule}_center_{k}"] = v
        rec["nearby_event_count_3s"] = max(rec[f"{r}_nearby_event_count"] for r in RULES)
        rows.append(rec)
        fig, ax = plt.subplots(4, 1, figsize=(11, 9), sharex=True)
        x = loc.time_s
        ax[0].plot(x, pd.to_numeric(loc.ttc_s, errors="coerce"), ".-", label="TTC")
        for th, col in [(1.5, "#c0392b"), (2.0, "#2980b9"), (2.5, "#27ae60")]:
            ax[0].axhline(th, color=col, ls="--", label=f"TTC {th}s")
        ax[0].set_ylabel("TTC (s)"); ax[0].legend(ncol=4, fontsize=7)
        ax[0].set_title(f"{case.source} row {center} | {case.selection_class} | center {t:.1f}s")
        ax[1].plot(x, pd.to_numeric(loc.drac_mps2, errors="coerce"), ".-", label="DRAC")
        ax[1].plot(x, pd.to_numeric(loc.net_gap_m, errors="coerce"), ".-", label="net gap")
        ax[1].legend(fontsize=7); ax[1].set_ylabel("DRAC / gap")
        ax[2].plot(x, pd.to_numeric(loc.closing_speed_mps, errors="coerce"), ".-", label="closing speed")
        ax[2].plot(x, pd.to_numeric(loc.speed_mps, errors="coerce"), ".-", label="follower speed")
        ax[2].legend(fontsize=7); ax[2].set_ylabel("m/s")
        colors = {"P1_strict": "#c0392b", "P2_middle": "#2980b9", "P3_sensitive": "#27ae60"}
        for rule, col in colors.items():
            if rec[f"{rule}_center_triggered"]:
                ax[3].axvspan(rec[f"{rule}_center_onset_s"], rec[f"{rule}_center_exit_s"], alpha=.18, color=col, label=rule)
                ax[3].axvline(rec[f"{rule}_center_confirm_s"], color=col, ls="--")
        ax[3].plot(x, pd.to_numeric(loc.ttc_s, errors="coerce"), color="0.4", alpha=.5, label="TTC context")
        ax[3].set_ylabel("event spans"); ax[3].set_xlabel("time (s)"); ax[3].legend(fontsize=7, ncol=4)
        for a in ax: a.grid(alpha=.2)
        fig.tight_layout(); pdf.savefig(fig); plt.close(fig)
    pdf.close()
    case_df = pd.DataFrame(rows); case_df.to_csv(out / "key_difference_cases.csv", index=False)
    decision = pd.DataFrame([
        {"rule":"P1_strict","what_it_detects":"TTC<1.5 s and span>=0.3 s","advantage":"lower event burden; later but stricter confirmation","cost":"misses P2/P3-only processes","status":"Proposal / Not Frozen"},
        {"rule":"P2_middle","what_it_detects":"TTC<2.0 s and span>=0.2 s","advantage":"intermediate burden and confirmation delay","cost":"no independent truth-based optimality evidence","status":"Proposal / Not Frozen"},
        {"rule":"P3_sensitive","what_it_detects":"TTC<2.5 s and span>=0.1 s","advantage":"earliest confirmation and broadest capture","cost":"more near-threshold and measurement-sensitive processes","status":"Proposal / Not Frozen"}])
    decision.to_csv(out / "candidate_rule_decision_table.csv", index=False)
    (out / "report.md").write_text(f"""# Task 2.5.2 关键差异案例分析\n\n本轮确定性选择 {len(case_df)} 个案例。中心事件只由中心原始行号是否属于该事件成员集合判定；同一车辆对 ±3 s 内的其他事件单独记录为 nearby_event_count，不替代中心事件。\n\nP1/P2/P3 的差异案例、事件边界和绝对确认时间见 `key_difference_cases.csv`；新图册见 `key_difference_casebook.pdf`。P1 更严格但会遗漏 P2/P3-only 过程；P3 更早确认但覆盖更多近阈值过程；P2 的中间位置是工程折衷，不构成科学优先证据。\n\n**P2 是否足够明确地值得优先采用？** 当前不足。已有成员级差异、中心归属和实际确认时刻证据；仍缺少独立事故/近失真值、公平采样稳健性、独立几何真实性和正式的消息漏报/误报代价权衡。所有参数保持 Proposal / Pending / Not Frozen。\n""", encoding="utf-8")
    cfg = {"schema_version":"stage_0_2.task_2_5_2.config.v1","selection_n":12,"center_matching":"source+trajectory_pair+original_row_number member inclusion","nearby_window_s":3.0,"scientific_parameters_frozen":False,"locked_holdout_opened":False}
    (out / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    audit_out = {"schema_version":"stage_0_2.task_2_5_2.audit.v1","cases":len(case_df),"pdf_pages":len(case_df),"center_membership_verified":int(case_df.center_event_membership_verified.sum()),"scientific_claim_eligible":False,"locked_holdout_opened":False}
    (out / "audit.json").write_text(json.dumps(audit_out, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    prov = {"created_at":datetime.now(UTC).isoformat(),"script":"code/scripts/run_stage_0_2_task_2_5_2_key_difference_cases.py","inputs":["stage_0_2_task_2_5_1_20261011_r2","stage_0_2_task_1_5_20261010_r4"],"scientific_status":"proposal_only"}
    (out / "provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    files = [{"path":q.name,"bytes":q.stat().st_size,"sha256":sha(q)} for q in sorted(out.iterdir()) if q.name not in {"manifest.json","SHA256SUMS"} and q.is_file()]
    (out / "manifest.json").write_text(json.dumps({"schema_version":"stage_0_2.task_2_5_2.manifest.v1","files":files}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    lines = [f"{sha(q)}  {q.name}" for q in sorted(out.iterdir()) if q.name != "SHA256SUMS" and q.is_file()]
    (out / "SHA256SUMS").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(json.dumps(audit_out, ensure_ascii=False))

if __name__ == "__main__":
    main()
