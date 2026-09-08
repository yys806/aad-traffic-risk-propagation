# AAD 实验索引

> 核对日期：2026-09-08。机器事实源为 `PROJECT_REGISTRY.json`；本页负责给人阅读。实验代码存在不等于 Gate 或科学结论通过。

## 当前顺序

`E00 工程底座 → E15-A / E16-A / E17-A 现实校准 → E01 协议锁定前验证 → 协议锁 → E02`。

当前唯一执行面是 E15-A 的 48 条 pNEUMA 人工 Round 1 pilot。E16-A 等待外部 Packet 访问；E17-A 与 E01 等待上游 Gate；E02 尚未实现且被机器规则阻断。

## E00 — SUMO 四单元工程链路验收

- 目的：验证状态隔离、统一时钟、车辆生命周期、五表封存和独立复算。
- 代码/入口/测试：`sumo_e00.py`；`run_e00_sumo.py`、`analyze_e00_sumo.py`、`compare_e00_sumo_runs.py`；`test_sumo_e00.py`、`test_formal_artifacts.py`。
- 配置与数据：seed `2026080701`，四格，`dt=0.2 s`，窗口 0–32 s；数据版本 `e00_real_sumo_20260907_primary_v3`；无学习模型/checkpoint。
- 结果：`RES-E00-PRIMARY-V3`、`RES-E00-ENV-COMPARE-V3`。
- 状态：工程验收通过；物理发送路径未接通，`scientific_claim_eligible=false`。

## E15-A — 真实轨迹 leader/TTC 校准

- 目的：检查 NGSIM 与 pNEUMA 是否支持可审计的 leader、风险事件和 TTC。
- 代码/入口/测试：`e15a.py`、`pneuma_mapmatch.py`、`pneuma_qa.py`；三个对应运行/准备脚本；真实轨迹、地图匹配和 QA 测试。
- 配置与数据：seed `20260907`，300 条样本、四层各 75、pilot 四层各 12，半径 50 m、窗口 1 s；NGSIM v2、pNEUMA mapmatch v2、manual QA v5。
- 结果：`RES-E15A-NGSIM-V2`、`RES-E15A-PNEUMA-MAPMATCH-V2`、`RES-E15A-PNEUMA-QA-V5`。
- 状态：`pending_human_round1`；人工 Gate 通过前不得生成 pNEUMA TTC。

## E16-A — SPMD 通信可观测性审计

- 目的：区分接收状态连续性与真正的 packet、时延、丢包和采用事件。
- 代码/入口/测试：`e16a.py`；`profile_e16a_rv_rx.py`、`run_e16a_observability.py`；正式设计测试。
- 数据边界：RV_RX 只支持 `receive_state_continuity_only`；官方 Packet 当前访问返回 HTTP 403。
- 结果：`RES-E16A-OBS-V3`。
- 状态：`pending_official_packet_access`；不得推断 packet loss、latency 或 controller adoption。

## E17-A — 真实参考覆盖度审计

- 目的：构建现实参考并检查后续仿真是否只覆盖容易成功的交通状态。
- 代码/入口/测试：`e17a.py`；参考准备与覆盖脚本；正式设计测试。
- 配置与数据：seed `20260907`，每个完整 site/window 最多 5000 条稳定哈希样本；版本 `e17a_real_reference_v1`。
- 结果：`RES-E17A-REAL-REF-V1`。
- 状态：`pending_pneuma_manual_and_simulation_sample`；pNEUMA TTC 尚未纳入。

## E01 — 协议锁定前数值验证

- 目的：验证解析真值、物理路径真值、方向一致性与时间步差异，并阻止未冻结容差进入正式实验。
- 代码/入口/测试：`e01_metrics.py`、`e01_validation.py`、`protocol_lock.py`；预锁验证与 readiness 脚本；正式设计与协议锁测试。
- 配置：时间步 0.10/0.05/0.02/0.01 s；`zero_tolerance=null`，科学容差未冻结。
- 结果：`RES-E01-PRELOCK-V2`、`RES-PROTOCOL-READINESS-V1`。
- 状态：技术真值检查通过，但 `protocol_lock_allowed=false`、`e02_allowed=false`。

## E02 — 核心效应确认实验

- 目的：在冻结协议和有效校准下估计通信采用对风险传播的核心效应。
- 状态：`agreed_pending_blocked`；尚未实现、未运行、无结果。
- 前置条件：E15-A、E16-A、E17-A、E01 以及协议锁全部满足。
- 禁止：不得跳过 Gate 创建 E02 入口、配置、样本量或结果。

## 维护规则

新增实验时，先给出研究者确认的 ID、研究问题和 Gate，再同步注册表、本索引、结果索引与研究状态。必须记录代码路径、入口、测试、代码版本、配置、参数、数据版本、模型/checkpoint、结果 ID、核心指标、结论边界和失败记录。历史探索统一进入 `HISTORY_INDEX.md`，不得伪装成当前实验。
