# P3 Task1 — 信息传播与控制器采用机制审计

任务：AAD-P3-TASK1-20261102。实际交付日期：2026-11-03（Asia/Shanghai）。状态：**COMPLETED_WITH_LIMITATIONS（只读审计与文档交付）**。三份契约为Proposed v0.1 / Awaiting Researcher Ratification；不是生产实现、参数冻结或科学机制验收。

## 1. 解决的问题与当前主线

本次将“有生命周期字段”与“有控制器消费证据”分开核验。结论是：现有生命周期一致性检查、合成工程fixture、孤立SUMO控制/状态读回能力均存在；但尚不能按一条具体消息追溯其实际策略消费、决策、命令、安全处理及执行。adopted=True在现有审计入口主要是由设计条件或时程赋值，不是消费凭证。

物理链维持Source Event → Vehicle Interaction → Physical Propagation → Physical Arrival。信息链维持Source Event Confirmed → Generated → Sent → Delivered → Validated → Adopted → Decision → Command → Actual Action。后者还须连接固定域区域风险测量和因果分析。送达、消费、命令、执行及作用分别是不同事实；时间先后不能证明因果。

P2阶段性收口，不自动追加同类校准或V；WP1内P3、P4继续推进不依赖最终物理到达解决的工作。P3当前优先补事件级证据接口，而非继续扩大通信文献或P2参数搜索。

继承事实：P0 Task1–3、P1 Task1–2已有交付；Task6设计完成有局限；Task7为576计划/575完成/1原失败，83候选探索；Task8为268计划/267完成/1失败或未执行，V因真值支持不足未执行。Task7原359/47/0及版本化overlay359/119/0同时保留；119不是独立Qualified，Qualified仍0。

**Formal A=0；Independent Qualified Witness=0；F0/Overall TR–TP=Unknown；Stage0.5=CLOSED_WITH_LIMITATIONS；Stage0.6=PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock=BLOCKED；Stage I=READY_ENGINEERING_ONLY；Stage1.1=NOT_AUTHORIZED。**

统一定义仍为[v0.4、27项](../definitions/README.md)。本任务未修改定义目录、生产源码、正式config、历史实验或Overleaf；新增SUMO、seed、V及holdout读取均0。

## 2. 审计范围、方法与证据入口

审计基线Git为4932cf08c46b2e95fdc2fdae63214fd25fbc39d8，起始工作区clean。按AGENTS治理读取项目入口、P1因果定义、Task20、最新P2报告及通信勘误；再回到实际源码与既有fixture。输入SHA和实际测试记录见[证据索引](../../../evidence/research/P3_TASK1_20261102/README.md)。

| 证据 | 可重复定位的事实源 | 覆盖范围 |
|---|---|---|
| S1 | [formal_design.py](../../../code/src/riskprop/formal_design.py) L122–237 | 生命周期列、布尔依赖、标量时间及age校验 |
| S2 | [stage_i_mechanism.py](../../../code/src/riskprop/stage_i_mechanism.py) L29–38、58–208、241–329 | 八列事件轴、轨迹差异检测、七事件合成fixture |
| S3 | [formal_artifacts.py](../../../code/src/riskprop/formal_artifacts.py) L113–149、213–240、346起 | protocol/action列、Parquet可读/列检查、manifest字节检查 |
| S4 | [formal_runner.py](../../../code/src/riskprop/formal_runner.py) L132–169、306–321 | 生命周期与command/applied/safety的合成赋值 |
| S5 | [stage_0_1_sumo.py](../../../code/src/riskprop/stage_0_1_sumo.py) L239–324 | 孤立工程烟测setter与native状态读回；本任务未运行 |
| S6 | [communication_observability.py](../../../code/src/riskprop/communication_observability.py) L78–173、192–227 | RV_RX接收状态连续性及明确禁止的推断 |
| E20 | [Task20报告](../../TASK20_STAGE0_CLOSURE_AND_STAGEI_READINESS_20261101.md)及其既有fixture目录 | 既有fixture配置、时间轴、provenance及SHA；本次只读核验 |

能力状态采用Implemented / Fixture Only / Documented / Unknown / Missing。Implemented仅表示该代码路径实现所述功能，不意味着本任务产生新运行证据。一个阶段可同时有已实现的局部接口与Missing的端到端证据。

## 3. 九阶段现状审计

