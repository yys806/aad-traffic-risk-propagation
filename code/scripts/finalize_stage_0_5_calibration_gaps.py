"""Assemble small, reviewable A+ evidence; never approves scientific settings."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"code/src"))
from riskprop.stage_0_5_calibration_gaps import RESULT_ID, seal_package
from riskprop.stage_0_5_calibration_readiness import _sha256_file, _write_json, _utc_now

REPORT="docs/STAGE_0_5_TASK_0_5_4A_SUPPLEMENT_CALIBRATION_GAPS.md"


def read(path): return json.loads(path.read_text(encoding="utf-8"))


def assemble(diagnostic: Path, benchmark: Path, output: Path):
    if output.exists(): raise ValueError("refusing to overwrite final evidence")
    output.mkdir(parents=True)
    for name in ["config.json","audit.json","access_audit.json","source_manifest.json",
                 "diagnostics.json","unified_strata.json","boundary_sensitivity.json"]:
        shutil.copy2(diagnostic/name,output/name)
    for name in ["benchmark_plan.json","benchmark_summary.json"]:
        shutil.copy2(benchmark/name,output/name)
    b=read(output/"benchmark_summary.json")
    runs=b["results"]
    configs={r["id"]:read(benchmark/r["id"]/"config.json") for r in runs}
    _write_json(output/"benchmark_configs.json",configs)
    numerical=[]
    # This inspects only new engineering states, not any real-data source.
    for r in runs:
        p=benchmark/r["id"]
        f=pd.read_parquet(p/"state.parquet",columns=["vehicle_id","time_s","edge_id",
            "longitudinal_position_m","speed_mps","acceleration_mps2","measurement_status","net_gap_m"])
        local=f[f.edge_id.eq("main_1")&f.longitudinal_position_m.ge(50)&f.longitudinal_position_m.lt(250)&f.time_s.ge(60)]
        planned={v.attrib["id"] for v in ET.parse(p/"demand.rou.xml").getroot().findall("vehicle")}
        observed=set(f.vehicle_id)
        missing=planned-observed
        diffs=f.sort_values(["vehicle_id","time_s"]).groupby("vehicle_id").time_s.diff().dropna()
        numerical.append(dict(id=r["id"],state_vehicles=len(observed),
            unserved_initial_vehicles=sum(v.startswith("initial_") for v in missing),
            unserved_inflow_vehicles=sum(v.startswith("inflow_") for v in missing),
            cadence_max_abs_error_s=float((diffs-.1).abs().max()),
            local_low_speed_share_below_5_mps=float(local.speed_mps.lt(5).mean()),
            acceleration_range_mps2=[float(f.acceleration_mps2.min()),float(f.acceleration_mps2.max())],
            invalid_measurement_rows=int(f.measurement_status.eq("invalid").sum()),
            missing_measurement_rows=int(f.measurement_status.eq("missing").sum()),
            raw_state_sha256=_sha256_file(p/"state.parquet"),
            numerical_comparability="not a convergence experiment; SUMO auto-enabled ballistic on .05s/action .1s runs, .1s integration not explicitly fixed"))
    _write_json(output/"benchmark_numerical_diagnostics.json",dict(runs=numerical,
        warning="Action step length '0.10' is used ... step-method.ballistic was not set. Setting it now to avoid collisions.",
        affected_runs=[r["id"] for r in runs if r["internal_step_s"]==.05],
        consequence="cost comparison only; a future numerical sensitivity must explicitly hold integrator, actionStepLength and sigmaStep fixed"))
    main=[r for r in runs if r["internal_step_s"]==.05]
    worst=max(r["wall_s_per_simulated_s"] for r in main)
    worst_bytes=max(r["output_state_bytes"]/r["simulated_s"] for r in main)
    example_duration=660+120
    budget=dict(status="Proposal",measured_pipeline_only=True,full_p2_pipeline_cost_verified=False,
        worst_wall_s_per_simulated_s=worst,evaluation_s_candidate=660,warmup_s_approved=None,
        formula="wall_s = (evaluation_s + W) * worst_cost; W is not yet justified",
        illustrative_W_s=120,illustrative_W_is_not_a_warmup_recommendation=True,
        example_run_wall_s=example_duration*worst,example_3seed_single_load_s=example_duration*worst*3,
        example_3seed_3load_config_s=example_duration*worst*9,
        example_9configs_3seed_3load_hours=example_duration*worst*81/3600,
        example_9configs_headroom_factor_2_hours=example_duration*worst*81*2/3600,
        example_state_bytes_per_run=worst_bytes*example_duration,
        example_81run_state_bytes=worst_bytes*example_duration*81,
        proposed_initial_max_configurations=9,configuration_count_is_not_authorization=True,
        abort_conditions=["collision or teleport", "state cadence/identity/conservation failure", "unbounded pending/initialization accumulation", "5 min benchmark wall cap", "approved memory/storage budget exceeded"],
        recommendation="approve only a bounded next-stage pilot or exploratory batch; benchmark does not justify a full formal-calibration/P2 budget")
    _write_json(output/"cost_budget_proposal.json",budget)
    protocol=dict(status="Proposal",approved=False,network="generic_highway_candidate",
        real_space=dict(y_m=[150,350],lanes=[1,2,3,4,5],denominator_lane_km=1.),
        sumo_space=dict(edge="main_1",lane_position_m=[50,250],lanes=3,denominator_lane_km=.6),
        density_thresholds_veh_km_lane=read(output/"unified_strata.json")["thresholds_veh_km_lane"],
        comparison="mainline per-lane flow plus local speed/density/following; not full-network equivalence",
        fleet="per-window source-scoped empirical class/annotated-length constraints; mapping pending",
        initial_free_parameters=dict(tau=dict(initial=1,range=[.5,2],response_points=[.5,1,2]),
            minGap=dict(initial=2.5,range=[1,3],response_points=[1,2.5,3])),
        parameter_ranges_status="engineering response brackets around official defaults, not empirical confidence or approved scientific bounds",
        extension_parameters=["accel then decel separately", "sigma sensitivity"],
        fixed_initial_parameters=dict(carFollowModel="Krauss",accel=2.6,decel=4.5,
            apparentDecel=4.5,emergencyDecel=9,sigma=.5),
        desired_speed_identifiability="Unresolved in constrained traffic; benchmark cap is not a calibrated desired speed",
        time=dict(internal_step_s=.05,recorded_step_s=.1,actionStepLength=.1,sigmaStep=1,
            integration_method="must explicitly choose and approve; no numerical equivalence claim",warmup_s=None,
            evaluation_s_candidates=[720,660],common_evaluation_s_candidate=660),
        tolerance={k:"Tolerance Not Yet Justified" for k in ["speed","acceleration","net_gap","closing_speed","p2_event_rate","flow","density","low_speed_fraction"]},
        local_stratum_p2="Unresolved; complete event membership/boundary policy not approved",
        recommendation="Path B: bounded exploratory response/deviation diagnostics, pending researcher authorization",
        path_A="only after domain, P2 mapping, model tolerances, timing and budget approved",
        paths_started=[],ready_to_start_stage_0_5_4b=False,reality_coverage_accepted=False)
    _write_json(output/"candidate_protocol.json",protocol)
    audit=read(output/"audit.json")
    audit.update(engineering_runs=len(runs),engineering_runs_completed=sum(r["status"]=="completed" for r in runs),
        engineering_ready="conditional: high local density runnable; insertion backlog and startup anomaly retained",
        measurement_ready="pending researcher limited P2-adapter approval",
        calibration_ready=False,reality_coverage_accepted=False,full_p2_pipeline_cost_verified=False)
    _write_json(output/"audit.json",audit)
    config=read(output/"config.json")
    config.update(boundary_policy=read(output/"unified_strata.json")["boundary_policy"],
        benchmark_plan_sha256=_sha256_file(output/"benchmark_plan.json"),
        actual_time_and_vehicle_config="benchmark_configs.json",candidate_scientific_config="candidate_protocol.json")
    _write_json(output/"config.json",config)
    files=[ROOT/"code/src/riskprop/stage_0_5_calibration_gaps.py",
        ROOT/"code/src/riskprop/stage_0_5_sumo.py",ROOT/"code/src/riskprop/ngsim_risk_calibration.py",
        ROOT/"code/src/riskprop/formal_risk_measurement.py",ROOT/"code/scripts/run_stage_0_5_calibration_gaps.py",
        ROOT/"code/scripts/benchmark_stage_0_5_calibration_loads.py",Path(__file__)]
    _write_json(output/"provenance.json",dict(result_id=RESULT_ID,created_at_utc=_utc_now(),
        diagnostic_provenance=read(diagnostic/"provenance.json"),
        benchmark_environment=b["environment"],code_sha256={str(p.relative_to(ROOT)).replace("\\","/"):_sha256_file(p) for p in files},
        local_diagnostic_package=str(diagnostic),local_benchmark_package=str(benchmark),
        source_package_sha256={str(p):_sha256_file(p) for p in [diagnostic/"manifest.json",benchmark/"manifest.json"]},
        source_manifest_sha256=_sha256_file(output/"source_manifest.json"),scientific_claim_eligible=False))
    _write_json(output/"test_record.json",dict(focused_regression=dict(passed=99,wall_s=38.75),
        initial_focused_interruption="stalled SUMO --version process killed; independent bounded probes succeeded; rerun passed",
        complete_test_first_failure="new module absent before implementation",full_suite="pending final verification",
        clone_verification="pending after commit",context_consistency_check="affected context and indices updated; no Approved Decision added"))
    parts=["\n## 11. 工程实测结果与预算\n",
        "SUMO 1.26.0，Windows 11，Python 3.13.5。四次均完成300s；下表密度/速度/通行率用预声明的工程摘要窗。峰值为20ms采样的Python＋本次子进程RSS，可能低于真实瞬时峰值。\n",
        "|运行|配置/进入/驶出/结束在场|末时未插入|峰值等待|实际局部密度|局部均速m/s|有效驶出veh/h|墙钟s|秒/模拟秒|峰值MB|状态行|状态MB|\n|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"]
    for r in runs:
        parts.append(f'|{r["id"]}|{r["configured_vehicles"]}/{r["departed_vehicles"]}/{r["arrived_vehicles"]}/{r["present_at_end"]}|{r["insertion_unserved_at_end"]}|{r["max_pending_vehicles"]}|{r["evaluation_achieved_density_veh_km_lane"]:.3f}|{r["evaluation_local_mean_speed_mps"]:.3f}|{r["evaluation_achieved_exit_flow_veh_h"]:.0f}|{r["wall_s"]:.2f}|{r["wall_s_per_simulated_s"]:.4f}|{r["memory"]["sampled_combined_rss_bytes"]/1e6:.1f}|{r["output_rows"]:,}|{r["output_state_bytes"]/1e6:.2f}|\n')
    parts += ["\n未插入指计划时刻早于结束但在本次有限窗口仍未进入，不能等同于SUMO永久拒绝。它们没有被删去或通过降低需求消除。进入−驶出−结束在场守恒残差四次均0；碰撞车辆0、teleport0；评价窗路上速度<0.1m/s的车辆最大数0、未出现持续停车式gridlock。边界等待队列存在，不能将其描述成零插入失败。\n",
        "\n0.05s运行均收到SUMO自动启用ballistic的提示；0.1s对照未显式固定积分器，故两者只可作工程成本对照，不能据此声称数值等价或收敛。未来正式数值敏感性须显式保持积分方式、action/sigma时钟相同。\n",
        "\n高层60s分段密度约43.84→53.87→30.96→67.96→66.25，网络平均在场数约140→159→193→213→234。交通加载与积压仍有初始化影响；平均密度达到目标附近不代表暖机充分，也没有复现真实停走波。没有据此延长/降低/重跑负载。各运行更多数值和初始/流入未插入分解见benchmark_numerical_diagnostics。\n",
        f'\n以最慢主基准 {worst:.4f} s/模拟秒作线性预算：单次成本≈(660+W)×{worst:.4f}s。**仅作预算示例**取W=120s（不是暖机建议），单运行约{budget["example_run_wall_s"]/60:.2f}min，单负载3-seed约{budget["example_3seed_single_load_s"]/60:.2f}min，三负载×3-seed每参数配置约{budget["example_3seed_3load_config_s"]/60:.2f}min；9个参数配置81次约{budget["example_9configs_3seed_3load_hours"]:.2f}h，2倍工程余量约{budget["example_9configs_headroom_factor_2_hours"]:.2f}h。按最大实测输出速率，示例单次约{budget["example_state_bytes_per_run"]/1e6:.1f}MB，81次约{budget["example_81run_state_bytes"]/1e9:.2f}GB，仅state，不含其他产物。\n',
        "\n建议初始预算上限9个候选配置，必须先批准；18个配置约翻倍。成本未包含正式全序列P2/评估器，也未证实更长运行的线性外推、3-seed方差或大表后处理内存，因此不能把这份预算标为完整0.5.4-B已验证成本。先批准一项完整链路pilot或受限探索批次。碰撞/teleport、守恒/身份/节奏失败、初始化积压无法消退、超过批准墙钟/内存/存储应提前终止并登记，不改需求抢救成绩。\n",
        "\n## 12. 当前准入结论\n\n|层级|结论|\n|---|---|\n|Engineering Ready|有条件：代表性高局部密度可运行并输出；存在插入积压、启动异常与未测P2全链成本|\n|Measurement Ready|工程缺陷未新增；仍待研究者有限批准0.5.4-A P2适配|\n|Calibration Ready|否：域/分层/事件归属/车型/时间/科学容差/预算未批准|\n|Reality Coverage Accepted|否：未校准、未验证、未通过Stage0.5 Gate|\n\n正式0.5.4-B不能现在自动启动。推荐由研究者选择路径B并明确授权；若选择路径A，先补齐并批准模型偏差容差等必要条件。本任务在此停止。\n"]
    report=(ROOT/REPORT).read_text(encoding="utf-8").split("\n## 11. 工程实测结果与预算")[0]+"".join(parts)
    (ROOT/REPORT).write_text(report,encoding="utf-8",newline="\n")
    (output/"report.md").write_text(report,encoding="utf-8",newline="\n")
    seal_package(output)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostics",type=Path,required=True)
    parser.add_argument("--benchmark",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    assemble(a.diagnostics,a.benchmark,a.output)
