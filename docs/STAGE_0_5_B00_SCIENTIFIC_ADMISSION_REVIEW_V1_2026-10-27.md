# Stage 0.5 B00 科研准入审查与研究者决策包 V1

Task：`AAD-0.5-B00-SCIENTIFIC-ADMISSION-REVIEW-01`。日期：2026-10-27（Asia/Shanghai）。

**审查已完成，科研审批仍待决。Research Proposal：暂缓可执行授权，先处理ENG-01/02/03；科学政策现在可以逐项审议。** 本文不签发科研批准、不创建候选或授权、不冻结协议。候选历史工程状态仍为 `READY_FOR_RESEARCHER_APPROVAL`，不能解释为现在即可执行B00。

## 1. 执行摘要

- **Verified Observation**：从GitHub核实origin/main与本地HEAD均为 `753b666a3c9e4b8d88add2ead1973ff8e2d4439f`，开始时已跟踪工作区干净。本轮新增文件造成的dirty与候选生成时dirty属于两个时点。
- **Verified Observation**：精确候选三SHA、347份历史绑定、12生产源闭包、既有SMOKE独立 `verify_receipt` 通过；38份科研/执行源与正式Git按属性检出的字节一致。没有由工程accepted=true单独获得科研授权的路径证据。
- **高优先级**：技术ready未检查B00 policy的accepted_build=false；实际协调器会先预约/记attempt，再由controller拒绝。这是拒绝式保护，但ready与可执行性不一致（ENG-01）。碰撞getter缺失被循环的or 0视同零，完整性不要求该getter；summary尚未作逐车计数交叉核算，合法pending也不等于实际全车插入（ENG-02/03）。
- **科研待决**：DS38确实仅改38辆初态车的数值10速度为max，79辆初态及1033辆非初态不变；初态/插入政策、测量合同、窗口、场景合理性均不由工程证书批准。
- **本轮SUMO/netconvert启动=0、真实TraCI=0、B00执行=0、新科研轨迹=0**。账本仅task_created、候选B00输出目录不存在。没有修改科学参数、审批、锁、Gate或历史事故。

完整矩阵15项，其中9项需要研究者决定；多分类分别列出。入口：[review_matrix.json](audits/stage_0_5_scientific_admission_review_v1/review_matrix.json)、[decision_packet.json](audits/stage_0_5_scientific_admission_review_v1/decision_packet.json)。

## 2. 当前事实与精确绑定

候选：`evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/`；Task `AAD-0.5-READY-TO-ADMIT-V3`；Run `V3_0750_B00_DS38_s20261201`。下表均为本轮复算：

| 对象 | SHA-256 |
|---|---|
| candidate-v6 proposal | `b43e2d3af03dd53dd23bee3abd027725f298f58c97a2ae73d868ca9168a229b3` |
| candidate-v6 manifest | `afddd83c77e1f7b9eaf64c3b5059f9d29f740b9bf003ed36d22325c93eee4978` |
| 工程集成证书 | `342ed54cccedcaf0d477ec72b70b98e956140179961dec2d59904d4648a71528` |
| SMOKE proposal | `a5f419029a7dc3ddc527d9b7e7e824c9f0f3779f4f3e17e769d87d472ca4a550` |
| SMOKE实际授权envelope | `a9ce5a370957387690adfcfc953e7d20d5a877d3d73e628418bd73b816b1271d` |
| runtime manifest | `3afa1fdb8eac97acf875d1a816eac168bfd39d3318414e316c85b4136d0a4abc` |
| 12生产源canonical映射闭包 | `b1598d279e2665c1c902bae827022440a34f668377fc0544b30fbcf84f8015c2` |
| SMOKE result.json | `ae4ce45d42b37b4b42598987c9bae22c50f69641b80ee49c5c5d2449f2df0c64` |
| capsule/engineering_acceptance.json | `a3276183a38b6bfd03e5c5e0eb67a61b86a8f193d4d5d541bea208ed669dd88b` |
| independent_receipt_acceptance.json | `e295f312bfa2c75258db162ee42bbeb0b1d01373060fdc641097b8c6e1784894` |
| isolation_runtime.json | `9c4251d748ec613214682195ce27ee6235d945fd4b25e0e86a249508414a5c5f` |
| controller_receipt.json | `316dcb625a55a7919a54e88e7986a7477f2972383e2d0a30d0ad94f32daf7606` |

