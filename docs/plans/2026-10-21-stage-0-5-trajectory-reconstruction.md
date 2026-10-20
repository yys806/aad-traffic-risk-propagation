# 计划：Stage 0.5 真实交通轨迹与交通过程重建（AAD-0.5-TR-RECON）

日期：2026-10-20（原文误标 2026-10-21，见文末勘误）。结果 `RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1`。

## 目标

回答「为什么 SUMO 能复现真实道路的断面流量却无法复现真实拥堵状态」，并给出有真实证据支撑、或明确标记为条件性的 SUMO 场景，为 Stage 0.6 / Stage 1 降低返工风险。

## 阶段与产出

| 阶段 | 内容 | 产出 |
|---|---|---|
| A | 只读盘点真实数据来源、几何、状态统计 | `lane_geometry.json`、`local_state.json`、`source_audit.json` |
| B | 重建进出、积累、守恒、时空演化、基本图 | `boundary_flows.json`、`conservation.json`、`space_time_60s.csv`、`jam_waves.json`、`fundamental_diagram_30s.csv` |
| B（旁证） | 官方 NGSIM 聚合表独立核对 | `official_crosscheck.json`、`code/configs/stage_0_5_ngsim_official_reference_v1.json` |
| C | 机制诊断与候选解释矩阵 | `capacity_diagnosis.json`、`hypothesis_register.json` |
| D | 依据观测几何 / 边界 / 初始状态重建条件场景 | `code/src/riskprop/stage_0_5_scene_reconstruction.py` |
| E | 运行前冻结的 3 项定向诊断 | `scene_diagnostic_plan.json`、`runs_RC*_summary.json` |
| F | 状态支持判定与失败分类 | `scene_state_support_verdict.json`、`scene_vs_real_congested_branch.json` |
| G | 收口、注册、证据、Git | 本计划的交付 |

## 预算与停止规则（运行前声明）

- 构造 3 次（RC1/RC2/RC3），预留独立 seed 重复 2 次，共 5 次。
- 若 RC2 与 RC3 均未落入真实目标 30 s 块包络 → 停止，报告 Evidence Insufficient，不做参数搜索。
- 任何工程失败（非零退出、teleport、碰撞）→ 停止本批。

## 硬边界

- 不修改 Stage 0.2 风险事件定义、身份 / 时钟 / 质量语义、分母。
- 不读取第三真实窗口 `us101__0820_0835` 或 locked holdout。
- 不写 Gate、不创建协议锁、不启动 Stage 1.1 或 ABCD。
- 不用驾驶行为参数补偿需求 / 供给 / 网络结构错误；行为参数诊断只作 Hypothesis 与 Proposed。
- 历史证据逐字节保留。

## 验证

- `python code/scripts/run_stage_0_5_trajectory_reconstruction.py`
- `python code/scripts/run_stage_0_5_scene_reconstruction.py`
- `python -m pytest tests/test_stage_0_5_trajectory_reconstruction.py tests/test_stage_0_5_scene_reconstruction.py -q`
- `python code/scripts/validate_project_docs.py --strict-git`
- `python code/scripts/export_project_evidence.py --repo-root .`
- `python code/scripts/export_project_evidence.py --repo-root . --verify`

> **日期勘误（2026-10-20）**：本文原标注执行日为 2026-10-21。核对提交时间（`afdc3d0` 的 author/committer date 为 2026-10-20 20:20:17 +08:00）与本地时区（Asia/Shanghai，+08:00）后确认实际执行日为 **2026-10-20**，原标注为撰写时的人工日期错误。文件名与正文按项目惯例保留不改，勘误在此显式登记；详见 `docs/literature/STAGE_0_5_METHOD_EVIDENCE_MAP.md` 文末。
