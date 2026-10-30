# Simulator–NGSIM Formal Comparability Matrix

日期：2026-10-30。工作包：AAD Round2 Closure WP2。

**Verified：当前一般 Formal P2 已符合研究者批准的 C；无需修改正式测量源码。** C 的事件资格按车辆对、身份与时间连续性判断，不要求成员同 native lane。D1 继续使用 same-native-lane 的局部诊断事件和暴露定义。**Unknown：SUMO–NGSIM 科学等价性。** 所有输出保持 formal_equivalence_accepted=false；合成测试不认证物理身份、距离或路径。

本报告与已批准决策 [AAD_ROUND2_RESEARCH_DECISIONS_20261030.md](AAD_ROUND2_RESEARCH_DECISIONS_20261030.md) 配套。Task2/3 的旧候选或待决文字仍是历史，不追溯改写；本轮 C/B 决策已由研究者明确作出。

## 影响范围与执行边界

- 新增独立离线审计脚本、定向测试、此报告及专属证据包；不修改共享正式测量实现、config、Rule A、身份规则或 Gate。
- 接口范围：FormalRisk extractor → NGSIM event extractor；SUMO native → formal source projection → FormalRisk extractor；独立 D1 local measurement。
- 只使用 16 个既有 Task2 内存合成案例、8 个新内存反例和已登记 Task2–Task7.2 便携证据。未读新的真实/仿真轨迹、第三窗口或 locked holdout，未运行 SUMO/TraCI。
- 验证采用 5 个直接相关测试文件；不跑全量 pytest 或全仓 compileall。seed 不适用：确定性合成输入，每案例执行一次，不是新机制实验。

审计脚本：[audit_stage_0_5_round2_closure_comparability.py](../code/scripts/audit_stage_0_5_round2_closure_comparability.py)。新增测试：[test_stage_0_5_round2_closure_comparability.py](../code/tests/test_stage_0_5_round2_closure_comparability.py)。机器包：[RES-AAD-ROUND2-CLOSURE-COMPARABILITY-20261030](../evidence/results/RES-AAD-ROUND2-CLOSURE-COMPARABILITY-20261030/)。

## 八维矩阵

Verified 仅表示表内明确限定的定义或工程范围已核验，不表示整个维度的科学等价性。Unknown 表示尚未闭合的跨接口或物理支持。

| 维度 | 当前实现和证据 | 最终状态 | 已验证范围与限制 |
|---|---|---|---|
| Event qualification | FormalRisk.PAIR_KEYS 不含 lane；extract_formal_source_events、SUMO build_sumo_p2_events 和 extract_sumo_formal_p2_events；Task2 换道、阈值及持续时间案例 | Verified | C 已实现。正常连续有效输入的成员、onset、confirmation 一致；显式 flags 端点及不一致预测量不在已验证等价域内。 |
| Identity | FormalRisk.continuity_is_valid、SUMO.following_link_is_valid/build_sumo_formal_source_frame；leader/incarnation 切换与 missing_leader_self_rows | Verified | scoped follower/leader incarnation/trajectory 守卫已核验。native/D1 接受上游已解析 leader 标签，formal 还需 leader 自身时刻的 frame；物理身份仍 Unknown。 |
| Continuity | 显式 identity_break/observation_gap 保真；FormalRisk 当前端标记与 native/D1 两端标记不同 | Unknown | 相同事件数不能证明成员或 onset 等价。0.2 s 标记反例产生 formal onset 0.2 s、native/D1 onset 0.3 s。 |
| Time | NGSIM 原始 row/frame/anchor 与 SUMO 派生 observation index/time_s；late-entry、粗 cadence、源时钟异常反例 | Unknown | 100 ms 正常域和晚入场绝对仿真时钟已核验。formal projection 重编号并覆盖输入 frame/global_time；两数据源绝对原点及视频 PTS 不可据此认证。 |
| Lane/path | C 与 D1 分层；B 要求真实时间化 lane/edge 连接及车辆交互见证；Task7.1/7.2 | Unknown | lane token、拓扑及合成 road_connection_witness 布尔值均不是实际经过证据。当前无已核验独立物理路径/到达时间。 |
| Measurement | real_trajectory.add_ngsim_leader_ttc、SUMO.compute_sumo_measurements、FormalRisk observed_confirmation_time | Verified | 可靠正 gap/closing 域内 TTC=gap/closing，0<TTC<2 s、跨度>=0.2 s、100 ms 不变。native 信任矛盾预计算 TTC 的反例仍未解决，不能推及物理精度。 |
| Exposure | D1.local_d1_measurement、SUMO.compute_exposure；Task4/5 onset 归属及边界案例 | Verified | D1 same-native-lane 诊断分母与一般 Formal P2 分母分别保留；不得用 C 事件数除以 D1 暴露。历史源 167/159 与 SUMO 0/0 分层保留。 |
| Missingness | measurement_status、缺 leader、Unknown boolean、NGSIM 边界观测；Task2 与补充探针 | Unknown | missing/invalid/not_applicable 不补零。formal/D1 对 Unknown boolean 硬拒绝，native truthiness、deterministic absent-field default 及来源可观测性不同。 |