原false envelope仍为 `6b37149d000f28258ee22bb499d7db7ee0e7a1255d4195c4bb7658f5aae8a463`。原始封存manifest/collection、broker/controller、输出、资源、命名空间与独立验收重新一致；SMOKE仅证明1车/3秒/60步合成工程链，不证明1150车/420秒B00动态支持。没有迁移旧授权。

运行时清单绑定SUMO1.26.0、TraCI22、Python及8031文件。本轮复核已封存清单/回执及源码关系，**未重新读取当前Linux全部8031文件、未重做live环境检查**；当前资源/内核为本轮unverified。未来不得以历史ready替代启动前检查。逐文件实际SHA和用途见[evidence_manifest.json](audits/stage_0_5_scientific_admission_review_v1/evidence_manifest.json)。

科研账本SHA=`63c3babe2a5808de5ec3e6734f21a2c56ec8d7cd53113fac8d5d593bd2f2f685`，只读解析仅一条task_created；未构造ResearchLedger、建锁或推进状态。此结论限于登记证据及精确输出位置，不声称盘点所有未登记外部文件。

## 3. 工程接受与科研授权的真实边界

证书schema为 `aad.native-integration-acceptance.v1`，accepted_for_new_task=true及input_and_test_resource_scope_accepted=true指工程链/静态输入资源资格。proposal schema为 `aad.native-admission.v4`，isolation.accepted_for_new_task是工程前提。profile同名false指科研准入显示状态；proposal三科研审批、admission三政策均false，profile四false及native_launch_locked=true保持。不能跨对象互换语义。

本轮保存全部相关字段位置，并区分当前V4、准备/验收与旧路径：[state_field_readers.json](audits/stage_0_5_scientific_admission_review_v1/state_field_readers.json)、[authorization_boundary_audit.json](audits/stage_0_5_scientific_admission_review_v1/authorization_boundary_audit.json)。实际调用：

| 当前调用方 | 检查与含义 |
|---|---|
| run_stage_0_5_admission_v3.main | V4显式跳过legacy NATIVE_LAUNCH_LOCKED入口拒绝；execute需要独立approval。profile不是此路径执行锁的读取来源。 |
| ExecutionAdapter.execute → execute_research | V4分支先authorization_reasons：精确task/run/proposal SHA、非空decision_record、三科研审批及三政策，然后technical_preflight_v4。 |
| ResearchLedger.reserve | V4再查独立精确approval；静态proposal保持false；还核验预算、输入/源、隔离、重复配置等。 |
| verify_envelope | 校验envelope/proposal/policy/input/source/runtime绑定及授权。 |
| broker → verify_live_context → NativeBackend.start | 从policy.accepted_build重建授权stub，实时kernel/resource/namespace和精确源检查后才可能SUMO。 |

工程true单独不足以放行；五项空目录纯函数反例检查缺审批/政策、错task/run/hash及policy false。decision_record只检查非空，没有独立身份或签名认证；真实人类决定由受信研究者与操作者提供，不得自行填JSON代替授权（AUTH-02）。本轮未创建科研envelope。

### ENG-01：ready与晚期硬锁冲突（高优先级）

固定研究policy SHA=`e7152b8ff703f23ed051ecc0fe9afae7b2b1190221338a79fddd822c08a54bf1`，binding.accepted_build=false。technical_preflight_v4验证工程证书及proposal.isolation true，却不检查该policy位。实际顺序：

`execute_research → technical_preflight_v4 → _execute_authorized → reserve → 独占envelope → running → launch_linux → 独占launch_attempt → broker.context.accepted_build=false → controller.main.verify_live_context → authorization_reasons → capsule_build_not_accepted`。

