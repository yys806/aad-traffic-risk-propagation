# AAD Experiments

> 这里只记录客观状态。完整字段以 `docs/PROJECT_REGISTRY.json` 为准，原始数字以 audit/manifest/表为准。

## 当前实验表

| 实验编号 | 实验目的 | config / 变量 | baseline | 数据集 | 主要指标 | 状态 | 客观实验结果 | 输出目录 |
|---|---|---|---|---|---|---|---|---|
| `stage_0_1` | 验证四格、五表与封存链 | seed `2026080701`，dt `0.2 s`，源事件/通道两变量 | 四格内部对照 | SUMO | 处理前等价、隔离、时钟、生命周期、物理路径 | `Verified` 工程层 | 工程检查通过；源/目标双走廊物理不连通，不能形成科学效应 | `code/outputs/formal/stage_0_1/` |
| `stage_0_2` | NGSIM 跟驰风险审计 | 候选 TTC 阈值 `2.0 s`；holdout=false | 无模型 baseline | NGSIM US-101、Lankershim calibration | measurement status、有效 TTC、事件数、TTC/DRAC 分布 | `Active` | v2 旧快照共 4,753,044 state rows、1,797,968 valid-TTC rows、4,758 events；异常和最终范围未收口 | `code/outputs/formal/calibration/stage_0_2_ngsim_v2/` |
| `stage_0_3` | 城市运动学与车型分布 | 时间加权主统计；车辆等权稳健；已批准连续性 0<Δt≤0.043 s（仅本文件）；bootstrap 2000×；R2 原始顺序/身份/质量 fail-closed 语义 | 不适用 | pNEUMA d1 | 分布与分位数 | `Completed / Closed`（2026-10-16 `pass` 有限范围） | 785 轨迹 / 1,239,475 状态；速度 TW mean=4.8382 m/s、VW mean=6.2077 m/s；R3 关闭包 fail-closed 复核全过、独立复算零差异；物理真实性 Unverified | `code/outputs/formal/calibration/stage_0_3_scientific_acceptance_20261016_r3/` |
| `stage_0_4` | 界定通信可观测证据 | RV_RX 仅作 receive-state continuity；trip 级分割 | 不适用 | SPMD RV_RX | packet schema、latency/loss/adoption 可观测性 | `Completed / Closed (Limited Scope)`（2026-10-17 Limited Scientific Acceptance，`pass_limited`） | RV_RX 连续性 Verified；RSE_BSM 车辆侧接收内容已核验；SEE-V2X 受控 PC5 候选参考；通信参数未冻结未校准；Packet 未下载（历史边界） | `code/outputs/formal/calibration/stage_0_4_limited_acceptance_v1/` |
| `stage_0_5` | 仿真—现实覆盖 | seed `20260907`，稳定哈希，最多每组 5,000 rows；场景职责/权重/阈值未冻结 | 场景内 real-real 距离候选 | NGSIM、pNEUMA、SUMO | Energy Distance、stratum coverage、场景内分层指标 | `Active` | AAD-0.5.0 只读审计完成；迁移前包含 25,000 kinematics、20,000 following、4,758 events，不能回接；无 SUMO 样本，canonical pNEUMA 与 writer 有字段冲突 | `code/outputs/formal/calibration/stage_0_5_real_reference_v1/` |
| `stage_0_6` | 数值验证与协议锁准备 | 科学容差尚未冻结 | 解析真值/物理真值 | 合成真值与前置 Gate | analytic/path truth、方向、时间步、readiness | `Active` / blocked | 技术检查通过；迁移前 readiness 为 `protocol_lock_allowed=false` | `code/outputs/formal/calibration/stage_0_6_prelock_validation_v2/` |
| `stage_1_1` | 核心效应确认 | `not_frozen` | `not_determined` | `not_created` | 尚未确定 | `Agreed` 但 blocked | 未实现、未运行、无结果 | 无 |

## 结果边界

所有当前登记结果均 `scientific_claim_eligible=false`。`evidence/results/` 中的阶段化目录名是便携索引；其中 JSON 内容保持原运行字节，因此仍可能出现旧实验编号或迁移前 Gate 文本，不能把目录重命名误读为重新运行。

## 历史实验

pNEUMA 地图匹配、候选前车和人工 QA 已由研究者批准退役，代码/测试/脚本位于 `legacy/`，完整输出位于 `code/outputs/history/legacy_experiment_ids/`，小型证据位于 `evidence/history/legacy_experiment_ids/`。其他 DRIFT 与传播 Pilot 见 `docs/HISTORY_INDEX.md`。

## 2026-10-10 当前 Stage 0.2 工程诊断包

`RES-STAGE-0.2-TASK-1.4`（任务 1.4 报告）：5,706,252 状态行、2,211,378 有效 TTC 行、5,381 原始与可靠候选事件、拒绝 0。数据为三个 US-101 TXT 与 Lankershim CSV；工程诊断包在 `code/outputs/formal/calibration/stage_0_2_task_1_4_20261010/`，不是科学风险频率或 Gate 通过。旧 v2 及任务 1.3 不覆盖。

## 2026-10-10 任务 2.2 运动学与持续性诊断

