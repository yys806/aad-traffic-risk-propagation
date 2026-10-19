# Stage0.5 局部跟驰探索、测量闭环与性能优化

日期2026-10-19。任务AAD-0.5-LF-EXPLORATION；结果`RES-STAGE-0.5-LOCAL-FOLLOWING-EXPLORATION-V1`。基线main/origin `b258c782a88dce2187ce221d67ef551a46227bc4`。统一证据在同名evidence/results目录。所有结论exploratory_diagnostic_only / Engineering Diagnostic Only，scientific_claim_eligible=false。

## 1. 已批准范围与工程结论

研究者方案A已批准：固定局部状态、跟驰与风险测量不再以完整入口回溢资格为前提。本轮建立了局部状态→同刻前车→净距/闭合/TTC→连续性/质量→核心P2与暴露→局部边界归属审计的工程闭环。没有启动ABCD、正式校准或现实覆盖验收。旧C完整入口回溢继续Evidence Insufficient，不被本轮新状态或候选worker输出追溯升级。

本轮3次定向运行（120/120/300s）全部完成，无数值/身份/时钟/守恒/碰撞/teleport/来源或资源阻断。新增接入微型0次，剩余定向5/8次。LF1/LF2是相同seed和输入的传输等价对照；LF3是同一轨迹采集延长，前120s逐字段相同，**不是3个独立交通重复，不能池化事件/暴露当科学样本**。

## 2. 实现调用链与固定空间

新入口run_stage_0_5_local_following.py → lf_runtime（来源、冻结、预算、停止）→ lf_worker（只读.05s状态、原数值/计数/队列）→ lf_transport（等价的11项GET）→ local_following.decorate/analyse → 原stage_0_5_sumo点态/暴露接口和原formal_risk_measurement.extract_formal_source_events / ngsim_risk_calibration核心。Stage0.2核心、旧SUMO适配器和历史证据均未改写。

固定对象：**原尺度C main_1，lane0/1/2，后车前端50≤lanePosition<250m，0.6 lane-km**。同时核对edge、lane集合和位置，不能仅凭名称归域。选择理由是沿用B1既有固定三车道局部口径、避开main_2缩减段并保留可核验lane-km分母，不是看本轮速度/风险后选区段。50m包含、250m不包含；同edge三车道之间换道可仍在域内，跨edge即重新判断归域。真实换道与edge转换/车群成员变化分别记录，不给P2添加未经批准的换道中断规则。

旧CD压缩C是[10,40)m/0.09lane-km，旧D为原尺度[50,250)m/0.6lane-km且只有9辆路径探针。它们的支持与输入不同，不合并比较。新run ID和计划只复用封存工程XML，不是补齐或重判旧B1/B1.2计划。本轮仅单一原尺度C，D没有新运行；旧压缩C仅用于离线间隙分析。

内部步长.05s、记录/审计每步；正式核心使用偶数tick的.1s记录。getLeader查询前视距离固定1000m，缺少观测前车不等于证明整个网络无前车；此类样本不进入可靠跟驰暴露，不能补成零风险。全网同刻前车incarnation先解析，然后才给后车标局部归属，前车允许在局部之外。没有先裁切导致的假missing。缺帧、身份切换、未知leader不连接事件/暴露。全局身份守恒、局部边界流、局部车辆时间和pending分开；未来未到期需求不计pending。

## 3. 点态语义与质量

物理净距=getLeader返回距离+后车minGap；同车道另由前车front−length−后车front独立核查。闭合速度=后车速度−前车速度，单位m/s。可靠且gap>0、closing>1e-3时TTC=gap/closing；严格沿用原符号和阈值。

| 状态 | 含义 | TTC/暴露处理 |
|---|---|---|
| valid | 身份与字段可靠且有效闭合 | 有限TTC；可评价跟驰 |
| not_applicable，非闭合 | 已知前车、可靠但不满足closing epsilon | TTC缺失；仍可进入可评价跟驰边 |
| not_applicable，无前车 | 没有观测前车 | 不是零风险，不能进入可靠跟驰暴露 |
| invalid | 可靠观测到非正净距 | 不计算有效TTC，可靠跟驰层保留、可评价层排除 |
| missing | 前车身份/速度/净距不能测量 | 未知，不补零；仅observation_quality别名为not_measurable |

没有把原measurement_status词汇改成新的科学定义。数据中未观测到invalid/missing不表示一般域被验证。公开加速度是报告的前一步平均量，数值重建始终取步初公开加速度；没有把步末值当步初。

## 4. 正式核心与局部P2可计算性

