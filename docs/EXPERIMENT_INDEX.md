# AAD 实验索引

> 最后核对：2026-09-08  
> 状态词遵循 `AGENTS.md`。实验代码存在不等于完整 Gate 或科学结论通过。

## 当前正式实验

### E00 — 基础设施与测量链验证

- 问题：四格运行、五表封存、运行隔离和独立复算链是否可靠。
- 日期：主包运行完成于 2026-09-07（本地时区日期；provenance 记录 UTC 时间）。
- 状态：`Verified`，仅工程 Gate。
- 代码：`code/src/riskprop/formal_*.py`、`sumo_e00.py`、`upstream_adapter.py`。
- 代码版本：Git `eb1bb0a`，运行时工作树为 dirty；provenance 另记录关键实现 SHA-256，不能只靠 commit 复原。
- 入口：`code/scripts/run_e00_sumo.py`、`analyze_e00_sumo.py`、`compare_e00_sumo_runs.py`。
- 配置/参数：seed `2026080701`，四格 `s0c0/s0c1/s1c0/s1c1`，时间步0.2秒，处理起点2秒，窗口0–32秒；以每个 cell 的 `config_frozen.json` 为准。
- 数据：AAD 内 SUMO `dual_corridor_sumo_minimal` 五表；模型/checkpoint：不适用。
- 主要结果：`RES-E00-PRIMARY-V3`、`RES-E00-ENV-COMPARE-V3`。
- 核心指标：处理前等价、消息生命周期、运行隔离、时间对齐、车辆生命周期、物理路径状态和双环境结构一致性。
- 结论边界：`scientific_claim_eligible=false`，不能证明信息介导效应。

### E15-A — 真实轨迹风险测量

- 问题：TTC/DRAC 等风险尺子能否在 NGSIM 与 pNEUMA 上得到可审计支持。
- 日期：当前 v2/v5 产物形成于 2026-09-07；v5 audit 记录创建时间。
- 状态：`Active`，当前唯一执行面是 pNEUMA 人工 Round 1。
- 代码：`real_trajectory.py`、`e15a.py`、`pneuma_mapmatch.py`、`pneuma_qa.py`。
- 代码版本：当前实现位于 dirty 工作树；精确复现依赖输入 SHA-256、审计包和当前实现文件，不得只写 Git HEAD。
- 入口：`run_e15a_ngsim.py`、`run_e15a_pneuma_mapmatch.py`、`prepare_pneuma_manual_qa.py`。
- 配置/参数：QA seed `20260907`，总样本300，四层各75，试标每层12，共48；邻域50米、轨迹窗口1秒。
- 数据：NGSIM 四个完整窗口；pNEUMA v2 地图匹配候选；v5 人工 QA 包。模型/checkpoint：不适用。
- 主要结果：`RES-E15A-NGSIM-V2`、`RES-E15A-PNEUMA-MAPMATCH-V2`、`RES-E15A-PNEUMA-QA-V5`。
- 核心指标：有效 TTC 行数、风险事件数、地图匹配状态、候选前车比例、人工 map/direction/leader 一致性与 uncertain 比例。
- 当前 Gate：`pending_human_round1`；人工通过前不生成 pNEUMA TTC。

### E16-A — 真实通信可观测性

- 问题：SPMD 现实字段能够直接支持哪一层消息链结论。
- 日期：当前 v3 audit 创建于 2026-09-07 UTC。
- 状态：`Active / external-blocked`。
- 代码：`e16a.py`。
- 代码版本：当前 dirty 工作树；数据身份由 audit 内 SHA-256 绑定。
- 入口：`profile_e16a_rv_rx.py`、`run_e16a_observability.py`。
- 配置/参数：按 calibration trips 统计 RV_RX 接收连续性；模型/checkpoint：不适用。
- 数据：calibration RV_RX；官方 Packet 当前访问返回 HTTP 403。
- 主要结果：`RES-E16A-OBS-V3`。
- 核心指标：RV_RX 行数、device-trip 数、Packet schema/latency/loss/adoption 是否可观测。
- 结论边界：当前只支持 `receive_state_continuity_only`，不能估计丢包、时延或 adoption。

### E17-A — 仿真现实覆盖

