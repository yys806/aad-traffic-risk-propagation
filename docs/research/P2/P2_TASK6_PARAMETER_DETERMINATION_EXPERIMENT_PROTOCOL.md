# P2 Task6 — 参数确定实验协议

协议版本：AAD-P2-PARAM-20261102-v1.0。日期：2026-11-02。状态：DESIGN_COMPLETE / EXECUTION_PENDING_RESEARCHER_CHOICES_AND_AUTHORIZATION。本协议服务下一项 **P2 Parameter Determination Experiment**，不是 Formal Protocol Lock，不授权 Stage 1.1。本次实际新运行数为0。

唯一科研定义：[统一入口](../definitions/README.md)，版本 AAD-SCI-DEF-20261102-P2T6-v0.4。[参数登记/SAC/十三字段/依赖矩阵](../definitions/PARAMETER_AND_CALIBRATION_REGISTER.md)是定义事实源；本文复述执行契约并引用该版本，不另立定义。一次性科学选择见[集中决策](P2_TASK6_RESEARCHER_DECISIONS.md)T6-R1–R6。所有数值推荐均为Proposal，未自动接受。

## 1. 目的、假设及范围

目的：为三个不同测量对象找到同时满足预定误报、有效检出、延迟和Unknown标准的稳定参数区域，明确交通/观测支持域；不证明AAD核心因果假设，也不以TR<TP选参。

- Micro：指定有限机制内真实实体、leader/follower逐跳响应及到区证据，沿用W1–W9和Potential/Observed/Qualified。
- Macro：同向分lane、固定区域/过去时空支持的q/k/u状态，不等最早微小物理影响。
- Cohort：固定名单/区域/观察窗的baseline-relative signed speed decline；非cohort区域车辆可能先响应。

优先SUMO模型内和显式合成真值校准，A/B/生成器分别报告。直接target状态注入是sensor-positive，只验证状态测量，不证明source→target传播。Formal A=0、独立Qualified=0、F0和总体TR/TP Unknown保持。

## 2. 下一实验一次性启动表

下一参数实验第一步将T6-R1–R6已接受内容写入校准专用run manifest，然后按本协议生成具体候选；**不增加新的设计任务**。

| 必填项 | 已有执行规则 | 未决影响 |
|---|---|---|
| 测量域/真值 | 固定region/lane/cohort/window、机制、a*/b*/真值误差及逐层标签 | 对应层校准前接受；缺标签可做算子验证，不能冻结该层性能 |
| SAC/验证 | p_F*、s*、u*、f_A*、d*、β_V、power、n/cap | 选择和验证前必需；科学损失由研究者决定 |
| 参考配置 | §6确定性生成网格/参考，成熟候选提取固定版本 | 下一实验内部生成，不需要再设计 |
| 正式δ/H*/η/α | §12–13沿P1，不用风险曲线反选 | 正式早窗前冻结；不评价风险的测量校准不因δ未知而阻塞 |
| 四格支持 | 共同源前机会/无源和非Q政策/实际分配 | 不阻塞测量校准或合格两臂，阻止无支持的四格识别声明 |
| 授权与资源 | 白名单、seed/dependency、split、n/cap、磁盘安全余量 | 本次无新运行授权；下一实验接受后直接执行，不改变Gate |

## 3. 历史数据能力审计与复用

只读明确非locked白名单；计数与哈希见[设计证据](../../../evidence/research/P2_TASK6_20261102/design_evidence.json)。

| 既有数据 | 可以支持 | 不可以支持 / 标签局限 | 下一实验复用 |
|---|---|---|---|
| Task3 V2：code/outputs/calibration/p2_task3_20261102_v2/ | 768面板、42候选、32,256评价；持续/缺口/趋势/状态机正确性、生成器内注入延迟 | 不是交通null FPR、真实Micro/Macro标签或交通灵敏度；42评价非42次重复 | 原validation已看过，下一轮只算历史开发证据，不重跑V2 |
| Task3 B：code/outputs/calibration/p2_task3_sumo_b_20261102/ | 60run、2,520评价；源执行/原始leader/lane/gap、区域中间响应；12个no-command run可作窄域背景描述 | 无预定cohort阳性，不能估灵敏度/延迟；命令组非自动target-null，不是F0 | 只复用；可检查Macro裁切和局部Micro候选，不冻结全域性能 |
| Task9经Task18修复/Task19分析 | Primary60+Supplementary40，同100条轨迹；native Follower动态、身份/gap/phase和真实局部响应 | 不是三批独立样本；共享候选输入/seed/参数；描述性最小滞后Unknown；无全区域/独立最早onset/完整链真值 | 以T18/19原路径/hash作局部检查，不重跑，不升级Formal A |
| 已审计NGSIM | 源事件定义/字段质量和条件性局部交通背景 | 源阳性非target arrival阳性；独立映射缺失则非Qualified | 仅合法已解封明确窗口，不扫描未知/locked目录 |
| pNEUMA/SPMD等 | 各自速度/区域或接收状态的既有有限描述 | 不恢复不存在的leader；接收非采用/动作；跨事件不拼witness | 非必要不新增下载，满足支持/合法性才纳入 |
| V1/Locked | V1只留失败历史 | V1数值已撤回；locked禁止读；TTC2s/持续.2s/gap.11s不是arrival参数 | 不进入校准/验证 |