| 阶段与状态 | 当前实现/字段与证据 | 时间和身份关联 | 失败状态/局限 | 必要改进 |
|---|---|---|---|---|
| Source Event Confirmed — Documented；P3资格关联Missing | S3有source_event_id、source_vehicle_id、payload；S4/S2按source_present构造 | run/pair/source_event可命名；没有消息行到独立资格版本/confirmation证据的外键审计 | Formal A仍0；字段或source_valid不能证明真实源资格；B/sham不升级A | 引用communication-blind资格、source类型、confirmation record/version及生成资格 |
| Message Generated — Fixture Only；schema检查Implemented | S1/S3有message_generated、generated_time_s、message_id；S2/S4构造 | 标量time；没有唯一性、payload hash及实体incarnation校验 | 未生成、日志缺失、NA在现boolean内不充分区分 | 生成器实际本体记录、载荷版本/hash与机会分母 |
| Message Sent — Fixture Only | message_sent、sent_time_s，S2按通道开关赋值 | 没有发送尝试/transport回执身份 | enqueue/send未分；关闭通道有producer标dropped，不能视无线丢包 | 实际发送调用点的attempt、发送结果及队列时间 |
| Message Delivered — Fixture Only；真实接收证据Unknown | message_delivered、delivered_time_s；S2 delivered=sent，S4由设计布尔生成 | 无接收端receipt/receiver available_at/时钟映射 | sender成功不能替代receiver证据；未见接收不能当packet loss | 接收端回执及发送—接收逐消息/尝试匹配、观测截止 |
| Message Validated — Fixture Only；逻辑检查Implemented | source_valid/target_valid/freshness_valid、validation_time_s；S1要求采用依赖验证 | 无validation_id、validator/version或TTL判定输入 | 布尔写入不证明检查执行；age一致不证明freshness规则；缺证不等invalid | 实际验证记录、拒绝原因、资格/目标/有效期证据 |
| Message Adopted — Fixture Only；消费证据Missing | adopted/adopted_time_s；S2 adopted=delivered；S4 adopted=source_present and channel_enabled；S5按2.2s时程 | 没有controller/policy版本、消费receipt、decision外键 | 被读取/纳入策略、拒绝、缓存、采用无动作不能可靠区分；Unknown折False风险 | 策略输入及实际消费凭证，关联具体决策；边界待研究者接受 |
| Controller Decision — Missing | protocol无独立决策实例/输入输出表；theory或run版本不替代controller版本 | 无decision_id、decision timestamp及输入快照 | 无法区分采用后保持决策、策略失败、决策变但无命令 | controller实例/version、policy/config hash、input/output及no-change原因 |
| Control Command Issued — 局部Implemented（工程烟测）；P3关联Missing | S3有command_acceleration_mps2；S4是合成；S5真实代码调用setAcceleration | S5命令由时程分支触发，无message→decision→command_id/issue receipt | API调用不等实际执行；没有可靠拒绝、取消、覆盖回执 | 在实际API点留command_id、decision引用、值/单位/有效区间、ack/status |
| Actual Action Executed — native readback局部Implemented；P3归属闭环Missing | S5读v/a/x并填applied_acceleration；S4是合成；S2动作差异为轨迹运算 | 无execution_id/command外键/执行区间；action_diverged按时程赋值 | safety_intervened=False写定；实测动作受native跟驰/安全层共同作用；无差异不是无采用 | 实际状态与执行记录、安全前后命令/原因；动作测量与因果作用分别分析 |

这九项没有被压成单一PASS。S5说明不能笼统声称“没有真实SUMO控制接口”，但孤立setter/readback仍不能证明有效消息进入实际策略并造成动作。

## 4. adopted=True实际能回答什么

S1校验的是记录的内部一致性：采用要求已送达且source/target/freshness为真；阶段时间不逆序；message_age等于adopted−generated。它不独立观测这些事件。S2 fixture在构造时即把delivered赋给adopted；S4由四格设计条件决定；S5在源/通道条件满足且时程到2.2s时赋adopted_time，并据此触发目标加速度命令。

| 研究者要求的问题 | 当前证据结论 |
|---|---|
| 消息是否进入目标控制器输入 | 没有版本化输入receipt；不能由message_delivered推出 |
| 控制器是否实际读取并纳入策略 | 缺消费路径记录；adopted布尔不足 |
| 是否关联具体决策 | 无decision_id/输入快照与策略版本关联 |
| 是否产生具体决策输出 | 缺实际策略决策表；命令值不替代决策输入/输出 |
| 是否形成下发命令 | 孤立S5工程调用存在，但无消费—决策—命令引用 |
| 车辆是否执行相应动作 | S5可读实际加速度；缺execution/command关联与执行状态，不能独立归因 |
| 安全约束是否覆盖/修改 | 字段存在但False写定；缺安全层凭证，不能认定无覆盖 |

