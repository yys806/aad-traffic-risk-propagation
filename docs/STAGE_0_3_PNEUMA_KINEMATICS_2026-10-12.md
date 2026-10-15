# Stage 0.3 pNEUMA 城市运动学校准综合实施与验收准备报告

> 日期：2026-10-12（Asia/Shanghai）。结果 ID：`RES-STAGE-0.3-PNEUMA-KINEMATICS-R1`。
> 正式验收准备包：`code/outputs/formal/calibration/stage_0_3_pneuma_kinematics_20261012_r1/`（不可覆盖）。
> 本文件是导航与解释摘要；数值以包内 audit/config/CSV/Parquet 与 SHA256SUMS 为准。

## 0. 结论摘要

- 完成 Stage 0.3 全部已授权工程与统计任务（A–E）与验收准备；独立复算零差异；全量测试 232 通过。
- pNEUMA 全量文件：785 条唯一轨迹（即 785 辆车；track 与车辆一一对应）、1,239,475 条状态记录、观测时间窗 [38.40, 888.00] s（文件内时钟）、采样间隔 0.04 s（25 Hz）、零缺口、零畸形块、零重复。
- 时间加权主统计：速度 mean=4.8382 m/s、P50=4.5824 m/s、P95=12.1176 m/s；纵向加速度 mean=-0.0044 m/s²、sd=0.7454 m/s²、P99=2.0192 m/s²，存在极端记录（min=-34.78、max=+47.75 m/s²），全部保留并做敏感性对照。
- 车辆等权稳健性：速度 mean=6.2077 m/s，比时间加权高 1.37 m/s；长轨迹、低速轨迹对时间加权贡献更大，方向合理。
- 已建立 Stage 0.5 标准化参考接口并通过现有 `write_real_reference_package()` 的真实全量兼容性测试（25,000 kinematics、20,000 following、4,545 events，pNEUMA TTC 未纳入）。
- 状态：**Stage 0.3 Gate Pass Candidate**，提交研究者审核。科学 Gate 未由本任务自行宣布通过。

## 1. 输入与完整性（任务 A，Observation）

- 文件：`dataset/pNEUMA/20181101_d1_0800_0830.csv`，73,509,485 bytes，SHA-256 `F9CDE0A3CA5010E2217EA4CBC0BDF26ED87BE1EC0D8C2BE5E2CB93AAC82BA28C`，与封存下载清单一致。
- 来源：Zenodo pNEUMA（doi 10.5281/zenodo.10491409）；许可按更严格的 CC BY-NC 4.0 管理（Zenodo 标记 CC BY 4.0，专题页存在不一致）。
- 流式解析审计（`audit_pneuma_source()`，非 `read_pneuma_wide()` 的信任复用）：785 行轨迹元数据 + 六字段状态块全部完整；无字段错位、无残缺状态块、无无法解析数值、无重复 track_id、无重复 (track,time)。
- 单位核查：speed=km/h（换算 m/s 保留双列）、longitudinal/lateral acceleration=m/s²、time=s，与 Zenodo 元数据一致。
- 时间与连续性：相邻 dt mode=median=0.04 s，P99=max=0.04 s；非正增量 0、时间倒退 0、缺口 0。本文件为等间隔 25 Hz，未假设 NGSIM 的 100 ms 语义。
- 工程锚定容差 0.043 s（modal dt + 5% + 1 ms）只用于 `time_weighting_eligible` 标记；正式科学容差未冻结。
- 解析性能：全量运行 273.7 s（含 bootstrap 2000 次与 Stage 0.5 接口测试），tracemalloc 峰值约 1.57 GiB；数据流式读取，不需要进一步工程优化。

## 2. 描述性统计（任务 B，Observation）

主统计=可靠观测时间加权（左矩形 [t_i, t_i+1)，末帧零时长，不跨缺口）；稳健性=车辆等权；车型组成=唯一轨迹计数。

### 2.1 速度分布（m/s，时间加权）

| 组 | 有效状态 | 暴露 s | mean | sd | P5 | P25 | P50 | P75 | P95 | P99 | max |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ALL | 1,238,690 | 49,547.6 | 4.8382 | 4.3700 | 0 | 0 | 4.5824 | 8.4693 | 12.1176 | 14.3829 | 21.3413 |
| Bus | 42,610 | 1,704.4 | 4.1404 | 4.1479 | 0 | 0 | 3.8832 | 7.9803 | 10.7331 | 13.0300 | 14.5024 |
| Car | 685,555 | 27,422.2 | 4.7200 | 4.3466 | 0 | 0 | 4.3463 | 8.3548 | 12.0488 | 14.0783 | 21.3413 |
| Heavy Vehicle | 3,935 | 157.4 | 4.4990 | 2.6449 | 0.0009 | 2.4436 | 5.2395 | 6.7056 | 8.1524 | 9.0443 | 9.1690 |
| Medium Vehicle | 96,845 | 3,873.8 | 2.3919 | 3.5080 | 0 | 0 | 0 | 4.5154 | 9.9393 | 11.6766 | 15.5450 |
| Motorcycle | 187,070 | 7,482.8 | 6.2691 | 4.5487 | 0 | 1.9885 | 6.6326 | 9.8528 | 13.4310 | 15.5975 | 21.0575 |
| Taxi | 222,675 | 8,907.0 | 5.2034 | 4.1615 | 0 | 0.2092 | 5.3604 | 8.6648 | 11.7637 | 14.0330 | 17.7203 |