B跨条件复用seed，60记录不自动跨条件iid；每split/no-command仅6seed。历史Wilson界保持原口径，不与本协议单侧exact示例混称。同源Task9/18/19不得重复计n。中间车响应不能替代独立目标Physical Arrival标签。

## 4. 正负标签、盲法及时间真值

### 4.1 标签先于检测器

每预列单位保存truth_version、layer、state_truth=positive/negative/unknown、source_attribution=specified/other/none/unknown、onset_allowed_set、恢复区间、label_source/hash、审查机制、a*/b*/误差和适用域。先冻结标签及hash，再计算候选；标注不看candidate/报警/风险效应。

真值可来自具有独立状态方程和已知响应时刻的构造数据，或独立高频全状态、实际控制/关系审计的受控模型记录，或带不确定性/争议的独立观测标签。**不能用待校准θ/h/q/coverage、同一change-point输出或计划命令时刻定标签。** 同seed对照不自动是真值。

Macro/Cohort以独立干净/高频状态轨迹和预定有限物理信号a*,b*标注；a*、b*不是算法θ/h。Micro还需真实身份、leader关系、独立源/响应区间和竞争解释；构造图fixture仅证连接逻辑。缺独立onset界则该层延迟Unknown，不补时间。自然交通因果归属不由模拟金标准保证。

### 4.2 Null与归属负对照

- N0无指定源背景：只有独立标签表明目标层没有指定状态变化才是state-null。无源但自然拥堵/减速可为any-source state-positive、specified-source attribution-negative；不能把正确状态报警记成误报。
- N1有源但独立真值表明在预定层/区域/时域未到达指定状态；与N0分别估FPR，不能以未Qualified或detector没报生成标签。N1不等排除任意小物理影响。
- A0竞争源/信号/换道/边界引起真状态变化：用于指定源错误归属；状态检出正确和指定源归属错误可以同时发生。

Micro阴性需完整机制/身份/时序覆盖；缺链且覆盖不足为Unknown。

### 4.3 Positive与失败

各层positive有独立onset区间、固定域和实际状态变化。受控SUMO传播阳性须有native目标响应、无target速度setter及来源审计；source命令执行不等到达。直接target状态fixture只验证sensor，不作自然传播阳性。模拟A/B域保持分离，不验证现实迁移。

无目标阳性的运行保留planned cell、原assignment和失败，不降θ、不移动cohort/region、不挑seed补成功。校准truth-positive条件性能与正式因果ITT是不同对象；正式ITT不按truth/Witness/采用成功筛样。报告planned→实际positive/negative/Unknown转化。

## 5. 最小充分实验矩阵

下表都是下一实验的Proposal，本次新运行0。优先同一raw离线重算参数，不为每个θ新启SUMO。比较内道路、vType、边界、源/对象域/控制条件固定，校准配置与正式配置隔离。

| 阶段 | 因素/水平和数据 | 控制/对照 | 独立重复与资源 | 输出/统计与停止 |
|---|---|---|---|---|
| 0 能力/可行域 | §3白名单、truth/pre/clock/区域支持 | 版本/hash，旧validation只历史 | 0新run | 标签inventory、SAC/可行域，缺标签仅对应项Unknown |
| 1 Null calibration C-N | N0/N1；预设需求低/中/高，基础需求×{.5,1,1.5}仅安全可行批准后；实际pre-Edie k另记 | 同道路/lane/vType/pre域；自然趋势保留 | 探索规划24新独立seed/格，2×3×24=144 | 两类event/window FPR、Unknown；非法条件停止，不混null |
| 1 Positive C-P | 四点(a*,b*),(2a*,b*),(a*,2b*),(2a*,2b*)，另局部非cohort响应点；三密度 | a*,b*独立truth域；命令目标非实际标签；局部点Cohort可阴性 | 5×3×24=360计划单位，多层同raw不重复计n | recall/miss/timely/延迟；无真阳性停止该项，不降阈 |
| 1 Attribution C-A | 竞争/非指定源A0，三密度 | specified与any-source分列 | 3×24=72；有适当标签可复用C-N/P，不增加n | FAR、Unknown；无真值不作准确率声明 |
| 2 Single-parameter | §6每参数低中高/类别2级，其他参考固定 | 同raw/truth/mask/聚合器 | 复用C≤576计划单位；候选非独立run | 参数曲线/代价/CI，单因素不排除交互 |
| 3 Interaction | 参数表11类依赖，连续低高四角+中心，类别2级 | 同run重复测量，主域不改 | 复用C；不足按§8在预列calibration总cap内新独立块，不能借V补样 | 交互差分和稳定区域，不做全参数笛卡尔积 |
| 3 Robustness | 三密度；采样{Δ,2Δ,4Δ}；缺失{0,5%,20%}及MCAR/块/MNAR；噪声{0,r_u,2r_u}；lane/leader/ID变化 | 完整truth为基准，mask流固定 | 原始独立run上派生；逐stress加missing×identity、Δx×Δt、density×θ四角 | 分层性能/适用域；多个mask不是新n |
| 4 Independent V | 冻结主向量及预列邻域，N0/N1/P/A与预定分层 | 新seed族；代码/候选/真值规则先hash | §8求n_V；跨场景主张需新场景块；不能复用已见V | 一次揭盲、§9–10联合验收；失败保留不回调伪独立 |
| 5 Freeze | 仅V通过的有限域参数 | 邻域稳定、所有损失约束 | 不为变绿自动加run | 推荐区间、证据/交互/适用不适用/Unknown；不自动Agreed |

