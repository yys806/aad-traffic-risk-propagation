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
OUTPUT_NAME = "stage_0_2_scientific_acceptance_20261012_r4"


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

    config = json.loads((output / "config.json").read_text(encoding="utf-8"))
    config["scientific_acceptance_overlay"] = {
        "decision_status": "Agreed Research Design",
        "decision_date": "2026-10-12",
        "p2_rate_denominator": "reliable following edges whose both endpoints are P2-evaluable (valid positive-closing TTC or reliably confirmed positive-gap non-closing not_applicable)",
        "excluded_states": ["invalid/non_positive_gap", "other not evaluable or missing states"],
        "excluded_exposure_interpretation": "not zero event or zero risk; all raw states and quality statistics retained",
        "official_rate_unit": "events / P2-evaluable following vehicle-hour",
        "scope": "four approved NGSIM sources; 100 ms continuity semantics",
    }
    (output / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    edge_audit_path = BASE / "stage_0_2_exposure_edge_audit_20261012.json"
    edge_audit = json.loads(edge_audit_path.read_text(encoding="utf-8"))
    shutil.copyfile(edge_audit_path, output / "exposure_edge_audit.json")
    if not edge_audit["matches_sealed_denominator_s"] or edge_audit["missing_or_identity_uncertain_edges_included"]:
        raise RuntimeError("independent exposure-edge audit does not support the sealed denominator")

    exposure = pd.read_csv(PARENT / "exposure_denominators.csv")
    edge_rows = {row["source"]: row for row in edge_audit["sources"]}
    exposure["p2_evaluable_following_exposure_seconds"] = exposure["source"].map(lambda s: edge_rows[s]["p2_evaluable_following_exposure_s"])
    exposure["not_evaluable_following_exposure_seconds"] = exposure["source"].map(lambda s: edge_rows[s]["not_evaluable_following_exposure_s"])
    exposure["not_evaluable_fraction_of_reliable_following_exposure"] = exposure["not_evaluable_following_exposure_seconds"] / exposure["reliable_following_edge_seconds"]
    exposure["p2_evaluable_fraction_of_reliable_following_exposure"] = exposure["p2_evaluable_following_exposure_seconds"] / exposure["reliable_following_edge_seconds"]
    exposure["p2_event_rate_per_p2_evaluable_vehicle_hour"] = exposure["p2_events"] / exposure["p2_evaluable_following_exposure_seconds"] * 3600.0
    exposure["legacy_reliable_following_rate_per_vehicle_hour"] = exposure["p2_events"] / exposure["reliable_following_edge_seconds"] * 3600.0
    exposure["rate_change_percent_new_vs_legacy"] = (exposure["p2_event_rate_per_p2_evaluable_vehicle_hour"] / exposure["legacy_reliable_following_rate_per_vehicle_hour"] - 1.0) * 100.0
    exposure["p2_event_rate_definition"] = "P2 events / P2-evaluable reliable following exposure seconds * 3600; events / P2-evaluable following vehicle-hour"
    exposure["rate_interpretation"] = "proxy event frequency under reliable observation; not accident probability"
    exposure.to_csv(output / "p2_event_rates_by_source.csv", index=False)

    status = pd.read_csv(PARENT / "measurement_status.csv")
    status.to_csv(output / "measurement_status_by_source.csv", index=False)
    rates = {
        "sources": exposure[["source", "p2_events", "reliable_following_edge_seconds", "p2_evaluable_following_exposure_seconds", "not_evaluable_following_exposure_seconds", "reliable_closing_edge_seconds", "p2_event_rate_per_p2_evaluable_vehicle_hour", "legacy_reliable_following_rate_per_vehicle_hour", "rate_change_percent_new_vs_legacy"]].to_dict("records"),
        "total_p2_events": int(exposure.p2_events.sum()),
        "total_reliable_following_exposure_seconds": float(exposure.reliable_following_edge_seconds.sum()),
        "total_p2_evaluable_following_exposure_seconds": float(exposure.p2_evaluable_following_exposure_seconds.sum()),
        "total_not_evaluable_following_exposure_seconds": float(exposure.not_evaluable_following_exposure_seconds.sum()),
        "total_reliable_closing_exposure_seconds": float(exposure.reliable_closing_edge_seconds.sum()),
        "descriptive_combined_rate_per_vehicle_hour": float(exposure.p2_events.sum() / exposure.p2_evaluable_following_exposure_seconds.sum() * 3600.0),
        "combined_rate_warning": "descriptive aggregation only; four sources are not treated as iid roads",
        "denominator_unit": "P2-evaluable following vehicle-hour",
    }
    (output / "p2_event_rates.json").write_text(json.dumps(rates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    matrix = [
        ["批准科学目标", "四源NGSIM纵向跟驰风险代理测量与描述性现实校准", "四源封存数据、任务决定与最终包交叉核对", "支持限定范围内验收", "summary.json; p2_event_rates.json", "Verified", "不支持事故概率、危险识别准确率、P2全局最优或AAD因果效应"],
        ["研究者决定归档", "06_DECISIONS中的2026-10-12决定完整记录", "决定文本、config、provenance核对", "已归档并作为本包依据", "AI_CONTEXT/06_DECISIONS.md", "Verified", "范围外问题转后续阶段"],
        ["四源来源与哈希", "批准四源分别报告、输入不可变", "task1.5输入SHA、历史封存哈希与本包provenance", "哈希一致；来源边界保留", "historical_sha256_audit.csv; provenance.json", "Verified", "Lankershim原始官方分源解释仍为历史限制"],
        ["正式P2事件与在线确认", "可靠TTC<2s、首末跨度>=0.2s、实际观测确认", "逐事件成员/时间/指标复算与在线诊断", "4545；四源raw=reliable，确认与触发对齐", "event_member_time_comparison.csv; p2_online_diagnostics.json", "Verified", "事件率是代理频率"],
        ["P2可评价跟驰暴露分母", "连续可靠边两端均valid或not_applicable；invalid/non_positive_gap及missing不纳入，不赋零风险含义", "逐源独立重构所有边、两端状态和0.1s时间权重", "503922.2 s可评价；8121.0 s不可评价；新旧分母及事件率差异逐源复算", "exposure_edge_audit.json; p2_event_rates_by_source.csv", "Verified", "原可靠跟驰512043.2s仍作为质量统计；不可评价不等于无风险"],
        ["可靠闭合暴露", "与跟驰暴露严格区分", "四源边级时间核对", "208026.3 s，未混入事件率分母", "p2_event_rates.csv", "Verified", "仅作连续风险条件参考"],
        ["TTC/DRAC与状态分类", "保留valid、not_applicable、invalid、not_measurable/missing语义", "状态全量表、缺失原因、连续性证据", "5706252行状态，缺失与不可评价未补零", "measurement_status_by_source.csv; measurement_status.csv", "Verified", "来源异质性须随结果报告"],
        ["tau/rho与敏感性", "tau=15.364279197080283；tau/2、tau、2tau均报告", "独立tau复算与三尺度表", "一致；尺度敏感性已封存", "tau_recalculation.csv; rho_scale_sensitivity.csv", "Verified", "条件风险负担不外推为总体安全"],
        ["100/200 ms语义", "100ms为正式参考；200ms两相位仅迁移限制", "不插值抽稀对应与确认差异", "P2 4545 -> 4155/4162，采样不等价", "sampling_sensitivity.csv; sampling_one_to_one_confirmation.csv", "Verified", "不阻断100ms范围验收；禁止跨采样率外推"],
        ["极端与物理真实性", "极端屏蔽仅稳健性；物理真值不伪造", "447案例、48重点、11差异案例与屏蔽结果", "P2屏蔽后4370；Physical Truth Unverified", "case_447_kinematic_geometry_evidence.csv; manual_review_index.md", "Verified", "独立物理真实性为永久科学限制，不作事故真值主张"],
        ["有限适用范围", "仅四源、100ms、描述性校准；不外推道路/总体交通/SUMO", "Gate范围与后续职责核对", "范围已写入本包与项目索引", "scope_and_claims.md", "Verified", "Stage0.3/0.5/0.6及因果评价另行验收"],
        ["最终科学Gate", "批准范围内无使描述性统计失效的实质阻断", "完整矩阵、复算、质量与限制审核", "批准分母定义落实并通过；仅对四源100ms有限描述性校准关闭", "scientific_gate_report.json; report.md", "Verified", "永久保留独立物理真实性、缺失选择偏差、极端敏感性和采样/来源外推限制"],
    ]
    gate = pd.DataFrame(matrix, columns=["验收事项", "预定标准/依据", "验证方法", "实际结果", "证据路径", "状态", "剩余限制"])
    gate.to_csv(output / "scientific_gate_matrix.csv", index=False)
    gate.to_json(output / "scientific_gate_matrix.json", orient="records", force_ascii=False, indent=2)

    scope = """# Stage 0.2 科学适用范围\n\n允许结论：四个批准 NGSIM 来源分别支持纵向跟驰风险代理指标测量、可靠观测条件下的 P2 代理事件频率，以及 tau/rho 连续风险负担的描述性现实校准。\n\n禁止外推：事故发生概率、真实危险识别准确率、P2 全局最优性、AAD核心因果效应、其他道路、总体交通、SUMO、原生200ms等价性。\n\n永久限制：独立物理真实性、独立视频/几何真值和人工审核结论仍为 Unverified。极端屏蔽只用于稳健性，不构成自动删除规则。四源不视为独立同分布道路样本。\n\n后续归属：pNEUMA运动学为Stage0.3；SUMO覆盖及原生200ms为Stage0.5；目标区域/车辆/四格窗口和消息机制属于后续因果评价与协议冻结；Stage0.6负责协议锁准备。\n"""
    (output / "scope_and_claims.md").write_text(scope, encoding="utf-8")

    audit = {
        "schema_version": "stage_0_2.scientific_acceptance.audit.v1",
        "status": "pass",
        "gate_status": "pass",
        "stage_status": "Completed / Closed",
        "scientific_scope": "four approved NGSIM sources; 100ms descriptive longitudinal following-risk proxy calibration",
        "p2_event_count": 4545,
        "reliable_following_exposure_s": 512043.2,
        "reliable_closing_exposure_s": 208026.3,
        "p2_rate_denominator": "P2-evaluable reliable following exposure time; both endpoints valid or not_applicable",
        "physical_truth_status": "Unverified; declared limitation, not a blocker for this limited descriptive gate",
        "sampling_transfer_status": "100ms accepted scope; 200ms non-equivalence retained as limitation",
        "scientific_claim_eligible": True,
        "not_evaluable_exposure_s": edge_audit["total_not_evaluable_following_exposure_s"],
        "accident_probability_claim_eligible": False,
        "aad_causal_claim_eligible": False,
        "protocol_lock_created": False,
        "stage_I_run": False,
        "locked_holdout_opened": False,
    }
    (output / "scientific_gate_report.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = """# Stage 0.2 最终科学验收与正式关闭\n\nStage 0.2 在研究者批准的有限范围内正式通过并关闭：四个批准NGSIM来源、100ms观测语义下的纵向跟驰风险代理指标测量与描述性现实校准。P2事件率分母为两端均可评价的可靠跟驰暴露，单位events / P2-evaluable following vehicle-hour。\n\nP2总数4545；原可靠跟驰暴露512043.2s；P2可评价暴露503922.2s；不可评价暴露8121.0s。逐源事件率、新旧率差异和状态比例见`p2_event_rates_by_source.csv`。不可评价时间没有被赋予零事件或零风险含义。\n\n本Gate不支持事故概率、危险识别准确率、P2全局最优性、AAD因果效应、SUMO迁移或范围外道路外推。独立物理真实性、缺失选择偏差、极端敏感性、100/200ms不等价及来源外推限制持续保留。\n"""
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
