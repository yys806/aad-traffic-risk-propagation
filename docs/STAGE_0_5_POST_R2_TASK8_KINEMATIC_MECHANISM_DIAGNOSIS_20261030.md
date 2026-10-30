# Task8：真实风险形成运动学与 Krauss 动力学约束诊断

日期：2026-10-30；Task ID：`AAD-S0.5-POST-R2-TASK8`。
状态：**Verified / 离线诊断完成；机制因果识别与独立物理真实性仍 Unknown**。
基线：`832e09520eaac68b5cef898372b664c880b10bdc`；执行前成功 `git fetch origin main`，HEAD=origin/main，工作区 clean。

本任务新 SUMO 运行、TraCI 连接、seed、视频、第三窗口轨迹、locked holdout、Round3 均为 **0**。所有数值均来自已有授权轨迹或历史机器产物；无参数搜索，无历史实验重跑。

## 1. 研究主线与主要发现

AAD 最终问题仍是：来源可追溯且被控制器实际采用的远端风险消息，是否能在普通物理影响到达前，经目标行为改变区域风险。本任务只推进 Stage 0.5 的风险参考与机制适用边界，不能证明信息链、传播、因果机制或仿真等价。

**Observation 1：真实源区风险并非普遍从五秒前的大正闭合速度直接延续而来。** 完整固定车对的初始 closing 中位数在两窗均为 **0.024384 m/s**，到 onset 为 **2.599944/2.313432 m/s**。初始 gap 中位数为 **7.604760/8.784336 m**，onset 为 **4.703064/4.392168 m**。这是风险条件下的描述，不是对照试验或效应估计。

**Derived 2：前车速度变化是重要的五秒闭合贡献，尤其 0805；后车速度变化并非普遍增加闭合。** 源区 `Cl` 中位数 **3.482340/7.387742 m**，`Cf` 中位数 **−0.478536/−2.470556 m**；`Cl>0` 为 **70/105、91/107**，`Cf>0` 为 **46/105、26/107**。`Cl>0` 且 `Cf<0` 同时出现 **50/105、78/107**。负 `Cf` 只表示五秒内后车速度相对自身初值的积分贡献为负，不表示每帧都减速或终点一定低于起点。

**Observation 3：原匹配对照下，风险形成期间的差异大于初始 closing 差异。** 原匹配、两侧均完整的 **94/89 对**中，`C` 事件−对照差的中位数为 **3.196666/4.053535 m**，`Cl` 为 **1.140181/4.021836 m**；初始 closing 差仅 **0.004572/−0.179832 m/s**。匹配是在 onset 速度等变量上进行，未匹配五秒前的状态和完整扰动输入，不能把差值解释成因果效应。

**Observation 4：SUMO 有切换、有强前车减速，也有高 closing；关键差异在状态与时序的联合组织。** 七个源区 TTC[2,3)s 片段中五个在五秒内更换 leader，不能拼接；仅 B00 一例、Round2 一例可做严格五秒分解。B00 稳定例有 **10.83 m/s** 前车速度最大回落，却只有 **0.449 m** 净闭合：其初始张开贡献和后车速度变化几乎抵消。Round2 稳定例中前车贡献 **6.194 m**，后车贡献 **−5.313 m**，净闭合 **1.581 m**。没有一个片段被改称 Formal P2。

**Verified 5：当前 Krauss 不是一个插入安全二次式或平衡间距公式。** 官方 1.26.0 的动态 ballistic 分支使用当前速度计算安全加速度，经 emergency correction、加速上界和紧急制动下界，再与 dawdling、LC2013 协调和动作时序交互。`minGap` 在正常调用之前从物理净距中扣除；减小它不移除 tau、制动或决策约束。源码机制已核实，但没有原生 active-bound 遥测，不能据此指定唯一根因。

## 2. 科研定义与权限冻结

- Source=`S_UPSTREAM_MAIN`，主线 lanes1–5、y[0,150)m；Target=y[150,350)m。
- 仿真评价窗[120,390)s；目标 cohort=`C_INPUT_ROUTE`。真实两来源完整独立时间轴沿用 Task6，不把仿真相对时钟强行平移到 NGSIM。
- Formal P2 保持既有 C pair/time 定义；D1 继续是独立同原生车道局部诊断；B 类物理路径必须有独立见证。
- 原 Round2 minGap1.0 源区候选维持 `CLOSED_FAILED_ORIGINAL_SOURCE_CONDITION`，seed20261201、Rule A PASS、Source0、Target-only1，无独立确认。
- `formal_equivalence_accepted=false`；物理路径与独立物理参考不足；Stage0.5 blocked；Stage0.6、Protocol Lock、Stage I 不变，Round3 不启动。

## 3. WP0：复用盘点与实际增量

