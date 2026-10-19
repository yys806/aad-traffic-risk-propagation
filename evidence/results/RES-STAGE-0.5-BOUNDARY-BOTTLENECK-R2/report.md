# AAD-0.5.4-B1.2：分层数值准入与道路边界—最小瓶颈机制再验证

结果：`RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2`。2026-10-19。`exploratory_diagnostic_only`。

**最终执行状态：前置接入检查工程阻断，B1_2_MAIN_MATRIX_ALLOWED=false。主矩阵 0/8，停在研究者决策节点。** 未补跑旧 B1 D、未重跑旧 C、未开展驾驶参数校准。

## 1. 研究者十项问题的回答

| 问题 | 本次可核验回答 |
|---|---|
| 1. 分层数值准入是否正确接入？ | 已接入真实 SUMO，严格布尔防御和步初加速度有效；但首个接入 fixture 发现近零清零分支遗漏，完整准入未通过。10,145 条已审计边：Exact Observable 5,028，Exact Reconstructable 5,019，Bounded 14，Not Evaluable 84（83 条合法 edge 转换、1 条终速不一致阻断）。精确适用 99.0340%，适用边通过 100%；不能把它称为全运行准入通过。 |
| 2. 队列契约实际接入资格？ | 合成/停止回归 142 passed；压缩三车道 SUMO 中已观察分车道图、车尾/净距、内部队列、上游扩展和入口邻近候选。71 条跨 edge 里程交叉检查、439 个 junction 状态支持该 fixture 的已检查路径坐标。完整时长、实际换道、D 三变二动态与持续入口回溢资格未验证，整体接入未获准入。 |
| 3. A/B/C/D 实际完成情况？ | 仅 integration_C 尝试一次，19.75 s 内部步触发工程阻断；最后完整记录/守恒帧 19.70 s。integration_D 未启动；主 A/B/C/D 两个 seed 均 not_attempted，主计划未冻结。无正式机制运行。 |
| 4. C 是否再次形成持续道路拥堵？ | 新主 C 未运行，不能回答。压缩工程 fixture 最早内部低速 9.4 s、pending 9.8 s、空间队列 11 s、入口邻近 12 s，未得到 Entry Spillback Supported；这不是 600 s 原尺度 C 的结果。不得把先低速、先 pending、后队列的时序解释为原主 C 的机制。 |
| 5. D 是否自然形成受约束交通？ | Unknown：新 D 网络静态和零步运行参数检查通过，动态 fixture 因 C 阻断未启动。无实际换道、队列、出口或密集跟驰结论。 |
| 6. C/D 差异与同容量资格？ | 无新主 C/D 成对结果，capacity_matched=false；不能比较强弱或独立机制。 |
| 7. 哪些状态接近真实？ | 无合格新主样本，Not Assessable。只读取两个已批准校准窗口的 SHA 绑定便携摘要，未按距离选择瓶颈；不把压缩压力 fixture 与真实窗口比较。 |
| 8. generic highway 局限？ | 仍非真实 US-101 几何；原尺度供给/结构机制本轮未能再验证。三变二动态、换道时间连续性、入口因果支持和全域队列资格有缺口。 |
| 9. 现在正式校准 Krauss？ | 本轮未新增足够合规、稳定、可测量的原尺度密集低速跟驰样本。没有启动正式校准的新增证据；先解决数值后处理适用域，再完成被阻断的接入职责。 |
| 10. 下一步应批准什么？ | 优先批准独立近零清零适用域验证及新接入计划；不调 tau/minGap、流量、信号或队列阈值。具体选择见第 10 节。 |

## 2. 授权与版本、历史边界

本次研究者批准方案 B 仅用于 B1.2 工程探索；批准受限队列候选接入和条件性新 A/B/C/D。科学阈值、正式校准、现实验收、独立验证和协议锁均未批准。

