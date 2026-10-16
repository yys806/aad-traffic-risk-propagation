# Stage 0.3 R2 边界修复与验收准备报告（AAD-S0.3-T02）

> 日期：2026-10-16（Asia/Shanghai）。结果 ID：`RES-STAGE-0.3-BOUNDARY-REPAIR-R2`。
> 正式验收准备包：`code/outputs/formal/calibration/stage_0_3_pneuma_boundary_repair_20261016_r2/`（不可覆盖，SHA256SUMS 校验通过）。
> 本文件是导航与解释摘要；数值以包内 audit/config/CSV/Parquet 与 SHA256SUMS 为准。R1 包（`stage_0_3_pneuma_kinematics_20261012_r1/`）保留为不可覆盖的历史证据。

## 0. 结论摘要

- 修复 R1 遗留的三项工程边界缺陷（原始时间顺序被排序掩盖、重复 `track_id` 字典覆盖、Stage 0.5 参考质量字段语义失真），不改变研究方法、科学参数或统计设计。
- 真实数据统计结果不变：785 原始轨迹行 / 785 唯一 track_id / 785 唯一轨迹 / 1,239,475 状态；时间加权速度 mean=4.8382 m/s（与 R1 逐位一致），车辆等权 mean=6.2077 m/s；时间加权纵向加速度 mean=-0.0044 m/s²、sd=0.7454 m/s²；bootstrap 95% CI 与 R1 一致。
- R1/R2 逐项比较 145 项指标：30 项为浮点末位差异（|差|≤1e-9，numpy 求和顺序/内存对齐效应，已用 R1 代码路径在 R1 封存状态上复算证明与本次修复无关），1 项为结构性差异（`stage_0_5_reference_quality_counts`：R1 未记录逐状态质量、R2 新增记录）。无任何计数、权重或记录层面的统计变化。
- 原始顺序、重复 ID 与质量状态专项审计在真实文件上全部为零异常；fail-closed 语义已由 9 个新增构造回归测试固定（含 `0.00→0.08→0.04` 时间倒退不可被排序掩盖）。
- 独立复算（不依赖生产模块、原始顺序语义）discrepancies=0；全量测试 315 passed。
- 状态保持 **Gate Pass Candidate（R2，边界缺陷消除）**，提交研究者最终裁决。科学 Gate 未由本任务宣布通过。

## 1. 根因分析与修复（工程事实）

### 1.1 任务 1：原始时间顺序审计被排序掩盖

- **原实现：** `flag_state_quality()` 先按 `(vehicle_id, time_s, raw_index)` 排序再检查相邻时间差；`dt_to_next_s`、`time_increment_nonpositive` 全部定义在排序后视图上。
- **缺陷：** 原始记录顺序中的时间倒退（如 `0.00 → 0.08 → 0.04`）在排序后变成合法递增序列，完全不可见；异常观测经排序可重新获得可靠时间权重。`compute_track_stats()` 的 `n_nonpositive_increments` 同样在时间排序后计算，恒为 0，属于同类缺陷。
- **修复：**
  1. 时间连续性在**排序前**按原始记录顺序（`raw_index`）逐轨迹评估，新增 `time_regression_in_raw_order`、`raw_order_time_anomaly`（进出任一非正原始边的状态）、`time_gap_flag`；`dt_to_next_s` 语义改为原始顺序相邻区间。
  2. 时间加权区间统一由**原始记录顺序邻接**定义（`[t_i, t_{i+1_raw})`）；时间排序仅用于规范分析输出顺序，不再定义区间。
  3. 引入统一可靠性掩码（解析失败 / 身份歧义 / 原始顺序异常 / 重复 (track,time)），被标记状态在 `integrate_time_weighted`、ECDF、状态份额、按速度分层、轨迹簇 bootstrap、绘图权重中一律不获得可靠时间权重——排序不可能让异常观测"重新取得"权重。
  4. 无插值、无补帧、无静默丢弃：全部原始记录保留并携带标记。
- **回归测试：** `test_flag_state_quality_raw_order_regression_not_masked_by_sort`（任务要求的 `0.00→0.08→0.04` 构造用例：倒退被标记、三个状态可靠权重为 0）、`test_flag_state_quality_gap_flag_respects_tolerance`、`test_time_weighting_respects_raw_order_anomaly_flags`（重复时间状态不可经排序重获权重）；原排序语义测试改为原始顺序断言。

### 1.2 任务 2：重复轨迹 ID 字典覆盖