继承TTC<2s、至少.2s观测连续跨度、首次实际满足跨度的确认时间、同车/同前车身份和真实.1s时钟、closing epsilon1e-3。max_gap_s=0.11与原时钟/帧相邻检查同时生效，不允许缺帧桥接。暴露继承可靠相邻跟驰边，两端measurement_status均在{valid,not_applicable}；invalid/missing不当零风险。事件率定义event_count / p2_evaluable_following_vehicle_hours，即每可评价跟驰车时。点样本数、任意长度风险片段、达到.2s片段、正式核心确认事件和暴露分别输出。

LF3局部有1222个TTC<2点、96个局部连续风险片段，其中88个满足.2s跨度。这些并非正式局部P2。全网原正式核心计算266个**工程**确认事件、42404.30veh-s可评价跟驰暴露；独立按原始身份/时钟/风险序列和边算术复核一致。这是算法可计算性证据，不是局部正式率或现实风险结论。

实际局部归属候选：起始在域86、确认在域87、全程在域83；端点均在域的可评价暴露14636.20s只是未批准候选。合成进入反例也给出起始归属0/确认归属1。不能默认任意一种，不能将全域266直接归到局部。**局部正式事件数、正式可评价暴露Unresolved；正式局部率Not Calculated**。既有Stage0.2定义不变，待研究者把目标估计量、边界/时间规则与分母一起冻结。未计算的新值不是0。

## 5. 新发现的适配器防御缺口

Documented Intent：身份和时间中断必须保留。Actual Implementation：旧build_sumo_formal_source_frame在其原生无错误recorder域内无条件写identity_break=False/observation_gap=False。超域接收带真实标志的外部frame会抹去证据。六行独立反例中已知中间身份断裂，旧适配器确认1个事件，新LF接口保留标志后0；原正式核心没有改变。见formal_adapter_break_counterexample.json及对应测试。

Status：已在本轮独立LF接口修复；旧适配器保留历史，不扩张其适用域。没有证据宣称历史原生运行受污染。另防止局部先裁切丢前车；这些是接口/工程修复，不是研究者新P2政策。

## 6. 14.35m间隙离线解释

读取的仅是已授权CD任务压缩C本地状态/队列帧，按portable SHA和角色复制；不是旧B1 C完整状态。60s见v00036前端65.499m、v00033车尾79.85392957m：上游lane余量1.001 + 显式internal lane8.12 + 下游lane车尾5.23392957 = **14.35492957m**。实际位置、车长和路径独立复算一致。漏算junction会错误变成6.23493m并可能错误连接；现有映射没有该错误。