本地/远端起点均为 `1c8f919ed419c21cc262c381286e550f9b590161`。先读取指定上下文、注册表、源码和三个历史报告；只把 `RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1/real_reference_summary.json` 的已批准两窗口摘要及 A+ 车型注记作为真实参考输入，按原 manifest SHA 核验。无旧 C 状态、历史 Stage 0.2 全源表、第三窗口或 holdout 输入。

- v1 胶囊计划已冻结但零交通尝试：源完整性复核发现胶囊分析 worker 副本过时，关闭为 superseded，保留计划和 ledger。
- v2 独立胶囊：冻结 2 个各最多 60 s 的接入 fixture。计划 SHA `8789f7336e68548e9fe43d743534124b16122c3e0376b12f3f8b137acc55aa16`。
- v2 第一 fixture 工程阻断后关闭；第二 fixture 未启动，剩余预算不用于绕过 C 或补齐 D。本次没有新增 SUMO 交通尝试。
- B0 19 次有限历史、任务隔离 false、验证物化 Unknown；旧 B1 A/B、C 两原阻断和 D not_attempted；B1.1 Pending Numerical Equivalence；B1.1-S 947/948 历史结果及所有原 SHA 均保留。

## 3. 数值政策、接口防御和反例

`reconstruct_signed_vnext` 只接受 `type(is_action) is bool`，否则返回 `Not Evaluable / action_step_identity_not_boolean`，candidate=None。决策时钟拒绝非有限/非法类型、非正步长、不整倍 action step、未来或过旧时间及不在内部网格的时间差。先有 16 failed/11 passed 的负面复现，再修复，27 项接口测试通过。未修改 B1.1-S 封存产物。

新 worker 对所有共同可见车辆的 0.05 s 相邻边流式检查，保存身份、incarnation、时间、步初/步末速度、公开加速度、lastActionTime、road/lane/位置、数值配置与车辆控制标记。非决策步使用前一内部状态的加速度；决策身份按步末 lastActionTime 与步初对齐。没有车辆 setter/控制调用；未知控制或身份/时钟/config 不放行。

精确位移仍用 `1e-6 m`；正常决策步正终速、非决策步候选以及静止位移分别核查。决策停车仅必要范围一致，不记 Exact Pass。合法 edge/lane 不连续没有位移相减，residual/actual_dx 保持 None；没有用位移反推候选速度。没有任意不可评价比例上限。

| 已审计分类 | 边数 | 占已审计边 |
|---|---:|---:|
| Exact Observable | 5,028 | 49.561360% |
| Exact Reconstructable Under Verified Conditions | 5,019 | 49.472647% |
| Bounded Consistency Only | 14 | 0.137999% |
| Not Evaluable | 84 | 0.827994% |
| 合计 | 10,145 | 100% |

10,047 条精确边全部通过，最大残差 `7.105427357601002e-15 m`；其中观察到25条非决策步负候选终速，按独立步初加速度核验。决策/非决策边分别为5,088/5,057。14 条 bounded 无越界。Not Evaluable 为 83 条合法 edge 转换和 1 条 `candidate_terminal_speed_inconsistent`。该分母只覆盖提前停止前实际已审计边，**包含最后 19.75 s 的部分车辆迭代**，不代表完整 60 s 或该末步全部车辆。无真实相邻 lane change，不能把 edge 转换当作换道测试通过。

阻断反例（车辆 `v00010`，`main_1_1`，19.70→19.75 s）：

- v0=`6.4835987978100174e-6 m/s`；步初公开 a=`-3.651175106531166e-5 m/s²`；步末 lastActionTime=19.65 s，明确为非决策步。
- 加速度延续得到候选 `4.6580112445444345e-6 m/s`，公开终速却为 0；没有把这条边标为 Exact。
- 实测位移 `1.620899752197147e-7 m`；假设清零后候选为 0 的解析位移 `1.6208996994525045e-7 m`，差约 `5.27e-15 m`。此计算是停止后的源码解释，**不是对原阻断的追溯放行**。
- 这不是“精确位移残差超过 1e-6 m”：触发的是更早的候选终速一致性防御。原预测位移与实测之差约 `1.16e-7 m`；单看位移容差会漏掉该适用域问题。

