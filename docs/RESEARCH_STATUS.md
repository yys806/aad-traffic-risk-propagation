# AAD 当前科研状态

> 最后核对：2026-09-08  
> 导航摘要，不替代各 `audit.json`、配置、原始表和复算结果。

## 当前研究问题

一条来源可追溯且确实被控制器采用的远端风险消息，能否在源扰动的普通物理影响到达目标区域之前，通过改变目标车辆集合的动作，改变目标区域总体风险。

## 两个科学阶段

- Stage I：识别并尝试证伪信息介导效应，必须使用完整四格的 intention-to-run 分母，不能按处理后的 adoption 或动作分化筛选样本。
- Stage II：仅在 Stage I 获得支持后，研究如何降低平均与尾部风险，并约束安全、效率和舒适性代价。

当前仍处于 Stage I 正式主效应实验前的测量和协议锁定阶段。

## 已验证

- E00 真实 SUMO 四格、五表、运行隔离、统一时钟、车辆生命周期、处理前一致和独立路径审计已形成机器证据。
- E00 只属于工程与测量基础设施 Gate，所有相关产物均为 `scientific_claim_eligible=false`。
- E01 的解析 TTC/DRAC/PET/碰撞真值以及物理路径真值 fixture 当前通过。
- E15-A NGSIM v2 已覆盖四个完整输入时间窗并形成状态/事件审计包。
- v5 pNEUMA 人工 QA 包已生成：300条盲样本，四层各75条，默认48条平衡试标。

## 正在进行

当前唯一执行任务是 E15-A pNEUMA Round 1 人工地图、方向和候选前车审计。先完成 v5 页面默认显示的48条试标，导出 `pneuma_map_leader_round1_completed.csv` 后再做只读统计和 Gate 判断。

## 当前机器 Gate

| 项目 | 状态 | 直接证据 |
|---|---|---|
| E15-A | `pending_human_round1` | `e15a_pneuma_manual_qa_v5/audit.json` |
| E16-A | `pending_official_packet_access` | `e16a_observability_v3/audit.json` |
| E17-A | `pending_pneuma_manual_and_simulation_sample` | `e17a_real_reference_v1/audit.json` |
| E01 | `pending_e15_e17_and_frozen_tolerances` | `e01_prelock_validation_v2/audit.json` |
| protocol lock | `protocol_lock_allowed=false` | `protocol_lock_readiness_v1.json` |
| E02 | `e02_allowed=false` | `protocol_lock_readiness_v1.json` |

## 尚未确认

- pNEUMA 候选前车关系是否达到人工 Gate；当前 `leader_relations_validated=false`。
- pNEUMA TTC；当前 `ttc_generated=false`，不得提前生成。
- SPMD Packet schema、逐包时延、丢包和 controller adoption；当前 RV_RX 只支持接收状态连续性。
- E17-A sim-real 覆盖是否通过。
- E01 的 `delta_eq`、`delta_R`、动作/状态容差和 E02 样本量。
- Stage I 主效应是否存在、方向和大小。

## 当前不能声称

- 不能说已发现远距离或类超距因果作用。
- 不能把 E00、真实数据相关性、历史 Pilot 或 calibration seed 写成主效应成立。
- 不能把消息交付当成控制器采用，也不能把采用当成动作或风险变化。
- 不能把当前论文称为具有完整科学结果的最终投稿稿。

## 已约定的继续顺序

1. 完成 v5 的48条人工试标并导出 CSV。
2. 保留真实错误和 `uncertain`，只读统计；不由 AI 改人工标签。
3. 人工 Gate 通过后才考虑 pNEUMA TTC 和完整 Round 1/2。
4. 补齐 E17-A 仿真样本与覆盖 Gate，并冻结 E01 容差。
5. 所有必需 Gate 通过后生成并校验协议锁。
6. 协议锁完成后，另行设计和运行 E02。

## 候选但非当前任务

跨控制器、跨风险类型、信息图、通信受损、物理连通、合流、尾部风险和 Stage II 控制优化已经出现在阶段计划中，但不属于当前执行面，不能因建立索引而视为已经获准执行。
