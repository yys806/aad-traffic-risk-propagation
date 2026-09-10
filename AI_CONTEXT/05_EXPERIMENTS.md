# AAD Experiments

> 这里只记录客观状态。完整字段以 `docs/PROJECT_REGISTRY.json` 为准，原始数字以 audit/manifest/表为准。

## 当前实验表

| 实验编号 | 实验目的 | config / 变量 | baseline | 数据集 | 主要指标 | 状态 | 客观实验结果 | 输出目录 |
|---|---|---|---|---|---|---|---|---|
| `stage_0_1` | 验证四格、五表与封存链 | seed `2026080701`，dt `0.2 s`，源事件/通道两变量 | 四格内部对照 | SUMO | 处理前等价、隔离、时钟、生命周期、物理路径 | `Verified` 工程层 | 工程检查通过；源/目标双走廊物理不连通，不能形成科学效应 | `code/outputs/formal/stage_0_1/` |
| `stage_0_2` | NGSIM 跟驰风险审计 | 候选 TTC 阈值 `2.0 s`；holdout=false | 无模型 baseline | NGSIM US-101、Lankershim calibration | measurement status、有效 TTC、事件数、TTC/DRAC 分布 | `Active` | v2 旧快照共 4,753,044 state rows、1,797,968 valid-TTC rows、4,758 events；异常和最终范围未收口 | `code/outputs/formal/calibration/stage_0_2_ngsim_v2/` |
| `stage_0_3` | 城市运动学与车型分布 | 仅速度、纵向加速度、车型；禁止 leader/TTC/DRAC | 不适用 | pNEUMA d1 | 分布与分位数 | `Not started` | 原始数据已就位；无新职责下的专用正式结果 | 待创建于 `code/outputs/formal/calibration/` |
| `stage_0_4` | 界定通信可观测证据 | RV_RX 仅作 receive-state continuity；trip 级分割 | 不适用 | SPMD RV_RX | packet schema、latency/loss/adoption 可观测性 | `Verified` 有限边界 | 旧快照：17,481,111 rows、7,601 device-trips；packet schema 未评估，时延/丢包/adoption 未估计 | `code/outputs/formal/calibration/stage_0_4_observability_v3/` |
| `stage_0_5` | 仿真—现实覆盖 | seed `20260907`，稳定哈希，最多每组 5,000 rows | real-real 距离作为参照 | NGSIM、pNEUMA、SUMO | energy distance、stratum coverage | `Active` | 迁移前包含 25,000 kinematics、20,000 following、4,758 events；无 SUMO 样本且需按新分工重建 | `code/outputs/formal/calibration/stage_0_5_real_reference_v1/` |
| `stage_0_6` | 数值验证与协议锁准备 | 科学容差尚未冻结 | 解析真值/物理真值 | 合成真值与前置 Gate | analytic/path truth、方向、时间步、readiness | `Active` / blocked | 技术检查通过；迁移前 readiness 为 `protocol_lock_allowed=false` | `code/outputs/formal/calibration/stage_0_6_prelock_validation_v2/` |
| `stage_1_1` | 核心效应确认 | `not_frozen` | `not_determined` | `not_created` | 尚未确定 | `Agreed` 但 blocked | 未实现、未运行、无结果 | 无 |

## 结果边界

所有当前登记结果均 `scientific_claim_eligible=false`。`evidence/results/` 中的阶段化目录名是便携索引；其中 JSON 内容保持原运行字节，因此仍可能出现旧实验编号或迁移前 Gate 文本，不能把目录重命名误读为重新运行。

## 历史实验

pNEUMA 地图匹配、候选前车和人工 QA 已由研究者批准退役，代码/测试/脚本位于 `legacy/`，完整输出位于 `code/outputs/history/legacy_experiment_ids/`，小型证据位于 `evidence/history/legacy_experiment_ids/`。其他 DRIFT 与传播 Pilot 见 `docs/HISTORY_INDEX.md`。