固定 SUMO 源码同一 commit 的 `MSVehicle.cpp` 第 127 行定义近零阈值，第 4600 行延续加速度，第 4644–4645 行在 finalizeSpeed 之后、TraCI 控制和 updateState 之前可把近零候选清零；不局限于决策步。`config.h.cmake` 第 219 行 NUMERICAL_EPS=0.001，`SUMOTime.h` 第 42 行定义 TS；本步阈值为 `0.1*0.001*0.05=5e-6 m/s`。反例与此机制一致，但未仪器化证明安装二进制实际走过的私有 stop-distance 条件。完整源码只在新本地输出，SHA 与行号见 `near_zero_source_audit.json`。

### 必须记录的冲突

- **Documented Intent**：B1.1-S 的既有适用叙述认为无车辆控制时，非决策步内部最终候选始终等于 `v0+a_pub_start*h`，任意符号均可精确核验。
- **Actual Implementation**：固定 SUMO 源码在加速度延续后仍可能近零清零；B1.2 的明确非决策步出现正的延续候选与零公开终速不一致，并被 fail-closed 防御阻断。
- **Evidence**：新反例、固定源码 SHA/行号、`numerical_branch_coverage.json`、实际关闭 ledger。
- **Affected Files**：`stage_0_5_stopping_observability.py::reconstruct_signed_vnext` 的适用域；`stage_0_5_b12_observation.py::audit_transition`；B1.2 后续数值准入规则。
- **Conflict**：先前微型范围的成功不能覆盖所有近零后处理。清零阈值是 SUMO 内部工程实现常数，不是新科学容差。
- **Status: Awaiting Researcher Decision**。保留原公式和本次阻断，不自动放宽速度一致性或位移容差、不改历史结论、不创建新运行版本继续实验。

## 4. 队列输入、计数与坐标

独立 `stage_0_5_b12_observation.py` 不改 B1.1 合成接口。全网守恒逐内部步使用完整身份集合；各 edge 独立计数。局部车辆数由位置筛选，边界进入/离开由相邻局部身份集合与位置交叉统计，单列出生/edge 原因，不能从全网插入/驶出推出局部流量。外部需求按当前可执行时刻的 due 与实际进入计算，并独立核对 TraCI pending。

最后完整 19.70 s 帧：实际进入 49、驶出 6、全网在场 43、外部 pending 17；已观测局部进入 32、离开 21。局部累计车辆时间 89.2 vehicle-s，采用已声明的 0.05 s 右端点离散支持。**fixture C 为压缩网络**，局部 `main_1 [10,40)`、3 车道、0.09 lane-km；不能冒充正式机制观察域 `main_1 [50,250)`、0.6 lane-km。未插入车辆不计密度。

坐标映射解析实际 net.xml 的 lane length、via 和 internal connection 链；逐车道构建 main_0→junction→main_1 路径，包含 junction 长度，不跨不同路径桥接。检查方向、端点相接、三条路径及 D 下游延续/终止车道。压缩 C 每路径 147.56 m，D 为原尺度。运行时用独立 TraCI traveled distance 增量核查映射：同 edge 9,662 次、跨 edge 71 次，最大差 `4.263256414560601e-14 m`；7,332 次同车道物理净距检查最大差 0。两模型量的数值一致不代表真实道路几何或现实精度已验证。

逻辑里程以加载的 SUMO lane-length 数值定义，其工程坐标不额外假设传感器噪声；真实世界位置精度 `Unknown`，网络 polyline 与 lane length 差异单独报告。没有照搬合成的 0.01 m。未检查的跨路径、匝道桥接不支持资格。数值位移仍对所有 edge/lane 转换明确 Not Evaluable，队列空间映射不替代位移精确核验。

