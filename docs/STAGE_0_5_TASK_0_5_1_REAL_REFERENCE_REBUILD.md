# AAD-0.5.1｜正式真实交通参考重建与统计口径验证

## 状态与边界

本报告记录 `RES-STAGE-0.5-REAL-REF-R2` 的工程重建和输入审计。它只重建 Stage 0.2/0.3 已批准的现实参考，不运行 SUMO，不做驾驶行为校准，不访问 locked holdout，不创建新的 real-real 上界，不冻结覆盖阈值，也不改变 Stage 0.2/0.3 的正式风险测量规则。Stage 0.5 仍为 `gate_status=pending_simulation_sample`；Protocol Lock 和 Stage I 继续阻断。

研究者在本任务开始前已批准三项职责：US-101 三个窗口是高速公路跟驰风险主线；Lankershim 是独立的城市道路跟驰风险辅助参考；pNEUMA 只承担城市混合交通运动学。完整可靠观测及时间加权语义为主统计，车辆等权为并列补充，轨迹簇和稳定哈希状态样本仅作敏感性或工程诊断。

## 正式输入与可追溯性

重建入口是 `code/scripts/rebuild_stage_0_5_real_reference.py`，核心实现是 `code/src/riskprop/simulation_real_coverage.py::write_formal_stage_0_5_reference_r2()`。入口拒绝覆盖既有输出；它先构造 `input_manifest.json`，逐项检查路径、SHA-256、schema、来源身份、质量契约和正式算法版本，再生成包。

输入如下：

| 逻辑组 | 正式输入 | SHA-256（已核验） | 职责 |
|---|---|---|---|
| US-101 | `ngsim_us101__0750_0805.parquet` | `684a5f0b96dc48116f16d581c278d7039c0554bf1c3cea8d6eda3e605e3e8644` | 高速公路跟驰风险主线 |
| US-101 | `ngsim_us101__0805_0820.parquet` | `7b0ef830c97a981da018d4e24b029e38aa2630387c728ea87b57926745880a9f` | 高速公路跟驰风险主线 |
| US-101 | `ngsim_us101__0820_0835.parquet` | `a673217765b9a57ed3ea2c743b56fae0c5f538c7517e8e78685721c750082abb` | 高速公路跟驰风险主线 |
| Lankershim | `ngsim_lankershim__complete.parquet` | `650969c29bfe0e604694dc9d4cc5a47076a6d10188bcd81443b55628a713356c` | 城市道路跟驰风险辅助 |
| NGSIM P2 | `p2_formal_events.parquet` | `aa749da3c8d68521111cc59f0d0f2746fecef868121d37ae76d3c75d43c10ae1` | 正式 P2 事件 |
| pNEUMA | `stage_0_5_reference_states.parquet` | `15893115824c43b00069b13308d9bff5048b92d7d217ac0c38c14523c7d42d65` | 城市混合交通运动学 |

NGSIM 状态输入来自 `RES-STAGE-0.2-SCIENTIFIC-ACCEPTANCE-R4`；P2 表来自最终闭合目录并核验 `rule=P2_middle`、`formal_algorithm_version=stage_0_2.formal_risk_measurement.v2`、总数 4,545。pNEUMA 输入来自 `RES-STAGE-0.3-BOUNDARY-REPAIR-R2`，并绑定 `RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3` 的统计摘要。canonical pNEUMA 的 11 个字段、类型、单位、质量状态、布尔资格和来源指纹均被 fail-closed 校验；其行内原始来源指纹为 `F9CDE0A3CA5010E2217EA4CBC0BDF26ED87BE1EC0D8C2BE5E2CB93AAC82BA28C`。

## canonical 接口修复

此前 writer 只认 `id/longitudinal_accel_mps2`，会拒绝 Stage 0.3 canonical 的 `vehicle_id/acceleration_mps2`。现在正式入口默认 `pneuma_schema="canonical"`，直接消费 Stage 0.3 文件，保留原始 `vehicle_type`、`quality_status`、`time_weighting_eligible` 和 `source_file_sha256`。旧四字段输入只有显式 `pneuma_schema="legacy"` 才能进入兼容测试路径，并在审计中标记为非正式 canonical。

新增测试覆盖：canonical Parquet → writer → reference Parquet 的真实字段结构；车型、质量和来源信息不丢失；缺少任一质量字段、未知质量状态、无效值、身份歧义或非原始质量状态与可靠资格冲突时拒绝；legacy 模式必须显式声明。`python -m pytest tests/test_simulation_real_coverage.py -q` 的定向测试结果为 8 passed。

## 重建包内容与质量事实

包目录为 `code/outputs/formal/calibration/stage_0_5_real_reference_r2/`，包含：

- `input_manifest.json`：6 个正式输入、来源/站点/窗口、结果 ID、SHA、schema、允许指标、质量契约和批准引用；
- `kinematics_reference.parquet`：每来源最多 5,000 行的有界运动学诊断样本；
- `following_reference.parquet`：每个 NGSIM 来源最多 5,000 行的有界有效跟驰诊断样本；
- `risk_event_reference.parquet`：完整 4,545 条正式 P2 事件；
- `ngsim_formal_metrics.json`：Stage 0.2 正式事件率、P2 可评价跟驰暴露和测量状态摘要的哈希绑定引用；
- `pneuma_statistics_summary.json`：Stage 0.3 正式时间加权、车辆等权、车型组成和抽样审计 CSV 的哈希绑定引用；
- `sampling_sensitivity.json`：固定 seed=20260907 的稳定哈希状态样本和轨迹簇样本对照；
- `independence_audit.json`：来源、窗口和车辆身份重叠审计；
- `audit.json`、`config.json`、`provenance.json`、`manifest.json`、`SHA256SUMS` 和便携 `report.md`。