进入顺序核查 `AI_CONTEXT/00_PROJECT_STATE.md`、注册表、研究状态/项目索引、PROJECT_CONTEXT 和 Git；随后阅读 AI_CONTEXT01/05/06/07、任务指定的 Task6/Post-R2/历史重放/固定前车提案/Round3 readiness，并回到四份绑定状态表、原 Task6 锚点、封存 XML、历史摘要和官方源码。

| 已有工作 | 可复用的实际内容 | 本次没有重做 | 本次新增或尚未解决 |
|---|---|---|---|
| Task4/5 Formal P2 与唯一 onset | 全来源543/732；源167/159、目标174/252；两个窗口不可因共享原始 ID 合并 | 不重新提取/筛选正式事件 | 对全部 Task6 源/目标事件锚点向前延长至5s |
| Task6 联合分布与±1/2/3s上下文 | gap–closing 联合组织、速度分层、宏观共同支持、原匹配对照、本地 identity_contexts | 不重算全量联合分布、不重匹配、不做新 bootstrap | 原始100ms的完整[-5,0]分解、严格覆盖和原配对差值 |
| Post-R2 源区近阈值4/3段 | 已列明 onset/end/leader/最小TTC及 band-exit | 不重建全部 FCD 或重新选择片段 | 七例固定 onset leader 的前置曲线、不能分解的明确分类 |
| 324次微观响应 | 12对×9配置×3seed，20s；response plan/metrics/summary指定payload旧SHA通过 | 不重复任一运行，不重新搜参 | 区分旧均一车型与当前五档异质B00，审查历史lag算法 |
| 历史24对、48个计划配置组合重放 | replay plan/summary指定payload旧SHA通过；23对有结果、43个评分组合 | 不重复、不以旧授权执行新实验 | 发现44%与26/48不一致，48计划与43执行摘要存在口径冲突，保留待决 |
| Newell/初始化诊断 | 既有 prototype、init summary与适用边界 | 不新增模型，不重新初始化 | 只作条件可表示性背景，不用插入检查代替动态跟驰 |
| Task7/7.1/7.2 | 无独立视频、许可、PTS/Global_Time与完整源车道覆盖验收 | 不采视频、不人工选案/审核、不读OB | 物理真实性继续 Unknown，不由内部残差替代 |

全来源543/732是继承的正式清单总数。本次分析面是项目固定 Source/Target，覆盖 Task6 **全部752个源/目标事件锚点和724个既有对照锚点**；其余区域正式事件保持原分类/数量，不纳入局部机制比较，不被删除或重标。七个 SUMO 诊断案例另计，分析单元共1483。

## 4. 输入、身份连续性与积分

输入为两个指定 canonical Parquet（1180598/1403095行）、B00 A03/Round2 measured_state（610725/645369行）、Task6保存的 identity_contexts 和 Post-R2 source_segments。四份状态文件 SHA 与既有绑定一致。没有重新调用事件提取器，也没有运行 Task6 的匹配算法。

原 Task6 本地锚点表此前没有独立便携密码学封印；本次记录其SHA，并将锚点数量、唯一性、原 onset gap/closing逐一与 canonical 行及已有公开统计核对。该限制在 `source_bindings.json` 明列，不把新计算SHA当作过去已封存的证明。身份/绝对时间/原event_id的对应关系只在忽略本地输出，不进入便携包。

严格分解要求：

1. 原 onset 唯一；onset前车在相同观测时刻可匹配。
2. [-5,0]含51个原始100ms点；follower与固定onset leader均完整，且原身份、帧、clock和显式连续性标志满足要求。
3. 51个 follower 点均报告同一 onset leader，状态可靠、gap正且速度有限；真实数据还逐点核对两角色 Global_Time、Frame_ID、来源/clock及 leader_frame_id。
4. closing字段与同一固定两角色 `vf−vl`一致。发生更换、不完整或无法匹配者保留整条诊断记录，分解值缺失，不补零。
5. 固定车对同换道只另分类，不给 Formal P2增加同车道条件。本次严格源区子集恰好没有观察到车道变化；这不是人为过滤规则。

积分严格采用相邻原始观测梯形和：

`C = Σ 0.1×(c[i]+c[i+1])/2`；`Cinitial=5c[-5]`；
`Cf=Σ0.1×((vf[i]−vf[-5])+(vf[i+1]−vf[-5]))/2`；`Cl`对leader同样计算并取负。
`Cgap=g[-5]−g[0]`；`R=Cgap−C`。

其中 `C=Cinitial+Cf+Cl` 是代数分解，不是三个可独立干预的因果效应。单位都是m。未通过完整性要求的序列不积分，不插值；未采用差分加速度作为主要证据。

### 4.1 覆盖、重复与缺失

| 窗口/区域 | 正式事件 | 严格事件 | 原对照 | 严格对照 | 原匹配两侧均严格 |
|---|---:|---:|---:|---:|---:|
| 0750 Source |167|105（62.87%）|165|132|94|
| 0805 Source |159|107（67.30%）|149|123|89|
| 0750 Target |174|132|168|154|119|
| 0805 Target |252|206|242|236|201|