各车道分别建立前端、车尾和净距连接；至少 2 辆、净距≤10 m。低速/停车为 5/0.1 m/s，辅助网格 50 m/低速比例0.5，入口/下游锚定50 m，持续2 s，快照1 s，全部 `engineering_candidate_for_B1_2`。换道或 edge 身份变化保守重置含该成员的组件时间连续性，缺帧不补。该实现的重置统计混合合法 edge 转换（本 fixture 52 次成员重置），**不能称为实际换道已验证**。

入口支持同时要求：持续且下游锚定的空间组件、当前 pending，以及对 pending 所分配入口车道独立计算的插入空间不足。三条路径各存在组件不等于全道路连续堵死。辅助分车道网格与历史池化网格不得覆盖主图判定；本次只做停止前的描述敏感性，不得借辅助方法升级入口回溢。

## 5. 真实接入 fixture 与准入矩阵

先冻结两项：C 为压缩 0.2 倍节点坐标的三车道走廊、150 辆压力需求、5/6.2/48.8 s 信号，仅检验观测；D 为原尺度三变二、18 辆从 lane2 进入，检验实际换道、路径和驶出。两项均最多60 s、seed20261019、固定 Krauss 与 A+ 长度。**该压力 C 的需求/信号不是主矩阵 C**。

| 接入职责 | 实际证据 | 状态 |
|---|---|---|
| 全网守恒、局部计数、空间进出 | 完整帧身份守恒，32/21 局部穿越 | Verified within partial fixture |
| 三车道分布、车长/车尾/净距 | 主线三车道实际状态、7,332 几何核对 | Verified within partial fixture |
| edge/junction 坐标 | 83 次实际 edge 转换；71 次支持域跨 edge 里程核对、439 junction 状态 | Verified within checked paths |
| 内部队列、上游扩展、入口邻近 | 11/12/12 s；没有丢帧平滑 | Candidate observed; partial |
| 外部 pending 与内部队列分开 | pending9.8 s、空间队列11 s；记录空间不足 | Verified observations; unique cause Unresolved |
| 无内部队列而外部积压 | 起初 pending 已出现，未得图组件 | Partial actual + independent synthetic |
| 内部队列未到入口/随后入口邻近 | 先后快照保留，入口邻近并非持续锚定链 | Partial actual |
| 实际持续入口回溢 | 未满足 Entry Spillback Supported | Evidence Insufficient |
| 真实换道、D 收缩动态、出口质量 | D 未启动 | Not Attempted |
| Evidence Insufficient 防御、缺帧/未知精度 | 独立合成负例 | Candidate software behavior Verified |
| 下游供给上下文 | 信号 runtime echo，与完整状态分别记录 | Verified fixture context |
| 数值分层完整准入 | 近零候选终速不一致 | Engineering Blocker |

合成软件行为与有限 SUMO 部分路径核验不构成完整 SUMO integration verified，更不构成 Scientific traffic validity。没有把缺项伪造为通过，整体准入 false。

## 6. 停止、隔离、资源与未执行矩阵

监督器以退出码、summary 工程 blocker、SHA、时间/内存/输出上限决定停止，不只看进程正常退出。C worker 输出 failure，进程退出码为0；监督器仍归类 `completed_with_engineering_blocker`，未启动 D，真实证明该停止路径生效。原始 summary 的 status=`failed` 与父控制器分类同时保留，说明层级而不互相覆盖。

接入预算：2 次各≤60模拟秒，单 worker 墙钟180 s、批次600 s、进程树3 GiB、输出1 GiB，无并行。本次1次尝试，worker2.576 s、父监督8.389 s、采样峰值136.08 MB、该运行输出约1.018 MB；墙钟不等于模拟时长。P2 没有在接入 fixture 计算，不能声称完整 P2 成本实测；队列成本含于 worker，没有独立计时。