这是fail-closed，未证实工程true导致未授权绕过。但未来合法approval也可能在预约/尝试消耗后拒绝，故ready不等于当前policy已允许执行。最小另任务建议：将锁一致性检查置于任何reserve/attempt前；统一显示/预检/执行含义；无数据测试false-policy零副作用拒绝、精确授权及漂移拒绝。任何代码/策略改变都要新闭包与精确绑定，不得直接翻旧policy或继承旧SHA批准。本轮不改守卫。

### ENG-02/03：观测缺失及误验收风险

collect_snapshot在碰撞getter异常时保留collision_count=None/异常；run_observation_loop用 `(frame.get('collision_count') or 0)>0`，finish只要求六类身份API、不要求collision_count。存在把不可用当零的静态路径；未声称历史碰撞或getter失败。另任务应补每步缺失即拒绝，并测试getter缺失、抛错、中途缺失和恢复不抹缺口。

verify_receipt对summary仅封存/hash/XML根检查；assess_capsule进一步重建FCD、TripInfo与原生身份，但没有summary inserted/ended/discarded与逐车总量对账。原生证据明确的pending可保持identity_accounting_complete=true，不等于1150全插入或117初态全在t0；B00非R臂无全车出发阈值。纯反例复现一直pending、actual_departure=None、right_censored=true仍可核算/已出发时钟完整。

研究者必须先决定117初态及各组的实际插入时限、延迟与删失接受政策；再另任务补summary交叉核算及冲突拒绝。不得由工程师自造阈值，不能将account-complete显示为initialization-approved。

## 4. Git状态与唯一绑定

proposal/scientific_diff记录git_commit=735bab0…、dirty=true，描述候选生成时工程helper/证书/报告尚未提交的快照；正式审查基线为753b666。不是仅凭提交说明认定安全：347历史文件复算、38源逐项与正式Git属性检出一致、12源闭包一致。旧candidate-v6审计manifest83项在本轮context增量前全部匹配。

formal_risk_measurement.py的Git原对象是LF，绑定执行字节是CRLF；.gitattributes明确eol=crlf，git cat-file --filters还原后SHA匹配。首次审查器错误按raw blob相等断言失败，按既定属性保存raw/filtered双哈希后通过，原失败日志保留。未修改生产源或Git属性。

prepare_stage_0_5_b00_admission_v6.py独立登记在工程软件/审计中，未属于12源原生闭包，native路径不import准备器。本轮helper也不接执行链。精确proposal SHA定义文档与传递哈希对象，不认证人类来源，也不能保证未来运行时/资源无漂移。dirty是可解释的历史时点，不能据此单独断言无影响。

四份context本轮增量会使其现值变化；旧audit manifest仍绑定753b666历史字节，后续按历史Git版本核验，不重写旧manifest。本轮最终字节由新审计清单另绑定。

## 5. 初始化政策与DS38的科学含义

静态复算1150=117初态+1033非初态；117均声明depart0，非初态声明0.3至419.6秒。只把117中原数值departSpeed=10的38辆改成max，不改depart/位置/车道/类型/route/顺序；另79初态及全部非初态保持。38个ID前缀为i0000–i0006、i0027–i0034、i0054–i0064、i0077–i0082、i0098–i0103，实际ID重复如i0000_i0000；全部before/after及79不变ID见[static_facts.json](audits/stage_0_5_scientific_admission_review_v1/static_facts.json)。

**Interpretation（机制解释）**：max把固定数值速度约束交给原生插入规则，受车道/车辆限制、前方交通和实际时刻影响；不是实际10m/s或t0成功的证据。当前input_acceptance对max只要求不超过适用限速，对数值速度要求插入值匹配。未用外部未核验文档给出更强保证。

DS38改变所比较的初态政策。共享DS38四臂可讨论该政策条件下的差异，不能将DS38与原初态之差归因为供给操纵。恢复原数值政策更贴近原声明，但已知不相容日志并未消失；另版安全政策可纳入i0007，却改变对象，需所有对照共同重绑。三选项均须研究者决定，动态有效性均未知（INIT-01）。