源区未严格分解者：0750有52条 follower不完整/中断、10条在完整两角色内更换leader；0805为37、15。分类有优先级，换道/leader变化观察标志另以非互斥列保存，不能把前述类别相加后当作所有转换总数。目标还保留两窗各1条 frame/time不匹配和0805两条 pair质量不一致。正式事件总数完全不变。

全部源区事件分别涉及123/113个后车，严格子集84/86个；全部源区对照为131/115个后车对应165/149行，严格子集108/97个后车对应132/123行。原锚点行无重复，但同车可反复出现：源事件单车最多5/8次，对照最多4/3次。严格事件加权点数5355/5457，去重 follower-time 后4864/4985；对照6732/6273点去重后6274/5702。**点数、事件数、不同后车和不同窗口都不是同一独立单位。** 不池化两窗，不做聚类推断或新 bootstrap。

### 4.2 延长到五秒后的原对照限制

Task6排除的是该后车正式事件区间±3s，原“非风险”是锚点资格，不保证本次整个五秒始终没有风险状态。严格源区对照中，7/132、3/123个样本在锚点之前出现至少一个`0<TTC<2`诊断点，其中6/1个出现在−3s之前；另有短阈值点不等于正式持续事件。严格源区事件自身也有20/105、17/107条在当前onset前出现过阈值点。

这些全部保留，不据此重新筛选事件或设计新对照。`precursor_window_caveats.json`把此限制和目标区对应计数完整列出。五秒曲线是已有事件前置历史，不能一律称从首次安全状态到首次风险的孤立过程。

## 5. WP1：真实源区五秒形成过程

### 5.1 事件与原对照：全部严格样本

以下是**各自严格子集的中位数**，不是相同n的配对估计。

| 指标 |0750事件n105|0750对照n132|0805事件n107|0805对照n123|
|---|---:|---:|---:|---:|
| 初始gap，m |7.604760|9.218676|8.784336|8.531352|
| onset/锚点gap，m |4.703064|9.998964|4.392168|9.720072|
| 初始closing，m/s |0.024384|0.131064|0.024384|0|
| onset/锚点closing，m/s |2.599944|0.082296|2.313432|0.085344|
| Cinitial，m |0.121920|0.655320|0.121920|0|
| Cf，m |−0.478536|−1.973504|−2.470556|0.751637|
| Cl，m |3.482340|0.386486|7.387742|0.266243|
| C，m |2.847746|−0.280492|4.127602|−0.215189|
| leader最大速度回落，m/s |3.230880|2.263140|4.020312|1.188720|

不同变量的中位数不能相加，也不能把中位速度曲线相减/积分来代替逐事件分解。源区事件的**均值**可验证可加性：

- 0750：`0.594215 −1.111587 +3.805368 =3.287997 m`（展示小数有末位舍入）。
- 0805：`0.868395 −2.776668 +6.466339 =4.558066 m`。

前车项可以大于净闭合，因为其他项抵消；不报告“因果贡献百分比”或对接近零/负C强行求比例。前车项是最大正项的事件为45/105、68/107，并非所有事件都由同一项主导。

### 5.2 保持原匹配的比较

仅在原事件及其原控制都完整时计算事件−对照，仍保留未匹配2/10个源事件和其余不完整情况。每个差值先逐对计算，再取分位数；**两个中位数之差不是差值的中位数**。

| 差值指标（事件−原对照的中位数） |0750，n94|0805，n89|
|---|---:|---:|
| 初始gap，m |−1.679448|−0.697992|
| onset gap，m |−4.424172|−4.209288|
| 初始closing，m/s |0.004572|−0.179832|
| onset closing，m/s |1.857756|2.417064|
| Cinitial，m |0.022860|−0.899160|
| Cf，m |0.709346|−1.371448|
| Cl，m |1.140181|4.021836|
| C，m |3.196666|4.053535|
| leader最大速度回落，m/s |0.725424|1.725168|

**Interpretation：** 初始间距提供部分区分，但0805全部严格子集的初始gap中位数甚至稍高于对照，不能推广为每个事件初始都更紧。初始正closing作为唯一解释受到削弱；五秒内速度关系的变化更突出。前车速度下降的积分贡献在两窗均可见、0805更强；后车加速不是所有事件的必要条件。真实后车响应函数、真实扰动生成原因和多车反馈仍未识别。

### 5.3 残差与测量质量

严格源事件 `|R|` 中位数 **0.020117/0.013868m**、p95 **0.056540/0.035921m**；原对照中位数 **0.022174/0.018440m**、p95 **0.063002/0.045827m**。每个样本代数闭合误差约机器浮点量级，详见 `sample_coverage.json`。