- **原实现：** `audit_pneuma_source()` 以 `track_meta[track_id] = {...}` 字典按 `track_id` 保存行元数据；不同原始行的重复 ID 后写覆盖先写。
- **缺陷：** 重复 ID 静默合并，后续重复检测失效；同一 ID 的两条原始行会被 `groupby("vehicle_id")` 合并为一条"可靠轨迹"；计数 `raw_track_rows` 实为唯一键数而非原始行数。
- **修复：**
  1. 审计单位改为**原始轨迹行**：`tracks_table` 每个源数据行一条记录（含 `source_row_number`、字段数、状态块数、行级解析状态）；新增 `raw_track_rows`（真实行数）、`unique_track_ids`、`duplicate_track_ids`、`duplicate_track_rows`、`identity_conflicts`（同 ID 异车型/异元数据）与 `duplicate_state_keys_count`。
  2. 重复 ID 状态全部标记 `identity_ambiguous`/`identity_status=ambiguous_duplicate_track_id`，不合并、不改名、不重命名为新车辆身份；状态行全量保留。
  3. fail-closed：歧义身份状态被可靠性掩码排除出全部可靠统计；`compute_track_stats()` 分组键改为 `(vehicle_id, source_row_number)`（无该列时回退 `vehicle_id`），原始行是统计单元；车辆等权、车型组成、bootstrap 只使用可靠轨迹行。正式管线（本固定源文件）遇到重复 ID 直接中止运行并报原因，不产生部分统计。
  4. 计数语义全部可复算：`raw_track_rows`=源数据行数，`unique_track_ids`=不同 ID 数，`parsed_state_records`=状态记录数。
- **回归测试：** `test_audit_duplicate_track_rows_are_flagged_not_merged`（同 ID 两行、时间不重叠：行数 3/唯一 2、状态 4 条全保留、可靠权重 0）、`test_audit_records_identity_conflicts_for_duplicate_rows`、`test_audit_flags_duplicate_track_time_within_row`。
- **真实文件核实：** 785 行 / 785 唯一 ID / 0 重复（独立复算同值），R1 的 785 计数在字典覆盖缺陷下碰巧正确，但 R1 的 `raw_track_rows` 语义是唯一键数；R2 起语义为真实行数且两者均单独记录。

### 1.3 任务 3：Stage 0.5 参考接口质量语义

- **原实现与缺陷：**
  1. `build_stage_0_5_reference_states()` 把 `quality_status` 统一填成常量 `"raw_parsed"`（R1 包内 1,239,475 条全部 `raw_parsed`，包括 785 条无可靠区间的末帧状态）；`time_weighting_eligible` 缺省时默认全 `True`。
  2. `write_real_reference_package()` 只读取 pNEUMA parquet 的 4 个数值列，`quality_status`/`time_weighting_eligible` 完全被忽略——接口能读取 ≠ 质量标记被传递 ≠ 后续统计保持权重，三者被混同。
- **修复：**
  1. `quality_status` 改为**逐状态推导**（优先级 parse_failed > identity_ambiguous > raw_time_anomaly > duplicate_time > raw_parsed）；无可推导标志时拒绝生成（`CalibrationContractError`），不再默认可靠。显式字符串参数保留为向后兼容入口。
  2. `time_weighting_eligible` 由**实际解析质量、轨迹身份、原始顺序连续性与可靠时间区间共同决定**（`parse_ok & ~identity_ambiguous & ~raw_order_time_anomaly & ~duplicate_time_in_track & 0<dt_to_next_s<=tolerance`）；无预计算列且无区间信息时同样拒绝默认。
  3. `write_real_reference_package()` 读取并使用质量字段：非 `raw_parsed` 状态 fail-closed 排除出 pNEUMA 运动学抽样池（计数入 audit），`time_weighting_eligible` 随 `kinematics_reference.parquet` 传递；稳定哈希抽样规则本身未改变；legacy 4 列 schema 仍接受并记录 `pneuma_quality_columns_present=false`。
  4. **设计建议（仅记录，不实现）：** 当前按状态无界抽样本身不带时间权重语义；若 Stage 0.5 正式覆盖统计需要保持时间加权权重，应使用随表传递的 `time_weighting_eligible` 或改为轨迹整簇抽样。该决定属 Stage 0.5 设计与研究者，本任务不擅自实现。
- **回归测试：** `test_build_stage_0_5_reference_states_derives_per_state_quality`、`test_build_stage_0_5_reference_states_refuses_unaudited_states`、`test_real_reference_package_propagates_pneuma_quality_fields`（含 legacy 兼容原测试）。
- **真实文件核验结论：** R2 包 `quality_status` 分布 `{raw_parsed: 1239475}`（本文件无解析/身份/顺序异常，逐状态推导结果为全部可靠解析）；`time_weighting_eligible` 1,238,690 / 1,239,475（785 条末帧无下一记录、零时长，与 R1 一致）；接口测试 25,000 kinematics / 20,000 following / 4,545 events，`pneuma_quality_columns_present=true`、排除 0、eligible 1,238,690、`pneuma_ttc_included=false`，Gate 保持 `pending_simulation_sample`。