## 6. 输入保真审查

| 文件 | 原policy-A准备输入SHA | 候选实际SHA/差异 |
|---|---|---|
| network.net.xml | `d69c79c4c2303125e696d86b5907cbd1e043f21971dde4c4903eb3ccf84dbdcf` | 同左，原字节一致 |
| routes.rou.xml | `4b1ee23fa4745d6c6b928f4a0f27bd752a6e057c4f8a50cf0221e1480167756e` | `db9e2ea2250a00d3b0dded552d6aedbaf62a46a3dcbb2d778e9b43d71eaf9128`；仅38速度 |
| run.sumocfg | `2eb1cc9ec8a306cd497d43cfd856d965bf7af77b8c3382992e24bba8d538617a` | `c55b242f09b6a86527852bf686f06f3347abc44aa1c16c199c51935ce93dc6c6`；新增TripInfo三项并XML重新序列化 |

新增选项仅tripinfo-output=tripinfo.xml、write-unfinished=true、write-undeparted=true。三阶段原准备→DS候选→当前候选路径、实际SHA、XML差异保存在static_facts。这里“原始”是既有登记准备场景，不是逐字节原NGSIM；未读locked holdout或重建上游数据。

明确配置seed20261201、420s、step0.05、FCD0.1、ballistic、单线程，time-to-teleport=-1、collision.action=warn（controller另监控事故早停）；B00五条main_2恒10、无新匝道脉冲。5个vType显式Krauss/LC2013、长度、tau、minGap、加减速度、sigma、actionStepLength/sigmaStep、speedFactor/Dev/maxSpeed等。未把全部SUMO默认显式化，未写选项仍依赖绑定1.26实现。未发现三文件未声明静态漂移；实际插入和默认值科学合理性仍未验证。

**文件级保真**证明执行符合批准文件/变换；**场景级合理性**决定是否为研究对象；**科学有效性**决定可支持何种结论。工程证书只支持静态输入/资源资格及已测合成链，不能自动批准后二者或DS38政策（INPUT-01）。

## 7. 正式测量契约与实际调用

未来生产路径确实为 `_execute_authorized → measure_completed_capsule → assess_capsule → parse_fcd → fcd_to_state_frame → measure_state_frame → local_d1_measurement / offset100_cloud`，不是仅存在未调用实现。本轮只静态审计，没有调用科研执行入口。

C6按同一native lane/edge、时刻的可观测前车，以前保险杠差减前车物理长度计算净间距；速度用原生值，mapped y仅区域/分块。内连接段/无可见同车道前车是missing/不可靠，不能补零风险；换native lane切断边/连续段，不虚构跨路段前车。车辆长度由绑定route/type获得，未知长度拒绝。状态适配首个加速度差分有fillna(0)实现；这不把缺失前车变为零风险，D1风险资格另依赖间距/TTC/可靠连续边。

D1：TTC>0且<2s、连续风险跨度>=0.2s；全上下文识别、onset归属。E为同run/scenario/身份生命周期/前车、100ms连续、native lane与质量/break/gap合格的整边数×0.1s；rate=3600N/E。零E不可评价；正E零事件仅是可评价零事件，不证明无风险。确认越窗、左延续、右删失分别保留。native break/gap沿用两端资格，真实参考入边break/前车可观测性不自动等价，仍须限定科学接纳。

点/onset窗[120,390)、mainline1–5、y[150,350)；整边要求前端>=120、后端<=390，逐格需要右端点。9×2格为30s×100m、5车道=0.5lane-km。参考SHA=`62b86fdc6a860e321dd29cb1e1c492c784ce9240974ca909b8be5cff1e788f17`；本轮18键、elapsed开始/时长/空间/observed/正D1核验，最小states5710、D1_E562.8veh-s。绝对采集时刻与elapsed列分开。参考正支持不能推导模拟也有。