任务 2.2 对任务 2.1 的 447 个案例按同后车—前车轨迹和实际连续帧检查风险持续性、位置/速度/加速度差分与几何证据边界。多帧连续 298、单帧尖峰 3、边界/缺帧 25；自动标签 C=349、D=98。前车长度的独立几何字段不足，几何真实性保持 Unverified。固定 48 个案例审核包和模板位于 code/outputs/formal/calibration/stage_0_2_task_2_2_kinematic_review_20261010_r6/；人工审核未完成。

## 2026-10-10 任务 2.2.1

修复任务 2.2 连续段解析并生成独立验收包。r6 与新结果 1 个案例由多帧连续变为间歇；新统计为 297/3/1/25/121，自动 C=349、D=98。代表案例四源各 12 个，显式配额覆盖普通、阈值、TTC、DRAC、间距类别；人工审核未完成。


## 2026-10-11 决策归档与参数核定

四来源时间加权 TTC 中位数为 11.378882、17.170886、16.312500、14.416058 s，批准尺度规则给出 tau=15.364279 s。P2 事件参考为 4,545。连续 rho、固定窗口贡献上下界和 P2 0.2 s 尚未进入正式 pipeline。


## 2026-10-11 连续风险时间尺度验证

使用 tau=15.364279 s 计算四源分布、TTC 分箱暴露/贡献、tau/2/2tau、极端压力和 P2 成员重叠。正式目标区域 burden 因固定区域/车辆/窗口缺失保持 Unresolved。


## 2026-10-12 Stage 0.2 综合收口（当前状态）

报告：`docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`；结果：`RES-STAGE-0.2-FINAL-CLOSURE`；最终包：`code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/`。四源5,706,252行状态、P2=4,545、唯一后车2,512/车辆对3,072逐事件独立复算一致；tau=15.364279197080283。可靠跟驰边512,043.2s、闭合边208,026.3s；固定分母与连续性fail-closed原语已测试。200ms两相位P2=4,155/4,162，存在消失/连接，不能证明采样等价。极端联合屏蔽P2=4,370，447中心全部唯一、125运动学探索标记，48人工判断仍空；独立物理真实性Unverified。验收准备包可提交研究者，**非Gate Pass Candidate**，Gate仍Active，正式质量标准/有限适用域与独立物理证据待研究者；Stage0.5覆盖及四格配置非本阶段阻断。无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。

## 2026-10-18 Stage 0.5 场景设计审计

只读审计报告：docs/STAGE_0_5_TASK_0_5_0_SCENARIO_DESIGN_AUDIT.md。Stage 0.5 仍为 Active / pending_simulation_sample；US-101 为高速风险主线候选，Lankershim 为独立城市风险辅助候选，pNEUMA 仅为单文件城市运动学补充。已确认标准化 pNEUMA schema 与当前 writer 直接列契约不兼容；现有迁移前 real-reference 包和旧 map-match 路径不能作为正式输入。抽样权重、车型映射、时间分辨率、场景化 Energy Distance 和覆盖阈值均未冻结，未运行 SUMO。

2026-10-18 AAD-0.5.1：`RES-STAGE-0.5-REAL-REF-R2` 已重建。canonical pNEUMA 直连 writer 的 11 字段、质量契约、原始车型和 source SHA 测试通过；四个 NGSIM state、正式 P2=4,545 和 Stage 0.3 R2/R3 统计摘要已进入版本化输入 manifest 与便携证据。完整可靠/时间加权/车辆等权语义保持既有批准结果；哈希状态和轨迹簇只作敏感性。real-real 独立性不足，覆盖阈值、车型映射、SUMO 时间步和校准/验证隔离仍待 0.5.2 决定，未运行 SUMO，Gate 未升级。

2026-10-18 AAD-0.5.2：新增候选覆盖协议报告 `docs/STAGE_0_5_TASK_0_5_2_COVERAGE_PROTOCOL_DESIGN.md`。候选主协议为 US-101 五层必要条件（基础运动学、跟驰交互、风险可观测性、P2 暴露/事件率、场景支持），无综合分数补偿；Lankershim 为独立辅助，pNEUMA 为单文件城市运动学补充。Energy Distance 保持辅助诊断，默认 0.90/0.95 未升级为阈值；校准/验证窗口、统计不确定性、辅助范围和 0.5.3 工程契约待研究者批准。

2026-10-18 AAD-0.5.4-A：新增 `RES-STAGE-0.5-CALIBRATION-READINESS-V1`（工程审计，非 Gate 结果）。测量等价性：16 项维度（10 Equivalent/Verified、6 Engineering Consistent Only、0 阻断）+ 16 个确定性边界用例全部符合预期；封存分母与事件率被独立复现（111,425.9 s/543 与 133,505.6 s/732）。校准窗口（仅前两个，SHA 校验 + 行级过滤，验证窗口 0 行）：0750_0805 均速 11.43 m/s、净间距中位 16.87 m、事件率 17.54 veh⁻¹h⁻¹；0805_0820 均速 8.94 m/s、净间距中位 13.96 m、事件率 19.74 veh⁻¹h⁻¹。轨迹簇 CI（2,000 次重采样）：事件率 [15.11,20.50] 与 [17.47,22.36]，均速 ±0.12 m/s；逐行 i.i.d. 窄 12.7 倍。时间步敏感性：内部 0.1/0.05/0.025 s 事件数一致（1），但边界移动 0.2 s/次减半，TTC 最小值 1.794→1.868→1.906 收敛；300 s 基准墙钟 24.2/27.7/33.8 s。准入清单 `ready_to_start_stage_0_5_4b=false`（5 待批准、5 阻断）。

