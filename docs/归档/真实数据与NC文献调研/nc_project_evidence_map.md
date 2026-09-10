# NC 结构与本项目证据映射

## 一、判定口径

本文件只做结构和证据映射，不写论文正文。证据状态使用四级：

- **已证明**：在明确模型/数据范围内有数学证明或可完全重现的决定性验证；不外推为真实交通普遍规律。
- **得到支持**：预注册主检验、机制审计和替代解释检查一致支持命题，但仍受仿真、场景或实现范围限制。
- **初步提示**：方向一致或机制链部分成立，但缺少主检验、外部效度或原始证据复核。
- **尚未验证**：现有材料不能支持该层主张。

`docs/归档/项目记录/项目历史/findings.md` 与 `docs/归档/项目记录/项目历史/progress.md` 记录了多轮合流实验。2026-08-07 的首轮冻结合流实验未通过门槛（`docs/归档/项目记录/项目历史/progress.md` L24–29；`docs/归档/项目记录/项目历史/findings.md` L23–26），之后通过独立“源事件资格”阶段和补充锁重新冻结正式种子，2026-08-08 的修正版记录为 14 项门槛通过（`docs/归档/项目记录/项目历史/findings.md` L679–686）。这两批结果应在论文中作为版本演进和失败账本分别保存，不能把早期失败结果覆盖或并入后期主统计。

此外，当前 Windows 项目树中没有定位到文档所写的 `outputs/decisive_*` 原始结果目录；本表对关键数值的状态写为“项目记录支持，原始产物待统一归档复核”，而不冒充已在本轮重新计算。

## 二、核心主张—证据矩阵