hwy_j1是priority junction，request有foes上下文。固定[MSVehicle源码](https://github.com/eclipse-sumo/sumo/blob/fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3/src/microsim/MSVehicle.cpp#L7492)要求link.hasFoes与keepClear等条件；记录位置靠近停车线，与阻塞链接/keep-clear解释兼容，但旧状态没有编译link标志和该私有决策分支，因果激活仍Unresolved。入口插入几何/pending是独立证据，不能代替junction原因识别。保持10m/2s，无重跑、消融或阈值修改，C完整回溢EI不变。

## 7. 性能优化与观测等价

批处理只发送GET_VEHICLE_VARIABLE（0xa4），仅9个设备参数+路线+停车任务共11 getter，每车每.05s均读取，无生命周期缓存或观测降频。使用原官方打包/类型解码，逐一校验状态、返回var/对象ID、长度和剩余payload；错误fail-closed。固定[TraCI服务器](https://github.com/eclipse-sumo/sumo/blob/fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3/src/traci-server/TraCIServer.cpp)按请求顺序处理GET，进入下一simulationStep前不推进运动；[官方客户端](https://github.com/eclipse-sumo/sumo/blob/fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3/tools/traci/connection.py)源码与已安装文件逐项指纹核对。13原数值源+6新协议源，共19具名源；二进制未修改。

| 测量 | LF1 同步 | LF2 批处理 |
|---|---:|---:|
| 相同输入/120s状态行 | 175679 | 175679 |
| 每步getter请求 | 1932469 | 1932469 |
| collector往返 | 1932469 | 5114 |
| collector墙钟s | 239.727 | 26.738 |
| worker墙钟s | 283.307 | 68.627 |
| controller墙钟s | 290.434 | 73.855 |
| 采样进程树MB | 186.64 | 166.81 |
| 运行输出MB（后处理前） | 20.73 | 20.73 |

除独立run_id/incarnation前缀，28个字段（含time、步初加速度、lastActionTime、设备/路线/stop与leader）**逐值相等，NaN等价，未用近似容差掩盖差异**。数值分类和全部交通统计相同。仅身份标签的合法构造另核验。一次配对worker实测约4.13倍、getter段约8.97倍；LF1期间还运行过4.86s合成边界测试，未隔离系统后台负载，所以这不是统计benchmark或可推广的精确加速承诺。观测相等和相同getter请求数不受该时间解释限制；没有用往返降低倍数冒充整段加速。全字段原始文件SHA分别保留，文件自身因运行标签不同不要求SHA相同。

LF3 300s：866816内部行，worker320.845/controller325.051s，采样进程树228.25MB，后处理前108.03MB；成功在600s worker、3GiB、总输出2GiB/任务7200s限制内完成。53边界用例包含literal wire、错误返回、阈值/身份/时间/控制/局部支持等。非空停车任务、特殊设备/一般上下文不外推此次观测等价。

600s未执行：基于LF3行成本，44s自由流驻留假设约268s，同当前平均在场/成本约642s；基于冻结配对LF2行成本，无驶出计划车辆时间保守情景约1929s。这些是**工程情景，不是置信界、不是实测全600s准入**；未来在场量、供给/pending、初始化均会影响成本。没有为扩大运行放宽资源限额。

## 8. 冻结计划、预算与实际执行

plan SHA `68ca9c3b187ae1de3d9a8e59af2afc220b2edcee55c707f99500be11d0f1c34e`。固定SUMO1.26.0 / 官方commit fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3；原尺度C网络、823辆0..600s工程需求/车型序列、Krauss/LC2013固定参数、原23.8/6.2/30信号、seed20261019、单线程、ballistic/.05s/actionStep.1。运行时逐车型/数值/空网/无控制/无恢复/设备/路线实际核实，未读取真实轨迹。每次有独立预声明职责，未挑seed、调流量、红灯、驾驶参数或队列阈值。

| run | 职责 | 模拟s | 最终状态 |
|---|---|---:|---|
| lf1_LF1 | 原同步观测基准和成本 |120| completed_with_diagnostic_warning |
| lf1_LF2 | 候选批处理观测/性能配对 |120| completed_with_diagnostic_warning |
| lf1_LF3 | 同一固定局部的较长描述/测量覆盖 |300| completed_with_diagnostic_warning |

LF3门槛在运行前冻结：配对所有字段相同、无共享阻断，并以无驶出计划车辆时间上界估计300s成本<540s。实际门槛预测481.49s，满足后才执行。预声明0..120/300是资源约束的工程采集支持，不是科学暖机/评价窗口；全数据保留，60s分段只用于描述。600s未计划运行，不因结果好坏追加。定向用3/8，剩5；旧2次接入已用完且未复用。P/N数值探针和旧失败均留存。

## 9. 数值、计数与跟驰复核

实际处理1218174内部状态、1217470相邻边：1214622精确全通过（含398已验证后处理），1318 bounded，1530合法edge/lane不可评价，0近零未决/数值阻断；最大残差2.842170943040401e-14m，1e-6m未改变。重复配对也计入工程覆盖数量，不当独立科学样本。有界分支只必要范围，不算精确；合法坐标变化不置零残差。

.1s点态共609030行（含重复配对），全局/局部分账按原始位置独立复核，详见local_global_accounting_audit.json。LF3实际进入376、驶出151、在场225、到期pending35、未来未到期412；全网守恒0。局部245入/178出，14680.35veh-s，密度分母0.6lane-km不含pending。不能把局部车辆时间当正式可评价跟驰分母。

LF3 424417个有前车点的距离换算全部重算一致；406768个同车道物理净距对照最大残差0。跨edge/不同lane的17649点保留官方route/getLeader工程证据，**未宣称所有route净距都独立几何重建**。局部身份/点态支持与数值步内可重建层分开，不能把bounded或换道边隐藏运动当精确轨迹。

## 10. 局部交通与点态风险：Observation

LF3全采集局部均速2.964m/s、平均密度81.5575veh/km/lane、.1s低速点比例77.03%、净距中位3.2565m。局部首次<5m/s为46.85s（.05s支持），首次<.1m/s为49.6s（.1s支持）。未与真实校准窗口做距离排序或调参。

| 采集段s | 平均密度veh/km/lane | 局部均速m/s | 低速车辆时间比例 |
|---|---:|---:|---:|
| 0–60 | 16.553 | 16.971 | 22.24% |
| 60–120 | 78.199 | 3.784 | 66.83% |
| 120–180 | 102.774 | 2.028 | 82.12% |
| 180–240 | 104.237 | 2.034 | 82.19% |
| 240–300 | 106.025 | 1.995 | 83.13% |

146825个局部点中65476 valid、81349 not_applicable，invalid/missing本次未观测。1222个TTC<2点中的1203处于前120s，后180s只有19个。全网266核心工程事件不代表局部风险增长；实际局部政策候选86/87/83不同，局部fragment数96/.2s片段88也不是同一个量。

## 11. Interpretation / Hypothesis / Proposal

Interpretation：固定人工供给下，当前Krauss能产生可测量的密集低速跟驰；测量链可计算点态与核心工程事件，且可以把不能正式归属的部分留未知。拥挤、闭合TTC点态和正式P2是不同观测层，不能互相替代。

Hypothesis：早期过渡和后续停走/相近速度可能使局部闭合风险分布不同；这不是初始化因果识别，也不是现实行为有效性证明。单一seed/固定人工信号、通用几何/无活动匝道，不能支持C/D容量、跨junction风险传播或真实US101结构/波传播结论。

Proposal：保留通用路网局部探索方向和本轮批处理接口。当前已有足够工程基础进入**正式测量/校准协议设计讨论**，没有权限或证据直接开始正式校准。不能事后把120s选为暖机，也不能按均速或P2挑瓶颈。

## 12. 仍需研究者决定的3项

| 优先 | 决定 | 本轮证据/推荐 | 阻断 |
|---|---|---|---|
|1|局部P2事件与分母归属|起始86/确认87/全程83；先明确目标估计量并共同冻结边界/暴露，不选更有利计数|正式局部P2数、暴露与率|
|2|正式初始化、暖机和评价支持|前120s风险点占绝大多数；120仅为原性能采集上限，先独立设计敏感性协议|正式校准样本/窗口|
|3|目标交通/跟驰状态、需求识别、科学容差与可识别性协议|人工信号/823工程候选不等于真实上游需求；推荐协议设计，非自动开始校准|现实覆盖Gate/正式校准/后续阶段|

普通工程性能、边界测试和证据维护不需要研究者逐步批准。当前剩余5次定向额度只能按新预声明职责使用；不自动扩展到ABCD或holdout。

## 13. 来源隔离、失败和历史保护

Python -S受控胶囊、声明来源角色/SHA、拒绝路径负面测试和访问日志保留；无真实数据、第三验证、holdout、Stage0.2全源表或旧B1 C完整状态读取。只复制已授权CD任务C的必要工程状态和几何。Python审计不等同OS/native绝对访问证明；依赖版本/入口文件/Python/已安装TraCI源码前后指纹匹配，不宣称完整DLL/OS证明。

两次辅助报告bootstrap调用失败均发生在测试/数据分析之前（一次缺PYTHONPATH，一次先导入runtime再安装guard）；失败记录/源码保留，修正后53项/附加审计通过，无新增交通重试。核心执行逻辑冻结后未改；主分析与后补prefix/成本审计分别记录源码SHA。

B0隔离false/验证Unknown；旧B1 C两阻断与D未运行；B1.1 Pending Numerical Equivalence；B1.1-S947/948；B1.2冲突/主0-8；N正近零Not Observed/integrationfalse；P受限成功但旧授权false；CD v1假阻断与C回溢EI，全部保持。AGENTS和五项既有文献删除不处理。

## 14. 验证、Context Consistency Check与科学状态

冻结前受控204项通过；逐用例53项通过（输入函数、参数、预期断言/拒绝、实际结果和影响见boundary_test_matrix.json）。原始位置/净距/时钟/事件与暴露独立复算；175679行配对及扩展前缀相等。纯Git全量817 passed / 14 skipped / 0 failed（134.52s），14项skip逐项见test_record.json，缺本地密封数据不算科学通过；其中既有软件回归另执行7次SUMO smoke共76s，不属于3次定向交通运行或新的接入微型预算。定向/便携/文档62项通过。纯Git严格文档--require-clean、compileall、便携SHA与45项冻结源码绑定均通过；最终提交推送及远端新克隆精确SHA结果保存在本地post_commit_verification.json。根工作区严格检查仍受五项既有文献删除影响，未恢复、暂存或修改这些文件；新任务在纯Git克隆验证。

工程闭环不等于科学Gate：gate=pending_simulation_sample；scientific_claim_eligible=false；ready_to_start_stage_0_5_4b=false；reality_coverage_accepted=false；protocol_lock_allowed=false；stage_1_1_allowed=false；Tolerance Not Yet Justified；Energy Distance real-real上界Not Identifiable；局部正式P2 Unresolved。ABCD、Stage0.5.5、Lock、StageI/II未启动。

完整状态/逐帧队列/完整核心事件和测量点保存在code/outputs/formal/calibration/stage_0_5_local_following_v1；Git只提交便携输入、审计、SHA和有限事件例子。当前登记与AI_CONTEXT同步本次实际事实，不把候选政策写成科学决定。
