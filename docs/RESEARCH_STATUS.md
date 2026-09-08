# AAD 当前科研状态

> 核对日期：2026-09-08。这里是导航摘要；数字和 Gate 以 `PROJECT_REGISTRY.json`、`evidence/` 和本机原始产物交叉核验。

## 当前研究问题

一条来源可追溯且确实被控制器采用的远端风险消息，能否在源扰动的普通物理影响到达目标区域以前，通过改变目标车辆集合动作，改变目标区域总体风险。

Stage I 负责识别并证伪信息介导效应，使用完整四格 intention-to-run 分母；Stage II 只在 Stage I 获得支持后研究风险优化及安全、效率、舒适性代价。当前仍在 Stage I 正式主效应之前。

## 已验证

- E00 四格、五表、运行隔离、统一时钟、车辆生命周期、处理前一致和独立审计有机器证据；它只通过工程 Gate。
- E15-A NGSIM v2 覆盖四个完整窗口并形成事件/TTC 参考；pNEUMA mapmatch v2 已生成候选 leader。
- pNEUMA QA v5 包包含 300 条盲样本、四层各 75、48 条平衡 pilot；包结构和 checksum 可核验。
- E16-A 已确认 RV_RX 有 17,481,111 行、7,601 个 device-trip，且解释边界只能是 `receive_state_continuity_only`。
- E17-A 已形成 25,000 条运动学、20,000 条跟驰和 4,758 条风险事件的部分现实参考。
- E01 的解析 TTC/DRAC/PET/碰撞真值、物理路径真值和时间步方向一致性通过。
- 九项已登记结果的小型 audit/config/manifest/provenance/checksum 快照进入 `evidence/`，可在纯 Git 克隆中校验哈希。

## 正在进行

当前唯一执行任务是 E15-A pNEUMA Round 1 人工地图、方向和候选 leader 审计。研究者先完成 v5 页面默认显示的 48 条 pilot，导出 `pneuma_map_leader_round1_completed.csv`，随后 AI 只读统计并报告 Gate，不更改人工标签。

## 当前机器 Gate

| 项目 | 状态 | 便携证据 |
|---|---|---|
| E00 | `engineering_pass_scientific_fail` | `RES-E00-PRIMARY-V3/e00_report.json` |
| E15-A | `pending_human_round1` | `RES-E15A-PNEUMA-QA-V5/audit.json` |
| E16-A | `pending_official_packet_access` | `RES-E16A-OBS-V3/audit.json` |
| E17-A | `pending_pneuma_manual_and_simulation_sample` | `RES-E17A-REAL-REF-V1/audit.json` |
| E01 | `pending_e15_e17_and_frozen_tolerances` | `RES-E01-PRELOCK-V2/audit.json` |
| protocol lock | `protocol_lock_allowed=false` | `RES-PROTOCOL-READINESS-V1` |
| E02 | `e02_allowed=false` | `RES-PROTOCOL-READINESS-V1` |

所有路径均位于 `evidence/results/`；本机原件位于 `code/outputs/formal/`。

## 尚未确认

- pNEUMA 候选 leader 是否达到人工 Gate，pNEUMA TTC 尚未生成。
- SPMD Packet schema、逐包时延、丢包和 controller adoption；官方资产当前访问返回 HTTP 403。
- E17-A sim-real 覆盖是否通过。
- E01 的 `delta_eq`、`delta_R`、动作/状态容差和 E02 样本量。
- Stage I 主效应是否存在、方向和大小。

## 当前不能声称

- 不能说已发现远距离、类超距或因果信息效应。
- 不能把 E00、真实数据相关性、历史 Pilot 或 calibration seed 写成主效应。
- 不能把消息交付当采用，把采用当动作变化，或把动作变化当风险变化。
- 不能把当前论文称为拥有完整科学结果的最终投稿稿。
- 不能因 Git 内已有摘要就声称大表、原始数据或人工标签已完整远端备份。

## 已确认的继续顺序

1. 完成 48 条人工 pilot，导出 CSV。
2. 保留真实错误和 `uncertain`，只读统计；由研究者判定人工 Gate。
3. Gate 通过后才考虑 pNEUMA TTC 和完整 Round 1/2。
4. 补 E17-A 仿真样本与覆盖 Gate，冻结 E01 科学容差和样本量。
5. 所有必需 Gate 通过后生成并校验不可覆盖的协议锁。
6. 协议锁完成后，另行确认 E02 的设计、实现和运行。

跨控制器、跨风险类型、信息图、通信受损、物理连通、合流、尾部风险和 Stage II 控制优化属于后续计划，不是当前已授权执行面。
