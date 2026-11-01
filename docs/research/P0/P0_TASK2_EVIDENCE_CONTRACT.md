# P0 Task 2：双传播证据契约

状态：**Proposal**。机器可读字段见 p0_task2_evidence_contract.json；变量级状态表见 p0_task2_variable_dictionary.csv。

## 1. 通用记录规则

每条原始或派生记录必须包含：

- schema_version；
- record_id；
- source_uri、source_row_id 或 source_artifact；
- event_id、vehicle_id、message_id 中适用的关联键；
- clock_id、clock_unit、timestamp；
- observed_vs_derived；
- quality_status；
- missing_reason；
- derivation_version；
- source_sha256。

时间戳使用秒或明确单位；不得把仿真时间、设备 monotonic time、GNSS time 和墙钟时间混在同一列。跨源转换要记录 clock_offset_estimate、同步方法和不确定范围。

quality_status 枚举：OBSERVED、DERIVED、PROXY、MISSING、INVALID、UNOBSERVABLE、NOT_APPLICABLE、UNKNOWN。

缺失、无效、不可观测、不适用和未知不能合并；任何风险聚合不得把它们填零。

## 2. Event Record

| 字段 | 类型 | 必填 | 来源/含义 |
|---|---|---:|---|
| event_id | string | 是 | 源事件稳定键 |
| source_vehicle_id | string | 条件 | 源车辆键；不可观测时保留 Unknown |
| event_time | number | 是 | 统一事件时钟 |
| event_location | object | 是 | 坐标、道路和 lane 的版本化位置 |
| event_type | enum | 是 | 预注册事件类型 |
| event_quality | enum | 是 | 事件识别质量 |
| clock_id / clock_unit | string | 是 | 时钟来源和单位 |
| source_uri / source_row_id | string | 是 | 原始证据定位 |
| source_sha256 | string | 是 | 原始文件/manifest 哈希 |

## 3. Message Record

| 字段 | 类型 | 必填 | 含义 |
|---|---|---:|---|
| message_id | string | 是 | 单个消息版本/实例键 |
| event_id | string | 是 | 源事件外键 |
| sender_id / receiver_id | string | 条件 | 发送和接收车辆/基础设施 |
| generation_time | number | 是 | 生成时间 |
| transmission_time | number | 条件 | 实际发送时间 |
| delivery_time | number | 条件 | 接收端确认时间 |
| verification_time | number | 条件 | 校验完成时间 |
| validation_result | enum | 条件 | valid、stale、invalid、unknown |
| channel_state | enum | 否 | open、closed、degraded、unknown |
| message_version | string | 是 | 内容/规则版本 |
| quality_status / missing_reason | enum | 是 | 字段质量和缺失原因 |

时间顺序校验：generation ≤ transmission ≤ delivery ≤ verification。若其中任一时间不可观测，不以插值替代，相关到达时间为 Unknown。

## 4. Controller Record

| 字段 | 类型 | 必填 | 含义 |
|---|---|---:|---|
| vehicle_id | string | 是 | 控制器所属车辆 |
| message_id | string | 是 | 消息外键 |
| adoption_time | number | 条件 | 采用时间 |
| adoption_status | enum | 是 | adopted、rejected、not_received、not_verified、unknown |
| rejection_reason | enum | 条件 | stale、invalid、unsafe、controller_busy、driver_override、unknown |
| controller_decision | object | 条件 | 决策状态和版本 |
| commanded_action | object | 条件 | 目标速度、加速度、制动或动作命令 |
| controller_clock_id | string | 是 | 控制器时钟 |

delivery、verification、adoption 不能由同一布尔列替代；adopted 也不能由观察到动作反推。

## 5. Vehicle Action Record

| 字段 | 类型 | 必填 | 含义 |
|---|---|---:|---|
| vehicle_id / timestamp | string/number | 是 | 车辆和轨迹时刻 |
| position | object | 是 | 坐标和空间参考 |
| speed / acceleration | number | 条件 | 原始或派生纵向运动 |
| leader_id | string | 条件 | 当前前车键 |
| net_gap | number | 条件 | 定义版本化的净间距 |
| action_change_status | enum | 是 | changed、unchanged、unknown、invalid |
| action_change_rule_version | string | 条件 | 阈值/持续时长规则 |
| trajectory_quality | enum | 是 | 连续性、身份和采样质量 |

## 6. Physical Propagation Record

| 字段 | 类型 | 必填 | 含义 |
|---|---|---:|---|
| event_id | string | 是 | 源事件 |
| physical_witness_id | string | 是 | 独立 witness 或模型路径 |
| source_time | number | 是 | 事件时间 |
| observation_time | number | 是 | 观测时间 |
| physical_state | object | 是 | 速度/密度/间距/风险状态 |
| propagation_status | enum | 是 | arrived、not_arrived、censored、unknown |
| arrival_time | number | 条件 | 物理到达；未知保留空并写原因 |
| reference_condition | enum | 是 | no_message、message_arm、independent_witness、model_counterfactual |
| independence_basis | string | 条件 | 说明为何可称独立/反事实 |

independent_witness 不是自动的 no_message；必须记录 independence_basis。

## 7. Risk Record

| 字段 | 类型 | 必填 | 含义 |
|---|---|---:|---|
| vehicle_id / timestamp | string/number | 是 | 车辆和时间 |
| risk_metric | enum | 是 | 研究者已批准的指标 |
| risk_value | number | 条件 | 数值；无效时为空 |
| validity_status | enum | 是 | valid、invalid、unknown |
| region_id | string | 条件 | 固定区域键 |
| evaluation_window | object | 是 | 起止和版本 |
| exposure_time | number | 条件 | 有效 vehicle-time |
| missing_reason | enum | 条件 | identity_gap、clock_gap、outside_region、sensor_loss、unobservable |

TTC/DRAC/PET 记录的是代理风险，不得自动转译为事故概率。

## 8. Exposure / Assignment Record

| 字段 | 类型 | 必填 | 含义 |
|---|---|---:|---|
| assignment_id | string | 是 | 随机化/策略分配键 |
| vehicle_id | string | 是 | 车辆 |
| message_assignment | enum | 是 | message、no_message 或策略版本 |
| message_exposure | object | 是 | 消息邻域和时间暴露 |
| physical_exposure | object | 是 | 跟驰/冲击波/物理邻域 |
| network_cluster | string | 是 | 预注册簇 |
| exposure_mapping_version | string | 是 | 映射版本 |
| assignment_probability | number | 是 | 已知随机化概率 |
| spillover_status | enum | 是 | isolated、leaked、unknown |

## 9. 完整性检查

1. 外键 event_id、message_id、vehicle_id 必须可追溯；
2. 同一 record_id 不得有冲突值；
3. 时间顺序必须单调；
4. adoption 不得早于 delivery/verification；
5. reference_condition 与 assignment 一致；
6. 缺失原因与 quality_status 一致；
7. 事件、消息、轨迹、风险和 manifest 的 SHA256 可复核；
8. 任何区域结果都要报告有效 vehicle-time、Unknown/INVALID 数量和聚类单位；
9. exposure_mapping_version 改变时不能静默重算旧结果；
10. 证据契约通过不等于科学效应成立。