主矩阵曾获条件授权的候选为两个 seed `20261019/20261020`、每 seed A→B→C→D、每次600 s、约1648 veh/h/lane、每次823辆；C23.8/6.2/30、D main_2三变二，驾驶参数固定。**主计划、主需求/车型序列和网络版本均未冻结/执行**，仅在未执行清单保留全部8项。不得称为被冻结的正式交通矩阵。主成本只可保留预估（自由流150 s、受约束450 s、单次600 s/任务7200 s、6 GiB/4 GiB），未获得本次主运行实测支持。

Python -S 胶囊路径/来源/角色/SHA、三个虚构拒绝路径和监督停止回归通过；实际 SUMO worker 的 Python 访问无意外拒绝。冻结后源码审计单独登记请求、SHA和用途，不读取真实轨迹。未证明 native/OS 绝对访问边界。根工作区没有全量 pytest；纯 Git 回归的数据缺失 skip 单列，不计科学通过。

## 7. 交通、跟驰、P2 与现实对照的适用域

本轮没有完整原尺度 A/B/C/D，故没有新的 B−A、C−A、D−A，也无供给能力匹配比较。两窗口真实均速/密度等只保留为已批准描述参考，不读取第三窗口，不把置信区间当容差。压缩 fixture 的初始化、几何、需求和供给均与主机制不同，不能给它现实相似度或主机制资格。

主矩阵本应保留全600 s和60 s分段，并比较0/60/120/300 s起点的初始化敏感性；本次因未准入而全部 Not Attempted，不批准科学 warmup。

Stage0.2 TTC/P2 定义未改。16项既有确定性边界与暴露回归在受控合成测试中通过。接入 fixture 未计算工程 P2 事件/率；缺失值不填0，局部正式 P2 继续 `Unresolved`，不能将任何 SUMO 全域率与真实局部率比较。

## 8. 四项机制假说矩阵

| 假说 | 支持证据 | 反对/限制 | 替代解释 | 可确认性 | 后续所需 |
|---|---|---|---|---|---|
| H1 到达扰动改变持续状态 | 本轮新主证据 None；旧 B1 A/B仍为历史参考 | 新 A/B未运行 | 原到达压缩可能只改变短时跟驰 | Evidence Insufficient | 数值准入后新的配对 A/B |
| H2 下游供给形成内部队列 | 部分压缩 fixture 观察到空间组件与上游扩展 | 数值阻断、非原尺度、未有持续入口支持 | 高压需求、短路段和人工长红混杂 | Evidence Insufficient for main mechanism | 修复适用域并验证入口资格，再运行原尺度 C−A |
| H3 三变二产生不同响应 | 新 D静态/零步检查；无动态主证据 | D fixture/主运行均未启动 | 错误连接、换道或供给差异尚未动态排除 | Unknown | 真实 D 换道/出口接入职责及成对 D−A |
| H4 固定 Krauss 支持受约束动力学 | 压缩 fixture 有低速跟驰和图组件的有限描述 | 原尺度稳定可用样本未增加；近零数值适用域阻断 | 压力需求和人工供给可产生非现实状态 | Evidence Insufficient for calibration readiness | 合规重复原尺度样本与后续研究者协议设计 |

以上是证据覆盖表，不作假说成立、算法优劣或论文结论。

## 9. 可重复性与证据入口

便携目录 `evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2/` 保存数值政策、冻结接入计划、输入压缩 bundle、源绑定、分支覆盖、反例、接入矩阵、隔离/停止、资源、所有未执行项、冲突和研究者决策。完整状态、队列快照、网络、源码、日志和图只在 `code/outputs/formal/calibration/stage_0_5_boundary_revalidation_b12_v2/`；v1零尝试记录也保留。

