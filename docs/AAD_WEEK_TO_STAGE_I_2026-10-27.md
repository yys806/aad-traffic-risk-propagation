# AAD 本周仿真与协议准备：2026-10-27

任务：`AAD-WEEK-2026-10-27-TO-STAGE-I-V1`；目标期限2026-11-01。事实基线为进入任务时已核对的`origin/main=e38f5240a6542ceb12ec7325a59899dd834132be`。本报告以实际产物为准，不将工程验收解释为科研效应成立。

## 1. 当前结论

**Verified：`B00_EXECUTED_MEASUREMENT_ACCEPTED`。** A03完整运行420s，8400个0.05s原生步；FCD为0.1s、评价窗口仍为`[120,390)`，seed仍为20261201。原生独立执行回执与八项测量验收全部通过。Stage0.5仅获得有限场景诊断证据，科学交互Gate仍`blocked`；Stage0.6得到可复算的数值预算和完整字段候选，科学容差尚未批准；StageI为`BLOCKED`，没有正式效应确认启动。

机器入口：

- `evidence/results/RES-AAD-WEEK-20261027-V1/`：运行、人口、测量、18格、失败与来源。
- `evidence/results/RES-STAGE-0.6-WEEK-20261027-V1/`：数值预算、32字段协议候选、当前Gate及锁校验。
- 原始大产物保留在`code/outputs/formal/calibration/stage_0_5_ready_to_admit_v3/runs/WEEK_0750_B00_IC1_s20261201_A03/`，不进入Git便携证据。

## 2. 初始化与执行修复

研究者在当前聊天明确授权速度修正及修复后直接运行；此授权来源不是数字签名或独立身份认证。审计全部117初态：只发现`i0007_i0007`属于确定的本类硬冲突。其main_1剩余距离0.13m，15.23→10m/s按emergencyDecel=9的最短距离为7.3307167m，无法在下游10m/s限速前减速。仅将该车departSpeed改为10.0；DS38、其余79辆初态的其他属性与1033非初态、位置、路线、车辆行为、网络均不改。修正routes SHA为`b6df8d9ce52b56fac50899cc2e6d1329c7858325aae0f0c86c76d77f796a7574`。没有把所有车速度设为10。

三次B00分别使用独占目录及新的proposal/policy/envelope。A01/A02完整运行后资源采样间隔超过原0.5s限制，均被拒绝；不能因轨迹完成而取消失败。heartbeat和RLock不足以保证共享进程中的采样及时性，A03改用同一capsule内独立进程采样，独立GIL，保留原资源阈值及cgroup硬限额。没有证据证明GC或文件系统是唯一原因。独立Linux持有GIL反例测试及新源码最小集成通过后才启动A03。

| 真实B00 | 时长/步数 | 控制器/载荷退出 | 资源样本 | 最大间隔s | 结果 |
|---|---|---|---:|---:|---|
| A01 | 420s/8400 | 0/0 | 10051 | 1.142993683 | 资源覆盖拒绝，原始证据保留 |
| A02 | 420s/8400 | 0/0 | 12717 | 1.120348533 | 资源覆盖拒绝，原始证据保留 |
| A03 | 420s/8400 | 0/0 | 3483 | 0.154145732 | 独立执行与测量通过 |

本任务B00真实启动3次；不把此前candidate-v8首步失败算入本任务。受执行源码影响的新版本3s集成各一次（r8/r9），均是工程集成，不代替B00。A03资源记录末时刻390.661674249 wall-s；峰值进程树RSS275808256B。磁盘、cgroup、只读输入、网络及子进程清理的原始采样和验收见运行证书；remaining_pids=[]，descendants_reaped=true。

A03协调器在原生执行回执Pass后因直接入口未加入`code/src`而发生`ModuleNotFoundError: riskprop`。原ledger的`measurement_rejected`保留。修复入口后以**candidate-v4-measurement零启动**重验同一封存轨迹，八项全部Pass；没有第四次SUMO。旧执行CLI原字节快照在`docs/audits/aad_week_20261027/a03_executed_coordinator_source.py`，SHA=`6d296c99892afcc0d8766d78fa798e3d6af81dad0bdc62217ea7102668eb7316`；不得把修复后CLI冒充A03当时执行源码。

## 3. 精确绑定与生命周期

A03 proposal SHA=`dec7658aa38f06b9a8182941344cc6d16ae1b268219415539f624961d04c7d86`；policy SHA=`8da5c25bd86d81fa1110b7ab96f4db4cffc81368aadeebf144b95b3989d0c053`；envelope SHA=`b562466a3c044bc29e90d745fab46bf755c5239ab4309690240ca7c3d611686f`。后验离线测量proposal SHA=`c06e5655186be507ff488dc31b029be232373a74ea7b912fd6fe9d6a8eab1cef`，明确native_launch_allowed=false。12原生生产源、运行时清单、输入和原始产物哈希均在provenance及独立receipt内。