576是探索资源规划示例，**不是充分功效n或交通经验**。各层实际positive/negative及独立n分别计；第五点与A0有不同层标签。正例设计点是目标truth范围，若实际SUMO未实现目标，只按独立真值分级保留，不强行算阳性。cap和场景实现进入启动一次选择，不能事后按成功补seed。未覆盖复杂机制可列不适用，不拖延全部交付。

## 6. 参考配置、单因素与关键交互

1. 接受科学损失、truth域、误差尺度后，用calibration处理前支持计算B_pre、原始Δ、缺口分位数与独立r_u；按统一参数表生成有限网格，去重并拒绝无法满足采样/持续/随访预算者。无r_u/d*/truth不填0。窗口网格从可用pre跨度生成，不把旧2/5/10s当经验。
2. 推荐Cohort full-N等车signed mean为主，median/比例辅助；constant baseline只在pre块外稳定性支持时使用，另比较仅pre拟合linear。均不支持则baseline域Unknown，不能post-source去趋势。Macro同域速度下降主候选、q/k补充；Micro候选提取固定成熟版本，不同时任意换算法/路径规则追报警。具体科学选择T6-R1接受。
3. 连续参数参考为可行网格中位序位；q取原始名义步长可支持的最严格值、c=1、hysteresis off、显式阴性重置。这是可复算的条件参考，不是最优或交通推荐。缺full-N时做missing bounds/Unknown，不用observed均值冒充。
4. 顺序W→baseline model→θ→h→q→coverage→recovery/hysteresis，再对应Macro/Micro参数；一次变一项，存同run差分。原始准备取W最大所需pre支持，不让不同W偷偷换样本。
5. 依统一依赖矩阵做各对2×2+必要中心，共享中心、不做全参数积；reaction×clock的范围来自独立truth，不制造正反应delay。包括W×model、θ×h、h×q、coverage×missing、recovery×hysteresis、w_M×θ_M、Δx×Δt、density×θ、reaction×clock、identity×missing及解析H*×η×α×n。
6. 对性能M，D_i=M_i(++)−M_i(+-)−M_i(-+)+M_i(--)。二元/比例时D_i∈[−2,2]，在独立run/block上求均值/CI/预定γ_int。Unknown用区间。不能只筛四配置共同成功者比较延迟；用及时有效检出或预定有界惩罚损失，说明不同对象。
7. 选同时满足损失的稳定区域；预列邻域性能差异区间须不超过ε_stab，而不是“交互不显著”。简单、可复算、少缺口假设可作同等性能决胜规则；最早报警/最晚arrival/显著risk不能选参。无可行区域如实报告。

## 6.1 具体候选生成与层内控制（下一实验内执行）

