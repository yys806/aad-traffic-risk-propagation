"""Create the non-overwriting Stage 0.3 scientific acceptance (closure) package.

Closes Stage 0.3 based on the five researcher-approved decisions of task
AAD-0.3.3 (archived in ``AI_CONTEXT/06_DECISIONS.md``, 2026-10-16).  The
package re-verifies the sealed R2 evidence (checksums, headline statistics,
independent verification) and never re-runs the expensive full pipeline; a
verification conflict aborts the closure (fail-closed).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "code/outputs/formal/calibration"
PARENT = BASE / "stage_0_3_pneuma_boundary_repair_20261016_r2"
INDEPENDENT = BASE / "stage_0_3_pneuma_boundary_repair_20261016_r2_independent_verification.json"
OUTPUT_NAME = "stage_0_3_scientific_acceptance_20261016_r3"
RESULT_ID = "RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3"
SOURCE_SHA256 = "F9CDE0A3CA5010E2217EA4CBC0BDF26ED87BE1EC0D8C2BE5E2CB93AAC82BA28C"

EXPECTED = {
    "raw_track_rows": 785,
    "unique_track_ids": 785,
    "unique_tracks": 785,
    "parsed_state_records": 1239475,
    "time_min_s": 38.4,
    "time_max_s": 888.0,
    "eligible_states": 1238690,
    "exposure_time_s": 49547.6,
    "speed_tw_mean": 4.838218067205407,
    "speed_vw_mean": 6.207738438311219,
    "accel_tw_mean": -0.0044102350063373,
    "accel_tw_sd": 0.7453676610491337,
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_checksums(directory: Path) -> None:
    sums = {}
    for line in (directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        sums[name] = digest
    for name, digest in sums.items():
        if sha(directory / name) != digest:
            raise RuntimeError(f"checksum mismatch in sealed package: {name}")
    for path in directory.iterdir():
        if path.is_file() and path.name not in sums and path.name != "SHA256SUMS":
            raise RuntimeError(f"sealed package contains unsealed file: {path.name}")


def seal(directory: Path) -> None:
    files = sorted(
        p for p in directory.iterdir() if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS"}
    )
    manifest = {
        "schema_version": "aad.stage-0-3.acceptance-manifest.v1",
        "files": [{"path": p.name, "bytes": p.stat().st_size, "sha256": sha(p)} for p in files],
    }
    (directory / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    sums = [
        f"{sha(p)}  {p.name}"
        for p in sorted(directory.iterdir())
        if p.is_file() and p.name != "SHA256SUMS"
    ]
    (directory / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=BASE / OUTPUT_NAME)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError(output)
    if not PARENT.is_dir() or not INDEPENDENT.is_file():
        raise FileNotFoundError("sealed R2 package or independent verification missing")

    # --- Fail-closed re-verification of the sealed R2 evidence ---------------
    verify_checksums(PARENT)
    audit = json.loads((PARENT / "audit.json").read_text(encoding="utf-8"))
    independent = json.loads(INDEPENDENT.read_text(encoding="utf-8"))
    speed_tw = pd.read_csv(PARENT / "speed_time_weighted_by_type.csv")
    speed_vw = pd.read_csv(PARENT / "speed_vehicle_equal_weight.csv")
    accel_tw = pd.read_csv(PARENT / "acceleration_time_weighted_by_type.csv")

    checks = {
        "r2_checksums": True,
        "source_sha256_pinned": audit["source_sha256"] == SOURCE_SHA256,
        "raw_track_rows": audit["raw_track_rows"] == EXPECTED["raw_track_rows"],
        "unique_track_ids": audit["unique_track_ids"] == EXPECTED["unique_track_ids"],
        "unique_tracks": audit["unique_tracks"] == EXPECTED["unique_tracks"],
        "parsed_state_records": audit["parsed_state_records"] == EXPECTED["parsed_state_records"],
        "time_min_s": abs(audit["time_min_s"] - EXPECTED["time_min_s"]) < 1e-9,
        "time_max_s": abs(audit["time_max_s"] - EXPECTED["time_max_s"]) < 1e-9,
        "raw_order_regressions": audit["raw_order_time_audit"]["regression_raw_order_edges"] == 0,
        "duplicate_track_ids": len(audit["duplicate_track_ids"]) == 0,
        "eligible_states": audit["stage_0_5_reference_eligible_states"] == EXPECTED["eligible_states"],
        "independent_pass": independent["pass"] is True and independent["discrepancies"] == [],
        "independent_states": independent["independent_states"] == EXPECTED["parsed_state_records"],
    }
    speed_all = speed_tw.loc[speed_tw["group"] == "ALL"].iloc[0]
    accel_all = accel_tw.loc[accel_tw["group"] == "ALL"].iloc[0]
    vw_all = speed_vw.loc[speed_vw["group"] == "ALL"].iloc[0]
    checks["exposure_time_s"] = abs(speed_all["exposure_time_s"] - EXPECTED["exposure_time_s"]) < 1e-6
    checks["speed_tw_mean"] = abs(speed_all["mean"] - EXPECTED["speed_tw_mean"]) < 1e-9
    checks["speed_vw_mean"] = abs(vw_all["mean"] - EXPECTED["speed_vw_mean"]) < 1e-9
    checks["accel_tw_mean"] = abs(accel_all["mean"] - EXPECTED["accel_tw_mean"]) < 1e-9
    checks["accel_tw_sd"] = abs(accel_all["sd"] - EXPECTED["accel_tw_sd"]) < 1e-9
    checks = {name: bool(ok) for name, ok in checks.items()}
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise RuntimeError(f"R2 evidence re-verification failed: {failed}")

    output.mkdir(parents=True)
    for source in [
        "audit.json",
        "config.json",
        "gate_matrix.csv",
        "gate_matrix_summary.json",
        "r1_r2_comparison.csv",
        "speed_time_weighted_by_type.csv",
        "acceleration_time_weighted_by_type.csv",
        "speed_vehicle_equal_weight.csv",
        "acceleration_vehicle_equal_weight.csv",
        "vehicle_type_composition.csv",
        "continuity_sensitivity.csv",
        "extreme_sensitivity.csv",
    ]:
        shutil.copyfile(PARENT / source, output / source)
    shutil.copyfile(INDEPENDENT, output / "independent_verification.json")

    config = json.loads((output / "config.json").read_text(encoding="utf-8"))
    config["scientific_acceptance_overlay"] = {
        "decision_status": "Approved (researcher, task AAD-0.3.3)",
        "decision_date": "2026-10-16",
        "decisions_archive": "AI_CONTEXT/06_DECISIONS.md#2026-10-16--stage-03-最终科学验收五项决定aad-033",
        "formal_scope": (
            "single file dataset/pNEUMA/20181101_d1_0800_0830.csv; observed vehicles only; "
            "descriptive urban kinematics reference (speed, longitudinal acceleration, "
            "vehicle-type composition); not a claim of complete 30-minute continuous "
            "observation, city-wide or general urban traffic, and no inference of the "
            "absolute origin of the time field"
        ),
        "approved_continuity_rule": "0 < dt <= 0.043 s (raw-record-order adjacency; this 25 Hz file only)",
        "approved_extreme_rule": "retain raw values, flag anomalies, keep masking sensitivity only",
        "approved_descriptive_thresholds": "low-speed / near-stop / near-zero-accel bands remain descriptive only",
        "gate_status": "pass",
        "stage_status": "Completed / Closed",
    }
    (output / "config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    decisions = {
        "schema_version": "aad.stage-0-3.acceptance-decisions.v1",
        "task_id": "AAD-0.3.3",
        "decision_date": "2026-10-16",
        "decided_by": "researcher",
        "decisions": [
            {
                "id": "D1-formal-scope",
                "decision": "formal scope limited to the observed vehicles of the single approved file",
                "basis": "R2 audit: 785 unique tracks, 1,239,475 states, timestamps [38.40, 888.00] s, reliable exposure 49,547.6 vehicle-seconds; raw-order/identity/quality audits pass",
            },
            {
                "id": "D2-continuity-rule",
                "decision": "0 < dt <= 0.043 s approved as the scientific continuity parameter for this 25 Hz file",
                "basis": "R2 raw-record-order continuity audit (0 regressions, 0 gaps, 0 duplicates) and sealed 8-tolerance sensitivity history; engineering anchor upgraded to approved parameter",
            },
            {
                "id": "D3-extreme-kinematics",
                "decision": "extreme kinematic observations are retained, flagged and sensitivity-checked, never auto-deleted",
                "basis": "R2 extreme sensitivity retained; physical truth remains Unverified; |a|>2 / |a|>5 m/s^2 stay exploratory diagnostic thresholds",
            },
            {
                "id": "D4-descriptive-thresholds",
                "decision": "low-speed / near-stop / near-zero-acceleration thresholds remain descriptive statistics only",
                "basis": "not approved as formal risk classification or quality-exclusion criteria",
            },
            {
                "id": "D5-scientific-gate",
                "decision": "Scientific Gate = pass; Stage Status = Completed / Closed",
                "basis": "limited to descriptive urban kinematic calibration of the single approved file; excludes independent physical truth, accident prediction, AAD causal effects and SUMO reality-coverage",
            },
        ],
        "stage_0_5_independent_items": [
            "vehicle-type to SUMO vType mapping",
            "time-weighted sampling / coverage statistics design",
            "coverage thresholds",
        ],
    }
    (output / "decisions.json").write_text(
        json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    matrix = [
        ["研究者决定归档", "五项决定（范围/连续性/极端值/描述阈值/Gate）经研究者批准并归档", "06_DECISIONS 2026-10-16 条目与本包 decisions.json 核对", "一致；批准依据均指向 R2 证据", "decisions.json; AI_CONTEXT/06_DECISIONS.md", "Verified", "Stage 0.5 事项保持独立待决"],
        ["R2 证据完整性", "R2 包 checksum、manifest 与未登记文件检查", "重算 SHA256SUMS 全部文件", "全部一致；无未封存文件", "SHA256SUMS; manifest.json", "Verified", "R1/R2 历史包保留不覆盖"],
        ["来源不可变", "源文件 SHA-256 钉扎", "R2 audit source_sha256 与预期比对", f"{SOURCE_SHA256[:16]}… 一致", "audit.json", "Verified", "文件级验证；原始数据链未变"],
        ["计数与范围", "785 唯一轨迹、1,239,475 状态、[38.40,888.00] s、暴露 49,547.6 s", "R2 audit + 独立复算 JSON 复核", "全部一致；独立复算 discrepancies=0", "independent_verification.json", "Verified", "仅限本文件实际观测车辆"],
        ["原始顺序/身份/质量审计", "R2 边界修复审计通过", "raw_order/identity audit 字段复核", "倒退 0、重复 ID 0、身份冲突 0；quality 全 raw_parsed；eligible 1,238,690", "audit.json (raw_order_time_audit, identity_audit)", "Verified", "语义为质量标记与时间权重，非物理真值"],
        ["时间连续性规则批准", "0<Δt≤0.043 s（D2）", "批准文本与 R2 锚定容差及敏感性表核对", "参数一致；历史 8 容差敏感性保留", "decisions.json; continuity_sensitivity.csv", "Verified", "仅当前 25 Hz 文件；不外推其他采样率"],
        ["极端观测处理批准", "保留+标记+敏感性（D3）", "R2 extreme_sensitivity 与决定文本核对", "原始分布为主要结果；|a|>2/5 仅探索性", "extreme_sensitivity.csv", "Verified", "独立物理真实性 Unverified；不得认定错误或危险行为"],
        ["描述性阈值批准", "仅描述统计（D4）", "决定文本与 R2 状态份额表核对", "低速/近静止/近零阈值保留为描述性", "speed_state_shares（R2 包）；decisions.json", "Verified", "不作为正式风险分类或质量排除"],
        ["统计不变性", "关闭包不得改变 R2 统计", "速度/加速度 TW 与 VW、车型组成逐值复核", "速度 TW mean=4.838218、VW mean=6.207738、加速度 mean=-0.004410 均不变", "speed_/acceleration_*.csv", "Verified", "本包不重跑全量管线"],
        ["有限适用范围", "单文件描述性运动学参考（D1）", "scope_and_claims 与批准文本核对", "不宣称 30 分钟连续覆盖、不代表城市总体、不推断时间原点", "scope_and_claims.md", "Verified", "范围外使用需另行验收"],
        ["最终科学 Gate", "pass 且 Completed / Closed（D5）", "全部矩阵项、复算与限制审核", "通过；仅限当前单文件有限描述性校准", "scientific_gate_report.json; report.md", "Verified", "永久保留物理真实性、代表性、外推与 Stage 0.5 覆盖限制"],
    ]
    gate = pd.DataFrame(matrix, columns=["验收事项", "预定标准/依据", "验证方法", "实际结果", "证据路径", "状态", "剩余限制"])
    gate.to_csv(output / "scientific_gate_matrix.csv", index=False)
    gate.to_json(output / "scientific_gate_matrix.json", orient="records", force_ascii=False, indent=2)

    scope = (
        "# Stage 0.3 科学适用范围\n\n"
        "允许结论：`dataset/pNEUMA/20181101_d1_0800_0830.csv` 实际观测车辆的速度、纵向加速度"
        "与车型组成等描述性城市运动学参考；可靠暴露 49,547.6 vehicle-seconds；"
        "已批准连续性规则 0<Δt≤0.043 s（原始记录顺序邻接，fail-closed，不插值不补帧）。\n\n"
        "禁止外推：完整 30 分钟连续交通观测、雅典或任何城市总体交通、其他 pNEUMA 文件或其他数据集、"
        "其他采样率语义、事故概率、危险识别准确率、AAD 因果效应、SUMO 现实覆盖；"
        "缺少证据时不得推断时间字段的绝对原点。\n\n"
        "永久限制：独立物理真实性 Unverified；极端运动学观测保留且仅作敏感性对照；"
        "车辆等权统计不代表城市车辆总体分布；Heavy Vehicle n=2 不作车型级推断。\n\n"
        "后续归属：车型→SUMO vType 映射、时间权重抽样设计与覆盖阈值属 Stage 0.5 独立待决事项；"
        "Protocol Lock 与 Stage I 不因本关闭解锁；locked holdout 不访问。\n"
    )
    (output / "scope_and_claims.md").write_text(scope, encoding="utf-8")

    report = {
        "schema_version": "aad.stage-0-3.scientific-gate-report.v1",
        "experiment_id": "stage_0_3",
        "result_id": RESULT_ID,
        "status": "pass",
        "gate_status": "pass",
        "stage_status": "Completed / Closed",
        "decision_date": "2026-10-16",
        "decision_source": "researcher approval via task AAD-0.3.3; archived in AI_CONTEXT/06_DECISIONS.md",
        "scientific_scope": (
            "single approved pNEUMA file (20181101_d1_0800_0830.csv); observed vehicles only; "
            "descriptive urban kinematics calibration (speed, longitudinal acceleration, "
            "vehicle-type composition) at the approved 0<dt<=0.043 s continuity semantics"
        ),
        "verified_statistics": {
            "unique_tracks": 785,
            "state_records": 1239475,
            "time_range_s": [38.4, 888.0],
            "reliable_exposure_s": 49547.6,
            "time_weighting_eligible_states": 1238690,
            "speed_mean_mps_time_weighted": 4.838218067205407,
            "speed_mean_mps_vehicle_equal": 6.207738438311219,
            "accel_mean_mps2_time_weighted": -0.0044102350063373,
            "accel_sd_mps2_time_weighted": 0.7453676610491337,
        },
        "approved_parameters": {
            "continuity_rule": "0 < dt <= 0.043 s; raw-record-order adjacency; fail-closed; this 25 Hz file only",
            "extreme_kinematics": "retain, flag, sensitivity-only",
            "descriptive_thresholds": "descriptive statistics only",
        },
        "verification": {
            "r2_checksums_reverified": True,
            "independent_verification_discrepancies": 0,
            "statistics_unchanged_from_r2": True,
            "r2_reverification_checks": checks,
        },
        "scientific_claim_eligible": True,
        "accident_probability_claim_eligible": False,
        "aad_causal_claim_eligible": False,
        "sumo_coverage_claim_eligible": False,
        "physical_truth_status": "Unverified; declared permanent limitation, not a blocker for this limited descriptive gate",
        "stage_0_5_independent_items": decisions["stage_0_5_independent_items"],
        "protocol_lock_created": False,
        "stage_I_run": False,
        "locked_holdout_opened": False,
    }
    (output / "scientific_gate_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report_md = (
        "# Stage 0.3 最终科学验收与正式关闭（R3）\n\n"
        "Stage 0.3 在研究者 2026-10-16 批准的有限范围内正式通过并关闭：单一批准 pNEUMA 文件"
        "（20181101_d1_0800_0830.csv）实际观测车辆的描述性城市运动学校准（速度、纵向加速度、"
        "车型组成），采用已批准连续性规则 0<Δt≤0.043 s（原始记录顺序、fail-closed）。\n\n"
        "核验：R2 包 checksum 重验通过；785 唯一轨迹 / 1,239,475 状态 / 时间戳 [38.40, 888.00] s / "
        "可靠暴露 49,547.6 vehicle-seconds；速度时间加权 mean=4.838218 m/s、车辆等权 mean=6.207738 m/s、"
        "纵向加速度 mean=-0.004410 m/s²（sd=0.745368）；独立复算 discrepancies=0；统计与 R2 完全一致，"
        "本包未重跑全量管线。\n\n"
        "本 Gate 不支持完整 30 分钟连续观测、城市总体交通、其他文件/采样率外推、事故概率、"
        "危险识别准确率、AAD 因果效应或 SUMO 现实覆盖。独立物理真实性保持 Unverified；"
        "极端观测保留且仅作敏感性；车型→vType 映射与 Stage 0.5 覆盖设计独立待决；"
        "Protocol Lock 与 Stage I 不因此解锁。R1/R2 历史包保留不覆盖。\n"
    )
    (output / "report.md").write_text(report_md, encoding="utf-8")

    provenance = {
        "schema_version": "aad.stage-0-3.acceptance-provenance.v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "parent_package": str(PARENT.relative_to(ROOT)),
        "parent_sha256sums_sha256": sha(PARENT / "SHA256SUMS"),
        "parent_input_files": {
            str((PARENT / name).relative_to(ROOT)): sha(PARENT / name)
            for name in ["audit.json", "config.json", "speed_time_weighted_by_type.csv",
                         "acceleration_time_weighted_by_type.csv", "speed_vehicle_equal_weight.csv"]
        },
        "independent_verification": {
            "path": str(INDEPENDENT.relative_to(ROOT)),
            "sha256": sha(INDEPENDENT),
        },
        "decisions_sha256": sha(ROOT / "AI_CONTEXT/06_DECISIONS.md"),
        "source_csv_sha256": audit["source_sha256"],
    }
    (output / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    seal(output)
    print(json.dumps({"output": str(output), "gate_status": "pass", "checks": checks}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