| 声明分组 | 声明 | 实际插入 | 已到达 | 仍在网 | pending |
|---|---:|---:|---:|---:|---:|
| 初态 | 117 | 112 | 112 | 0 | 5 |
| 非初态 | 1033 | 893 | 745 | 148 | 140 |
| 总体 | 1150 | 1005 | 857 | 148 | 145 |

全部ID有可追溯状态。实际插入不等于全部在声明时刻插入：初态出发延迟median=0、p95=4.9525s；非初态median=21.75、p95=62.51s。末态145辆由native pending API确认，未删除、未改seed/窗口，不因FCD缺席猜状态。summary最终记录t=419.95对应最后完成步，loaded1150、inserted1005、running148、waiting145、ended857、arrived857、discarded0；8400条summary与8401身份观察、TripInfo（含未完成/未出发）及FCD首次出现/结束逐步交叉验收。

8400个要求观测的步均有有效碰撞观测；collisions=0、teleports=0、discarded=0。碰撞getter表示**碰撞车辆数量**，不冒称碰撞事件计数；summary事件聚合另行核对。discard API没有可靠逐车getter的限制保留，但本次聚合discarded=0且1150身份均核算，没有猜测丢弃ID。完整原始逐车表在本机封存；Git只保存聚合及其完整表SHA。

## 4. Stage0.5实用验收

18/18单元均有状态及正D1暴露。实际D1暴露9778.4veh-s、97784条有效边，局部611辆、111324状态。局部有效TTC状态62206，not_applicable36666，missing12452；缺失没有补零。**已确认局部P2 onset=0、risk state=0**，率为`evaluable_zero_events`；这是有支持域内的零事件，不是推断无日志即零。

18格与已绑定0750真实参考的平均速度10.489726/10.459475m/s、密度41.231111/44.100370veh/km/lane；逐格差异与closing、D1暴露见matched18.csv。均值接近不证明动态等效。真实18格参考不含P2计数，不杜撰同格事件对照。历史M3交互不相容证据继续有效，单次B00不能将其洗白。

结论：**Verified有限范围诊断；总体科学Gate blocked**。本次允许解释有限420s、单seed、实际延迟插入下的交通状态、暴露和重建；不能据此证明现实风险绝对拟合、源事件触发效应或因果可识别性。零局部源风险不是次要统计偏差，它直接限制消息源和触发效应检验。pending本身不是阻断，主要问题是可解释的源事件/干预条件。

首选最小后续设计：复用现有同初始化B00/B10/B01/B11**供给×匝道诊断**，先由研究者确定有意义源条件及尚未确定的匝道脉冲契约，再作配对机制检验；不要把该四臂冒充StageI通信效应四格，也不扩大重做整个研究框架。支持成立后再用独立配对seed pilot估计效应方差。当前没有新干预臂启动。

## 5. Stage0.6数值预算与科学候选

沿用derive_delta_eq、正式rho tau=15.364279197080283s及现有物理路径实现。规则预先在脚本固定：TTC0=1/2/4/8/16s×horizon=.2/.4/.8s的15个平滑fixture，步长.1/.05/.02/.01；解析Decimal、独立math.fsum；120个gap/closing端点精度fixture，逐来源higher99%保留全部案例。

| 误差来源 | higher99%绝对rho误差 | 适用说明 |
|---|---:|---|
| 解析数值 | 0 | 本fixture域，不是全软件误差为零 |
| 时间离散 | 0.003126623630 | 已声明平滑轨迹，非实际SUMO动态对照 |
| 独立分析器 | 约3.33e-16 | 同一输入的独立积分计算 |
| 重建/量化 | 0.007484070782 | gap≥1m、closing≥.5m/s及±.01端点扰动 |

现有max规则候选0.007484070782不保证误差源联合界；保守sum候选每臂0.010610694411、两臂0.021221388823、四臂DID0.042442777646。它们仅是声明fixture域的候选，不能用作P2事件率容差或独立物理世界系统误差界B。解析真值与物理路径fixture通过；真实动态效应方向及.1/.05/.02配对收敛尚未建立，不能将fixture方向充作真实处理方向。

A03全部valid状态244664中，240620支持±.01 gap/closing四角敏感性计算，4044近零/边界排除；higher99%=0.009846098293、max=0.017363312053。此值高于部分fixture重建候选，进一步说明**不能把fixture候选当真实全局保证**。这是编码状态条件敏感性，不是已知真实重建误差，也不据此提高阈值。