| 因素 | 有限候选与参考规则 | 固定控制 |
|---|---|---|
| W/model | W∈{B_pre/4,B_pre/2,3B_pre/4}的可行值；constant/仅pre拟合linear | 同一最大pre原始支持；只用cal-pre块外预测选模型 |
| θ_P/θ_M | max(r_u,Q_.90/.95/.99(cal-null固定域最大残差))；另列a*/4,a*/2,a*，正值去重 | Cohort/Macro各自null、单位/算子；阈值不定义truth；稀少tail量只探索，不能称已校准1%FPR |
| h_P/h_M | {max(2Δ,d*/4),max(2Δ,d*/2),d*}中可行值 | 用实际末−首跨度，不加一帧；预算小于采样/持续下限则不可行 |
| q_P | {Δ,g_50,g_90}中≥Δ值；严格可支持参考 | gap-bridged单标；放宽不能冒称连续观测 |
| c_P/missing | {1,1−m,1−2m}∩(0,1]；m为预置0/.05/.20 | 固定N、同mask/identity/退出，MNAR不靠gate修复 |
| recovery/hysteresis | 阴性重置；退出持续{0,h_ref}；hysteresis off或θ_exit=θ_enter−r_u可行者 | entering规则固定，先报首次onset，再报复发/状态寿命 |
| Macro空间/时间 | 固定主域长L；内部Δx∈{L/4,L/2,L}，Δt∈{Δ,2Δ,4Δ}，w_M∈{d*/4,d*/2,d*}中≥2Δ者 | 同lane/同向/同总域，禁止为更晚arrival改主region |
| Micro响应/反应窗/质量 | 固定成熟提取版本；响应强度由独立null/a*标签探索；宽窄反应窗只由独立反应间隔支持；clock/gap误差来自审计 | W1–W9不放宽，leader/ID切换分段；无反应truth则该数值Unknown |

连续参考取候选序位中点；类别constant、阴性重置、hysteresis off；q严格、c=1。所有候选及被拒原因在揭盲V前固定，不用B的0.02级波动、V1值、Formal源参数或作者经验阈值充默认。数学域/本探索网格/交通经验范围仍分开，后者Unknown。

若正式H*未定，校准先独立固定监测H_cal和绝对d*，不把H_cal自动当正式H*；准备至少B_pre最大支持及源后H_cal+d*观察，确认/availability已含持续与look-ahead，不能遗漏末端待确认。真onset无法界定时延迟Unknown。

物理测量校准通信固定关闭（或fixture不适用），native follower/Observer只读不控制目标；source控制/直接target sensor fixture分别标识。所有新交通场景及源强度须在下一实验批准的安全域内；本任务不生成配置。原始输入、模型、warmup、车辆特征、需求、源作用时刻/位置与层对象在参数比较内固定。

Macro执行：每lane R_l×(t−w_M,t]裁切实际轨迹片段，D=Σ域内车距、V=Σ域内车时、A=L_lw_M，q=D/A、k=V/A、u=D/V仅V>0。部分进入/退出/换道按域内部分计；不跨长缺口，不双计边界；lane/边界/插值误差存原段及界。V=0时u undefined，未知抽样p_i仅observed traffic，lane不简单相加冒充总量。窗口crossing/真onset/确认分别报告。

事件匹配先固定：每层每预列truth事件至多匹配一个首有效检出，onset允许集合须与独立truth及实证误差支持相容，confirmation/availability须在预定有效信号/随访支持内；早于可行truth区间或恢复后报警单列false/late，不因最后终于报出而计有效。多truth事件按预定ID和时间非贪心选择最有利者；主版优先每run一个index机会。源前报警在positive运行也单独报告。


## 7. 独立单位、seed与split

依赖键至少scenario_family/traffic_realization/exogenous_stream/input_trace/run-block；同seed跨条件保守同block，共同输入不支持新场景总体外推。detector/车辆/帧/窗口/mask非n；独立seed也不自动证明代表性。

新cal_root与val_root用独立命名空间及SeedSequence或等效审计映射生成显式manifest；具体整数下一实验启动冻结，不复用旧202611020/202711020集合。保存派生seed、运行顺序和共享流，失败仍占原记录。

按完整场景/连续轨迹/同源输入/最大依赖block先split，不拆帧/相邻窗。Calibration内可block交叉验证但不是外部V。两条历史输入仅条件性支持，不叫新交通总体验证。

既有Locked holdout不读取、不枚举内容、不参与选择。下一新授权数据可预先封存独立holdout清单，本协议不要求打开；已看V不能改名holdout。新V只用一次；失败重调则记录已消耗V、协议变更和另预列新V/预算，不能循环至通过。

## 8. 独立样本量、精度与功效

### 8.1 精确二项条件

独立单位须来自声明的同质层/预定混合抽样且标签误差已处理。每run一个盲预列index机会；多事件先按“至少一次错误”的run指标或固定run比例统计，不套事件数二项CI。固定有限总体无放回用设计相容/超几何界。密度分层按共同预定权重，各层n/CI分别报；若要求各层均达标，family和样本量按层展开。未知簇依赖不能直接用iid公式。

坏数x/n的单侧Clopper–Pearson上界U=Beta^{-1}(1−β_c;x+1,n−x)，x=n时1；检出y/n下界L=Beta^{-1}(β_c;y,n−y+1)，y=0时0。β_c=β_V/J_V，揭盲前列完整family，n=0则Unknown。