低速（<1 km/h）时间占比 31.7%，近静止（<0.5 m/s）32.6%，高速（≥16.67 m/s≈60 km/h）0.10%——典型拥堵城市早高峰。分车型直方图与 ECDF 见包内 `fig_speed_histogram.png`、`fig_speed_ecdf.png`（图注含样本量与权重）。

### 2.2 纵向加速度分布（m/s²，时间加权）

- 总体：mean=-0.0044，sd=0.7454，P5=-1.1940，P25=-0.2172，P50=0，P75=0.2264，P95=1.1501，P99=2.0192；min=-34.7828，max=+47.7523。
- 状态占比：加速 32.7%、减速 32.3%、近零（|a|≤0.05）35.0%。
- 极端记录存在（约 2.4% 暴露 |a|>2 m/s²；0.2% >5 m/s²），作为极端值敏感性保留，不作质量/安全分类。
- 分车型与按速度分层条件分布见 `acceleration_time_weighted_by_type.csv`、`acceleration_by_speed_stratum.csv`；加速度 ECDF/直方图见包内图。
- 正/负加速度描述不等同于全部油门/制动控制行为。

### 2.3 车型组成（唯一轨迹）

Car 443（56.4%）、Motorcycle 153（19.5%）、Taxi 137（17.5%）、Medium Vehicle 30（3.8%）、Bus 20（2.5%）、Heavy Vehicle 2（0.25%）。状态数与暴露见 `vehicle_type_composition.csv`。原始类别保留；与 SUMO vType 的映射未批准（Decision Required）。

### 2.4 车辆等权 vs 时间加权

| 指标 | 时间加权 | 车辆等权 | 差 |
|---|---|---|---|
| 速度 mean (m/s) | 4.8382 | 6.2077 | -1.3695 |
| 速度 P50 | 4.5824 | 5.5452 | -0.9628 |
| 加速度 mean (m/s²) | -0.0044 | -0.0208 | +0.0164 |
| 加速度 P50 | 0.0000 | -0.0037 | +0.0037 |

车辆等权仅代表本文件 785 条被截断轨迹的等权平均，受观测范围、轨迹截断与采样机制影响，不等于城市真实车辆分布。

## 3. 质量、敏感性与统计可靠性（任务 C，Observation）

1. 原始 vs 可靠观测：1,239,475 条全部解析成功；时间加权可用 1,238,690（排除 785 条末帧零时长）。
2. 缺失/异常：无缺失、无畸形块；极端速度 23 条 >20 m/s（0.001%）、极端 |a| 记录保留。
3. 极端值影响：屏蔽 |a|>2 m/s² 后 mean 由 -0.0044 变 +0.0017；屏蔽 speed>20 m/s 后 mean 变化 -0.0003 m/s。均值对极端加速度敏感，分位数稳健。
4. 连续性候选规则：8 个容差下暴露 28,075.8–49,547.6 s、速度 mean 4.8382–4.8584 m/s；0.04 s 严格等间隔容差会错误排除 43% 有效区间（浮点表示所致），说明容差必须考虑浮点容差；≥0.045 s 结果不变。
5. 时间加权 vs 车辆等权差异见 2.4。
6. 车型不均衡：Car 占 56% 轨迹；Heavy Vehicle 仅 2 条，其车型级统计不确定性极大（bootstrap 区间退化），不应过度解释。
7. 统计不确定性（轨迹整簇 bootstrap，2000 次，seed=20261012）：速度时间加权 mean 95% CI [4.4042, 5.3137]；加速度 mean 95% CI [-0.0084, -0.00036]；车辆等权区间见 `bootstrap_vehicle_equal_weight.csv`。同一轨迹的帧不作为独立样本。

运动学一致性（内部诊断，非物理真值）：Δv/Δt 与报告加速度偏差中位 0.0036 m/s²（P95 0.0417）；位置—速度偏差中位 0.3899 m/s（P95 1.8700）；轨迹行驶距离相对偏差中位 1.57%；平均速度偏差中位 0.022 km/h。报告元数据与逐状态汇总总体自洽。

## 4. Stage 0.5 参考接口（任务 D，Observation）