因此必须分开Message Validated、Controller Adopted、Adoption-induced Action Effect。前两项需要不同组件证据；第三项需要P5适当机制干预与因果识别，不能用更多日志字段替代。已采用但不改变决策/动作是合法结果，不得从ITT移除。

## 5. 联合时间轴、动作与风险的边界

S2的MECHANISM_EVENT_COLUMNS只有run_id、pair_id、event_id、event_type、time_s、vehicle_id、region、source。build_joint_timeline截取这八列，传入的其他消息/决策/命令字段也不会保留。validate_mechanism_events检查必需列、身份非空及全表时间非递减，不验证消息消费或跨阶段外键。event_id只是不同事件ID，不能代替共同message_id。

compare_paired_action在相同车辆/时间共同可见的轨迹上找持续速度差异，可作为模型动作候选。它不验证消息消费、不识别adoption因果贡献，也不自动解决未共同观测者选择。

没有physical_arrival_time_s时，联合轴返回Unknown及scientific_claim_eligible=False，这是必须保留的守卫。传入一个scalar时按全表最早adopted/action/risk与其比较；函数本身不校验此scalar的物理资格，也未证明这些事件属于同一消息链。

Task20既有时间轴为生成1.0、发送1.1、送达1.2、验证1.3、采用1.4、动作候选1.5、risk_observation2.0s；均是合成工程示例，物理到达为null/Unknown。三个共同观测点的配对差异不是因果或科学时间证书。该fixture provenance为fixture_only=true、SUMO runs=0、scientific_claim_eligible=false；其历史Git为0e5017cc31a378576e26d836116711de2645dd70，不冒称当前基线运行。

下一接口须分别保留实际动作候选、风险观测时间、风险状态onset、总体因果T_R、独立分层T_P及各自时间区间/phase/available_at。风险观测晚于动作并不证明风险变化由该动作导致。第一早窗主张仍服从P1总体H*、同域F0和同时误差预算。

## 6. 实现偏差与待决记录

以下记录用于避免将旧工程语义直接升级为科研证据；本任务停止对这些生产逻辑的修改，完成授权内审计。每项均为Status: Awaiting Researcher Decision（未来接口/操作语义接受），不是修改既有定义。

| Documented Intent | Actual Implementation | Evidence | Affected Files | Conflict / Status |
|---|---|---|---|---|
| 不可观测保留Unknown | fillna(False).astype(bool)折叠缺失；非空字符串也可能被宽泛bool化 | S1 L163–166 | formal_design.py及未来生产producer | 现boolean工具不能无损承载P3证据；Awaiting Researcher Decision |
| 未发送、未接收与真实丢包区分 | S5通道关闭写message_dropped=True；S4也由设计构造 | S5 L312–324；S4 L132–169 | fixture兼容映射/未来通信接口 | 历史值保留，不能据此估丢包率；Awaiting Researcher Decision |
| 采用来自实际策略消费 | 设计布尔/时程直接赋adopted | S2 L275；S4 L139；S5 L252–256 | runner/controller接线 | 消费操作边界及凭证未实现；Awaiting Researcher Decision |
| 事件级可追溯和时间不确定性 | 八列轴丢关联字段，以全表最早事件比较 | S2 L175、192–201 | stage_i_mechanism.py | 需版本化外键/时间包络；Awaiting Researcher Decision |
| 安全/执行状态有实际证据 | safety=False写定，action_diverged按时程 | S4 L315；S5 L291–292 | action producer/未来安全接口 | 缺安全与执行凭证；Awaiting Researcher Decision |

此外S1时间必填检查主要是isna，不能当作完整finite-time保证；S3列存在/manifest完整性也不能保证源资格、消息唯一性或证据真实性。补字段而不改变实际producer记录路径不能解决这些问题。

## 7. 三份核心契约与通信证据