零坏例：U=1−β_c^(1/n)，U≤p*需n≥ceil(logβ_c/log(1−p*))；全部检出：L=β_c^(1/n)，L≥s*需n≥ceil(logβ_c/log s*)。单项β_c=.05时，FPR上界1%最少299个独立null，5%需59；s*=95%需59个全成功positive，90%需29。这些是最有利观测下的可行n，**不是90%验收功效n**。Unknown/失败/family会增n。

给good坏率p_good<p*，c_n=max{x:BinomCDF(x;n,p*)≤β_c}，选最小n使BinomCDF(c_n;n,p_good)≥1−β_pow。Sensitivity以miss同理。可审核规划假设：good FPR=.2%对1%标准、good miss=1%对5%标准、power=.90，均不是已观测性能。精确计算见design_evidence.json及可复算脚本。不得用大量帧/条件池化代替n；n超过cap时报告资源/标准冲突。

以下为已计算规划例，非实验结果；n指对应同质独立标签层，不能跨null/密度/层随意池化。

| 总验证失败预算 / 族J | 坏率标准 / good规划值 | 单项目标power | 最小n / 允许坏数 / 实际power |
|---|---|---|---|
| .05 / 1 | FPR≤.01 / true .002 | .90 | 773 / 3 / .92864 |
| .05 / 1 | miss≤.05 / true .01 | .90 | 153 / 3 / .93149 |
| .05 / 15 | FPR≤.01 / true .002 | .90 | 1470 / 5 / .92221 |
| .05 / 15 | miss≤.05 / true .01 | .90 | 290 / 5 / .92682 |
| .005 / 15 | FPR≤.01 / true .002 | .90 | 2118 / 7 / .93375 |
| .005 / 15 | miss≤.05 / true .01 | .90 | 386 / 6 / .90444 |

上述是单项power，不保证整个family同时通过power=.90。整体90%可预分β_pow,c≤.1/J_accept，逐项求n取各标签层最严者，或用经验证的真实联合设计功效；不能假设指标独立相乘。脚本另给保守整体验收规划，V最终n/cap和精度/延迟一并冻结。

### 8.2 延迟和Unknown

主验收以“真阳性在d*内有效且可用检出”为Bernoulli成功，miss/Unknown为失败，用exact下界；不只报成功者平均。真onset=[L,U]时延迟∈[t_available−U,t_available−L]，成功须保守上端≤d*，跨界不计成功。另存first-positive、confirmation、availability三个延迟、onset定位误差、中位/P90/P95及区间。

分位数CI用二项秩/设计相容簇法，删失不机械填∞算普通均值。验证n同时满足及时检出、u*、f_A*与各null精度，取最严者；各层标签不同不能宣称共用一个充分n。

面向η早窗的可行性必须额外检查：detected early mass + Unknown可能早到质量 + 统计上带余量 + m_delay < η。故95%灵敏度/5%Unknown证书不能支持η=1%，即便单项测量标准通过。推荐预分m_delay≤η/4、Unknown≤η/4（η=1%时timely sensitivity≥99.75%、Unknown≤.25%），另给detected mass/抽样保留严格余量；这都是待研究者接受的损失方案。脚本提供.25%和.5%坏率的可行n及.25%坏率/true .05%规划的power。达不到时只报告有限测量推荐/真实到达Unknown，不能反调η。

### 8.3 交互精度/功效

独立block的D_i∈[−2,2]，K_int个对比双侧同时半径4√[log(2K_int/β_int)/(2n)]。半径≤ε_int的充分条件n≥ceil[8log(2K_int/β_int)/ε_int²]。若要检测|ED|≥γ_int且power≥1−β_pow，须再给随机均值偏差余量或用设计相容且经覆盖验证的模型；不能把精度公式称功效，不能写“n=24足够识别交互”。n不足如实宽CI/交互未排除。

### 8.4 后续正式风险功效（本次不运行）

实际Y范围R=B_R−A_R、两臂平衡n、族J_R和最小备择τ_alt=−δ−g（g>0）下，置信带与测量宽度消耗g。无额外测量宽度的保守充分界为

\[
n>\frac{2R^2}{g^2}\left[\sqrt{\log(4J_R/\alpha_R)}+\sqrt{\log(2J_R/\beta_{pow})}\right]^2.
\]

n取右侧实数的floor+1以保证严格不等号。有测量宽度先扣g的可证最坏部分；余量≤0则不可行。更有效的设计相容功效可用新授权校准方差，但不读locked、不反调δ。当前g/方差/最终聚合Unknown，不报伪正式n。

## 9. 评价指标和明确分母

每项含layer/domain/truth/detector版本、密度/缺失层、独立n、planned attempts、label-Unknown和CI方法；不只报accuracy。

