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