未来要求：4200个FCD帧0..419.9、8401个0.05s原生身份快照0..420、8400控制/回读；18格各>=10状态、正D1、完整时间与右端点。vehicle-s、D1跟驰暴露、密度分母不同。TripInfo核对depart/delay/speed/lane/pos/arrival，与departed/arrival和FCD首现对账；事件观测容一个step时差，100ms首FCD不替代精确插入时刻。unfinished/undeparted显式记录；负depart/缺TripInfo不推discard。journal哈希链重放后对摘要；未知/重复ID、时钟冲突、缺帧、必要API缺失拒绝。summary数值对账与全车插入政策尚有ENG-03缺口。

| 历史问题 | 本次B00关系及剩余边界 |
|---|---|
| C1点/边分母 | 当前调用D1边函数；旧runner点率不当当前基线，真实/模拟边等价未自动接受。 |
| C2错位分块 | 当前offset100为两个完整100m格；旧50/100/50格覆盖不追认。 |
| C3时距误标 | 旧g/closing错名不进入B00主D1验收；未来引用需明确g/v等公式。 |
| C4时间/分母混用 | 历史可由全采集/内部窗解释；本次只绑指定elapsed参考，不混全域统计。 |
| C5计划/执行包络差异 | 本次八检查不调用旧membership；旧通过不变成新Gate或阈值。 |
| C6物理测量 | 当前走修复链，只部分可观测；旧事件不自动升级，变零不等于风险不存在。 |
| C7初始化 | 当前仍A窗；历史残留/缩窗代价未解决，P2已接触，不是盲验证。 |

依据WP1审计、C6/C7离线报告及当前函数；未机械重审无关历史实验，未重测旧原始轨迹。MEASURE-01保留有限可观测合同/另版合同的研究者决定。

## 8. 实际插入、i0007与交互相容性

历史日志SHA=`2eaf711e946b275deb93cfba10660475ada7223f936ba2596f562b9b5ad4d258`：第1行i0007在t0因slow lane ahead不能按声明速度出发；第2行i0063在t180出发速度过高，后续TraCI关闭。i0007_i0007仍depart0、lane5、pos233.91、speed15.23、route from_main_1_through；i0063在38变换内。历史供给臂t180降速与B00恒10不同，不能推B00同样失败；i0007未变也不能保证成功。aggregate discarded=1不证明具体ID，FCD缺失不等于pending/discard。

静态可解：车辆/变换范围、日志指名、计时定义。动态未知：actual depart/延迟/安全插入/速度施加、互动队列、碰撞、残留、discard身份和18格支持。未来应逐车保存声明、loaded/pending/departed、精确TripInfo、active/on-road/arrival、首末FCD与有限终点删失；初态117、非初态1033及各组实际供给分开。完成step后的速度不得冒充插入值，discard必须身份级原生证据及hash。

原生Error、控制/版本不符、输入/hash/时钟漂移、未知/矛盾身份、必要接口缺失、teleport/collision、资源/隔离失效、未满足预声明插入/支持或完整回执，均失败/拒绝，不作为完整结果。合法pending/有限终点删失的科学接受由研究者事前决定；不能丢异常车/换窗口获得通过。ENG-02/03需要先另任务消除。

失败也必须封存stdout/stderr、native_console、异常栈、coordinator/controller失败、identity_events/interrupted摘要、未完成XML、资源样本、输入/源/envelope及SHA，明确阶段/启动次数/清理结果；独占位置，不自动重试、不覆盖失败。历史 `POLICY-A-VALIDATION-SCOPE-01 = Not Accepted` 完整保留，新SMOKE没有追认它。

## 9. C7窗口政策与科学可识别性

历史C7（Historical Observation，未本轮重算）：0750最后局部初态记录130.5s，A窗[120,390)含106条=10.6veh-s初态记录；候选B共同起点180s、14格/210s，支持缩短且恢复期变化。当前候选固定A窗18格/270s。历史清空不保证DS38清空，也不证明稳态/间接影响消失。研究者可接受A有限初始化影响，或另版B窗/操纵时序；不得本轮/运行后改窗，不得删初态车后声称同一总体（WINDOW-01）。