- 问题：后续仿真是否覆盖真实交通状态，而非只覆盖容易成功的样本。
- 日期：当前 v1 audit 创建于 2026-09-07 UTC。
- 状态：`Active`。
- 代码：`e17a.py`。
- 代码版本：当前 dirty 工作树；每个现实参考输入由 audit 中 SHA-256 绑定。
- 入口：`prepare_e17a_real_reference.py`、`run_e17a_coverage.py`。
- 配置/参数：seed `20260907`，每个完整 site/window 最多5,000条稳定哈希样本。
- 数据：NGSIM 与 pNEUMA 现实参考；pNEUMA TTC 明确排除。模型/checkpoint：不适用。
- 主要结果：`RES-E17A-REAL-REF-V1`。
- 核心指标：运动学、跟驰和风险事件样本量；后续 sim-real 覆盖指标尚未形成通过结果。
- 当前 Gate：`pending_pneuma_manual_and_simulation_sample`。

### E01 — 预锁测量与路径验证

- 问题：指标实现、物理路径判定和时间步是否满足冻结前的正确性要求。
- 日期：当前 v2 audit 创建于 2026-09-07 UTC。
- 状态：`Active`。
- 代码：`e01_metrics.py`、`e01_validation.py`、`protocol_lock.py`。
- 代码版本：当前 dirty 工作树；真值案例和审计 schema 由 v2 包记录。
- 入口：`run_e01_prelock_validation.py`、`check_protocol_lock_readiness.py`。
- 配置/参数：时间步0.1/0.05/0.02/0.01秒；`delta_eq`、`delta_R` 和零效应容差尚未冻结。
- 数据：解析运动学/路径真值 fixture；模型/checkpoint：不适用。
- 主要结果：`RES-E01-PRELOCK-V2`、`RES-PROTOCOL-READINESS-V1`。
- 核心指标：TTC/DRAC/PET/碰撞匹配、四类路径状态匹配、时间步方向一致性与相邻步长差值。
- 当前 Gate：解析真值通过，但容差与样本量尚未冻结。

### E02 — Stage I 主效应

- 问题：协议锁定后的四格主效应是否支持信息介导的非最近邻风险影响。
- 日期：未启动，无实验日期。
- 状态：`Agreed pending / blocked`；未启动。
- 前置条件：E15-A、E16-A、E17-A、E01 和 `protocol_lock_v1.1` 全部满足。
- 当前准入：`e02_allowed=false`。
- 代码版本、配置、参数、数据、模型/checkpoint、结果和指标：尚未形成可执行冻结入口，不得由索引推断。

## 后续阶段计划

| 阶段 | 实验编号 | 当前证据状态 |
|---|---|---|
| 阶段 1 | E02–E04 | 计划框架；E02 被 Gate 阻断 |
| 阶段 2 | E05–E08 | `Proposed/Agreed plan`，非当前执行面 |
| 阶段 3 | E09–E10 | `Proposed/Agreed plan`，非当前执行面 |
| 阶段 4 | E11–E13、E15–E17 | 部分 calibration 子实验 Active，其余为计划 |
| 阶段 5 | E14、E18–E19 | `Proposed/Agreed plan`，依赖 Stage I |
| 阶段 6 | 全文复算 | 依赖所有科学与论文 Gate |

## 历史实验

这些内容可回答“是否尝试过”，但不能覆盖当前协议或直接进入正式 Results：

| 历史主题 | 输出入口 | 状态 |
|---|---|---|
| DRIFT 可用性审计 | `code/outputs/drift_qualification_20260716/` | `Historical` |
| 风险事件数据集 | `code/outputs/risk_event_dataset_20260716/` | `Historical` |
| 局部传播基线 | `code/outputs/local_propagation_baseline_20260718/`、`local_propagation_baseline_drift_20260719/` | `Historical` |
| Nonlocal Pilot A | `code/outputs/nonlocal_pilot_a_20260726/` | `Historical` |
| Nonlocal Pilot B 及两个 corrected 变体 | `code/outputs/nonlocal_pilot_b_20260802*/` | `Historical`；版本差异需读各 summary 与旧交接 |
| 更早 Pilot/feasibility | `code/outputs/pilot_20260714/`、`code/outputs/feasibility_week/` | `Historical` |

对应代码、命令和测试分别位于 `code/src/riskprop/legacy/`、`code/scripts/legacy/` 和 `code/tests/legacy/`；历史判断从 `code/README.md`、`记录/README.md` 和 `docs/归档/` 追溯。

## 新增实验时必须补充

实验 ID、研究问题、日期、状态、代码、配置、参数、数据版本、模型/checkpoint（如适用）、结果 ID、Gate、结论边界和失败记录；随后同步 `PROJECT_REGISTRY.json` 与 `RESEARCH_STATUS.md`。