这支持严格子集的**内部运动学一致性**，削弱“所有事件均是粗大五秒 gap–speed不一致”的描述。gap和速度可能来自同一提取流程，互相一致不是独立物理真实性；不排除headway、车道、身份误注或少数异常。不能由此估计噪声造成的事件比例，更不能绕过 Task7 门槛。

### 5.4 目标区独立补充

目标严格事件132/206个，初始gap中位11.492484/9.660636m；`Cinitial`中位1.501140/1.303020m，`Cf`为−4.690948/−3.523336m，`Cl`为7.262698/7.903769m，`C`为5.026228/4.813402m。目标结果同样描述前车下降与后车抵消的组合，但不与源事件合并，不把Round2唯一目标事件变成源传播见证。

目标区0750严格事件仍有一例五秒`|R|=2.967990m`，该样本保留；源区的小残差不能推广为所有区域、所有样本都一致。目标区完整残差分位数/最大值见`sample_coverage.json`，没有按残差再筛选正式事件或严格身份子集。

## 6. WP2：七个 SUMO 近阈值案例

沿用 Post-R2 原片段顺序，TTC band=[2,3)s。所有角色都保留原固定身份，图中蓝点是报告的当前leader gap；红色仅在当前leader等于onset固定leader时显示，不连接跨leader间距跳变。closing仅在实际配对时显示；单点也画出并标注支持数，不填成连续曲线。

| 案例 | arm | 片段onset s | onset gap m | onset closing m/s | minTTC s | 固定onset pair的连续前置后缀 | 五秒leader转换 |
|---|---|---:|---:|---:|---:|---:|---|
|1|B00|230.6|14.6904|6.77|2.169926|0s / 1点|有；onset leader换道|
|2|B00|324.2|32.3204|11.45|2.822742|0s / 1点|有；onset leader换道|
|3|B00|334.0|16.8604|5.73|2.498345|5s / 51点|无|
|4|B00|362.4|16.6804|7.73|2.157878|0s / 1点|有；onset leader换道|
|5|Round2|168.3|3.0904|1.04|2.971538|5s / 51点|无|
|6|Round2|235.7|30.1804|11.29|2.673198|0s / 1点|有；onset leader换道|
|7|Round2|311.0|34.3304|11.54|2.831874|1s / 11点|有；onset leader换道|

全五秒固定双车分解只有案例3与5：

|案例|g−5→g0 m|c−5→c0 m/s|Cinitial m|Cf m|Cl m|C m|Cgap m|R m|
|---|---|---|---:|---:|---:|---:|---:|---:|
|3 B00|17.3104→16.8604|−3.29→5.73|−16.4500|16.4025|0.4965|0.4490|0.4500|0.0010|
|5 R2|4.6704→3.0904|0.14→1.04|0.7000|−5.3130|6.1940|1.5810|1.5800|−0.0010|

**Observation：** 案例3的前车先加速、再大幅降速，五秒最大回落10.83m/s，但相对于五秒初值的速度积分项仅0.4965m。最大回落、终点变化、积分贡献是不同量，不能互相替代。案例5的前车下降贡献较大，但后车变化抵消了大部分闭合。切换例可在新leader进入时产生高closing，但相应gap仍约14.7–34.3m。原band全段最小TTC始终≥2，后续原诊断均为band-exit，没有新增正式风险。

**Interpretation：** 不能说SUMO缺少一切前车扰动或一切换道。当前案例显示，扰动的时间位置、初始张开/间距和后车响应抵消共同决定是否进入小gap–高closing结构；这与Task6联合组织差异相容。七例经过“接近阈值”条件选择，不能推断网络扰动总体分布或宣称安全公式已被识别为唯一根因。

## 7. WP3：官方 SUMO 1.26.0 实现机制

直接读取 Eclipse SUMO 官方 `v1_26_0`，annotated tag对象`de3c3f37a2908397bc398a2bfe3b98232252ba8f`解析到 commit **`fa7df22d7f1c4ae245192ecc32410a49f1ffb2a3`**。17个必要源码/头文件和tag元数据保存在本任务忽略目录；逐文件SHA、函数起止行和固定commit URL见 `krauss_source_map.json`。以下结论来自源码，不是只据文档或二手说明。

### 7.1 实际封存配置

实际两份XML逐元素/属性比较：只有五个vType的 `minGap 2.5→1.0`；network与run.sumocfg分别字节相同。

|参数|B00 A03|Round2|
|---|---|---|
|模型 / LC|Krauss / LC2013|相同|
|tau s|0.7389146576529666、1.093342856277335、1.3877275660721775、1.8288599276236361、2.5614676647488244|相同|
|minGap m|2.5|1.0|
|accel / decel / apparentDecel / emergencyDecel m/s²|2.6 / 4.5 / 4.5 / 9.0|相同|
|sigma / actionStepLength / sigmaStep|0.5 / 0.1s / 1.0s|相同|
|internal step / ballistic / FCD cadence|0.05s / true / 0.1s|相同|