**Observation**：B00是0750/seed20261201/DS38、无供给/匝道新增干预的初始化与支持诊断，没有处理差异，当前没有B00科学观测。未来成功只能支持该次配置下的工程记录与限定域观测。

**Interpretation**：同政策四臂可形成S10−B00、R01−B00、SR11−R01−S10+B00条件性比较；仍可能被实际供给人数/插入延迟、初态、有效前车支持、窗口、测量版本与随机性混杂。不能把原初态旧风险表与DS38新表之差归因供给作用，不能只保留有利格/车辆。

**Hypothesis**：非局部风险差异可能来自普通交通传播、局部密度/速度、供给时延、初始化残留或可观测支持选择。单次B00甚至同seed四臂有限差分都不自动区分AAD机制和一般交通机制；工程namespace隔离不是科研干预隔离。

**Research Proposal**：先审议B00资格诊断；若通过，再单独审议同初态/同身份供给四臂，披露N/E、缺失/删失、逐格支持和状态。更强主张需预声明估计量、匹配对照、传播/通信机制消融、时空延迟证据、多seed重复、初始化/窗口敏感性；不得挑seed、调δ/h/B或事后Gate。共同支持条件下结论不等于原总体效应。

**Researcher Decision**：是否值得承担可能失败的初始化诊断，采用何种初态/插入/删失/支持目标，何时再审机制和重复设计。B00不能直接支持现实交通泛化、稳态、因果超距作用、Stage0.5 Gate或Stage1.1通过。

## 10. 决策矩阵摘要

完整JSON逐项有证据路径/SHA、函数行号、Observation/Interpretation、不确定性、多分类、选项解决的问题/新假设/科学影响、验证责任与明确下一步。以下是摘要，不是正式批准：

| ID | 分类 | 处理/待决定内容 |
|---|---|---|
| AUTH-01 | 现有证据 | accepted分层已解释，工程true不能独立放行。 |
| ENG-01 | 工程歧义 | 高：ready与晚期policy锁冲突，先另任务修复/新绑定。 |
| ENG-02 | 工程歧义 | 高：collision None不能视零，补缺失拒绝。 |
| ENG-03 | 工程歧义+研究者+动态 | 实际初态插入/合法pending/删失政策及summary对账。 |
| GIT-01 | 现有证据+工程边界 | dirty时点/347文件/38源解释，保留raw与属性检出SHA。 |
| INIT-01 | 现有证据+研究者+动态 | DS38、恢复原数值或另版；改变则重绑。 |
| INPUT-01 | 现有证据+研究者 | 文件保真与场景合理性/科学有效性分开决定。 |
| MEASURE-01 | 现有证据+研究者+动态 | 接受部分可观测C6/D1/18格合同或另版。 |
| WINDOW-01 | 研究者+动态 | A窗残留还是另版B窗/时序，禁止事后切窗。 |
| DYNAMIC-01 | 现有证据+研究者+动态 | i0007保留诊断风险或先另版，discard不可猜。 |
| DYNAMIC-02 | 研究者+动态 | 条件解决后是否另授单次B00；本轮不授权。 |
| IDENTIFY-01 | 研究者+动态 | B00有限目标及四臂/重复/机制对照边界。 |
| HISTORY-01 | 现有证据+科学边界 | 当前调用相关性明确，Not Accepted/旧科学等价不追认。 |
| AUTH-02 | 工程信任边界+研究者 | 精确JSON依赖真实决定来源，是否需要更强认证。 |
| ENV-01 | 历史证据+未来实时 | 历史live通过，当前live本轮未重验。 |

九项明确答复：ENG-03、INIT-01、INPUT-01、MEASURE-01、WINDOW-01、DYNAMIC-01、DYNAMIC-02、IDENTIFY-01、AUTH-02。先选择科学目标/政策，再完成高优先级工程复核，最后审议新精确执行对象；无需为本报告重跑SMOKE。

## 11. 验证、失败保留与上下文一致性

实际命令/退出码/原始stdout和stderr哈希见[validation_record.json](audits/stage_0_5_scientific_admission_review_v1/validation_record.json)及validation子目录。原始bytes先保存，再安全显示；不把旧1331测试或旧live当本轮运行。

