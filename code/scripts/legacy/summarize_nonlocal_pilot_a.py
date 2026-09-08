from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskprop.legacy.nonlocal_pilot_summary import (  # noqa: E402
    compare_pre_treatment_trajectories,
    locate_first_applied_time,
    summarize_mechanism_log,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize nonlocal Pilot A outputs.")
    parser.add_argument("--simulation-root", type=Path, required=True)
    parser.add_argument("--region-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _read_jsonl(path: Path) -> pd.DataFrame:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return pd.DataFrame(rows)


def _find_emission(root: Path, mode: str, penetration: int) -> Path:
    matches = sorted((root / mode / "emissions").glob(f"merge_ours_p{penetration}_*_emission.csv"))
    if len(matches) != 1:
        raise ValueError(
            f"Expected one p{penetration} {mode} emission, found {len(matches)}"
        )
    return matches[0]


def _warning_counts(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "emergency_braking_warning_count": text.count("performs emergency braking"),
        "safe_speed_clipping_message_count": text.count("Safe velocity clipping applied"),
    }


def main() -> None:
    args = parse_args()
    simulation_root = args.simulation_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    mechanism_tables: dict[tuple[int, str], pd.DataFrame] = {}
    mechanism_rows = []
    pattern = re.compile(r"merge_ours_p(60|80)_(on|shadow_off)_seed(\d+)\.jsonl")
    for path in sorted((simulation_root / "mechanism_logs").glob("*.jsonl")):
        match = pattern.fullmatch(path.name)
        if match is None:
            continue
        penetration = int(match.group(1))
        mode = match.group(2)
        run_seed = int(match.group(3))
        records = _read_jsonl(path)
        mechanism_tables[(penetration, mode)] = records
        mechanism_rows.append(
            {
                "penetration_pct": penetration,
                "mode": mode,
                "configured_run_seed": run_seed,
                **summarize_mechanism_log(records),
            }
        )
    mechanism_summary = pd.DataFrame(mechanism_rows).sort_values(
        ["penetration_pct", "mode"]
    )

    on_metrics = pd.read_csv(simulation_root / "on" / "per_run_results.csv")
    off_metrics = pd.read_csv(
        simulation_root / "shadow_off" / "per_run_results.csv"
    )
    metric_columns = [
        "returns",
        "velocities",
        "outflows",
        "collision_count",
        "ttc_violation_rate",
        "thw_violation_rate",
        "accel_variance",
        "hard_brake_count_lt_6",
        "emission_min_ttc",
        "emission_min_thw",
    ]
    metric_rows = []
    pair_rows = []
    for penetration in (60, 80):
        on_log = mechanism_tables[(penetration, "on")]
        off_log = mechanism_tables[(penetration, "shadow_off")]
        on_emission_path = _find_emission(simulation_root, "on", penetration)
        off_emission_path = _find_emission(simulation_root, "shadow_off", penetration)
        on_emission = pd.read_csv(on_emission_path)
        off_emission = pd.read_csv(off_emission_path)
        applied_location = locate_first_applied_time(on_log, on_emission)
        first_applied_time = applied_location["first_applied_time_s"]
        if first_applied_time is None:
            raise ValueError(f"p{penetration} on run never applied ETA mechanism")
        consistency = compare_pre_treatment_trajectories(
            on_emission,
            off_emission,
            first_applied_time_s=float(first_applied_time),
        )
        on_row = on_metrics.loc[on_metrics["penetration_pct"].eq(penetration)].iloc[0]
        off_row = off_metrics.loc[off_metrics["penetration_pct"].eq(penetration)].iloc[0]
        on_mechanism = mechanism_summary.loc[
            mechanism_summary["penetration_pct"].eq(penetration)
            & mechanism_summary["mode"].eq("on")
        ].iloc[0]
        off_mechanism = mechanism_summary.loc[
            mechanism_summary["penetration_pct"].eq(penetration)
            & mechanism_summary["mode"].eq("shadow_off")
        ].iloc[0]
        seed_match = (
            int(on_row["configured_run_seed"])
            == int(off_row["configured_run_seed"])
            and int(on_row["sumo_seed"]) == int(off_row["sumo_seed"])
        )
        pair_pass = (
            seed_match
            and bool(consistency["pre_treatment_keys_match"])
            and bool(consistency["pre_treatment_values_match"])
            and int(on_mechanism["applied_count"]) > 0
            and int(off_mechanism["would_trigger_count"]) > 0
            and int(off_mechanism["applied_count"]) == 0
        )
        pair_rows.append(
            {
                "penetration_pct": penetration,
                "configured_run_seed": int(on_row["configured_run_seed"]),
                "sumo_seed": int(on_row["sumo_seed"]),
                "seed_match": seed_match,
                **applied_location,
                **consistency,
                "on_applied_count": int(on_mechanism["applied_count"]),
                "off_would_trigger_count": int(off_mechanism["would_trigger_count"]),
                "off_applied_count": int(off_mechanism["applied_count"]),
                "pair_validation_pass": pair_pass,
            }
        )
        for metric in metric_columns:
            on_value = float(on_row[metric])
            off_value = float(off_row[metric])
            metric_rows.append(
                {
                    "penetration_pct": penetration,
                    "metric": metric,
                    "on": on_value,
                    "shadow_off": off_value,
                    "on_minus_off": on_value - off_value,
                }
            )

    pair_consistency = pd.DataFrame(pair_rows)
    metric_comparison = pd.DataFrame(metric_rows)
    warnings = {
        "on": _warning_counts(simulation_root / "run_logs" / "on.log"),
        "shadow_off": _warning_counts(
            simulation_root / "run_logs" / "shadow_off.log"
        ),
    }
    region_summary = pd.read_csv(args.region_root / "scale_summary.csv")
    scale_comparison = pd.read_csv(args.region_root / "scale_comparison.csv")
    pilot_pass = bool(pair_consistency["pair_validation_pass"].all())

    mechanism_summary.to_csv(output_dir / "mechanism_summary.csv", index=False)
    pair_consistency.to_csv(output_dir / "pair_consistency.csv", index=False)
    metric_comparison.to_csv(output_dir / "metric_comparison.csv", index=False)
    summary = {
        "pilot_validation_pass": pilot_pass,
        "claim_boundary": "One-seed smoke validation only; not a formal causal effect estimate.",
        "mechanism_summary": mechanism_summary.to_dict("records"),
        "pair_consistency": pair_consistency.to_dict("records"),
        "metric_comparison": metric_comparison.to_dict("records"),
        "warning_counts": warnings,
        "region_scale_summary": region_summary.to_dict("records"),
        "region_scale_comparison": scale_comparison.to_dict("records"),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        "# 非局部 Pilot A 实验汇总",
        "",
        f"机制冒烟验收：{'通过' if pilot_pass else '未通过'}。四组均为 1 个 seed，不作为正式因果效应。",
        "",
        "## 区域尺度",
        "",
        "| L0 (m) | 暴露区域 | 风险区域 | episode |",
        "|---:|---:|---:|---:|",
    ]
    for row in region_summary.to_dict("records"):
        lines.append(
            f"| {row['nominal_length_m']:g} | {int(row['exposed_region_count'])} | "
            f"{int(row['risk_region_count'])} | {int(row['event_count'])} |"
        )
    lines.extend(
        [
            "",
            "## 开关与配对",
            "",
            "| 渗透率 | on应用 | off候选触发 | off应用 | 首次应用(s) | 首次分化(s) | 处理前一致 |",
            "|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in pair_rows:
        lines.append(
            f"| {row['penetration_pct']} | {row['on_applied_count']} | "
            f"{row['off_would_trigger_count']} | {row['off_applied_count']} | "
            f"{row['first_applied_time_s']:.1f} | {row['first_divergence_time_s']:.1f} | "
            f"{'是' if row['pre_treatment_keys_match'] and row['pre_treatment_values_match'] else '否'} |"
        )
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- 这 4 次只证明区域算法、ETA 日志、开关和同 seed 配对能工作。",
            "- SUMO 仍出现安全速度覆盖/急刹警告，风险指标不能只看控制器目标动作。",
            "- 正式因果结论仍需要多 seed 配对实验、置信区间和安慰剂检查。",
        ]
    )
    (output_dir / "实验汇总.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