NGSIM没有真实tau身份；不能把某个真实ID映射成五档之一，亦不能用观测gap反推tau后声称已知驾驶员参数。历史均一tau1.0/1.6配置不是当前异质B00。

### 7.2 正常动态跟驰调用链与 tau/minGap

关键源码：`MSVehicle.cpp`3124–3201、3236–3318；`MSCFModel_Krauss.cpp`112–126；`MSCFModel.cpp`947–1023、877–942。

1. `MSVehicle::adaptToLeaders`常规同向路径由前车后端位置与后车前端位置构造物理净距，再**扣 follower minGap**。交给followSpeed的gap不是项目报告的原始物理net gap。
2. `adaptToLeader`将该gap、当前ego速度、leader速度以及leader的 `getCurrentApparentDecel()`传给 `Krauss::followSpeed`。
3. `followSpeed`先处理可选driver-state感知误差，再调用 `maximumSafeFollowSpeed`。封存车型未配置driver-state装置，本任务没有凭空加入感知误差。
4. `maximumSafeFollowSpeed`取 `headway=myHeadwayTime=tau`，把可用距离变为 `adjustedGap + brakeGap(vl,max(egoDecel,leaderMaxDecel),0)`，调用安全停车速度计算。ballistic下leader制动距离为`vl²/(2max(...))`（非正速度为0），不是把tau直接当实际反应延迟。
5. 同时应用加速上界及ballistic紧急减速度下界，再进入最终速度协调。

**tau如何进入动态分支：** 设内部步长h=0.05，`G=max(0,adjustedGap+leaderBrakeDistance−NUMERICAL_EPS)`，`v0=max(0,egoSpeed)`，`T=tau`（源码headway为0时用h）。正常动态分支求一个在T时间内施加的安全加速度a，返回`v0+a·h`，不是求一个与当前速度无关的插入速度。

- 若`G≤v0T/2`，采用能在G内停车的制动加速度；G=0时有专门的紧急/停车返回。
- 否则解`v1=−bT/2+sqrt((bT/2)²+b(2G−Tv0))`，`a=(v1−v0)/T`，再返回`v0+ah`。
- 之后还可能触发紧急修正；上述分支式不能单独当完整followSpeed。

`g≈vτ+minGap`只能作特定等速/等制动、无随机扰动与其他约束下的平衡参照，不是全部动态行为的精确公式，更不是所有历史状态的可行性定理。

### 7.3 三种减速度参数

`MSCFModel.cpp`56起构造字段、77–88、947–1075、331–338：

- **decel=4.5**：ego正常制动参数，进入安全停车计算和brakeGap；leader制动距离计算使用`max(ego decel,predMaxDecel)`，源码明确这是避免两车停车轨迹提前相交的保守处理。
- **apparentDecel=4.5**：常规follow链向后车暴露的前车制动能力；它不是实际观测加速度。`MSVehicle.cpp`7873起的 `getCurrentApparentDecel`在本固定版本实际只返回配置apparentDecel，取当前减速度与配置最大值的代码是被注释掉的，不能把注释当运行逻辑。插入/部分LC链显式使用leader模型 `getMaxDecel()`，不能把两条调用链混为一谈；本配置二者数值相同但语义不同。
- **emergencyDecel=9.0**：正常动态所求制动超过decel时，还会进入 `calculateEmergencyDeceleration`及放大/上下界修正；Krauss ballistic返回值再不能低于 `minNextSpeedEmergency`。因此安全速度需求过低时，实际可实现制动下界可能优先，不可将某个子函数输出宣称为绝不可超过的硬历史状态边界。

`maximumSafeFollowSpeed`的emergency修正在非插入、非`gComputeLC`条件下有专门分支；负gap和换道计算另有路径。当前四张100ms状态表不提供完整原生活动分支遥测。

### 7.4 sigma、sigmaStep与动作周期

`MSCFModel_Krauss.cpp`41–60、68–97、129–150；`MSVehicle.cpp`2072–2078、4589–4636：

- `dawdle2`抽U∈[0,1)，从候选速度减去`h·sigma·speed·U`（低速分支）或`h·sigma·accel·U`；ballistic负速度停车指示不被该噪声覆盖。不是对每个观测速度独立叠加高斯噪声。
- 当sigmaStep大于内部步长时，按原生相位条件更新并保存 `accelDawdle`，其间沿用保存的加速度且被当前安全速度范围夹住。`sigmaStep=1s`与`actionStepLength=.1s`是不同机制；确切更新还依赖车辆创建/决策相位。
- 内部0.05s积分，动作步0.1s时重新选择速度范围/调用finalizeSpeed；非动作内部步延续既有加速度。tau不是0.1s动作周期，也不是1s随机更新周期。
- `finalizeSpeed`189–255中，先考虑停车与制动/速度范围，调用 `patchSpeedBeforeLC`，再调用lane-change的 `patchSpeed`，还有startup等处理。随机性不能脱离这些限制单独解释为“真实波动强度”。