四个 NGSIM 状态表共 5,706,252 行、7,607 个来源内车辆身份（车辆数按来源分别记录；跨窗口不能直接相加解释为独立车辆）。测量状态保留 `valid`、`missing`、`invalid`、`not_applicable`，缺失和不可适用均不转换为零风险。正式 P2 事件按来源为 US-101 543、732、1,043，Lankershim 2,227，合计 4,545。事件率和分母直接引用 Stage 0.2 R4 的正式 CSV/审计，不从有界样本重算。

pNEUMA canonical 表为 785 条唯一轨迹、1,239,475 条状态；全表 `raw_parsed`，其中 1,238,690 行具备 `time_weighting_eligible`。车型原始类别保留为 Bus、Car、Heavy Vehicle、Medium Vehicle、Motorcycle、Taxi。canonical 状态表没有逐行可靠区间长度，因此本包不假装从布尔资格重算时间权重；正式时间加权统计引用并绑定 Stage 0.3 R2/R3 已封存摘要，车辆等权统计同样引用正式摘要。

## 统计口径与抽样审计

主统计仍是完整可靠观测及 Stage 0.2/0.3 已批准定义。状态行数、可靠暴露时间、车辆等权和来源/窗口/车型分组分别报告；P2 事件率只使用 Stage 0.2 的 P2 可评价跟驰暴露分母。`time_weighting_eligible` 是资格标记而不是时长，不能单独作为权重值。

稳定哈希状态样本改变了观测单位的时间权重：长轨迹提供更多状态的事实被有界抽样打散，且不能保证极端状态、车型比例和连续跟驰结构保持。因此它只用于有界工程计算/诊断。轨迹簇样本以来源、站点、窗口和车辆（若有轨迹 ID 则按轨迹）为簇，优先整簇纳入并固定 seed；它更好保留连续性和车辆代表性，但仍是诊断样本，不能替代完整统计。`sampling_sensitivity.json` 同时比较均值、P05/P50/P95、车辆数、车型比例、可靠资格行数和极值范围。任何有界样本都标记为禁止重算正式 P2 事件率。

本次固定上限的诊断结果也说明了限制：稳定哈希 5,000 状态在四个 NGSIM 来源覆盖约 1,341–1,920 个车辆，pNEUMA 覆盖 748/785 个车辆；速度均值相对完整行统计的变化约为 NGSIM 0.02–0.06 m/s、pNEUMA 0.02 m/s，不能据此证明时间加权无偏。轨迹簇上限只保留 7–9 个 NGSIM/pNEUMA 车辆簇，速度均值可明显偏移（例如 pNEUMA 4.84→7.22 m/s），这正是连续性敏感性而不是正式分布估计。

## 来源独立性与 real-real 限制

三个 US-101 窗口和 Lankershim 的车辆 ID 存在大量字符串重叠，说明 ID 不能跨来源解释为全局唯一身份；窗口也来自相邻时间段，不能自动当作独立 iid 真实来源。pNEUMA 只有一个文件、一个站点/窗口，不能产生可信的独立 real-real 组。`independence_audit.json` 记录这些冲突，并明确不把相邻片段伪装成独立组。因此当前 `evaluate_simulation_coverage()` 的 real-real Energy Distance 参考上界在场景内仍是 `Not Identifiable / Pending Stage 0.5.2`；实现默认的 0.90 覆盖和 0.95 分位数没有被提升为科学验收阈值。

## Observation 与 Interpretation

**Observation：** canonical pNEUMA 直连 writer 成功；6 个正式输入的 SHA、来源身份和字段契约通过；P2 表为 4,545 条且分组计数与 R4 一致；pNEUMA 的 785/1,239,475、车型和质量资格与 R3/R2 摘要一致；完整 P2 表和正式暴露/事件率引用已进入 R2 包；有界抽样和来源重叠审计已封存。

**Interpretation：** 这证明真实参考接口和可追溯重建具备工程可行性，不证明 SUMO 已覆盖现实分布，也不证明任何阈值或因果效应。US-101 可承担主线高速跟驰风险参考；Lankershim 只能独立辅助解释；pNEUMA 只能补充单文件城市运动学。real-real 阈值和 Stage 0.5 正式通过条件仍需 0.5.2 的研究者批准。

## 交接状态

当前包把 0.5.2 需要的输入、场景职责、质量状态、权重限制和候选独立性冲突明确化，但没有冻结车型到 SUMO `vType` 映射、SUMO 时间步、覆盖阈值、校准/验证分区或新的评价算法。下一步应在研究者批准后进入 0.5.2，设计分场景指标和校准/独立验证隔离；之后才能构建无消息 SUMO 样本。Stage 0.5 Gate、Stage 0.6、Protocol Lock 和 Stage I 状态均不变。