## 2. R1/R2 逐项统计差异（任务 4）

R1 是比较基准，不是必须维持的目标值。包内 `r1_r2_comparison.csv` 共 145 项：

| 类别 | 数量 | 说明 |
|---|---|---|
| 完全一致 | 114 | 含速度时间加权 mean=4.838218067205407、暴露 49,547.6 s、车辆等权速度 mean=6.207738438311219、车型组成全部、dt 分布全部、bootstrap 95% CI（速度 [4.4042, 5.3137]、加速度 [-0.0084, -0.00036]）、计数全部 |
| 浮点末位差异 | 30 | |差|≤1e-9（最大 3.6e-12），来自 numpy 求和顺序/内存对齐；无计数、权重或记录变化 |
| 结构性差异 | 1 | `stage_0_5_reference_quality_counts`：R1 未记录（统一填 `raw_parsed`），R2 新增逐状态质量计数 |

**浮点差异归因验证：** 用 R1 的原始代码路径在 R1 封存的 `states_audit.parquet` 上复算（同一输入、同一容差、逐位相同的 dt 数组），得到的加速度时间加权 mean 为 -0.004410235006337358，与 R2 一致而与 R1 当年存储值相差 1 ulp——证明这些末位差异是原 R1 运行的环境性求和对齐效应，与本次修复无关，且本次修复未引入任何统计语义变化。

主要统计对照（R2 值；R1 同位）：

| 指标 | R2 | R1 |
|---|---|---|
| 原始轨迹行 / 唯一 ID / 唯一轨迹 | 785 / 785 / 785 | 785（行数语义当时为唯一键数） |
| 状态记录 | 1,239,475 | 1,239,475 |
| 可靠权重资格状态 | 1,238,690 | 1,238,690 |
| 时间加权速度 mean / P50 / P95 (m/s) | 4.8382 / 4.5824 / 12.1176 | 相同 |
| 车辆等权速度 mean (m/s) | 6.2077 | 相同 |
| 时间加权加速度 mean / sd (m/s²) | -0.0044 / 0.7454 | 相同（末位 ulp） |
| 车型组成（轨迹数） | Car 443、Motorcycle 153、Taxi 137、Medium Vehicle 30、Bus 20、Heavy Vehicle 2 | 相同 |
| bootstrap 速度 mean 95% CI | [4.4042, 5.3137] | 相同 |
| Stage 0.5 接口测试 | 25,000 / 20,000 / 4,545，质量字段传递 | 25,000 / 20,000 / 4,545（质量字段被忽略） |

## 3. 原始顺序、重复 ID 与质量状态专项审计（真实文件）

- 原始记录顺序（排序前评估）：时间倒退 0、非正增量 0、原始顺序异常状态 0、重复 (track,time) 状态 0、超容差缺口 0。
- 身份（行级）：785 原始行、785 唯一 ID、重复 ID 0、身份冲突 0、可靠轨迹行 785。
- 质量：解析成功 1,239,475（`parse_failed` 0）；`quality_status` 全部 `raw_parsed`；`time_weighting_eligible` 1,238,690（785 末帧零时长除外）。
- 以上全部由 `verify_stage_0_3_independent.py` 独立复算（重新实现解析、按原始顺序聚合，不依赖生产模块），discrepancies=0。

## 4. 测试完整性与数量差异解释（任务 5）

- **Stage 0.2 收口报告 287 passed**：当时全量收集数（`python -m pytest tests`，含 `tests/legacy` 与 `tests/real_data`），在 Stage 0.3 的 19 个新测试加入之前：287 + 19 = 306。
- **R1 报告 232 passed**：R1 时全量树为 306，但该次运行收集范围排除了 `tests/legacy`（74 个测试）：306 − 74 = 232。
- **R2（本次）315 passed**：306 + 本次新增 9 个测试（`test_pneuma_urban_kinematics.py` 新增 8 个、`test_simulation_real_coverage.py` 新增 1 个），收集范围含 legacy 与 real_data，无跳过、无失败、无未收集。
- 结论：三个数字的差异完全由**收集范围**与**测试新增**解释，不存在测试被静默移除；同一棵树上三种口径互洽（287+19=306=232+74）。
- **"测试通过但审计口径错误"实例（已修复）：** R1 的 `test_flag_state_quality_detects_reversal_duplicate_and_gap` 断言的是排序后 dt 语义（`[0.02, 0.02, 0.0]`），因此通过的同时掩盖了原始顺序缺陷；R2 改为原始顺序断言（`[0.04, 0.00, -0.02]` + 倒退标记）并新增构造回归测试固定语义。
- `tests/real_data/spmd` 4 个测试依赖本地 SPMD 数据集（本机存在，通过）；`tests/legacy` 为历史 Pilot 管线测试（通过，仅作回归保护，不参与当前正式结论）。

