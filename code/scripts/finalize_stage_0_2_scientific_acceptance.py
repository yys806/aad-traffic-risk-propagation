"""Create the non-overwriting Stage 0.2 scientific acceptance package."""
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
PARENT = BASE / "stage_0_2_final_closure_20261012_final_r1"
OUTPUT_NAME = "stage_0_2_scientific_acceptance_20261012_r3"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seal(directory: Path) -> None:
    files = sorted(p for p in directory.iterdir() if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS"})
    manifest = {"files": [{"path": p.name, "bytes": p.stat().st_size, "sha256": sha(p)} for p in files]}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    sums = [f"{sha(p)}  {p.name}" for p in sorted(directory.iterdir()) if p.is_file() and p.name != "SHA256SUMS"]
    (directory / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=BASE / OUTPUT_NAME)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)

    for source in ["audit.json", "config.json", "provenance.json", "gate_matrix.json", "summary.json", "validation.json", "final_interface_reverification.json", "paper_version_conflict.md", "exposure_denominators.csv", "measurement_status_transitions.csv", "sampling_sensitivity.csv", "sampling_one_to_one_confirmation.csv", "extreme_sensitivity.csv", "rho_scale_sensitivity.csv", "tau_recalculation.csv", "p2_online_diagnostics.json", "p2_formal_events.parquet"]:
        shutil.copyfile(PARENT / source, output / source)

    edge_audit_path = BASE / "stage_0_2_exposure_edge_audit_20261012.json"
    edge_audit = json.loads(edge_audit_path.read_text(encoding="utf-8"))
    shutil.copyfile(edge_audit_path, output / "exposure_edge_audit.json")
    if not edge_audit["matches_sealed_denominator_s"] or edge_audit["missing_or_identity_uncertain_edges_included"]:
        raise RuntimeError("independent exposure-edge audit does not support the sealed denominator")

    exposure = pd.read_csv(PARENT / "exposure_denominators.csv")
    exposure["p2_event_rate_per_vehicle_hour"] = exposure["p2_events"] / exposure["reliable_following_edge_seconds"] * 3600.0
    exposure["p2_event_rate_definition"] = "P2 events / reliable following exposure seconds * 3600"
    exposure["rate_interpretation"] = "proxy event frequency under reliable observation; not accident probability"
    exposure.to_csv(output / "p2_event_rates_by_source.csv", index=False)

    status = pd.read_csv(PARENT / "measurement_status.csv")
    status.to_csv(output / "measurement_status_by_source.csv", index=False)
    rates = {
        "sources": exposure[["source", "p2_events", "reliable_following_edge_seconds", "reliable_closing_edge_seconds", "p2_event_rate_per_vehicle_hour"]].to_dict("records"),
        "total_p2_events": int(exposure.p2_events.sum()),
        "total_reliable_following_exposure_seconds": float(exposure.reliable_following_edge_seconds.sum()),
        "total_reliable_closing_exposure_seconds": float(exposure.reliable_closing_edge_seconds.sum()),
        "descriptive_combined_rate_per_vehicle_hour": float(exposure.p2_events.sum() / exposure.reliable_following_edge_seconds.sum() * 3600.0),
        "combined_rate_warning": "descriptive aggregation only; four sources are not treated as iid roads",
        "denominator_unit": "vehicle-hour",
    }
    (output / "p2_event_rates.json").write_text(json.dumps(rates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    matrix = [
        ["批准科学目标", "四源NGSIM纵向跟驰风险代理测量与描述性现实校准", "四源封存数据、任务决定与最终包交叉核对", "支持限定范围内验收", "summary.json; p2_event_rates.json", "Verified", "不支持事故概率、危险识别准确率、P2全局最优或AAD因果效应"],
        ["研究者决定归档", "06_DECISIONS中的2026-10-12决定完整记录", "决定文本、config、provenance核对", "已归档并作为本包依据", "AI_CONTEXT/06_DECISIONS.md", "Verified", "范围外问题转后续阶段"],
        ["四源来源与哈希", "批准四源分别报告、输入不可变", "task1.5输入SHA、历史封存哈希与本包provenance", "哈希一致；来源边界保留", "historical_sha256_audit.csv; provenance.json", "Verified", "Lankershim原始官方分源解释仍为历史限制"],
        ["正式P2事件与在线确认", "可靠TTC<2s、首末跨度>=0.2s、实际观测确认", "逐事件成员/时间/指标复算与在线诊断", "4545；四源raw=reliable，确认与触发对齐", "event_member_time_comparison.csv; p2_online_diagnostics.json", "Verified", "事件率是代理频率"],
        ["可靠跟驰暴露分母", "可靠相邻跟驰边，包含身份连续且可判定的非闭合状态，不跨断点、不重复末帧", "四源5,120,432条边独立重构；检查source/clock/follower/leader、global time、frame、time_s、gap与身份标志，并统计边两端状态", "512043.2 s，与封存值逐源精确一致；但四源均有invalid/non_positive_gap端点边，Lankershim 7,557.4 s (6.20%)，三US-101分别187.4/178.7/197.5 s；若事件可评价性要求排除这些边，正式分母口径冲突", "exposure_edge_audit.json; p2_event_rates_by_source.csv; exposure_denominators.csv", "Decision Required", "必须由研究者确认invalid/non_positive_gap边是否仍属于P2事件率的可靠跟驰分母；不得擅自改写批准分母"],
        ["可靠闭合暴露", "与跟驰暴露严格区分", "四源边级时间核对", "208026.3 s，未混入事件率分母", "p2_event_rates.csv", "Verified", "仅作连续风险条件参考"],
        ["TTC/DRAC与状态分类", "保留valid、not_applicable、invalid、not_measurable/missing语义", "状态全量表、缺失原因、连续性证据", "5706252行状态，缺失与不可评价未补零", "measurement_status_by_source.csv; measurement_status.csv", "Verified", "来源异质性须随结果报告"],
        ["tau/rho与敏感性", "tau=15.364279197080283；tau/2、tau、2tau均报告", "独立tau复算与三尺度表", "一致；尺度敏感性已封存", "tau_recalculation.csv; rho_scale_sensitivity.csv", "Verified", "条件风险负担不外推为总体安全"],
        ["100/200 ms语义", "100ms为正式参考；200ms两相位仅迁移限制", "不插值抽稀对应与确认差异", "P2 4545 -> 4155/4162，采样不等价", "sampling_sensitivity.csv; sampling_one_to_one_confirmation.csv", "Verified", "不阻断100ms范围验收；禁止跨采样率外推"],
        ["极端与物理真实性", "极端屏蔽仅稳健性；物理真值不伪造", "447案例、48重点、11差异案例与屏蔽结果", "P2屏蔽后4370；Physical Truth Unverified", "case_447_kinematic_geometry_evidence.csv; manual_review_index.md", "Verified", "独立物理真实性为永久科学限制，不作事故真值主张"],
        ["有限适用范围", "仅四源、100ms、描述性校准；不外推道路/总体交通/SUMO", "Gate范围与后续职责核对", "范围已写入本包与项目索引", "scope_and_claims.md", "Verified", "Stage0.3/0.5/0.6及因果评价另行验收"],
        ["最终科学Gate", "批准范围内无使描述性统计失效的实质阻断", "完整矩阵、复算、质量与限制审核", "分母包含无法判定P2的invalid/non_positive_gap边；正式事件率口径需研究者裁决", "scientific_gate_report.json; report.md", "Blocked", "在分母语义裁决前不得正式关闭"],
    ]
    gate = pd.DataFrame(matrix, columns=["验收事项", "预定标准/依据", "验证方法", "实际结果", "证据路径", "状态", "剩余限制"])
    gate.to_csv(output / "scientific_gate_matrix.csv", index=False)
    gate.to_json(output / "scientific_gate_matrix.json", orient="records", force_ascii=False, indent=2)

    scope = """# Stage 0.2 科学适用范围\n\n允许结论：四个批准 NGSIM 来源分别支持纵向跟驰风险代理指标测量、可靠观测条件下的 P2 代理事件频率，以及 tau/rho 连续风险负担的描述性现实校准。\n\n禁止外推：事故发生概率、真实危险识别准确率、P2 全局最优性、AAD核心因果效应、其他道路、总体交通、SUMO、原生200ms等价性。\n\n永久限制：独立物理真实性、独立视频/几何真值和人工审核结论仍为 Unverified。极端屏蔽只用于稳健性，不构成自动删除规则。四源不视为独立同分布道路样本。\n\n后续归属：pNEUMA运动学为Stage0.3；SUMO覆盖及原生200ms为Stage0.5；目标区域/车辆/四格窗口和消息机制属于后续因果评价与协议冻结；Stage0.6负责协议锁准备。\n"""
    (output / "scope_and_claims.md").write_text(scope, encoding="utf-8")

    audit = {
        "schema_version": "stage_0_2.scientific_acceptance.audit.v1",
        "status": "blocked",
        "gate_status": "blocked",
        "stage_status": "Active - scientific decision required",
        "scientific_scope": "four approved NGSIM sources; 100ms descriptive longitudinal following-risk proxy calibration",
        "p2_event_count": 4545,
        "reliable_following_exposure_s": 512043.2,
        "reliable_closing_exposure_s": 208026.3,
        "p2_rate_denominator": "reliable_following_exposure_time",
        "physical_truth_status": "Unverified; declared limitation, not a blocker for this limited descriptive gate",
        "sampling_transfer_status": "100ms accepted scope; 200ms non-equivalence retained as limitation",
        "scientific_claim_eligible": False,
        "blocking_issue": "Reliable-following denominator contains invalid/non_positive_gap endpoint edges; researcher must confirm whether these are eligible for P2 event-rate denominator.",
        "accident_probability_claim_eligible": False,
        "aad_causal_claim_eligible": False,
        "protocol_lock_created": False,
        "stage_I_run": False,
        "locked_holdout_opened": False,
    }
    (output / "scientific_gate_report.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = """# Stage 0.2 最终科学验收（待裁决）\n\n本包不执行正式关闭。独立边级核验确认封存跟驰暴露为512043.2秒且连续性条件满足，但分母包含invalid/non_positive_gap端点边；这些边不能判定P2事件是否可评价。四源影响量已在`exposure_edge_audit.json`中逐源列出。\n\n正式P2事件率暂按批准公式计算并保留，但在研究者确认该状态是否属于可靠跟驰分母前，Gate保持Blocked，不能写入stage_status=Completed / Closed。\n\n独立物理真实性仍为Unverified，100/200ms不等价、极端屏蔽及后续阶段边界均保留。\n"""
    (output / "report.md").write_text(report, encoding="utf-8")
    provenance = {
        "schema_version": "stage_0_2.scientific_acceptance.provenance.v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "parent_package": str(PARENT.relative_to(ROOT)),
        "parent_sha256": sha(PARENT / "SHA256SUMS"),
        "input_files": {str((PARENT / n).relative_to(ROOT)): sha(PARENT / n) for n in ["audit.json", "config.json", "provenance.json", "gate_matrix.json", "summary.json", "validation.json", "exposure_denominators.csv"]},
        "independent_exposure_edge_audit": {"path": str(edge_audit_path.relative_to(ROOT)), "sha256": sha(edge_audit_path)},
        "decisions_sha256": sha(ROOT / "AI_CONTEXT/06_DECISIONS.md"),
        "source_state_sha256": sorted(sha(p) for p in (BASE / "stage_0_2_task_1_5_20261010_r4/states").glob("*.parquet")),
    }
    (output / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    seal(output)
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