| 指标 | 分母与计数 | CI/适用限制 |
|---|---|---|
| Event FPR，N0/N1分列 | 每独立真state-null机会固定监测域至少一次错误状态报警 | exact或设计界；无法判断给[FP,FP+Unknown]，上端坏数验收 |
| Window FPR | 预定不随结果移动的真null窗中报警 | 重叠窗非独立；每run错误窗比例，再按run/簇界，不按窗数算n |
| Sensitivity/Recall | 全独立truth-positive中正确匹配有效检出 | Unknown不成功；exact/簇下界；说明a*/b*范围 |
| Miss rate | 同positive分母内未有效检出，含Unknown | 与recall同分母才互补；known miss/Unknown另分 |
| Detection delay | 全positive中first-positive/确认/可用减真onset区间 | 条件分布同时报及时有效检出概率、失败、删失、Unknown |
| Valid detection rate | 全truth-positive中满足身份/支持/顺序/质量/匹配的检出 | 另报报警中有效比例（precision-like），不混名/分母 |
| Unknown rate | 全预列attempts/assignment，含失败，不只成功run | label-Unknown与detector-Unknown分原因；run级exact/簇界 |
| Coverage | Cohort ΣM/N；Macro空间时间、D/V支持及p_i；Micro边/身份支持 | 固定域/N，不等η，不修复MNAR |
| False attribution | 全已知非指定源/竞争源机会错误归属指定源 | 独立标签，Unknown坏数上界；any-source Macro可预列N/A，不填0 |
| 分层/交互稳定性 | 预设密度/缺失/噪声/lane、同run参数对比 | 同时family或明确描述CI，不选择最佳层外推 |

V主family列每层两类FPR、timely valid recall、Unknown和source-specific需要时FAR；每个验收域/层/密度/候选/邻域的额外检验进入J_V。N/A仅用于预先无该归属定义的对象，不把缺证变0。只验预定加权混合总体不能声称每密度均达标。

## 10. 选择、稳定区域和冻结

C上先满足truth/质量/支持，再约束FPR/timely recall/Unknown/FAR，保留Pareto可行邻域。不得看risk/TR/TP或V选参。性能相当时选简单可审计/少桥接者，非只选最快报警。

V中适用的每预列层：坏率上界≤标准、及时有效检出下界≥标准、Unknown/FAR上界达标；邻域差异区间符合ε_stab，交互区间排除预定重要不稳定γ_int。**不显著不等稳定/等效**。n/标签不足Unknown；可评估但不满足标准Not established。

只有独立V通过者可标Recommended-for-freeze，研究者接受后才Agreed。输出每参数值/范围、raw/hash、性能CI/n、交互/敏感性、适用/不适用及Unknown。别层通过不填补本层漏检证书。

## 11. 两臂和四格因果接线

测量校准不改变四格矩阵。信息链source→生成资格→实际generation→send→delivery→validation→adoption→实际action→区域risk逐段记录；物理链另行测量，时间先后不自动识别中介。

两臂顺序：Z_S=1源过程→communication-blind确认/Qpre→随机Z_C→消息/动作/结果。Qpre无通信提前暴露，仅用Z_C前规则，绝不使用未来送达/验证/采用/动作/Witness。τ_Q(t)=E[Y(1,t)−Y(0,t)|Z_S=1,Qpre=1]；F0,ℓ^Q同资格、H权重、region/time/layer版本。全部原assignment ITT，链路失败/拒绝不移无消息臂，缺失保留界；确认前已到达仍保留。

四格τ_SC=(μ11−μ10)−(μ01−μ00)需要共同源前总体、四格完整政策、实际可辩护ZS/ZC随机分配及正概率、一致结果/干扰支持。Qpre对ZC是前变量，对ZS可能是后变量；Q(1)是有源时潜在资格，ZS=0看不到其成员。principal-stratum可定义不等可识别；即使Q(0)=0也不显示Q(1)。非Q不随机ZC则τ_nonQ不可估。

同源前总体/权重下τ_SC=pτ_Q+(1−p)τ_nonQ−τ_S0是代数恒等式，非识别证明；缺项不补0、不用同seed补反事实。外推全部有源需非Q支持/已接受运输条件。源前共同opportunity（路段/时段/预列车辆或场景）是不同资格对象，须研究者接受，不冒称现有Qpre。

formal_design.py只核四格配置差异、生命周期和共享前缀，不证明随机/positivity。无源政策没有source message可为动态policy的零发送事实；通信assignment效应为零仍需完整policy等价/设计证据，不自动填0。

分析顺序：资格/随机分配/干扰审计→合格两臂ITT与匹配F0→生命周期失败描述→分层总体早窗；四格支持通过后另报，principal-stratum/全source外推非默认。每簇随机单位、partial interference/污染、正概率及实际独立n须有记录；只有配对模型情景时只称模型对比。

## 12. 时间集合、CDF识别界和Risk同时带

