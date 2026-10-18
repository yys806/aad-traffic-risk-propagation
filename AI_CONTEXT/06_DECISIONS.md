# AAD Confirmed Decisions

本文件只记录研究者明确决定或已存在的稳定项目约束，不把 Codex 分析写成科研决策。

## 2026-10-16 — Stage 0.3 最终科学验收五项决定（AAD-0.3.3）

状态：`Agreed Research Design / Approved`；研究者通过任务 AAD-0.3.3 明确批准，直接落实，不再另行请求裁决。验收依据：`RES-STAGE-0.3-BOUNDARY-REPAIR-R2`（785 唯一轨迹、1,239,475 状态、时间戳 [38.40, 888.00] s、可靠暴露 49,547.6 vehicle-seconds、原始顺序/身份/质量审计通过）。

1. **正式适用范围**：仅 `dataset/pNEUMA/20181101_d1_0800_0830.csv` 实际观测车辆的速度、纵向加速度与车型组成等描述性城市运动学参考；不宣称完整覆盖 30 分钟连续交通观测，不代表雅典或城市总体交通，缺少证据不推断时间字段绝对原点。
2. **时间连续性规则（正式科学参数，仅当前 25 Hz 文件）**：`0 < Δt ≤ 0.043 s`；保持 R2 原始记录顺序判断、身份可靠性、解析质量与 fail-closed 规则；不插值、不补帧、不跨缺口计权；原工程锚定容差升格为已批准参数，历史敏感性记录保留。
3. **极端运动学观测**：原始保留、异常标记、敏感性对照；可评价的极端速度/加速度不自动删除；原始分布为主要结果；`|a|>2`、`|a|>5 m/s²` 仅探索性诊断阈值；独立物理真实性保持 `Unverified`；不得直接认定为错误或危险行为。
4. **描述性分类阈值**：低速、近静止、近零加速度阈值保留用于统计描述，不批准为正式风险分类或质量排除标准。
5. **Scientific Gate**：`pass`；`Stage Status = Completed / Closed`。仅针对当前单文件的有限描述性城市运动学校准，不含独立物理真实性、事故预测、AAD 因果效应或 SUMO 现实覆盖验证。

影响范围：阶段 0.3 关闭；R1/R2 历史产物保留不覆盖；Stage 0.5 车型映射、时间权重抽样与覆盖阈值继续独立待决；Protocol Lock 与 Stage I 不因此解锁；locked holdout 不访问。

## 2026-10-16 — Zotero AAD 文献库分类决定（AAD-0.3.4）

状态：`Approved`（研究者决定；执行记录与决定分开，见下）。

- **决定内容**：批准 `TJU → AAD` 调整为六个主题集合：01_风险事件与安全指标、02_混合自动驾驶传播与控制、03_闭环仿真与场景测试、04_人类行为交互与轨迹预测、05_非局部交通流模型（原 05_非局部风险与因果验证更名并拆分）、06_类超距与因果理论（新建）；目标计数 7/11/7/4/11/16（共 56 条）。批准退役期刊维度的 `NC_统一汇总`（11 篇 NC 论文改由 `NC` 标签追踪）。批准本次**不合并、不删除、不修改** 7 对 AAD↔DRIFT 同 DOI 重复条目（双方 item key 保留，合并需另行讨论）。
- **执行授权**：批准通过 Zotero 官方本机 API 授权对话框（`/api/local/authorize`）执行上述调整。
- **影响范围**：文献管理流程（`doc/literature-notes/`），不影响任何科研阶段、统计或 Gate。
- **执行状态**：2026-10-17 已通过官方授权接口全部执行并核验（六集合计数达成、56 item key/附件无丢失、DRIFT 未动）；逐条 before/after 记录 `doc/literature-notes/zotero_reorg_2026-10-17_execution.json`。59 份退役 PDF 与 56 条论文的 3 份差额保留 `Unverified`。

## 2026-09-10 — pNEUMA 当前职责

- 日期：2026-09-10。
- 决策内容：研究者明确决定批准 pNEUMA 前车推断与人工复核退役；pNEUMA 当前只承担城市运动学校准。
- 相关背景：阶段化迁移发现旧人工 QA Gate 与拟定的新职责冲突，Codex 停止并请求决定后获得批准。
- 影响范围：阶段 0.3、阶段 0.5、注册表、代码/脚本/测试 legacy 边界及历史证据。
- 对应代码：`code/src/riskprop/real_trajectory.py::read_pneuma_wide()`；退役实现位于 `code/src/riskprop/legacy/pneuma_mapmatch.py`、`pneuma_qa.py`。

