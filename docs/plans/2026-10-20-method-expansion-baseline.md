# 计划与任务基线：AAD-0.5-METHOD-EXPANSION

日期：2026-10-20。结果 `RES-STAGE-0.5-METHOD-EXPANSION-V1`。

## 1. 进入时的真实项目状态（Observation）

| 项 | 值 | 核验方式 |
|---|---|---|
| 远端/本地 HEAD | `be68a13b26a1da3cdd72ad72c34ed504c6ecce8b`（`origin/main` 同步） | `git fetch` + `git rev-parse HEAD origin/main` |
| 最新提交时间 | 2026-10-20 23:36:47 +0800 | `git log` |
| 工作区 | 仅 5 项 `doc/literature-notes/` 既有删除（任务开始前即存在，未处理） | `git status --branch --short` |
| Stage 0.5 Gate | `pending_simulation_sample` | `docs/PROJECT_REGISTRY.json`、`AI_CONTEXT/00_PROJECT_STATE.md` |
| `scientific_claim_eligible` / `reality_coverage_accepted` / `protocol_lock_allowed` / `stage_1_1_allowed` | 全部 `false` | 同上 |
| 科学容差 δ / 精度 h | `Tolerance Not Yet Justified` | `RES-STAGE-0.5-FINAL-CLOSURE-V1/delta_h_basis_audit.json` |
| 校准窗口 | `us101__0750_0805`（clock [120,840)）、`us101__0805_0820`（clock [180,840)） | 见下 |
| 状态表 SHA | `684a5f0b96dc4811…`（1,180,598 行）与 `7b0ef830c97a981d…`（1,403,095 行） | `source_audit.json` |
| 第三窗口 / holdout | 本次读取 0 行 / 0 次 | `source_audit.json` |

## 2. 预算台账（Observation）

| 台账 | 授予 | 实际执行 | 保留未用 |
|---|---|---|---|
| `RES-STAGE-0.5-FINAL-CLOSURE-V1`（D5） | 最多 5 次：≤3 构造 + ≥2 独立 seed 重复 | FC1、FC2 | FR1、FR2（**不转移**） |
| `RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1` | 3 构造 + 2 保留重复 | RC1、RC2、RC3 | RC1r、RC2r（**不转移**） |
| `RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1` | 48 次微型重放 | 43 组合 | — |
| **本任务** | 见 `response_plan.json`（324 次）+ 初始化 24 次 + Newell 24 次（离线） | 逐项写入 `response_summary.json` / `init_summary.json` | — |

本任务不继承、不占用任何既有预留额度。

## 3. 可直接复用与不可直接复用的模块

**可直接复用**：`stage_0_5_leader_replay`（重放、Brockfeld/NRMSE、配对 bootstrap）、`stage_0_5_jam_definition`（状态定义族、零模型）、`stage_0_5_trajectory_reconstruction`（canonical 加载、几何、边界流量、时空面）、`stage_0_5_scene_reconstruction`（观测几何网络、FCD 解析）、`export_project_evidence.py`、`project_docs.py`。

**不可直接复用及其原因**：
- `stage_0_5_final_closure`：其运行计划守卫把构造运行上限写死为 3、并要求 ≥2 次独立重复；本任务的诊断目录结构与其自由度不同，故只借用其地区域定义与误差判据语义，不借用其计划守卫。
- `stage_0_5_b12_*` / `cd_*`：数字与队列契约针对固定边界机制场景，与微观重放无关。
- `stage_0_5_scene_reconstruction` 的宏观场景：保留但不在本任务重跑（见 Phase 5 判定）。

**已知实现缺陷（上一任务遗留并已修复）**：`setSpeed` 持久覆盖后车速度、前车每样本领先、时钟错一拍；本任务开始时这三项已修复并有回归测试。**本任务新发现**：插入失败被误判为"永久拒绝"（实为延迟插入），见 `docs/STAGE_0_5_INITIALIZATION_FIDELITY.md`。

## 4. 假设矩阵（H1–H6）与判别设计

| 假设 | 判别实验 | 本任务阶段 |
|---|---|---|
| H1 轨迹/状态支持不足 | 行为阶段覆盖矩阵（时长、速度变化、低速、贴近、减速、闭合） | `coverage` |
| H2 初始化与插入检查造成假性错配 | 两条受验证的初始化路线 + 前车保真度与首步连续性核验 | `init` |
| H3 跟驰模型结构/参数不适合 | 单因素有界目录 + IDM + Newell 原型，同输入同指标 | `response`、`newell` |
| H4 随机性与参数效应混杂 | 同一 seed 集跨配置 + 每配置 3 seed + `sigma=0` 界 | `response` |
| H5 单车行为与宏观拥堵传播存在落差 | 局部窗 vs 长期窗分离 + 扰动传播（幅值比、滞后） | `response` |
| H6 需求/供给/结构造成错配 | 宏观对照（门控；本任务未执行，见 `macro_decision.json`） | `macro` |

## 5. 执行顺序与停止规则

1. 先做离线（文献、覆盖、可辨识性），再做微型试点，再扩大。
2. 每个批次运行前写冻结计划与 SHA；失败保留并转向。
3. 停止：前车跟随偏差超容差、SHA 不匹配、插入未在声明等待窗内完成、资源风险。
4. 不做 `tau` 网格搜索、不联合调参、不按 P2 选样本、不以插入检查失败自动夹取后再混入原始结果。

## 6. 硬边界

不访问第三窗口/holdout；不修改 Stage 0.2 事件定义、身份/时钟/质量语义、分母；不写 Gate/协议锁；不启动 Stage 1.1/ABCD；不改官方 SUMO 二进制；不改 `AGENTS.md`。