记录native/reference time、clock ID/单位、step index/phase、observation/availability、offset校正、drift及误差来源。共同误差抵消须有证据，不默认独立平方和。source actual onset=[L_S,U_S]与confirmation/计划时间分开；推荐t_E=onset允许区间，具体T6-R1接受，Formal P2确认规则不改。

逐层S_iℓ可为区间并集且含∞：exact仅有真值依据；left(−∞,U]；interval(L,U]外扩clock；right(C,∞]仅在所有此前可能合格onset可排除；Unknown为全允许域。长缺口中发生后恢复、末端待确认或无Qualified但覆盖不足均不当right-censored。相对时间至少覆盖[L_A−U_S,U_A−L_S]，risk对所有允许source/clock映射取包络。

Macro同时存[t−w_M,t]支持、算子crossing、raw-response候选、首次阳性、确认和可用。算子crossing不是真最早物理onset；不减w_M伪校正，无独立延迟证书就保留更宽时间集合。

\[
a_{i\ell}(t)=1\{\mathcal S_{i\ell}\subseteq(-\infty,t]\},\quad
b_{i\ell}(t)=1\{\mathcal S_{i\ell}\cap(-\infty,t]\ne\varnothing\}.
\]

集合覆盖真onset时a≤1{T≤t}≤b；样本识别界[mean a,mean b]，Unknown贡献[0,1]，不删/不设∞。不要求删失独立；抽样不确定性另算。

独立代表性有界单位，或固定资格有限总体SRS无放回时，K_P个预定endpoint×time×层上界取ε_P=√[log(K_P/α_P)/(2n0)]、U0ℓ=min(1,mean b+ε_P)。双侧同时界把K_P换2K_P。n0=0/无支持Unknown。时间相关不阻止union，未知run/簇依赖则不能套iid；分层用共同预定权重合成界，n不池化。不同概率/网络分配用设计相容界。

若S只覆盖detector-defined时间，不能叫真实物理F0。独立同域验证若证明P(真到达而无d*内有效检出)≤m_delay，带明确失败预算，可保守桥接F_true(t)≤F_det,available(t+d*)+m_delay，再加抽样/测量误差截到1；需随访至H*+d*。Unknown仍在b，漏检质量不得漏计。条件性灵敏度非逐例无误差，也不能未验证跨B/A或现实迁移。无桥接只给detector-defined对象，真实到达Unknown。

风险保持P1固定窗口积分/固定cohort等权：formal_risk_measurement.py的rho=exp(−TTC/τ)，contribution_bounds和integrate_fixed_window给[0,1]贡献/均值和[0,L_Y]定长积分。故既有固定L_Y主候选范围为[0,L_Y]，已批准时间均值为[0,1]；前后差/四格差按实际线性变换另推范围。不能任意截断DRAC或另定义风险以满足有界条件。

全部assignment按原臂；每单位测量包络[Y_i^L,Y_i^U]。n_z为真正独立臂单位，J_R列全部预定时点×risk endpoint×region×层。双侧同时带：

\[
e_z=(B_R-A_R)\sqrt{\frac{\log(4J_R/\alpha_R)}{2n_z}},\quad
L_R=\overline Y_1^L-\overline Y_0^U-e_1-e_0,\quad
U_R=\overline Y_1^U-\overline Y_0^L+e_1+e_0.
\]

4J_R覆盖两臂两方向；只声称上带时可用2J_R，不能把pointwise CI当simultaneous band。依赖独立抽样/每臂SRS有限总体或适用设计界；多层权重/总体明示。无可信范围/设计不硬算。cluster max-t/设计相容bootstrap需独立簇、矩条件、实际分配重采样和独立覆盖审核，不是无条件exact；Fisher sharp-null不能直接替代异质ATE/SESOI带。KM/Turnbull仅相应right/inspection机制成立时作效率方案，不修复信息性Unknown。

## 13. 联合预算与最终总体早窗判定

α_R+α_P+α_clock+α_measure≤α。R是risk同时统计，P是物理CDF同时抽样，clock是估计钟界失败，measure是真值/测量包络/漏检证书联合失败。实证确定性包络不机械耗概率；估计界写失败概率和验证域。β_V=.05的性能证书不能当α_measure=.005的正式保证，须相应n/family或已接受预算；不重复使用同一概率保证却漏控其族。

H*、网格和持续规则先固定：risk的U_R在预列连续网格段均<−δ且段确认结束≤H*；同资格无消息每预定层潜在物理U0ℓ(H*)<η；clock/measurement及延迟桥接均纳入。各层分别给有限scope结论，不创跨层OR/AND标量。多早窗预先扩family/同时界，不看曲线选H*。