### 7.5 LC2013交互与插入约束的区别

`MSLaneChanger.cpp`799–1168：换道安全检查同时评估目标车道前后间距，动作步与内部步不同时用tau remainder和当前加速度外推速度，再调用 `getSecureGap`并乘lane-change safety factor；重叠另行阻断。`MSCFModel::getSecureGap`168–185是后车brakeGap减前车brakeGap的非负部分，换道计算中对已在制动车辆还存在修正。`MSLCM_LC2013::patchSpeed/_patchSpeed`197–428包含协作速度建议。纵向跟驰与横向选择相互约束，不能把LC当作完全独立的外加轨迹。

`MSLane::safeInsertionSpeed`1410–1447扣除minGap后检查空间，调用 `insertionFollowSpeed`；基类354–361明确在ballistic插入时传`egoSpeed=0,onInsertion=true`。安全停车877–899的插入分支解的是插入后恒速headway加后续制动距离，即`−bT+sqrt((bT)²+2bG)`，当前速度在该分支不参与。插入还可被后车安全、速度限制、可用车道等条件阻断。

历史 `stage_0_5_leader_replay.py::insertion_safe_speed`180起使用连续二次式做初始速度筛查/辅助夹取。它不是当前动态followSpeed，亦未完整表达所有原生插入路径；本任务不修改这段历史实现，不用其拒绝比例证明真实交通不物理。

### 7.6 可选精确状态包络：本次未生成

本次完成源码调用链，不生成 `krauss_constraint_diagnostics.json`。理由不是用简式替代，而是100ms封存状态不足以重建0.05s决策相位、保存dawdle加速度、完整native leader/LC建议等整个实际下一步约束上下文。`krauss_constraint_scope.json`记录未计算范围。可识别的子函数公式已说明，不能因此声称已重放实际next-step控制。

即使将来计算固定输入下的精确子函数或五tau反事实包络，NGSIM的tau仍不是已知身份；超过该步安全上界也仅说明当前输入/参数下约束差异，不证明历史上绝不可能，也不证明真实不物理。没有为补齐此可选项扩展工程或运行SUMO。

## 8. WP4：历史结果综合与竞争机制矩阵

324条历史结果指定SHA通过。均一K_tau1.0的Brockfeld均值53.084638%，minGap1为45.777107%，IDM_T1.0为47.561502%；这些是12对分层子样本的条件响应，不是本源区总体风险效应。其lag/amplitude摘要确有变化，仍受选样、初态、差分构造episode和小分母影响。旧48配置组合中主口径和夹取口径不能混合解释动态响应。

### 8.1 发现并保留的历史冲突

- **Documented Intent：** 历史报告§1/3描述48次独立进程、26个插入拒绝并称44%。
- **Actual Implementation：** 机器`replay_summary.json`记录26/48=54.1667%，48 planned、43 reported executed，43个评分组合、23个不同车对。
- **Evidence：** `RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1/replay_summary.json`及原历史报告。
- **Affected Files：** 原报告与原summary；本任务不修改它们。
- **Conflict：** 算术冲突已核实；旧机器执行字段与“48次进程”的口径未由原始ledger重新认证，真实启动总数保留Unknown。旧26条拒绝日志也不被重新包装成新物理真值。
- **Status: Awaiting Researcher Decision。** 该分支不作科研逻辑修正；其余本任务离线诊断继续完成。

Task6已发现的METHOD-EXPANSION旧run_metadata哈希不符和trajectory_coverage_matrix缺件继续保留。只核验实际复用的具名payload，不报告整个旧包通过。

|机制|Observation / Derived|反对证据与限制|Interpretation / 当前判断|
|---|---|---|---|
|H1 初态|原配对初始gap差为负，初始closing差很小/负|未匹配五秒初态；0805全部严格子集初始gap并不更小|gap部分支持；仅初始正closing解释被削弱|
|H2 后车响应|Cf中位为负，0805有78例Cl正而Cf负；历史固定输入仍有spacing误差|无当前异质B00共同物理输入结果；kinematics不是已识别控制器|动态响应差异仍开放；普遍加速致险解释被削弱|
|H3 前车扰动|Cl在真实事件中较大，配对差尤以0805突出|B00也有10.83m/s回落；七例不代表网络分布，初态和响应耦合|重要运动学形成路径获支持；网络输入差异的唯一因果解释仍Unknown|
|H4 多车/换道|部分真实事件有转换，SUMO五个近阈值例也有转换|105/107个固定pair源事件仍存在；缺失不能称无转换|局部关联支持；“全切入”或“SUMO无换道”被削弱|
|H5 测量质量|严格五秒R小且与对照相近|同源提取不独立、headway/lane/极小TTC未物理核验|粗大内部不一致非普遍描述；真实物理质量仍Unknown|
|H6 Krauss约束|官方源码证实tau/制动/缓冲/随机记忆/动作/LC共同作用|minGap单因素网络失败不隔离唯一bound；无active-bound遥测|实现机制Verified；导致源零事件的因果份额Unknown|