| 待写主张 | 当前状态 | 已有证据 | 仍缺什么 | 允许的表述边界 |
|---|---|---|---|---|
| 类超距作用可被严格定义为信息介导的非最近邻风险效应 | 得到支持（定义层） | 理论稿定义完整链 `S_A -> M_A -> delivery -> adoption -> U_B -> R_B`，区分 `G_P/G_I`，给出四格潜在结果、时间不等式和证伪条件（`docs/归档/项目记录/项目历史/类超距作用理论整理_2026-08-08.md` L5–70）。 | 统一符号；把“无直接边”和“无任何物理路径”分别定义；说明 estimand 依赖的风险指标和处理版本。 | 可称“本文提出并操作化”；不能称“交通领域已公认规律”。 |
| 信息图有边不等于消息已交付/采用 | 得到支持（协议与实现语义），待原始日志复核 | 理论稿明确区分可传输、交付和采用；决定性规格要求 event/source/receiver、生成、发送、丢包、交付、年龄、核验、采用全生命周期（理论稿 L20–39；设计规格 L38–49）。 | 把每个正式 trial 的完整日志和 schema 随归档提交；检查空值和异常顺序。 | 可称“实验协议显式区分并审计”；不能从接口存在推断现实车辆采用。 |
| 四格交互 `Delta_NL` 识别指定消息的增量信息效应 | 得到支持（仿真内） | `r00/r01/r10/r11` 只改变源风险与指定通道；定义 `Delta_NL=(R11-R10)-(R01-R00)`；采用前轨迹一致和控制格零采用被列为门槛（设计规格 L38–49, L88–122）。 | 形式化 consistency/SUTVA 范围；证明 C=0 不改变计算负载或其他控制路径；原始配置 diff；多控制器重复。 | 对风险负担指标，负值才表示降低风险；不能脱离指标方向解释符号。 |
| 双走廊存在仿真内信息介导的非物理路径效应 | 得到支持，待本地原始产物复核 | 项目记录：80/80 有效，20/20 配对为负，均值 -0.1312075，95% CI [-0.1320726,-0.1303981]，拓扑审计 80/80 跨走廊路径为 0，机制门槛通过（`docs/归档/项目记录/项目历史/findings.md` L19–21；`docs/归档/项目记录/项目历史/progress.md` L20–22）。 | 把配置、预注册、80 次原始 state/protocol/risk/emission、run-level 表、拓扑审计、统计脚本和 checksum 归入当前项目；由一条干净命令重算。 | 可称“在冻结双走廊仿真中支持信息介导效应”；不能称真实交通规律、物理超距或真实 V2X 已验证。 |
| 错误来源、错误时间和 delivery-only 不会改变动作 | 得到支持，待原始产物复核 | 项目记录 36/36 独立通信核验；错误来源、错误时间、delivery-only 均 0 采用，中/重通信受损采用 12/2 步（`docs/归档/项目记录/项目历史/findings.md` L21；`docs/归档/项目记录/项目历史/progress.md` L22）。 | 逐消息日志、效应而非只报采用次数、过期 placebo、随机无关消息 placebo。 | 可称“门控逻辑通过预设负对照”；不能证明所有伪消息都无效。 |
| 合流场景中冻结机制可迁移 | 得到支持（修正版仿真），但必须保留早期失败 | 早期冻结实验只 12/20 形成真实源事件，主门槛失败（`docs/归档/项目记录/项目历史/progress.md` L24–29）；独立资格化和重新冻结后记录 80/80 完成、`Delta_NL=-0.0102834`、CI [-0.0119463,-0.0082990]、18/20 为负、14 项门槛通过（`docs/归档/项目记录/项目历史/findings.md` L679–686）。 | 原始产物统一归档；解释新资格阶段为何不是看过结果后的 outcome tuning；与双走廊同参数/归一化对照；更多合流几何和需求。 | 只能称“物理连通合流场景的机制迁移支持”；不能称物理路径不存在，也不能把效应绝对值与双走廊直接比较。 |
| 消息响应早于物理传播 | 得到支持（协议/仿真时序），证据范围需分层 | 理论要求 `t0 <= tg <= td <= ta < tau_P`；整个结果窗排除物理传播还需 `ta+H < tau_P` 或 `tau_P=+infinity`（理论稿 L37–49）。双走廊 `tau_P=+infinity`；合流记录采用先于分化（`docs/归档/项目记录/项目历史/findings.md` L685）。 | 合流中经验 `tau_P` 的定义、估计误差和逐 trial 图；区分路径存在、预计到达和已造成结果。 | 双走廊可说结果窗结构隔离；合流最多说信息先行，不能说物理传播没有参与整个窗口。 |
| 结果不是共同交通状态造成 | 得到支持（配对仿真），现实未验证 | 同种子四格、采用前目标轨迹一致、相同目标风险动作、通道仅屏蔽指定消息（设计规格 L38–49, L122）。 | 更严格的 pre-treatment balance 表；不同控制器；共同控制信号 placebo；真实数据中时变混杂处理。 | 可排除冻结仿真中的已审计共同状态差异；不能排除建模共同偏差。 |
| 机制具有跨控制器、跨风险类型普适性 | 尚未验证 | 当前核心效应依赖透明规则控制器、指定 braking/TTC 场景；理论稿也将闭环控制优化列为后续（理论稿 L70）。 | 至少两类独立控制器；制动、合流、cut-in 等风险类型；不同通信图和车辆渗透；预言性方向/阈值。 | 当前不能称“普适交通机制”；最多称“可操作机制假说和能力证明”。 |
| 真实交通存在“采用导致动作和风险变化”的完整闭环 | 尚未验证 | 当前下载/字段审计表明 SPMD `RV_RX` 能观察接收侧远车状态，但没有生成时间、逐包发送/接收配对和控制采用；NGSIM/pNEUMA/INTERACTION 是轨迹数据。 | SPMD Packet + sender table 配对或实车/HIL；控制器内部采用日志；可干预或准实验设计。 | 公开轨迹只能外部锚定物理传播和风险指标；没有 adoption 就不能写现实采用因果效应。 |
| 实验可重复 | 初步支持 | 项目记录固定种子、冻结配置、bootstrap/置换种子、回归测试；NC 对照文献也普遍开放处理数据/代码。 | 决定性输出当前未在 Windows 项目树定位；需 manifest、checksum、环境锁、单命令重算和失败账本。 | 在归档完成前写“代码和协议可重复设计”，不要写“独立完全复现”。 |

## 三、NC 五篇常见结构到本项目的映射

| NC 结构功能 | 五篇中的共同做法 | 本项目现有材料 | 当前缺口 |
|---|---|---|---|
| 把问题提升到一般科学层 | 从单一算法上升到传播过程、早期信号、统一风险原理或网络响应规律 | 物理传播与显式信息传播具有不同拓扑/时间尺度，且消息链可审计 | 尚未展示跨控制器/拓扑的一般规律；“类超距”命名可能分散审稿人注意力 |
| 定义可观测对象 | 每篇都给状态、参数、响应时间或指标 | `G_P/G_I`、消息生命周期、`Delta_NL`、`I_TTC` 已定义 | `B_TTC` 与 `I_TTC` 必须在正文首次出现时分开；现实数据映射尚未写成 measurement table |
| 最小机制图 | Fig. 1/2 通常先把机制视觉化 | 已有完整作用链和时间不等式 | 缺一张同时显示两张图、四格处理、消息审计和物理到达边界的总图 |
| 决定性主检验 | 理论、经验或基线比较直接回答主张 | 双走廊四格是最强识别核心 | 需要把原始输出、效应分布、负对照和拓扑审计集中为一套可复现结果 |
| 多层外部锚定 | 多城/跨日/跨场景/经验网络/鲁棒性 | 合流迁移；SPMD/NGSIM/pNEUMA/INTERACTION 数据路线 | 合流目前只有一种几何；真实数据不能观察 adoption；没有 HIL/封闭道路 |
| 泛化与边界 | 改变需求、阈值、时延、渗透、网络结构，并展示失败 | 中重通信受损、placebo、早期零效应和失败种子均有记录 | 缺跨控制器、风险类型、信息图拓扑；失败账本尚未变成主文可见结果 |
| 开放与复现 | 五篇均有 Data/Code availability | 有测试、冻结种子和配置记录 | 决定性原始输出需统一回收；真实数据许可和不可再分发条款需写清 |