## 2026-09-10 — 长期人机协作机制

- 日期：2026-09-10。
- 决策内容：Codex 作为 Research Engineer；科研决策归研究者，ChatGPT 网页端承担讨论与科研解释；Codex 维护工程、实验事实、Git 和 AI_CONTEXT。
- 相关背景：项目需要由研究者、ChatGPT 与 Codex 长期协作，并能从 GitHub 快速恢复状态。
- 影响范围：`AGENTS.md`、`AI_CONTEXT/`、任务验证、提交和推送流程。
- 对应代码：`code/src/riskprop/project_docs.py` 检查长期上下文文件。

## 已有稳定约束

- AAD 是当前项目，`D:\shen\TJU\DRIFT` 只读。
- 现有阶段 0 结果不构成核心科学效应；协议锁通过前不得进入阶段 1.1。
- 缺失不补零，不可观测不推断，不通过看 holdout、挑种子或降低阈值制造正向结果。
- 历史结果保留式归档；机器事实源与人类索引同步更新。

## 2026-10-10 任务 1.4 边界授权

Agreed：具有明确字段证据的诊断片段可作为候选事件的保守连续性边界，不视为官方物理轨迹；不确定前后车不得进入可靠事件，原始候选和拒绝原因须保留。来源 unknown 不伪造，最终科学事件规则与阈值未决定。实现与全量证据见任务 1.4 报告及 RES-STAGE-0.2-TASK-1.4。


## 2026-10-11 — Stage 0.2 科研设计确认

状态：`Agreed Research Design`；以下设计已由研究者确认，但不等于已实现、已验证或 Scientific Gate 已通过。

- 研究范围：目标区域纵向闭合风险负担，不代表总体交通安全风险或事故概率。
- 源事件：P2 为主要候选（可靠 TTC<2.0 s，连续风险观测首末跨度≥0.2 s）；`t_confirm` 必须是实际观测确认时刻；缺失/身份中断不代表风险解除；短间隔事件不合并，消息去重另行处理；TTC 触发，DRAC 仅用于严重程度和稳健性；P1/P3 保留为敏感性对照。
- 连续风险：可靠有效闭合 TTC 使用 `rho=exp(-TTC/tau)`，不以 P2 阈值截断；保留 valid/not_applicable/invalid/not_measurable 语义；区分瞬时 rho 与贡献 b；未知归属或测量贡献用 [0,1] 上下界；固定目标车辆/边界/窗口、无跨缺帧插值、车辆等权、窗口时间积分和上下界 DID。
- 校准：tau 使用四来源可靠闭合 TTC 的来源内时间加权中位数，最终为排序中间两来源平均；同时报告来源异质性及 tau/2、2tau；极端值保留并做敏感性；NGSIM 现实参考分为基础跟驰、连续风险负担和 P2 事件特征；SUMO 覆盖属于 Stage 0.5。
- 未冻结：消息去重时间窗、正式质量门槛、Stage 0.5 容差、最终实现默认值和 Protocol Lock。

## 2026-10-12 — Stage 0.2 最终有限科学验收范围与事件率分母

状态：`Agreed Research Design`；本决定授权在限定范围内完成 Stage 0.2 正式验收与关闭。

- 科学目标：仅验收四个批准 NGSIM 校准来源支持的纵向跟驰风险代理指标测量与描述性现实校准；不验证事故发生概率、真实危险识别准确率、P2 全局最优性或 AAD 核心因果效应。
- 有限范围：四源分别报告；100 ms NGSIM 连续性语义为正式参考；200 ms 两相位仅作为迁移限制，不视为采样等价；保留缺失、无效、非闭合与极端观测；极端屏蔽只作稳健性分析；独立物理真实性保持 `Unverified`；不外推到其他道路、总体交通或 SUMO。
- 正式事件率：`P2_event_rate = P2_event_count / reliable_following_exposure_time`，统一报告 events / reliable-following vehicle-hour；可靠闭合暴露另列，不得混用。该事件率是可靠观测条件下的代理事件频率，不是事故概率。
- 验收原则：批准规则和统计必须可复现；来源、身份连续性、风险状态、事件时间和暴露分母必须有证据；缺失、异常和敏感性如实报告；缺少独立事故真值不自动否决有限描述性校准，但若测量缺陷足以使限定结论失效则阻断。
- 阶段边界：Stage 0.3、Stage 0.5、目标区域/车辆/四格窗口、消息机制、Stage 0.6、Protocol Lock 和 Stage I 不因本决定完成；不得访问 locked holdout。

