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

显式校准 ZIP 成员 → `_read_source()`（US-101 无表头 TXT、Lankershim CSV）→ `annotate_ngsim_trajectory_identity()` → `standardize_ngsim_states()` 内调用 `add_ngsim_leader_ttc()` → `extract_rear_end_events()` → 完整 state 与原始/可靠/拒绝 candidate Parquet、audit、配置、provenance 和校验包。

净间距由报告的前向间距减去匹配 leader 车长；仅在 leader 可匹配、净间距为正且 follower 正在闭合时计算 `TTC=g/Δv` 与 `DRAC=(Δv)^2/(2g)`。诊断身份采用 site/source_member/source_period/原始编号/观测帧时钟锚；unknown 来源时段不推断为官方标签。记录冲突传播到整个诊断序列，保留原行号；单帧 TTC 数学有效与 identity/leader 可靠性分别标记。事件在完整状态序列上检查前车变化、片段与 100 ms/帧连续性，缺口后第一帧可以开始新事件；不确定前后车不能进入可靠事件。默认 `extract_rear_end_events()` 返回可靠工程候选，`return_diagnostics=True` 返回原始/可靠/拒绝三表；未冻结科学阈值。

## pNEUMA 数据流

`dataset/pNEUMA/20181101_d1_0800_0830.csv` → `pneuma_urban_kinematics.audit_pneuma_source()` 流式审计与解析（或历史接口 `real_trajectory.read_pneuma_wide()`）→ 逐状态表（速度、纵/横向加速度、时间、车型、元数据）→ `flag_state_quality()` 时间质量标记 → 时间加权/车辆等权统计、敏感性与 bootstrap → `build_stage_0_5_reference_states()` 标准化参考 → Stage 0.5 `write_real_reference_package()`。不推断道路、leader、TTC 或 DRAC。2026-10-12 专用阶段 0.3 汇总入口与验收包已实现。

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

## 2026-10-10 前车匹配收尾

NGSIM leader lookup 在存在诊断字段时使用 run scope、Global_Time、diagnostic_clock_anchor_ms、Frame_ID 和唯一原始前车身份；重复或缺失字段不猜测。任务 1.5 独立核查真实 Lankershim 0 跨时钟匹配，四源回归 0 行核心差异。


## 2026-10-12 Stage 0.3 参考接口

stage_0_3 验收包 `stage_0_5_reference_states.parquet`（含 dataset/site/window_id/vehicle_id/vehicle_type/time_s/speed_mps/acceleration_mps2/quality_status/time_weighting_eligible/source_file_sha256）可直接进入 `write_real_reference_package()`；NGSIM 与 pNEUMA 不拼接为 iid 样本。

## 2026-10-16 R2 质量语义（当前）

R2 起 `quality_status` 逐状态推导（parse_failed/identity_ambiguous/raw_time_anomaly/duplicate_time/raw_parsed），`time_weighting_eligible` 由解析质量、轨迹身份、原始顺序连续性与可靠区间共同决定；`write_real_reference_package()` 读取 pNEUMA 质量字段并将非 raw_parsed 状态 fail-closed 排除出运动学抽样池（计数入 audit），`time_weighting_eligible` 随 kinematics_reference 传递；稳定哈希抽样规则未变。时间加权区间由原始记录顺序邻接定义，排序不定义区间。

## 2026-10-12 正式测量与收口接口

task1.5四源状态→独立全序列/P2在线提取→r4→不可覆盖final_r1验收包；病例与抽稀产物保留成员和断点，便携证据只含小型摘要。 依据：相应源码及 `docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`。
