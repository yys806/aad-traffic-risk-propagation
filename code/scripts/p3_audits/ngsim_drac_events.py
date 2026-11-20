"""0.2.0 NGSIM 真实 DRAC≥3.4 事件率与成因分类。

【复用，不重写】
净距/闭合速度/DRAC/缺失原因全部由项目既有实现负责：
  `code/src/riskprop/real_trajectory.py`
  - `read_ngsim_nested_csv(outer_zip, inner_zip_member, csv_member)`
  - `add_ngsim_leader_ttc(df)` → headway_m（已扣**前车**车长）、closing_speed_mps、
    drac_mps2、lane_id、leader_id、speed_mps、acceleration_mps2、measurement_status
本脚本只做它没做的三件事：事件合并、成因分类、汇总。

【口径（GPT 第七十六轮裁决后的修订版）】
 事件合并：同一后车连续超阈，中间允许最多 **3 个连续有效但低于阈值的帧**（10 Hz 下 0.3 s）；
           缺帧、无前车、无效帧（missing/invalid）**直接断开**。
 成因四类（按事件起点帧判，优先级 切入 > 前车强刹 > 同前车未见强刹 > 未分类）：
   切入           ：新前车在事件前 3.0 s 内曾出现在**后车当时所在车道**，
                   且后车自身在这 3.0 s 内**未换道**
   前车强刹       ：同一前车，且在起点前 0.5 s 内**连续三帧** acceleration ≤ −3.0 m/s²
   同前车未见强刹 ：同一前车，未见上述强刹
   未分类         ：缺历史 / 换了前车但无法解释
 暴露分母：有效跟驰车·公里（measurement_status ∈ {valid, not_applicable} 且 leader_matched）；
           缺配与无效净距单列。

【验收（GPT 给的手算对照）】
 车头距 50 ft、前车长 30 ft、两车速度 50 / 25 ft/s
 → g = (50−30)×0.3048 = 6.096 m；c = (50−25)×0.3048 = 7.62 m/s；DRAC = 4.7625 m/s²

用法：
  python ngsim_drac_events.py --unit-check
  python ngsim_drac_events.py --sites US-101
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "code/src"))
from riskprop.real_trajectory import add_ngsim_leader_ttc, read_ngsim_nested_csv  # noqa: E402

DATA = ROOT / "dataset/NGSIM"
OUT = ROOT / "code/outputs/analysis/P3_ngsim_drac"

THR_MAIN = 3.4
THR_SENS = (3.0, 4.5)
MERGE_FRAMES = 3
CUT_WINDOW = 30
LEAD_BRAKE_THR = -3.0
DT = 0.1

SITES = {
    "I-80": ("I-80-Emeryville-CA.zip", "i-80-vehicle-trajectory-data.zip"),
    "US-101": ("US-101-LosAngeles-CA.zip", "us-101-vehicle-trajectory-data.zip"),
    "Lankershim": ("Lankershim-Boulevard-LosAngeles-CA.zip",
                   "lankershim-boulevard-vehicle-trajectory-data.zip"),
    "Peachtree": ("Peachtree-Street-Atlanta-GA.zip",
                  "peachtree-street-vehicle-trajectory-data.zip"),
}


def _inner_zip(outer: Path) -> tuple[bytes, str]:
    with zipfile.ZipFile(outer) as o:
        cands = [n for n in o.namelist()
                 if n.lower().endswith("vehicle-trajectory-data.zip")]
        if not cands:
            raise RuntimeError(f"{outer.name}: 外层无轨迹包，实际 {o.namelist()[:5]}")
        return o.read(cands[0]), cands[0]


def list_csv_members(site: str) -> list[str]:
    """每个时段只返回**一个**成员：优先 .txt（GPT：US-101 的 CSV 有截断记录，TXT 完整），
    没有 txt 才用 csv。否则同一时段会被算两遍。"""
    outer_name, _ = SITES[site]
    blob, _ = _inner_zip(DATA / outer_name)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names = z.namelist()
    by_dir: dict[str, dict[str, str]] = {}
    for n in names:
        low = n.lower()
        if not low.endswith((".csv", ".txt")):
            continue
        if "reconstructed" in low:
            continue
        parent = n.rsplit("/", 1)[0] if "/" in n else ""
        ext = "txt" if low.endswith(".txt") else "csv"
        by_dir.setdefault(parent, {})[ext] = n
    out = []
    for parent in sorted(by_dir):
        d = by_dir[parent]
        out.append(d.get("txt") or d.get("csv"))
    return out


def _read_member(site: str, member: str) -> pd.DataFrame:
    """读一个时段文件。

    US-101 两个坑（实测）：
    1. 列名是 `Preceeding`（多一个 e），与 I-80 的 `Preceding` 不同；
    2. 另有同内容的 `.txt` 版本，**无表头、空格分隔**，GPT 第七十六轮指出
       「US-101 优先用已核完整的 TXT，旧 CSV 有截断记录」。
    这里两者都读，txt 按标准 18 列赋名。
    """
    outer_name, inner_name = SITES[site]
    cols = ["Vehicle_ID", "Frame_ID", "Total_Frames", "Global_Time", "Local_X", "Local_Y",
            "Global_X", "Global_Y", "v_Length", "v_Width", "v_Class", "v_Vel", "v_Acc",
            "Lane_ID", "Preceeding", "Following", "Space_Hdwy", "Time_Hdwy"]
    if member.lower().endswith(".txt"):
        blob, _ = _inner_zip(DATA / outer_name)
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            with z.open(member) as f:
                df = pd.read_csv(f, sep=r"\s+", header=None, names=cols)
    else:
        df = read_ngsim_nested_csv(DATA / outer_name, inner_name, member)
    # 统一列名
    ren = {}
    if "Preceeding" in df.columns:
        ren["Preceeding"] = "Preceding"
    if "Space_Hdwy" in df.columns:
        ren["Space_Hdwy"] = "Space_Headway"
    if "Time_Hdwy" in df.columns:
        ren["Time_Hdwy"] = "Time_Headway"
    if ren:
        df = df.rename(columns=ren)
    return df


def load_site(site: str, verbose: bool = True) -> pd.DataFrame:
    parts = []
    for member in list_csv_members(site):
        if verbose:
            print(f"  [{site}] 读 {member}", flush=True)
        df = _read_member(site, member)
        df = add_ngsim_leader_ttc(df, run_id=f"{site}:{member}")
        parts.append(df)
    if not parts:
        raise RuntimeError(f"{site}: 没读到任何轨迹文件")
    return pd.concat(parts, ignore_index=True)


def unit_check() -> bool:
    g = (50.0 - 30.0) * 0.3048
    c = (50.0 - 25.0) * 0.3048
    drac = c * c / (2.0 * g)
    ok = abs(g - 6.096) < 1e-6 and abs(c - 7.62) < 1e-6 and abs(drac - 4.7625) < 1e-3
    print(f"手算对照：g={g:.4f}（应 6.0960）c={c:.4f}（应 7.6200）"
          f"DRAC={drac:.4f}（应 4.7625）→ {'通过' if ok else '不通过'}")
    return ok


def extract_events(df: pd.DataFrame, thr: float = THR_MAIN) -> list[dict]:
    df = df.sort_values(["run_id", "id", "Frame_ID"], kind="mergesort")
    events = []
    for (run, vid), grp in df.groupby(["run_id", "id"], sort=False):
        fr = grp["Frame_ID"].to_numpy()
        drac = grp["drac_mps2"].to_numpy()
        status = grp["measurement_status"].astype(str).to_numpy()
        lane = grp["lane_id"].astype(str).to_numpy()
        lead = grp["leader_id"].astype(str).to_numpy()
        lacc = grp["acceleration_mps2"].to_numpy()
        gap = grp["headway_m"].to_numpy()
        close = grp["closing_speed_mps"].to_numpy()
        speed = grp["speed_mps"].to_numpy()

        usable = (status == "valid") | (status == "not_applicable")
        cur, below_run = None, 0
        for i in range(len(fr)):
            hit = usable[i] and drac[i] == drac[i] and drac[i] >= thr
            if hit:
                if cur is None:
                    cur = {"on_idx": i, "peak": float(drac[i]), "last_idx": i}
                else:
                    cur["peak"] = max(cur["peak"], float(drac[i]))
                    cur["last_idx"] = i
                below_run = 0
                continue
            if cur is None:
                continue
            if usable[i] and (fr[i] - fr[cur["last_idx"]]) <= MERGE_FRAMES:
                below_run += 1
                if below_run <= MERGE_FRAMES:
                    continue
            events.append(_make_event(run, vid, cur, fr, lane, lead, lacc, gap, close, speed))
            cur, below_run = None, 0
        if cur is not None:
            events.append(_make_event(run, vid, cur, fr, lane, lead, lacc, gap, close, speed))
    return events


def _make_event(run, vid, cur, fr, lane, lead, lacc, gap, close, speed) -> dict:
    i = cur["on_idx"]
    cause, note = _classify(i, fr, lane, lead, lacc)
    return {"run": run, "veh": str(vid), "on_frame": int(fr[i]),
            "peak_drac": round(cur["peak"], 3),
            "gap_m": _f(gap[i]), "closing_ms": _f(close[i]), "v_ego_ms": _f(speed[i]),
            "lead_id": lead[i], "lead_acc_ms2": _f(lacc[i]),
            "cause": cause, "note": note}


def _f(x):
    return None if x != x else round(float(x), 3)


def _classify(i, fr, lane, lead, lacc) -> tuple[str, str]:
    j0 = max(0, i - CUT_WINDOW)
    if i == j0:
        return "同前车未见强刹", "no_history"
    old_lead, new_lead, ego_lane = lead[j0], lead[i], lane[i]
    if old_lead != new_lead and old_lead not in ("0", "nan", "<NA>", "None"):
        ego_lane_changed = len({lane[k] for k in range(j0, i)}) > 1
        new_lead_in_lane = any(
            lead[k] == new_lead and lane[k] == ego_lane for k in range(j0, i)
        ) if new_lead not in ("0", "nan", "<NA>", "None") else False
        if (not ego_lane_changed) and new_lead_in_lane:
            return "切入", f"new_lead={new_lead}"
        return "未分类", (f"lead_changed old={old_lead} new={new_lead} "
                          f"ego_lane_chg={ego_lane_changed}")
    k0 = max(0, i - 5)
    win = [lacc[k] for k in range(k0, i)]
    for a in range(len(win) - 2):
        trio = win[a:a + 3]
        if all(x == x and x <= LEAD_BRAKE_THR for x in trio):
            return "前车强刹", "consecutive3"
    return "同前车未见强刹", ""


def stratify(df: pd.DataFrame, events: list[dict]) -> dict:
    """按净距 × 后车速度交叉分层（GPT 第七十七轮 Q1 选 (d)）。

    每层报：暴露（车·公里与车·小时）、超阈帧数、按起点归层的事件数。
    慢速层额外给每千车·小时的率（距离分母小，只看每公里率会失真）。
    """
    ok = df["measurement_status"].isin(["valid", "not_applicable"]) & df["leader_matched"]
    d = df.loc[ok]
    gap = d["headway_m"].to_numpy()
    spd = d["speed_mps"].to_numpy()
    drac = d["drac_mps2"].to_numpy()
    hit = (drac == drac) & (drac >= THR_MAIN)

    gap_bins = [(0, 1), (1, 2), (2, 5), (5, 10), (10, 30), (30, 1e9)]
    spd_bins = [(0, 5), (5, 1e9)]
    out = []
    for gl, gh in gap_bins:
        for sl, sh in spd_bins:
            sel = (gap >= gl) & (gap < gh) & (spd >= sl) & (spd < sh)
            n = int(sel.sum())
            if n == 0:
                continue
            exp_km = float((spd[sel] * DT).sum() / 1000.0)
            exp_h = n * DT / 3600.0
            out.append({
                "gap_lo": gl, "gap_hi": (None if gh > 1e8 else gh),
                "speed_lo": sl, "speed_hi": (None if sh > 1e8 else sh),
                "n_frames": n, "exposure_veh_km": round(exp_km, 3),
                "exposure_veh_h": round(exp_h, 4),
                "n_over_thr_frames": int(hit[sel].sum()),
                "share_of_all_frames": round(n / len(d), 6),
            })

    # 事件按起点归层
    ev_frame = {(e["run"], str(e["veh"]), e["on_frame"]): e for e in events}
    key = list(zip(d["run_id"], d["id"].astype(str), d["Frame_ID"]))
    idx = {k: i for i, k in enumerate(key)}
    for row in out:
        cnt = 0
        for k, e in ev_frame.items():
            i = idx.get(k)
            if i is None:
                continue
            if not hit[i]:
                continue
            g_i, s_i = gap[i], spd[i]
            if (g_i >= row["gap_lo"]
                    and (row["gap_hi"] is None or g_i < row["gap_hi"])
                    and s_i >= row["speed_lo"]
                    and (row["speed_hi"] is None or s_i < row["speed_hi"])):
                cnt += 1
        row["n_events_by_onset"] = cnt
        row["rate_per_1000_veh_km"] = (
            round(cnt / row["exposure_veh_km"] * 1000.0, 3)
            if row["exposure_veh_km"] > 0 else None)
        row["rate_per_1000_veh_h"] = (
            round(cnt / row["exposure_veh_h"] * 1000.0, 2)
            if row["exposure_veh_h"] > 0 else None)
    return {"strata": out}


def run_with_filter(df: pd.DataFrame, min_gap: float | None,
                    min_speed: float | None, tag: str) -> dict:
    """按过滤器重算事件与暴露，并报告相对首次运行的事件流转。"""
    sub = df
    if min_gap is not None:
        sub = sub[~(sub["headway_m"] < min_gap)]
    if min_speed is not None:
        sub = sub[~(sub["speed_mps"] < min_speed)]
    ev = extract_events(sub)
    ok = sub["measurement_status"].isin(["valid", "not_applicable"]) & sub["leader_matched"]
    exp_km = float((sub.loc[ok, "speed_mps"] * DT).sum() / 1000.0)
    n = len(ev)
    return {"tag": tag, "min_gap": min_gap, "min_speed": min_speed,
            "n_events": n, "exposure_veh_km": round(exp_km, 2),
            "rate_per_1000_veh_km": (round(n / exp_km * 1000.0, 3) if exp_km else None),
            "cause_counts": dict(_count([e["cause"] for e in ev])),
            "_keys": {(e["run"], e["veh"], e["on_frame"]) for e in ev}}


def _count(items):
    d = defaultdict(int)
    for x in items:
        d[x] += 1
    return dict(d)


def summarize(site: str, df: pd.DataFrame, events: list[dict]) -> dict:
    ok = df["measurement_status"].isin(["valid", "not_applicable"]) & df["leader_matched"]
    exp_km = float((df.loc[ok, "speed_mps"] * DT).sum() / 1000.0)
    n = len(events)
    causes = defaultdict(int)
    for e in events:
        causes[e["cause"]] += 1
    return {"site": site, "n_events": n,
            "exposure_veh_km_valid": round(exp_km, 2),
            "rate_per_1000_veh_km": (round(n / exp_km * 1000.0, 4) if exp_km > 0 else None),
            "n_rows": int(len(df)), "n_vehicles": int(df["id"].nunique()),
            "cause_counts": dict(causes),
            "unclassified_share": (round(causes["未分类"] / n, 4) if n else None),
            "peak_drac": (round(max(e["peak_drac"] for e in events), 3) if n else None),
            "missing_reason_counts": df["missing_reason"].astype(str).value_counts().to_dict(),
            "examples": sorted(events, key=lambda e: -e["peak_drac"])[:5]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", nargs="+", default=["US-101"])
    ap.add_argument("--unit-check", action="store_true")
    ap.add_argument("--limit-rows", type=int, default=None)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    if args.unit_check:
        return 0 if unit_check() else 1

    out = {}
    for s in args.sites:
        print(f"=== {s} ===", flush=True)
        df = load_site(s)
        if args.limit_rows:
            df = df.head(args.limit_rows)
        ev = extract_events(df)
        r = summarize(s, df, ev)
        r["stratified"] = stratify(df, ev)
        r["sensitivity"] = []
        base_keys = {(e["run"], e["veh"], e["on_frame"]) for e in ev}
        for tag, mg, ms in [("g>=1", 1.0, None), ("g>=2", 2.0, None), ("v>=5", None, 5.0)]:
            sr = run_with_filter(df, mg, ms, tag)
            keys = sr.pop("_keys")
            sr["kept"] = len(keys & base_keys)
            sr["lost"] = len(base_keys - keys)
            sr["new"] = len(keys - base_keys)
            r["sensitivity"].append(sr)
        out[s] = r
        cc = r["cause_counts"]
        tot = r["n_events"] or 1
        print(f"  事件 {r['n_events']}；有效暴露 {r['exposure_veh_km_valid']:.1f} 车·公里；"
              f"率 {r['rate_per_1000_veh_km']}/千车·公里；峰值 {r['peak_drac']}", flush=True)
        print("  成因：" + "，".join(f"{k} {v}（{v/tot*100:.1f}%）" for k, v in cc.items()),
              flush=True)
        del df

    (OUT / "ngsim_drac.json").write_text(json.dumps(out, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    print(f"\nwritten: {OUT/'ngsim_drac.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