## 四、建议的 Results 图序

这不是论文正文，而是可供后续确认的章节骨架。图序沿用精读中最稳定的“对象定义 -> 决定性识别 -> 机制审计 -> 迁移 -> 外部锚定 -> 边界”结构。

### 1. Operationalizing information-mediated non-nearest-neighbor risk effects

- Fig. 1a：物理交通图 `G_P` 与信息图 `G_I`，标出最近邻、多跳物理路径和远端显式消息。
- Fig. 1b：`source event -> generation -> send -> loss/delay -> delivery -> validation -> adoption -> action -> risk` 生命周期。
- Fig. 1c：`t0, tg, ts, td, ta, t_action, tau_P` 时间轴和结果窗口。
- Fig. 1d：四格处理与 `Delta_NL`，在图注中说明风险负担指标下正负方向。
- 本节只提出操作定义、可观察量和证伪条件，不报告控制效果。

### 2. Decisive identification under physical disconnection

- Fig. 2a：双走廊拓扑、零路径审计和固定目标对。
- Fig. 2b：一个代表性 trial 的四格时间序列，消息、动作、TTC 分轨显示。
- Fig. 2c：20 个配对种子的 `Delta_NL` 原始点、均值/区间和等效阈值，不只放柱状均值。
- Fig. 2d：r00/r01/r10/r11 的采用前轨迹一致、采用和碰撞门槛。
- 主张边界：冻结仿真内、指定透明控制器、指定风险负担。

### 3. Auditing mediation and falsification conditions

- Fig. 3a：消息生成、交付、核验、采用、动作变化的逐级转化率。
- Fig. 3b：wrong-source、wrong-time、expired、delivery-only 负对照。
- Fig. 3c：时延/丢包/更新率剂量下的交付、采用与风险效应，允许非单调。
- Fig. 3d：失败和零效应 trial，说明失败发生在源事件、交付、采用、动作还是风险结果哪一层。
- 这一节用来排除“有通信边 = 已交付”“已交付 = 已采用”“已采用 = 风险已变”的逻辑跳跃。

### 4. Transfer to a physically connected merge

- Fig. 4a：合流图中的源、目标、普通物理路径和经验物理到达。
- Fig. 4b：早期冻结实验为何失败（8 个源事件未真实形成）及停止规则。
- Fig. 4c：独立源资格阶段、补充锁和修正版正式结果，明确是新冻结批次。
- Fig. 4d：信息采用、首次动作分化和经验物理到达的逐 trial 顺序。
- 主张边界：机制迁移和信息先行，不是物理断开证据。

### 5. External anchoring with real-world data

- Fig. 5a：数据集—可观察层级矩阵：轨迹、物理邻接、消息接收、发送/接收配对、时延/丢包、采用。
- Fig. 5b：NGSIM/pNEUMA/INTERACTION 上统一 TTC/物理传播测量的跨数据稳定性。
- Fig. 5c：SPMD 接收侧远车消息/状态的可达性、时序和缺失模式；只有完成 Packet + sender pairing 后才画真实丢包/时延。
- Fig. 5d：现实数据不能观察 adoption 时的 DAG/识别边界，明确 estimand 降级为“消息可达/接收与动作关联”或“物理传播基线”。
- 本节不能笼统命名为 real-world validation，图题必须写明验证哪一层。

### 6. Generality, limitations and prediction tests

- Fig. 6a：至少两类控制器或采用规则。
- Fig. 6b：不同风险事件、通信图拓扑和 CAV penetration。
- Fig. 6c：效应的归一化比较和性能—安全副作用。
- Fig. 6d：预先列出的证伪区：无交付、无采用、采用晚于物理到达、动作不变、风险不变。
- 只有这组结果完成后，正文才有资格讨论“一般机制”；否则本节应改为限制和未来检验。

## 五、可直接使用的整篇章节骨架

### Introduction

