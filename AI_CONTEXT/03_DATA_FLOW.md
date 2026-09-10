# AAD Data Flow

## 总览

```text
raw data
-> dataset（本机、Git 忽略）
-> preprocessing / 标准化
-> tabular model input（当前不是 tensor）
-> 确定性测量或 SUMO 运行
-> post-processing / 事件合并或稳定抽样
-> evaluator / Gate
-> metrics + audit + manifest + provenance + SHA256SUMS
-> evidence（Git 内小型只读快照）
```

## NGSIM 数据流

`dataset/NGSIM/*.zip` → `real_trajectory.read_ngsim_nested_csv()` → `add_ngsim_leader_ttc()` → `ngsim_risk_calibration.standardize_ngsim_states()` → `extract_rear_end_events()` → state/risk-event Parquet 与 audit。

净间距由报告的前向间距减去匹配 leader 车长；仅在 leader 可匹配、净间距为正且 follower 正在闭合时计算 `TTC=g/Δv` 与 `DRAC=(Δv)^2/(2g)`。连续低 TTC 帧按 vehicle/leader 和时间间隔合并成事件，不能把每帧当独立事件。

## pNEUMA 数据流

`dataset/pNEUMA/20181101_d1_0800_0830.csv` → `real_trajectory.read_pneuma_wide()`，将“每条轨迹一行、后接六字段状态块”展开为逐状态表。当前保留字段包括车辆类型、位置、速度、纵/横向加速度和时间；不推断道路、leader、TTC 或 DRAC。专用阶段 0.3 汇总入口与正式产物仍未实现。

## SPMD 数据流

`dataset/SPMD/selected/RV_RX.csv.zip` → `communication_observability.profile_rv_rx_calibration()`，按完整 `DeviceID|Trip` 的 SHA-256 首字节划分 calibration/locked holdout → 接收状态连续性 profile → `build_stage_0_4_status_package()`。观察间断不等于丢包，RV_RX 行不等于消息，且当前无已验证 adoption 字段。

## SUMO 数据流

`stage_0_1_sumo.run_real_sumo_stage_0_1()` 生成物理隔离的双走廊网络，对四个 `s/c` cell 分别启动 SUMO；TraCI 状态进入 state/emission 表，消息生命周期进入 protocol 表，控制进入 action 表，风险窗口进入 risk 表。随后 `formal_design` 检查四格、处理前等价、隔离、时钟、生命周期与路径；`formal_artifacts` 封存并校验文件。

## 覆盖与准入数据流

NGSIM 跟驰参考 + pNEUMA 运动学参考 → `write_real_reference_package()` 稳定哈希抽样 → SUMO calibration 样本 → `evaluate_simulation_coverage()` 比较 real-real 与 sim-real energy distance 及类别覆盖 → 阶段 0.6 技术真值 → `protocol_lock_readiness()` → 条件完整时 `write_protocol_lock()`。

## 重要数据结构

- `REAL_STATE_COLUMNS`：dataset/site/window/vehicle/time/位置/速度/加速度/road/lane/leader/net gap/closing speed/measurement status/missing reason。
- `RISK_EVENT_COLUMNS`：事件身份、车辆与 leader、时间边界、持续时间、TTC/DRAC/PET、纳入状态与算法版本。
- 阶段 0.1 五表字段契约：`formal_artifacts.TABLE_REQUIRED_COLUMNS`。
- 当前数据均为行式 DataFrame/Parquet；不存在已确认 tensor shape、dataloader 或 neural model input。