- Supported：该层有限scope的识别、质量、同时统计和SAC全部满足，只支持总体early-window。
- Not established：可评估但CI/持续/到达/损失条件未达标，不自动否定假设。
- Unknown：关键资格/positivity/truth/clock/覆盖/风险范围或漏检界不足，无法判断所声称对象。

允许不同层结论不同；不以缺Witness认定无到达，不给某处理事件跨世界提前秒数。

## 14. 停止与失败保留

硬停止：未授权数据/holdout访问，Formal定义或正式配置漂移，身份/clock/truth断裂，无法确认磁盘安全余量，危险/碰撞/teleport超批准场景，版本/分配/hash漂移。保留失败、原assignment及有效观察，不能删run/重分配。

证据停止：没有独立阳性/可靠null，cap内达不到精度/power，Unknown令arrival上界必然≥η，或无稳定可行参数。该层Unknown/Not established，不降科学标准/θ，不追加seed/移动区域追阳性，不增加前置设计任务。低影响细节不阻塞其余可执行校准。

固定n后统一V分析；可做预定工程安全检查，但不逐次窥视直到通过。主要对象/标准/矩阵变化回集中决定，保留旧版本/原因。

## 15. 可复现、资源和最小数据契约

运行前存Git SHA与dirty diff标识、协议/run manifest SHA、解释器/依赖/SUMO/TraCI与二进制来源、平台、独立单位/seed/split/采样机制、输入/truth SHA、网格/参考/SAC/family/n/cap。大型实验前记录空闲盘、预计raw/临时需求及系统安全余量。Windows默认；另获WSL授权时仅指定/home/shen/AAD，记录环境，不复制全数据集。

新校准输出code/outputs/calibration/<approved_run_id>/，不覆盖Task3/正式结果。raw、控制/Observer/消息、truth、detector分开存。便携只小表/config/audit/manifest/provenance/SHA，不含原始大表、日志、密封键、HTML/PDF/图片。

单位表最低字段：planned_unit_id/dependency_block/scenario/domain/split/assignment及概率或N/A/source_type/Qpre及时间/lane-region-cohort版本/truth及允许时间集合/完整detector向量/每层状态-onset-confirmation-availability/coverage-clock-missing_reason/逐项质量门/输出-hash-退出。消息生命周期不得合并成一个success。

时间表分别记录：planned perturbation、actual source physical onset、first positive observation、confirmation、message eligibility、generation、sending、delivery、validation、adoption、actual action onset、risk onset（总体统计对象）、各层physical onset/confirmation、observation/availability；未知存Unknown+原因，不补0/时间。

## 16. 结果报告与参数冻结交付格式

下一实验输出：

1. 协议/代码/manifest版本与偏离；各阶段planned/completed/failed/Unknown、真实独立n/dependency。
2. N0/N1/P/A标签数、来源、逐层域/不适用和从planned到实际标签转化。
3. 每参数候选、推荐值/范围与依据；单因素、重要交互、稳定邻域/敏感性。
4. §9各指标分子/分母/CI/family/预算、延迟区间、Unknown原因和所有失败。
5. 一次V结果和消耗记录；未验证域/参数Unknown，不自动Agreed。
6. 逐层Recommended-for-freeze / Not established / Unknown与研究者接受入口；没有正式risk/early-window证据则明确未评价。
7. provenance/SHA、注册/便携索引、Context Consistency Check、定向验证、真实commit/push/远端HEAD。

## 17. 方法来源与阅读范围

复用[Task5方法笔记](P2_TASK5_STATISTICAL_METHOD_NOTES.md)：Frangakis–Rubin原文HTML全文；Hoeffding关键定理/有限总体章节部分阅读；Hall/FHWA测量节部分阅读；Zhang正式全文只借候选提取/图边界，不迁阈值。Edie原文仍未得，本次不称精读，也不无限搜索。

新增仅NIST官方e-Handbook §7.2.4.1定向核查二项比例exact方法：https://itl.nist.gov/div898/handbook/prc/section2/prc241.htm （2026-11-02）。它不提供交通损失标准；不是新增论文，不另建PDF库。AAD应用的设计/标签/分母条件由本文给出。

## 18. 定稿校验与下一项直接执行

顺序：一次接受集中启动项→具体manifest/白名单/split/seed/资源→独立truth与SAC→生成参考/网格→Null/Positive/归属校准→固定其他参数逐项重算→关键交互/robustness→按验收/power确定最终V的n→候选/代码/规则hash冻结→一次新V→稳定区域/适用不适用/Unknown→研究者接受推荐冻结。

协议SHA和输入来源哈希在design_evidence.json。复算命令：python docs/research/P2/task6_support/calculate_design_evidence.py；此脚本只做显式历史白名单读与设计数学，不运行交通实验。不造提交自身自指SHA。**不新增Task6.1/6.2或其他设计任务；剩余真正科学判断集中一次接受，参数未知由下一参数确定实验求得。**