便携核验入口：`code/scripts/verify_stage_0_5_revalidation_evidence.py`。封存报告以本文件为准；测试、纯Git、compileall、文档和证据验证结果见 `test_record.json` 及最终收口记录。既有五项文献索引删除与私人笔记未处理。

## 10. 下一步研究者决策表

| 项目 | 本轮事实 | 建议 | 需要批准/补齐 |
|---|---|---|---|
| 工程机制保留 | A/B/C/D主矩阵未启动；原设置未调 | 保留原机制候选，封闭本批 | 独立新计划；不得称补跑旧B1 |
| 最必要工作 | 明确非决策步出现近零清零候选差异 | 独立审计清零前/后速度、隐藏stop条件及精确可识别域 | 批准新数值适用域验证和接入预算；不调1e-6m |
| 队列接入 | 部分路径/分域验证通过，真实换道和持续入口资格未完成 | 完成原预声明缺口，阈值保持工程候选 | 新fixture职责/预算；不能挪用未运行D当已验证 |
| 网络/供给 | D仅静态；人工信号不是US-101设施 | 先动态连通/换道/出口，再原尺度成对比较 | 供给设计可解释性；C/D容量匹配需独立设计 |
| 真实US-101几何 | generic仍无真实几何资格 | 研究者决定是否开展真实几何核对/重建 | 车道/匝道/织入和供给证据，不能由均速决定 |
| 交通需求 | 1648来自内部断面，非已识别上游需求 | 保留候选强度，不搜索 | 冻结到达、OD、车型和上游需求可识别职责 |
| 科学容差 | Tolerance Not Yet Justified | 单独协议设计 | 速度/密度/加速度/跟驰允许偏差的科学依据 |
| 局部P2 | Unresolved | 保持核心P2，先解决事件空间归属和暴露 | 研究者批准局部/分层成员与分母规则 |
| 正式Krauss校准 | 本轮未新增可用原尺度密集低速样本 | 不启动 | 工程准入、稳定可测量状态、重复与后续正式协议 |

正式状态始终：`stage_0_5.gate=pending_simulation_sample`；`scientific_claim_eligible=false`；`ready_to_start_stage_0_5_4b=false`；`reality_coverage_accepted=false`；`protocol_lock_allowed=false`；`stage_1_1_allowed=false`。容差 `Tolerance Not Yet Justified`；Energy Distance real-real上界 `Not Identifiable`；局部正式P2 `Unresolved`。


## 11. 最终验证与 Context Consistency Check

- 冻结前受控胶囊142 passed、0 skipped；严格布尔/时钟修复的先失败测试为16 failed/11 passed，修复后27 passed。
- 收口定向测试（新接入/便携正负/接口/项目文档）74 passed。
- 纯Git全量回归626 passed、14 skipped，139.34s。13项因缺本地真实或封存数据，1项为-S胶囊专属启动检查（已在胶囊通过）；逐项原因见test_record.json，不算科学通过。
- 纯Git检出的严格文档`--strict-git --require-clean`、便携证据、12个工程输入解码、31个冻结源码绑定和compileall通过。代码与观测输入冻结SHA保持不变。
- 根工作区严格文档检查仅因既有`doc/literature-notes/zotero_reorg_2026-10-17_execution.json`缺失而失败；五项既有删除未恢复、未暂存。纯Git入口单独通过。提交后原工作区clean检查预期仍受这五项既有删除限制。
- 首次独立绘图触发7次可选字体/缓存路径拒绝，保存原审计；改为胶囊内MPLCONFIGDIR和包内字体缓存后0拒绝，三图已目视检查。无新的SUMO运行、无数值/队列测量或资格改写。
- Context Consistency Check覆盖当前状态、架构、数据流、模块、实验、已批准决定、已知问题与changelog；更新注册表及阶段/结果/项目索引。研究背景和核心算法未改变，AI_CONTEXT/01无需更新，AGENTS.md未修改。