协议候选已完整列出32个必需key及各自value/status/source/remaining；尚无事实支持的split、paired variance、最终n保持Unknown，不伪造。首选科学提案为rho全尺度δR=.05、δplan=.10、h=.0125；备选.10/.20/.025表示更粗的科研问题，不能因首选失败自动采用。5个百分点是明确科学价值判断，未由软件测试批准。alpha单侧.025、power=.90、n=max(100,n_power,n_precision)为规划候选，最终n必须使用真实配对差方差；同seed的三次重复不是三个独立样本。

epsilon_input建议精确配对输入/哈希零差；epsilon_state中的.01m/.01m/s/.1s仅是记录分辨率候选，非已验证动态等效容差。物理路径、右删失、缺失纳入、固定cohort、2s风险窗、seed与独立确认集规则均明确列出并保留待冻结状态。B为独立simulator-to-world因果对比偏差界，当前Unknown；首选将首阶段效应解释限制在已验证模拟条件内，科学批准后才改变外推范围，不能以数字容差冒充B。

## 6. StageI前置条件和最小待决项

重新读取当前Stage0.2 pass与Stage0.4 pass_limited，结合本次0.5/0.6报告调用**未修改的**protocol_lock_readiness及write_protocol_lock。结果protocol_lock_allowed=false、stage_1_1_allowed=false；writer实际拒绝，无锁生成，不沿用旧RES-PROTOCOL-READINESS-V1快照。

剩余的真正科研决定是：

1. 首选仅0750：复用本次已验收B00为诊断基线，沿用既有S10/B10五车道10→5→10、`[180,240)`脉冲，R01/B01对原总计60辆非初态匝道车辆保留各60s块归属和数量，块内声明depart压至20–25s，SR11/B11仅组合两项；先一个seed20261201的完整诊断块，最多需要补三臂而非重跑基线。此为既有设计的具体继续候选，尚未运行/批准。0750与0805不混为重复，0805不在本次速度修正授权内。匝道首选保持“全系统响应（含插入延迟）”估计对象：逐块列出全部声明ID、实际depart、进入/删失和相对B00的时序差，不把旧90%候选自动当科学合格线。研究者需确认实际操纵的判读契约及源事件定义；有源支持后才能准备消息处理实验。当前B00零源事件不足以直接确认远端消息效应，不能保证供给/匝道候选一定产生P2。
2. 批准精确endpoint/cohort/风险窗与SESOI、适用范围；首选上述.05/.10/.0125提案和模拟条件内解释，不把有限现实偏差等同真实世界偏差已量化。
3. 在1–2确定后执行真实配对校准及动态步长核验，按实际差方差计算n，完成独立split/来源绑定，再由原协议锁校验解锁。当前数据不能推导这些未知值。

本周工程产物与基线测量完成，不存在要求研究者重复批准同一速度/资源/入口修复的问题。不能在缺少单独有效设计时直接运行StageI正式确认。

## 7. 验证与历史保护

定向初始化218通过；资源监督扩展223通过/2平台跳过；Linux独立进程/GIL测试5通过；零启动测量及数值/协议相关27通过。本轮无数据全量1386通过/17跳过/7原生测试明确排除（371.52s，audit越界0、SUMO0）；compileall、严格文档和60个结果/908文件证据校验通过。最终实际计数与哈希统一见新结果validation_record.json及`docs/audits/aad_week_20261027/final_validation.json`，不将此前复用回归写成本轮全量。

candidate-v6/v8、旧policy false、旧envelope、旧失败、原SMOKE、历史POLICY-A Not Accepted均保留。AI_CONTEXT、注册表、阶段/结果索引和执行记录以本报告及两个新结果同步；旧块只保留其历史时点。Git状态与提交SHA从实时Git及提交后验证记录读取，禁止在被提交文件中虚构自引用提交SHA。

Postcommit source-byte check: the first independent checkout exposed Windows autocrlf conversion of newly bound numerical modules. Failed check retained in docs/audits/aad_week_20261027/postcommit_eol_failure.json. Four affected numerical/protocol modules now explicitly pin LF, while the existing formal-risk CRLF binding remains unchanged. Bound native, scientific, input and output hashes remain strict raw-byte checks. Other unmodified legacy test-source EOL differences are separately disclosed; the333-file software manifest records the exact source snapshot used by the full suite. No source-body change or extra SUMO launch. Repair: docs/audits/aad_week_20261027/postcommit_eol_repair.json.
