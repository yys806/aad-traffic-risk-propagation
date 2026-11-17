"""Generate the AAD results ledger from a path3 summary file.

阶段：P1 ｜ 运行目录：code/outputs/analysis/<run> ｜ 数据：<run>/path3_summary.json
      ｜ 脚本：code/scripts/make_ledger.py

Why this exists
---------------
Every number in docs/ used to be transcribed by hand, and hand transcription is exactly
where the "0.55% vs 0.63%" class of error came from (an absolute difference written as a
percentage, base 0.8760). This script prints the table straight from the run output and
refuses to print a relative figure without its base.

Usage
-----
  python code/scripts/make_ledger.py code/outputs/analysis/<run>/path3_summary.json
  python code/scripts/make_ledger.py <summary.json> --out <ledger.md>

退出码：0 正常；2 表示发现一致性错误（相对值与其基数算不平）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 基数低于这个值时，除以它会放大到不可解释（隔离场景 instant 口径实测约 1.2e-4）
SMALL_BASE = 1e-3


def fmt(v, nd: int = 6) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v != 0.0 and abs(v) < 1e-4:
            return f"{v:.3e}"
        return f"{v:.{nd}g}"
    return str(v)


def relative(delta: float | None, base: float | None) -> tuple[str, bool]:
    """Return (text, interpretable). A relative change is only reported with its base."""
    if delta is None or base is None or base == 0:
        return "—", False
    rel = delta / base
    if abs(base) < SMALL_BASE:
        return f"{rel:+.2%}（基数过小，不可解释）", False
    return f"{rel:+.2%}", True


def build(summary_path: Path) -> tuple[str, list[str]]:
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    cfg = data.get("config", {})
    arms = data.get("arms", {})
    contrasts = data.get("contrasts", {})
    errors: list[str] = []

    out: list[str] = []
    out.append("# AAD 结果账本（自动生成，请勿手改）\n")
    out.append(f"来源：`{summary_path.as_posix()}`")
    out.append("")
    out.append("| 配置项 | 值 |")
    out.append("|---|---|")
    for key in ("seeds", "risk_mode", "response", "ttc_tau", "leader_brake_mps2",
                "native_tau_s", "sham_factor", "sham_delta", "peak_scale"):
        if key in cfg:
            out.append(f"| {key} | {fmt(cfg[key])} |")
    out.append("")

    # ---- per-arm table ----
    out.append("## 各臂结果\n")
    out.append("| 种子 | 臂 | 风险(车·时加权) | 风险(旧名单口径) | 暴露(车·秒) | 区域均速 "
               "| 吞吐(辆) | 里程(m) | 执行倍率均值 | 采纳 | 施加 |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for seed, by_arm in arms.items():
        for arm_name in ("opn0", "sham", "opn1"):
            r = by_arm.get(arm_name)
            if not r:
                continue
            out.append(
                f"| {seed} | {arm_name} | {fmt(r.get('risk_meantime'))} "
                f"| {fmt(r.get('risk_roster'))} | {fmt(r.get('exposure_veh_s'))} "
                f"| {fmt(r.get('cost_speed_mean'))} | {fmt(r.get('throughput_veh'))} "
                f"| {fmt(r.get('distance_m'))} | {fmt(r.get('factor_mean'))} "
                f"| {fmt(r.get('n_adopted'))} | {fmt(r.get('n_applied'))} |")
    out.append("")

    # ---- contrasts, always with the base ----
    out.append("## 对比（每个相对值都带基数）\n")
    out.append("| 种子 | 基数 opn0 | Δ(opn1−opn0) | 相对 | Δ(sham−opn0) | 相对 "
               "| Δ(opn1−sham) | 相对 |")
    out.append("|---|---|---|---|---|---|---|---|")
    for seed, row in contrasts.items():
        o0 = row.get("opn0")
        cells = []
        for dkey, rkey in (("d_opn1_opn0", "rel_opn1_opn0"),
                           ("d_sham_opn0", None),
                           ("d_opn1_sham", "rel_opn1_sham")):
            d = row.get(dkey)
            txt, ok = relative(d, o0 if rkey is None else (o0 if "opn0" in (rkey or "") else row.get("sham")))
            if rkey:
                # 用报告里已有的相对值，但独立复算一遍做一致性检查
                reported = row.get(rkey)
                if reported is not None and d is not None:
                    base = o0 if rkey.endswith("opn0") else row.get("sham")
                    if base not in (None, 0):
                        recomputed = d / base
                        if abs(recomputed - reported) > 1e-9:
                            errors.append(
                                f"seed={seed} {rkey}: 报告值 {reported!r} 与复算值 "
                                f"{recomputed!r} 不一致（Δ={d!r}, base={base!r}）")
                txt = f"{reported:+.2%}" if reported is not None else "—"
                if abs(o0 or 0) < SMALL_BASE:
                    txt += "（基数过小）"
            cells.append(fmt(d))
            cells.append(txt)
        out.append(f"| {seed} | {fmt(o0)} | " + " | ".join(cells) + " |")
    out.append("")

    # ---- base warning ----
    bases = [row.get("opn0") for row in contrasts.values() if row.get("opn0") is not None]
    if bases:
        mean_base = sum(bases) / len(bases)
        out.append(f"**基数均值 = {fmt(mean_base)}。**")
        if abs(mean_base) < SMALL_BASE:
            out.append(f"⚠️ 基数小于 {SMALL_BASE}：所有相对变化都会被放大到不可解释。"
                       "这种口径下只能报绝对差与基数，**不得**引用任何百分数。")
        out.append("")
        # consistency: relative must equal delta/base
        for seed, row in contrasts.items():
            for rkey, dkey, bkey in (("rel_opn1_opn0", "d_opn1_opn0", "opn0"),
                                     ("rel_opn1_sham", "d_opn1_sham", "sham")):
                rel, d, b = row.get(rkey), row.get(dkey), row.get(bkey)
                if rel is None or d is None or b in (None, 0):
                    continue
                if abs(d / b - rel) > 1e-9:
                    errors.append(f"seed={seed} {rkey}: {rel!r} != {d!r}/{b!r}")

    out.append("## 一致性检查\n")
    if errors:
        out.append("发现下列不一致：\n")
        for e in errors:
            out.append(f"- {e}")
    else:
        out.append("相对值与基数算得平，未发现不一致。")
    out.append("")
    out.append("> 说明：本表由脚本生成。任何要写进论文或汇报的数字，必须从本表取，不得手抄。")
    return "\n".join(out), errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("summary")
    ap.add_argument("--out", default=None, help="write the ledger markdown here")
    args = ap.parse_args()
    path = Path(args.summary)
    if not path.exists():
        print(f"not found: {path}", file=sys.stderr)
        return 1
    text, errors = build(path)
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