1. 交通风险可沿物理相互作用传播，但显式信息网络允许风险线索以不同拓扑和时延到达远端目标。
2. 现有非局部交通流、V2X 控制和级联风险研究各覆盖部分链条，尚未同时区分生成、发送、交付、采用、动作和风险结果。
3. 科学缺口不是“通信是否有用”，而是如何识别指定远端消息在物理影响到达前造成的可归因风险效应。
4. 本文贡献按定义、决定性识别、连通场景迁移、现实外部锚定四层写；每层同时给边界。

### Results

1. Operational definition and falsifiable conditions.
2. Four-cell identification in physically disconnected corridors.
3. Message-lifecycle mediation, placebos and communication impairment.
4. Qualified transfer to a physically connected merge.
5. Real-data external anchoring at observable layers.
6. Generality tests or, if unfinished, explicit scope boundary.

### Discussion

1. 已支持的是仿真内信息介导效应和场景迁移，不是量子/超光速现象。
2. 双走廊提供识别强度但人为性高；合流提高场景真实性但存在物理路径，两者互补。
3. 真实轨迹可验证物理风险测量和传播背景，不能替代采用日志。
4. 透明控制器既利于机制归因，也限制一般性；跨控制器结论必须另行实验。
5. 数据、代码、许可、失败实验和不可识别层级一并公开或说明。

### Methods

1. Formal estimand, treatment versions and assumptions.
2. Physical and information graph construction.
3. Message lifecycle and controller adoption rule.
4. Dual-corridor calibration, preregistration and four-cell runs.
5. `I_TTC` definition, valid-leader/positive-gap/closing-speed rules and outcome window.
6. Merge qualification, supplemental lock and version separation.
7. Paired bootstrap, sign permutation, practical-equivalence threshold and multiplicity policy.
8. Placebos, delivery-only mediation and impaired channels.
9. Real-data ingestion, field mapping, TTC harmonization and missing-data rules.
10. Reproducibility, failure ledger, software/hardware and data availability.

## 六、NC 与 IEEE 路线的条件判断

### 继续 NC 路线的最低条件

1. 决定性原始输出和统计能在干净环境一键复算，所有关键数字有文件级 provenance。
2. 合流修正版与早期失败批次清楚分离，并能说服审稿人新资格阶段不是依据 outcome 事后选种子。
3. 至少完成一项真正外部数据证据，同时严格标注其只验证物理传播、消息接收或发送/接收配对中的哪一层。
4. 加入跨控制器、跨风险类型或跨信息图拓扑的预言性结果，使贡献超出单一通信控制器。
5. 主图形成“定义—识别—机制—迁移—现实—边界”的完整链，失败和零效应进入主文或扩展数据。

这些条件满足后，论文可尝试定位为“显式信息网络改变交通风险传播的可识别机制”。其中第 4 条最关键：没有一般性检验，NC 主张仍容易被审稿人还原为人为双走廊中的能力证明。

### 更适合 IEEE Transactions 的收缩条件

若现实 adoption 无法观察、跨控制器/拓扑也来不及完成，但仿真协议和合流控制结果可重复，则应转为：

- 一种来源可追溯、采用可审计的远端风险消息控制与评估框架；
- 四格反事实和生命周期日志作为方法严谨性，而非普适自然机制；
- NGSIM/pNEUMA/INTERACTION 用于真实轨迹驱动、风险指标和场景复现；
- SPMD 仅在完成字段链时报告接收/时延/丢包，不主张采用因果效应。

这一路线仍需要真实数据，但证据任务是证明方法在现实分布和通信条件下有工程效用，而不是证明新的普适交通规律。

## 七、下一步优先级

1. **P0：回收并冻结决定性实验原始产物。** 为双走廊、早期失败合流、资格阶段和修正版合流分别建立 manifest、checksum、配置和单命令重算入口。
2. **P0：建立现实数据 measurement table。** 对每个字段写明能观察生成/发送/接收/时延/丢包/采用/动作/风险中的哪一项，不能观察的留空。
3. **P1：完成统一轨迹 TTC/物理传播基线。** 先用 NGSIM 的 leader 关系验证，再处理 pNEUMA/INTERACTION 的 lane/leader 推断不确定性；不直接比较未归一化的 `B_TTC` 与 `I_TTC`。
4. **P1：完成 SPMD 最小发送—接收配对可行性。** 只有 Packet 和 sender 表能稳定配对后，才升级为时延/丢包证据；adoption 仍需另行数据或实验。
5. **P1：设计跨控制器的一项预注册实验。** 选择与当前规则控制器原理不同但输入信息相同的控制器，固定风险指标、窗口、种子和失败门槛。
6. **P2：按上述骨架开始写作。** 先写可稳定的 Introduction 问题链、操作定义、Methods 和失败边界；所有未完成现实结果保留占位，不先写结论。