## 2026-10-12 — Stage 0.2 最终可评价暴露分母裁决

状态：`Agreed Research Design`；研究者正式批准用于 Stage 0.2 P2 代理事件率。保持 P2=4,545、P2 规则、tau、rho及历史产物不变。

- 正式分母为可靠且 P2 可评价的跟驰暴露时间。可靠相邻观测边两端均须可评价，且来源、诊断时钟、前后车身份、帧号、时间戳和实际连续性符合正式规则。
- `valid` 正闭合 TTC 与 `not_applicable` 且可靠确认正间距、非闭合均可评价并纳入；`invalid/non_positive_gap`及其他不可评价状态排除。
- 保留所有状态、原始观测和质量统计；排除不可评价暴露不代表无风险，不插值、不补零、不改变原始状态。可靠跟驰暴露仍单独报告，不与可评价分母混称；可靠闭合暴露另行报告。
- 正式事件率为 `P2_event_count / P2_evaluable_following_exposure_time`，单位 `events / P2-evaluable following vehicle-hour`，仅解释为可评价可靠观测下的代理事件频率，不是事故概率。

## 2026-10-17 — Stage 0.4 有限科学验收范围决定（AAD-0.4.8）

状态：`Approved Research Decision`；研究者经任务 AAD-0.4.8 明确批准。

- **决定内容**：①Stage 0.4 不再以获得完整、精确的真实 V2V 时延、PDR 与距离衰减模型为本阶段必须目标；②接受现有 SPMD/SEE-V2X 支持的有限证据范围与已确认的不可观测/不可识别限制；③停止进一步大规模通信数据集搜索、下载与重复复核；④未校准部分作为标记为不确定的实验/敏感性参数处理；⑤不授权将未经验证参数标为真实校准、不修改核心因果识别规则、不启动 Stage I；⑥以 **Limited Scientific Acceptance** 为目标验收 Stage 0.4。
- **验收对象（仅）**：真实通信数据的可观测性边界、已验证的描述性通信证据、后续通信仿真参数的不确定性处理原则。**Gate=`pass_limited`；Stage Status=`Completed / Closed (Limited Scope)`**。
- **不验收**：真实通信性能模型准确性、真实 PDR/时延数值校准、距离相关通信函数、信息/控制器采用、AAD 核心因果效应。
- **边界**：RV_RX V3 的 `pending_official_packet_access` 与原始 Packet HTTP-403 记录保留为历史事实，不改写；Protocol Lock 与 Stage I 不因本验收解锁；locked holdout 不访问；Stage 0.5/0.6 其余前置条件保持未完成。
- **影响范围**：阶段 0.4 状态与 readiness、Stage 0.5 承接、Stage 0.6 通信参数不确定性声明规则。
- **对应证据**：`RES-STAGE-0.4-LIMITED-SCIENTIFIC-ACCEPTANCE-V1`（`code/outputs/formal/calibration/stage_0_4_limited_acceptance_v1/`）。

## 2026-10-18 — Stage 0.5.1 真实参考职责与统计口径授权

状态：`Approved Research Decision`；研究者在 AAD-0.5.1 开始前明确批准，以下仅记录已批准范围，不冻结后续 SUMO 校准参数。