- 标准化参考：`stage_0_5_reference_states.parquet`（dataset/site/window_id/vehicle_id/vehicle_type/time_s/speed_mps/acceleration_mps2/quality_status/time_weighting_eligible/source_file_sha256）。
- 真实全量接口测试：现有 `write_real_reference_package()` 直接消费本阶段参考视图 + 四个 Stage 0.2 封存 NGSIM state + 正式 P2 事件表，输出 kinematics 25,000、following 20,000、events 4,545，`pneuma_ttc_included=false`，Gate 保持 `pending_simulation_sample`。测试包：`stage_0_3_pneuma_kinematics_20261012_r1_stage05_interface_test/`。
- 抽样车型保持审计：稳定哈希抽样 5,000 行最大状态份额偏差 0.0074、最低车型轨迹保留率 94.1%（`sampling_balance_audit.csv`）。现有抽样不破坏车型层级，但是按状态而非轨迹抽样，不能保持轨迹内部时间结构；候选改进（轨迹整簇抽样）留给 Stage 0.5 设计决定。
- NGSIM 与 pNEUMA 的道路类型、交通环境、采样语义、车型组成不同；本阶段不拼接为独立同分布现实样本，不冻结 Stage 0.5 场景分层、SUMO 参数、energy distance 容差或覆盖 Gate。

## 5. 测试与独立复算（任务 E）

- 新增 19 个单元测试（`code/tests/test_pneuma_urban_kinematics.py`）：解析、残缺块、单位、时间重复/倒退/缺口、身份与车型统计、时间加权积分与分母、首末边界、车辆等权、分车型、连续性稳健性、Stage 0.5 接口、包不可覆盖。
- 独立复算脚本 `code/scripts/verify_stage_0_3_independent.py`（不依赖生产模块重新解析与聚合）：计数、分车型轨迹数、时间加权 mean/P50/暴露与包内一致，checksum 包校验通过，discrepancies=0。
- 全量 pytest：232 passed（含 Stage 0.1/0.2/0.4/0.5/0.6 回归）；测试通过≠数据质量通过≠科学验收通过。

## 6. 验收矩阵与 Gate 状态

`gate_matrix.csv` 共 9 项：Verified 5（其中工程/描述性限定）、Decision Required 1、Not Applicable 1、Unverified 1，另连续性项为“Verified (engineering); 科学容差 Decision Required”。详见包内 `gate_matrix.csv` 与 `report.md`。

**状态：Stage 0.3 Gate Pass Candidate** —— 工程与已批准统计设计完成，提交研究者审核科学适用范围与未冻结参数。

## 7. Decision Required（需研究者批准的最小清单）

1. 正式时间连续性容差（当前为 0.043 s 工程锚定；候选敏感性已封存）。
2. 低速/近零加速度等描述性阈值是否转为正式分类（当前仅探索性候选）。
3. 极端速度/加速度记录的正式质量标记规则（当前全部保留 + 敏感性对照）。
4. pNEUMA 车型到 SUMO vType 的映射规则。
5. 本单文件结果在 Stage 0.5 中的适用范围声明（30 分钟、单区域、2018-11-01 早高峰）。
6. Stage 0.3 科学 Gate 是否通过（本包为候选，未自行宣布）。

## 8. Limitation（证据不能支持什么）

- 不代表整个雅典、所有城市道路或一般交通条件；单 30 分钟文件、时空代表性受限。
- 不是跟驰风险、事故概率或 AAD 因果效应证据；pNEUMA 风险职责已退役且未恢复。
- 运动学一致性为内部诊断；无独立视频/几何/物理真值（Unverified）。
- 车辆等权不等于城市车辆总体分布；Heavy Vehicle n=2 不宜推断。
- pNEUMA 平滑/滤波处理链未独立核验；报告字段由数据提供方生成。

## 9. 产物清单（包内，SHA256SUMS 校验）

`audit.json`、`config.json`、`provenance.json`、`manifest.json`、`SHA256SUMS`、`report.md`、`states_audit.parquet`、`stage_0_5_reference_states.parquet`、`track_stats.csv`、`track_consistency.csv`、`speed_time_weighted_by_type.csv`、`acceleration_time_weighted_by_type.csv`、`speed_vehicle_equal_weight.csv`、`acceleration_vehicle_equal_weight.csv`、`vehicle_type_composition.csv`、`speed_state_shares.csv`、`acceleration_state_shares.csv`、`acceleration_by_speed_stratum.csv`、`weighting_comparison_by_type.csv`、`continuity_sensitivity.csv`、`extreme_sensitivity.csv`、`bootstrap_vehicle_equal_weight.csv`、`sampling_balance_audit.csv`、`gate_matrix.csv`、`kinematic_consistency_summary.json`、`fig_speed_histogram.png`、`fig_speed_ecdf.png`、`fig_accel_histogram.png`、`fig_accel_ecdf.png`、`fig_dt_histogram.png`。