精确函数位置和 SHA256 见 source_bindings.json。核心位置（当前基线 80abab044063803219f6ceadfeb3562c3939aaa1）：

| 文件 | 函数/位置 | 核验内容 |
|---|---|---|
| code/src/riskprop/formal_risk_measurement.py | PAIR_KEYS:57–58；extract_formal_source_events:61–129；continuity_is_valid:269–298 | source/pair 范围、确认时间、当前端 flags、完整 clock 检查，无 lane 限制 |
| code/src/riskprop/ngsim_risk_calibration.py | extract_rear_end_events:201 起 | 原始事件分段、显式中断、原始成员行保留 |
| code/src/riskprop/stage_0_5_sumo.py | compute_sumo_measurements:1070–1162；following_link_is_valid:1226–1286；_risk_mask:1302–1304 | TTC 生产域、native 两端标记和源 clock；预计算 mask 信任边界 |
| code/src/riskprop/stage_0_5_sumo.py | build_sumo_formal_source_frame:1620–1692；extract_sumo_formal_p2_events:1695–1742 | flags 保真、派生 frame/time、leader 自身 frame、科学等价 false |
| code/src/riskprop/stage_0_5_d1_measurement.py | local_d1_measurement:43–161，尤其90–107/113–157 | 独立 same-native-lane、两端 flags、可靠暴露、正 TTC、onset 归属 |

## 合成反例与成员证据

原 Task2 16 案例全部以当前源码重跑，历史包不重写。逐接口完整输入/输出位于 synthetic_case_inputs.json、synthetic_case_results.json。其覆盖正常跟驰、lane/edge、leader/incarnation 切换、显式 flags、缺帧、负 TTC、2 s 阈值、0.2 s 持续边界、退出重入、窗口边界和无 leader。

8 个补充探针位于 additional_probes.json。基准为 t=0.0…0.6 s 的 7 帧、已解析固定 pair、有效低 TTC。

| 探针 | native | formal-aligned | D1 | Observation |
|---|---|---|---|---|
| normal | onset 0.0、confirm 0.2、end 0.6、7成员 | 相同 | 相同 | 有效连续域内成员及确认一致。 |
| identity_break at 0.2 | onset 0.3、confirm 0.5、4成员 | onset 0.2、confirm 0.4、5成员 | 同 native | flags 未丢失，但端点约定不同。 |
| observation_gap at 0.2 | onset 0.3、confirm 0.5、4成员 | onset 0.2、confirm 0.4、5成员 | 同 native | 三接口各1事件不足以证明等价。 |
| source_frame_discontinuity | onset 0.2，源 frame 异常使前段切断 | onset 0.0；重编号后7成员 | onset 0.2 | projection 不认证原始 frame 连续性。 |
| source_clock_discontinuity | onset 0.2，原始毫秒步长异常切断 | onset 0.0；按 time_s 重建 clock | onset 0.2 | 原始 clock 与派生 clock 支持不同。 |
| missing_leader_self_rows | 依赖上游 resolved identity，1事件 | 缺 leader_frame，0可靠事件 | 1事件 | leader 自身观测要求不同。 |
| unknown_flag | 按当前 native truthiness 行为保留结果 | Stage05EngineeringError | MeasurementContractError | Unknown 不应被当作已证连续；此处保留拒绝。 |
| negative_ttc_premeasured | ttc_valid=true 且 TTC=-1，native mask 可接受1事件 | ValueError：non-risk event member | 0事件 | 有效生产器不会生成该矛盾输入；输入契约仍有防御差异。 |

这些是合成工程反例，**不是封存源区零事件的原因证据**。既有 post-R2/Task6 显示可靠源支持内没有任何 0<TTC<2 状态；不能用本轮反例挽救已关闭的 minGap=1.0 原分支。

## C 之外冲突记录

### CF-CONTINUITY-ENDPOINTS

- Documented Intent：检查并保持 explicit continuity flags、身份与时钟保真；C 不授权改变既有身份或时间规则。
- Actual Implementation：native/D1 阻断前后两端有 flag 的链接；FormalRisk.continuity_is_valid 只检查 current 的 identity_break/observation_gap。
- Evidence：additional_probes.json 中两 flag 案例；同为1事件，但 onset/confirm/members 为 0.3/0.5/4 对 0.2/0.4/5。
- Affected Files：code/src/riskprop/formal_risk_measurement.py、code/src/riskprop/stage_0_5_sumo.py、code/src/riskprop/stage_0_5_d1_measurement.py。
- Conflict：成员资格和确认时间不能宣称跨接口一般等价；修正会改变 C 之外的连续性语义。
- Status: Awaiting Researcher Decision。

### CF-SOURCE-CLOCK-PROJECTION