机器矩阵分别存有Observation、Derived、Interpretation、Hypothesis、Proposal和反对证据，避免把描述强行提升为科学结论。

## 9. WP5：固定前车实验是否足够有区分力

现有 `FIXED_LEADER_PAIRED_EXPERIMENT_PROPOSAL_20261030.md` 的方向和minGap-only公平配对原则可保留。它能在**输入保真、相同实际初态与合格可观察支持**下检验minGap对条件后车响应的影响；不能单凭两臂选出H1–H6中的唯一根因，也不能恢复网络leader与follower的双向反馈。

**Derived 判别恒等式：** 相同被施加的leader速度轨迹、相同leader初速、相同实际follower初速下，`ΔCinitial=0`、`ΔCl=0`，因此**`ΔC=ΔCf`**；`ΔCgap=ΔCf+ΔR`。这是比仅报gap误差或TTC更直接的条件响应比较。初始匹配必须使用相同**物理净距**，不能用各臂扣minGap后的不同距离冒充相同初态。

### 9.1 最小补充建议（均为Proposed，不是新的执行冻结）

1. 冻结现有五档vType的应用/分配依据。NGSIM的真实tau未观测；不得按结果选type，也不自动追加五档×重复数的新矩阵。其具体映射/反事实解释交研究者决定。
2. 同一leader扰动使用同一锚点、同一可观察horizon比较所有臂/seed。历史`response_metrics`637–694在observed/simulated两边分别对leader位置差分并选择episode，再比较平均lag；这不是已冻结的共同输入lag估计器。
3. 记录原始速度响应、gap、closing、Cinitial/Cf/Cl/Cgap/R及初态读回。lag和amplitude分项报告；不把最小值时差叫真实反应时间。平坦/多极值/窗口边界删失和小振幅分母保留Unknown及理由，不补0。
4. 保留每臂每seed的事件状态、Formal P2及独立D1可评价暴露。单臂插入失败或初态被夹取即缺少公平比较支持，不能通过沉降后再匹配来掩盖。

现有提案已要求最终估计器、边界和输入冻结，因此本次只补齐这些可审查细节，不改seed、不选N、不增加重复次数、不启动实验；原独立物理参考门槛完全保持。

### 9.2 实验判别矩阵

|未来观察结果|支持的解释|不能支持|
|---|---|---|
|两臂在共同合格输入/初态下均再现真实vf、gap、closing与C|这些条件下后车响应可表示；网络输入/初态组织成为更强竞争解释|不能单独证明网络扰动生成是唯一原因，不能认可总体等价|
|两臂均持续错失vf/Cf，minGap-only差小|共同输入下的响应错配不由该minGap对照充分解释|不能独立归因tau、sigma、Krauss公式、动作周期或测量误差|
|minGap1只改善gap，vf/Cf/closing/lag不改善|缓冲/spacing平移的证据|不是动态响应或区域风险真实性修复|
|minGap1同时使vf/Cf/closing更接近参考，批准seed内一致|合格条件下minGap相关的响应差异|不是原Round2确认、源事件恢复或Round3授权|
|只有TTC/P2变化，核心速度响应仍不符|风险几何可以变化|阈值命中不能单独验证机制或仿真|
|输入跟踪、初态、身份/暴露或插入只一臂失败|工程/可表示性缺口，比较支持不足|不得作公平动态响应比较或隐藏剔除|
|案例/指标/type/seed方向不一致|条件异质性或输入判别力不足|不得挑seed或宣布单一根因|

## 10. 文献复核与采用边界

复核Task6完整阅读审查和 `doc/literature-notes/STAGE_0_5_METHOD_EVIDENCE_MAP.md` 的方法与适用条件，未新增论文，也不把既有全文阅读记录谎称本次重新获取全文。

|已有阅读证据|作者方法/条件|AAD已采用|本次未采用/不能推出|
|---|---|---|---|
|Brockfeld2004 L3|36试验场车对、0.1s，记录leader驱动follower、按spacing误差评价/优化|历史重放与按车对报告|不搬优化搜索或12–17%为本项目容差|
|Schrader2024 L4|路侧雷达、单边SUMO中施加leader，分spacing/speed/accel评价与滤波|既有重放、分项gap/speed误差|不把未经验证的差分加速度评分当真值，不新校准|
|FHWA-HRT-21-071/2021 Task6审查|四站点提取误差、轨迹/聚合校准比较，注明NGSIM部分为其综述|检查身份/质量/总体与条件支持|不据二手综述判定AAD事件全是噪声|
|Wang2022 L13|可辨识性依赖模型、输入、初态和误差，非Krauss定理|保留竞争解释与条件判断|不把其模型结论搬成当前Krauss不可辨识性证明|
|Kolekar2020 Task6全文记录|风险场模型七类情景的定性驾驶现象与作者机制解释|检查纵/横向交互上下文|不迁移为NGSIM切入因果比例或新模型选择|