## 5. 执行的验证命令与环境

| 验证 | 命令 | 结果 |
|---|---|---|
| Stage 0.3 专项测试 | `python -m pytest tests/test_pneuma_urban_kinematics.py tests/test_simulation_real_coverage.py tests/test_real_trajectory.py -q` | 38 passed |
| 全量测试 | `python -m pytest tests -q`（Windows/miniconda Python 3.13，pytest 8） | 315 passed，0 skipped，0 failed |
| 编译检查 | `python -m compileall -q src scripts tests` | OK |
| 正式管线 | `python code/scripts/run_stage_0_3_pneuma_kinematics.py`（源 SHA 钉扎 F9CDE0A3…，278.7 s，峰值约 2.53 GiB） | 生成 R2 包 |
| 独立复算 | `python code/scripts/verify_stage_0_3_independent.py --package …r2` | discrepancies=0，pass=true |
| 文档与证据 | `validate_project_docs.py --strict-git`、`export_project_evidence.py --repo-root .`（`--verify`）、`pytest tests/test_project_docs.py` | 见提交记录 |
| 源文件完整性 | SHA-256 `F9CDE0A3CA5010E2217EA4CBC0BDF26ED87BE1EC0D8C2BE5E2CB93AAC82BA28C` | 与 R1/封存清单一致，未变化 |

## 6. 验收矩阵与 Gate 状态

包内 `gate_matrix.csv` / `gate_matrix_summary.json` 共 11 项：Verified 2、Verified (engineering) 4、Verified (descriptive) 2、"Verified (engineering); 科学容差 Decision Required" 1、Decision Required 1、Not Applicable 1、Unverified 1。新增三项 R2 行（原始顺序与身份审计、Stage 0.5 质量语义均已按工程口径 Verified）。本包为 **Stage 0.3 Gate Pass Candidate（R2）**，科学 Gate 由研究者裁决。

## 7. Decision Required（维持留给研究者，本任务未新增科研决定）

1. 正式时间连续性容差（工程锚定 0.043 s，未冻结；8 候选敏感性已封存）。
2. 极端速度/加速度观测的正式质量标记规则（当前全部保留 + 探索性敏感性）。
3. 低速/近零加速度描述性阈值是否转为正式分类（当前仅探索性候选）。
4. pNEUMA 车型到 SUMO vType 的映射（留待 Stage 0.5 设计）。
5. 单文件城市运动学参考的正式适用范围声明（30 分钟、单区域、2018-11-01 早高峰）。
6. Stage 0.3 科学 Gate 是否通过。
7. （新增记录，不新增实现）Stage 0.5 正式覆盖统计是否使用 `time_weighting_eligible` 保持时间加权权重或改用轨迹整簇抽样。

## 8. Limitation（不变）

- 不代表整个雅典、所有城市道路或一般交通条件；单文件时空代表性受限。
- 不是跟驰风险、事故概率或 AAD 因果效应证据；pNEUMA 风险职责已退役且未恢复。
- 运动学一致性为内部诊断；无独立视频/几何/物理真值（Unverified）。
- 车辆等权不等于城市车辆总体分布；Heavy Vehicle n=2 不宜推断。
- 本次修复只消除工程边界缺陷并核验语义，不构成科学 Gate 通过的证据。

## 9. 产物清单

- 修复与测试：`code/src/riskprop/pneuma_urban_kinematics.py`、`code/src/riskprop/simulation_real_coverage.py`、`code/scripts/run_stage_0_3_pneuma_kinematics.py`、`code/scripts/verify_stage_0_3_independent.py`、`code/tests/test_pneuma_urban_kinematics.py`、`code/tests/test_simulation_real_coverage.py`。
- R2 验收包（32 个文件，含新增 `r1_r2_comparison.csv` 与 `gate_matrix_summary.json`）：`code/outputs/formal/calibration/stage_0_3_pneuma_boundary_repair_20261016_r2/`。
- Stage 0.5 接口测试包：`…_r2_stage05_interface_test/`（含 reference_package：kinematics 25,000、following 20,000、events 4,545）。
- 独立复算：`…_r2_independent_verification.json`（pass=true，discrepancies=0）。
- 便携证据：`evidence/results/RES-STAGE-0.3-BOUNDARY-REPAIR-R2/`。