- Documented Intent：核查原始时钟、row/frame 和时间原点，不能以适配接口通过代替原始观测连续性。
- Actual Implementation：formal projection 从 time_s 重建 global_time_ms，按 incarnation 重建 observation_index/frame_id/original_row_number；native/D1 消费可用原始字段。
- Evidence：source_frame_discontinuity/source_clock_discontinuity 反例保留原始输入与投影后时间字段；onset 0.2 对 0.0。
- Affected Files：code/src/riskprop/stage_0_5_sumo.py（build_sumo_formal_source_frame、following_link_is_valid）、code/src/riskprop/stage_0_5_d1_measurement.py。
- Conflict：投影只提供已声明仿真 recorder 域的字段语义，不能认证外部预计算输入的原始 frame/clock；改变此行为需要另行输入契约决定。
- Status: Awaiting Researcher Decision。

### CF-PREMEASURED-QUALITY-AND-LEADER-SUPPORT

- Documented Intent：未知/缺失不视作安全，可靠 TTC 为正、身份及 leader 见证可追溯。
- Actual Implementation：native mask 信任 ttc_valid；formal 正值检查拒绝负 TTC。native/D1 可依上游已解析 leader 身份，formal 需要同刻 leader 自身 frame。formal/D1 硬拒绝非显式布尔标记；native 使用 truthiness。
- Evidence：negative_ttc_premeasured、missing_leader_self_rows、unknown_flag；生产器负 gap/非闭合反例另由新增测试确认不会生成有效 TTC。
- Affected Files：code/src/riskprop/stage_0_5_sumo.py、code/src/riskprop/formal_risk_measurement.py、code/src/riskprop/stage_0_5_d1_measurement.py。
- Conflict：预计算接口的防御要求和可观测支持不同；本轮不擅自统一质量/身份规则，不改正式生产器。
- Status: Awaiting Researcher Decision。

## B 物理路径资格

Agreed 的 B 是独立于 C 的见证标准：pair 两身份可追踪；有时间化 lane/edge；有连续 follower–leader 关系；道路连接有物理依据；转换顺序可核验。五项均需实际观察及可审计出处。旧 Task2 的 synthetic road_connection_witness=true 只测试一个候选分段逻辑，**不满足真实 B 认证**。

当前 Task7.1/7.2 仍无闭合的许可、video PTS/Global_Time 和 Camera7/8 源区完整覆盖。路径和物理到达均 Unknown；不根据 onset、confirmation、lane ID 或拓扑填补未观测路径。

## 验证结果与可复现信息

执行环境：Windows 原生 D:/miniconda/python.exe，Python 3.13.5、pandas 2.2.3（精确环境见 validation_record.json）。本地输出 code/outputs/formal/calibration/round2_closure_comparability_20261030/。完整原始 stdout 只留本地，未放入便携证据。

首次定向命令由 validation_record/test_attempts 精确记录：5文件，**100 Passed、3 Failed**。三个失败全部来自该解释器缺少 pyarrow/fastparquet，均为已有 Parquet 写入测试；新增13项全部 Passed。原始失败保留在本地 pytest_stdout.txt，不追溯伪装成首次通过。

第二次使用 POSIX 路径形式的 --deselect 在 Windows 未匹配这三个节点，仍为100 Passed、3 Failed；这是审计执行筛选缺陷，原始 stdout_attempt_2 和 test_attempts.json 完整保留。修正为三个唯一测试名的 -k 排除后，第三次 **100 Passed、3 deselected（16.38 s）**，关闭 pytest cache 并使用独立 basetemp。没有修改历史测试。三个节点明确列为 **Blocked / Not Passed**：

- test_stage_0_5_measurement_equivalence.py::test_guard_denies_row_scoped_reads_outside_the_calibration_windows
- test_stage_0_5_measurement_equivalence.py::test_calibration_states_read_helper_refuses_a_foreign_window
- test_stage_0_5_d1_measurement.py::test_actual_state_runner_uses_d1_not_point_exposure

复现命令：

~~~powershell
python code/scripts/audit_stage_0_5_round2_closure_comparability.py --run-tests --exclude-known-parquet-tests
~~~

上述排除不代表三项通过，不安装依赖、不改历史测试。新增文件定向语法 AST 检查 Passed。Task2–Task7.2 的8个既有便携包按原 SHA256SUMS 逐文件验证，**95个列出文件全部 Passed**，运行前后哈希保持一致；包内数量分别11、7、11、8、20、17、12、9，见 historical_integrity 字段。一次有据解释器依赖核查确认 D:/miniconda/python.exe 的 pyarrow/fastparquet 均无可导入 spec，原始 metadata 仅留本地 dependency_check.json。

Not Run：新 SUMO、TraCI、新轨迹分析、第三窗口、holdout、视频下载、盲审、机制实验、全量 pytest、compileall。Not Applicable：本合成审计的随机seed/运行重复设计和科学不确定性估计。

## 结论层级

- Observation：C 已实现，D1 独立；正常有效域内事件成员和确认可对照；flag端点、原始clock投影、缺leader/预计算质量存在明确反例；历史8包未改变。
- Interpretation：仅给出工程含义——现有接口有受限可比范围，尚不支持一般科学等价声明；不解释真实/仿真差异的因果来源。
- Hypothesis：本工作包不新增科研机制假设。
- Proposal：研究者后续决定以上 C 之外的接口契约；当前维持科学等价 false、物理路径 Unknown 和全部科研 Gate。