- 既有candidate verifier：exit0，独立verify_receipt Pass、精确三SHA一致，未调用prepare/执行入口。
- 本轮实际technical_preflight_v4(inspect_runtime=False)：命令exit0；返回ready=false、BLOCKED_ENGINEERING，唯一technical_error为live_Linux_runtime_and_resource_check_required，authorization_pending非空。这是刻意不做live检查的静态结果，不推翻或冒充候选封存的历史ready=true。
- 静态事实器首次exit1（raw Git blob与CRLF执行字节的审查假设错误），按既定属性修正审查器后新日志exit0；原失败保留，生产源未改。
- 五项AST提取纯函数反例：exit0，空临时目录/纯内存合成对象，无科研数据、授权文件或原生入口导入。
- 文档测试默认Temp及首次任务内临时目录各exit1（均13个setup权限错误，未运行测试断言）；不改ACL，使用新独占任务目录和工具权限后13 passed、exit0。两次失败及原始日志完整保留。
- 远端核验首次exit128（受限环境schannel SEC_E_NO_CREDENTIALS），工具网络权限下重验exit0，仍753b666；失败保留。
- 文档严格检查、证据verify、文档测试、矩阵/哈希/受保护对象及提交后纯Git验证，以validation记录和最终回执的实际命令/退出码为准；skip与失败不计pass。没有生产代码修改，不重跑全量或原生软件测试。

提交前实际严格文档与便携证据verify均exit0，矩阵/9决定/证据SHA/历史83项manifest和受保护对象检查exit0；完整routes允许字节变换及sumocfg三输出项全树比较exit0，审查helper语法检查通过。5项纯审查反例和13项文档测试均通过，无skip。最终提交SHA、push及提交后新纯Git检出的真实命令/日志SHA另存任务内交付回执，避免在被验证提交内自引用其自身SHA；不会将提交前日志当提交后结果。

便携限制：7份本机原准备/DS输入或原始失败日志在本机实际读取/复算，清单明确portable=false；纯Git可复核当前候选、347封存文件、源码/报告/聚合静态核算，但不能冒充重新读取这7份本机文件。审查器显式列出其缺失，缺任何便携文件则拒绝。旧审计文档哈希按基线Git版本重建。新audit目录用局部.gitattributes固定原字节；提交后新检出显式core.autocrlf=false，仍遵循既定formal_risk_measurement.py的CRLF属性。

本轮不是科研结果登记，未修改机器注册表/正式结果。通用exporter已知会漏三个独立扩展登记，为遵守历史原字节边界不执行其写入模式，仅执行既有便携证据--verify；不将这个范围限制冒充重新导出成功。纯审查helper做语法检查，不扩大到全量生产测试。

只增加本报告、审查helper/结构化产物及四份context日期增量；candidate-v5/v6、历史证据/失败/授权、账本、AGENTS、正式决定、生产代码/config保持。旧manifest按历史Git时点核验，不追写。没有新的实时环境认证或科研轨迹。

## 12. 下一步与停止条件

1. 研究者阅读本报告与九项决定，可先审科学政策，明确不同时授权执行。
2. 另行工程任务处理ENG-01/02及ENG-03对账，提供无数据反例、重绑及独立验证；本轮只报告，没有代改。
3. 科学定义或代码/策略若变化，建立新精确版本，保留candidate-v6，不迁移旧SMOKE授权。
4. 所有条件有证据后，再由研究者对新精确proposal作单次B00决定，启动前做必要实时检查。不重复SMOKE或无关旧实验。

停止：绑定漂移、policy/锁不一致、关键观测缺失、科学定义未决、实时资源/隔离失败、必须改科研语义才能继续。未来实际Error/身份/控制/支持异常须按事前合同失败封存，不自动重试、不事后筛选。

**最终科研状态：RESEARCH_APPROVAL_PENDING。** 审查与决策材料完成不代表科研准入、授权、实验验证或Gate通过。