本次核心公式来自研究者指定的运动学恒等式与梯形积分，不需要扩展文献或更换科研变量。官方SUMO源码属于必须的实现依据，已按固定tag直接核验。

## 11. 无法识别的问题与后续建议

**Unknown：** 独立物理真实性；真实tau/感知/驾驶策略；前车扰动在网络中的总体生成机制；不完整源事件的五秒双车贡献；换道的因果份额；实际native哪些安全bound在何时起作用；已封存网络与真实车辆/时钟的精确对应；fixed-leader总体不确定性、N与功效。

**Proposal：** 先完成独立物理参考、文件许可、时间和车道覆盖门槛；随后由研究者审核现有固定前车方向的上述最小判别细节。当前值得检验的具体问题是：在同一可信leader输入和相同实际初态下，现有异质Krauss是否能再现真实follower的速度变化与积分闭合，minGap-only差异体现为缓冲平移还是动态响应变化。此建议不构成新实验授权或科研方向裁决。

物理门槛是下一实验的实际阻断；源码阅读与小R不能解除。历史记录冲突留待研究者，不因完成Task8提升Gate。

## 12. 产物、复现与验证

便携包：`evidence/results/RES-STAGE-0.5-POST-R2-TASK8-KINEMATIC-MECHANISM-DIAG-20261030/`。

- `event_precursor_decomposition.csv`752行、`control_precursor_decomposition.csv`724行；ordinal分析单元、状态与缺失完整保留，非身份/物理抽样密钥。
- `precursor_summary.csv`、`event_control_comparison.csv`、`precursor_profiles.csv`、coverage/overlap/caveats/signs。
- `sumo_near_threshold_profiles.csv`、`sumo_near_threshold_cases.csv`；7例相对时间匿名派生表。
- 官方 `krauss_source_map.json`、`sealed_configuration_audit.json`、未执行精确包络的scope记录。
- 历史复用/文献复核、机制矩阵、固定前车判别矩阵、输入绑定、验证、manifest与SHA。

图像按项目规则仅保存在 `code/outputs/diagnostics/post_r2_task8_20261030/figures/`，不进入Git便携证据：

1. `source_precursors.png`、`target_precursors.png`：逐事件原始100ms数据的中位/IQR，标明严格n/全体n；不连补缺失。
2. `source_closing_contributions.png`：三项带符号贡献的中位/IQR，明确中位数不能相加。
3. `all_sumo_near_threshold.png`：全部七例及实际onset-pair支持数。
4. `representative_original_matched_pairs.png`：两窗各一原匹配事件/对照。按初始gap/closing、Cf/Cl的标准化中位距离最小选择中心例，完整规则与ordinal见`representative_profile_selection.json`；不是物理审核选案，不替代总体曲线。

代码：`code/scripts/analyze_stage_0_5_post_r2_task8_kinematic_mechanism.py`，`code/scripts/package_stage_0_5_post_r2_task8_mechanism.py`；定向测试：`code/tests/test_stage_0_5_post_r2_task8_kinematic_mechanism.py`。生产测量模块和正式config不变。

本机默认Python3.13.5/pandas2.2.3可用但缺Parquet引擎；只在任务忽略目录安装pyarrow25.0.1，没有修改全局环境。复现需提供已有Parquet读取依赖、四个相同SHA状态表和原Task6本地锚点；仅Git检出可检查便携结果/源码映射与manifest，不能凭空重建忽略原始轨迹。

```powershell
$env:PYTHONPATH='D:/shen/TJU/AAD/code/outputs/diagnostics/post_r2_task8_20261030/deps'
python -X utf8 code/scripts/analyze_stage_0_5_post_r2_task8_kinematic_mechanism.py
python -X utf8 code/scripts/package_stage_0_5_post_r2_task8_mechanism.py
```

首次新增与直接依赖定向测试36 passed；补齐锚点与便携导出边界后最终40 passed。独立保存结果复核覆盖1197条完整双车轨迹、7182个积分分项和304个配对汇总字段，最大积分差约1e-12m。输入/产物SHA、docs检查与验证范围见 `validation_record.json`；封存后全局export/verify回执保存在其指向的本地记录，避免循环修改封存哈希。对三份新增Python及本次修改的exporter做语法检查，不执行全量pytest/全仓compileall/全仓SHA审计。所有最初环境/命令失败和修复保留在本地execution_notes及验证记录；历史失败不伪装为首次通过。