- **场景职责**：US-101 三个窗口承担高速公路跟驰风险主要参考；Lankershim 作为独立城市道路跟驰风险辅助参考，不与 US-101 合并为 iid 总体，也不是 US-101 主 Gate 的必要条件；pNEUMA 仅承担单文件城市混合交通运动学（速度、纵向加速度、原始车型和分车型统计）。pNEUMA 不承担前车推断、TTC、DRAC、P2 或风险事件。
- **canonical 接口**：Stage 0.5 正式入口直接消费 Stage 0.3 canonical schema，保留 `vehicle_id`、原始 `vehicle_type`、速度/加速度、`quality_status`、`time_weighting_eligible`、来源指纹以及来源/站点/窗口；缺字段、类型/身份/数值/质量契约错误 fail-closed。legacy 输入若保留只能显式标识，不得静默接入正式路径。
- **统计口径**：完整可靠观测及已有时间加权语义为主统计；车辆等权为并列补充；轨迹簇抽样用于连续性/车辆代表性敏感性；稳定哈希状态抽样仅用于有界工程预览或诊断。任何有界抽样不得冒充完整分布或用于重算正式 P2 事件率。
- **边界**：以上授权不决定真实车型到 SUMO `vType` 映射、SUMO 时间步、覆盖阈值、校准/验证划分或 real-real 科学上界；Stage 0.5 Gate 仍 `pending_simulation_sample`，Protocol Lock 和 Stage I 继续阻断。
- **证据**：`RES-STAGE-0.5-REAL-REF-R2`、`docs/STAGE_0_5_TASK_0_5_1_REAL_REFERENCE_REBUILD.md`。

## 2026-10-18 — Stage 0.5.2/0.5.3 工程范围与协议原则授权

状态：`Approved Research Decision`；研究者批准以下原则用于 Stage 0.5.3 工程建设。具体网络、需求、车型、驾驶行为、时间步、容差和 Gate 判据仍未冻结。

- **US-101 分区**：07:50–08:05 与 08:05–08:20 作为 calibration，08:20–08:35 作为预先指定的 temporal validation；第三窗口已有公开摘要，不能称为完全盲化；三窗口同站点，只支持有限同道路时间外推，不能宣称跨道路泛化；跨窗口字符串车辆 ID 不等于物理身份；validation 失败必须进入可追溯新协议版本。
- **五层必要条件**：基础运动学、跟驰交互、风险可观测性与评价资格、正式 P2 事件/可评价暴露、场景支持与样本质量。各层不能用综合分数互相补偿。
- **风险可观测性**：区分交通状态导致的不可评价、真实采集/身份缺陷和 SUMO 输出工程错误。SUMO 不人为复制 NGSIM 采集缺陷；缺失原因必须分别记录。
- **P2 关系**：P2 数量、暴露和事件率不是互相独立的精确匹配目标；事件率继续为完整 P2 事件数除以 P2 可评价跟驰 vehicle-hour。事件定义、连续性、身份和暴露分母正确属于必要条件；事件率是代理频率，不是事故概率。
- **容差方法**：以完整可靠观测为主，按车辆/轨迹簇处理相关性，结合来源内变化、窗口差异和未来 AAD 风险敏感性形成候选容差；任何具体数值仍未批准，不得由未来 SUMO 结果倒推。
- **Energy Distance**：仅作场景内多维辅助诊断；`minimum_stratum_coverage=0.90` 与 `real_real_quantile=0.95` 仍是工程默认值，不是科学阈值；当前 real-real 上界保持 `Not Identifiable`。
- **辅助场景职责**：Lankershim 是独立城市道路跟驰风险辅助，不进入 US-101 主 Gate；pNEUMA 仅承担速度、纵向加速度、车型组成和分车型运动学，不承担 TTC、DRAC、前车、P2 或风险事件。
- **Stage 0.5.3 工程范围**：允许建立分场景配置、候选网络/需求结构、可配置 vType、无消息基线入口、统一状态输出、TTC/P2 适配接口和校准/验证隔离。网络、需求、车型映射、驾驶行为、时间步、暖机/评价窗口、容差和 Gate 判据必须继续标记为 engineering fixture 或 pending，未获批准前不得写成科学冻结。
- **参数分类**：场景参数必须显式分为 `engineering_fixture_only`、`researcher_approved_scientific`、`pending_scientific`；0.5.3 中任何网络、需求、车型映射、驾驶行为、时间步、暖机/评价窗口都不得写入 Approved。
- **工程语义统一（工程决定，非科学参数）**：`closing_speed_mps = follower_speed_mps - leader_speed_mps`；TraCI `getLeader` 距离是「物理保险杠净间距 − 后车 minGap」，`net_gap_m = leader_traci_distance_m + follower_min_gap_m`，并以同车道独立几何残差 0.0 m 核验。Stage 0.1 的 `relative_speed_mps = leader − follower` 符号相反，不得复用其 TTC 解释。
- **边界**：`experiment_mode=no_message_baseline` 不等同于 Stage I 正式 `(0,0)`；Stage 0.5 Gate、Protocol Lock 和 Stage I 状态不变。