- [MESSAGE_LIFECYCLE_CONTRACT](MESSAGE_LIFECYCLE_CONTRACT.md)：身份、载荷、九阶段、尝试/接收者、多对多引用、时钟与不确定性；未生成、未送达、无效、未采用、采用无动作、Unknown、右删失、NA分别记录；没有接收行不推断丢包。
- [CONTROLLER_ADOPTION_CONTRACT](CONTROLLER_ADOPTION_CONTRACT.md)：controller/policy版本、input/consumption receipt、decision、command、安全和execution、风险附件；日志消费与adoption因果作用分离。
- [COMMUNICATION_ASSUMPTIONS](COMMUNICATION_ASSUMPTIONS.md)：8类通信参数逐项登记Measured、Documented、Controlled-Test Reference、Literature Prior、Engineering Assumption、Sensitivity Only、Unknown；不冻结任何数值。

采用最新Stage0.4有限验收与0.4.7.2勘误，不能恢复早期摘要中已纠正的结论。RV_RX仅接收状态连续性；Bristol创建时间不等接收时间；SEE日志匹配/记录时延算术不等真实PDR或跨设备同步；复制GNSS不能支持距离关系、GNSS在线不等无线在线；THEA/WYDOT驾驶员响应不等自动控制器Adoption。没有新的通信实测或文献下载。

## 8. WP路线及长期规划修订

| 宏观包 | 保留的工作线 | 当前处理 |
|---|---|---|
| WP0 科学问题与理论基础 | P0+P1 | 基本完成，保留创新局限、DAG、estimand和证伪规则 |
| WP1 传播机制与风险测量证据 | P2/P3/P4并行 | P2阶段收口；P3当前重点；P4沿现有Formal基础完善 |
| WP2 因果实验与统计协议 | P5+P6 | 提前设计准备；冻结依赖WP1及研究者科学决策 |
| WP3 端到端工程集成与独立验证 | P7+P8 | 接口准备可并行；先导、独立验证、确认性实验分开授权 |
| WP4 预注册与正式准入 | P9 | 完整证据/协议/样本量/版本/预注册/Lock和明确授权后才进Stage1.1 |

唯一授权OB规划由2525行v1.0迁移为2302行v1.1 Revised Proposal；保留10条P线、12个display公式块及42项原Stage1.1准入条目。目标/交付物按WP归并，技术规范/验收、理论、文献及科研治理保留；过期当前快照与串行路线被替换。P0–P9、Task ID、代码和历史证据不改名。详见[迁移说明](ROADMAP_REVISION_NOTE.md)及hash，不把OB全文复制进便携证据。

## 9. 最有价值的下一步与研究者决策

建议下一项为**一项有界的P3采用凭证与跨阶段引用接口实现，加最小合成契约验证**；通过后可直接向P7集成交付接口。覆盖正常消费、拒绝、采用无动作、安全覆盖、重复/过期、孤儿/跨run引用、同step不同phase、缺时钟/状态。它只验证记录契约，不启动交通实验或证明H1–H4。

研究者需接受的实质选择集中为：细化采用边界（策略输入消费而非仅读取过滤器）；实际controller/policy及安全层的职责；Enabled/Disabled是否仅切断消息对策略的输入及其资格总体/随机化；未来通信模型的来源与适用范围。本文给出接口建议及影响，不选择算法或通信数值、不修改Agreed定义。

WP2继续继承source-present assignment ITT（含链路失败/安全覆盖）与最终四格；采用率、采用开关reduced form、实际采用IV/LATE不能混为一谈。机制资格须先于Z_A确定，仍不自动代表主ITT总体。不批准先导/V/正式实验，也不自动延长P2研究。

## 10. 验证、影响范围与剩余限制

影响判断：新增文档/证据，更新状态入口及单一授权OB规划；未改变模块接口、运行行为、数据处理、正式科学逻辑。四份既有定向测试覆盖生命周期、Stage I工程轴/动作运算、artifact和通信可观测性工具；不覆盖真实通信、策略消费、因果或生产闭环。

指定四文件测试已完成：**42 passed in 18.56s**。首次默认临时目录因WinError5导致29 passed/13 setup errors；改为任务隔离basetemp仅重试一次通过，没有改代码/依赖或清理用户临时文件。首次失败记录保留。未运行全量pytest、SUMO、Task20入口或RV_RX profiler。

最终文档、相对链接/字段、输入hash、规划保留、既有Task20 SHA、Git检出字节及证据导出核验，实际结果统一记录在[validation.json](../../../evidence/research/P3_TASK1_20261102/validation.json)；只有对应记录PASS才称通过，工程验证不升级科学状态。

剩余限制：没有新控制器消费凭证、实际安全覆盖证据、独立物理到达/来源归属支持、参数Independent V或严格早窗桥接。本次解决的是证据要求及接口缺口定位，不能认定信息链科学机制或AAD核心假设已经成立。