2026-10-18 AAD-0.5.3：新增独立 SUMO 工程骨架 `stage_0_5_sumo.py` 和入口 `run_stage_0_5_sumo_baseline.py`。US-101 `generic_highway_candidate`（3 主线段 × 3 车道 + 入口/出口匝道）以 seed=20260907、internal 0.1 s、recorded 0.1 s 完成两个工程 fixture：①baseline_mixed_demand（90 s）：8,453 state、17 vehicles（全部进入并驶出）、6,118 leader rows、724 valid TTC rows、min TTC 6.971 s、工程 P2=0、P2 可评价跟驰暴露 609.4 s（0.1693 veh-h）；②measurement_probe_queue_stop（40 s）：2,720 state、7 vehicles、1 个工程 P2 事件（onset 3.1 s、确认 3.3 s、持续 2.4 s、TTC min 1.794 s），Stage 0.2 formal-alignment adapter 给出完全一致的事件边界。同 seed 重复运行 SHA-256 一致。Lankershim/pNEUMA 为 candidate_entry_only；所有网络、需求、vType、行为、时间步、暖机/评价窗口和容差仍未科学冻结。结果 `RES-STAGE-0.5-SUMO-BASELINE-ENGINEERING-V1`，仅 engineering_only。

## 2026-10-18 AAD-0.5.4-A+ 定向补充

`RES-STAGE-0.5-CALIBRATION-GAPS-V1`：两个原始校准TXT共2,583,693行与R2状态100%连接，冲突0；来源车辆2169/2017，汽车比例96.173%/97.323%、汽车中位长4.4196m，车型/长度物理真值仍Unverified。源时钟解释952.8/999s、两源重叠89.5s，没有发现标准化时间错误。候选主线1–5、150≤y<350m；首尾按最长观测轨迹时长100.9/123.5s作候选缓冲后，保留12/11个60s片，统一密度阈值42.8767/48.0828veh/km/lane，内部覆盖720/660s；300m主线1648/1449.82veh/h/lane。局部/分层P2完整成员归属未批准，率Unresolved。

四次300s工程负载完成（SUMO1.26.0，seed20261018，recorded.1s）；.05s低/中/高实际密度41.91/48.06/54.76，墙钟100.27/103.03/116.24s，峰值合计RSS271.9/297.8/327.7MB，末时未插入0/17/23，无碰撞/teleport/守恒残差。初始化积压仍在，60s不是批准暖机；.05s自动ballistic而.1s积分器未显式固定，不能声称数值收敛。完整P2提取成本未含入。Engineering Ready有条件、Measurement Ready待有限批准、Calibration Ready=false、Reality Coverage Accepted=false；所有科学容差Tolerance Not Yet Justified，推荐路径B受限探索仅Proposal，未启动。Gate继续pending_simulation_sample，无验证/holdout/下载/正式校准/锁/Stage I/II。

依据：`docs/STAGE_0_5_TASK_0_5_4A_SUPPLEMENT_CALIBRATION_GAPS.md`及同ID的diagnostics、unified_strata、benchmark、candidate_protocol、audit。完整包`code/outputs/formal/calibration/stage_0_5_calibration_gaps_v1_final/`。Context Consistency Check：不将Proposal写入06_DECISIONS的Approved Research Decision。


## 2026-10-18 B0受限探索

2026-10-18 AAD-0.5.4-B0（RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1）：受限探索完成19/23次，4次高输入seed20261019响应未运行。统一27.78m/s上限、空初态、ballistic显式、internal.05/recorded.1、action.1、sigmaStep1；三个基准输入1087.364/1449.818/1648veh/h/lane仅实现局部密度10.37–15.75、均速约27.1，局部低速/P2均0。tau2三次末期未服务21/22/71，入口main0约2.5–20.1m有低速插入/加速，局部段无拥堵。B0-EXEC-STOP-01：原调度器未因completed+blocker停止，发现后人工停止，源码停止后修复并测试；最后worker峰值内存Unverified。推荐先批准需求边界/最小结构对照，不继续参数搜索掩盖状态支持缺口。所有结果exploratory_diagnostic_only、scientific_claim_eligible=false；Gate=pending_simulation_sample、Calibration Ready=false、Reality Coverage Accepted=false、正式容差Tolerance Not Yet Justified、Energy Distance上界Not Identifiable；无验证/holdout/正式校准/锁/Stage I。依据：docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md、同ID证据和execution_ledger。 全部300s固定五个60s片及5s图表保留；19次合计约541.1s、已监控峰值595.18MB、约224MB产物。高输入响应缺第二seed，无统计确认。
