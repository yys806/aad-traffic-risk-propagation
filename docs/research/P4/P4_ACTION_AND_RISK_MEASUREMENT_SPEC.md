# P4 动作与区域风险测量规范

Task: AAD-P4-TASK1-20261103。版本：P4-MEASUREMENT-PROPOSAL-v0.1。日期：2026-11-03。

**状态：审计事实 Verified；操作化建议 Proposal / Awaiting Researcher Decision。** 本文是统一定义的应用方案，不新增 Definition ID，不修改 [v0.4 / 27项](../definitions/README.md)。Formal rho/P2、P1 estimand、P3 schema、Gate、Protocol Lock 和 Stage1.1 授权均不变。本文不宣称已经部署完整区域风险计算器。

## 1. 对象、证据和结论层级

状态约定：**Fact / Verified**为实际源码、配置或已有记录可复核事实；**Inference**为基于这些事实的有限工程推断；**Proposal**为尚待批准的测量/接口选择；**Unknown**为当前证据不能确定。现有数值原语能够支持候选式的部分计算是工程Inference，不等于完整区域结果已实现或科学方案Agreed。

| 对象 | 本任务可观测量 | 与P1关系 | 不能据此推出 |
|---|---|---|---|
| Control Decision | decision_id、输入snapshot、policy版本、intent | 策略决策 | 已下发或执行 |
| Control Command | command_id、API、请求上限、发出时间 | 命令层 U^{cmd,*} 的记录 | 车辆已有运动响应 |
| Command Execution | command/execution引用、getter、post-step状态、命令有效区间 | 施加约束的执行见证；原生约束后的真实执行还受SUMO机制影响 | 已完整识别物理执行器输入 U* 或消息因果作用 |
| Actual Action / Behavioral Response | 实际v/a/位置、车道、leader/gap及合格配对差异 | 运动状态 X* 的观测及响应代理 | 所有状态均等同U*；区域风险因果效应 |

依据：[P1理论](../P1/THEORY_AND_CAUSAL_MODEL.md)的命令、实际输入和状态区分；[P7实际接线](../../../code/src/riskprop/p7_message_runtime.py)的ACK/post-step读回。setMaxSpeed改变可行速度上限，不直接施加已知加速度。getMaxSpeed相等证明上限设置成功；post-step运动才是实际状态证据。持续命令期间的每个execution不是一次新的独立干预。

必须区分三层结论：消息采用后有运动差异；风险贡献有描述差异；通信策略改变总体区域风险。前两层即使同时出现，也不推出第三层。P4负责测量，不执行P5/P6识别。

## 2. Action Measurement 候选方案

D7已Agreed：连续实际速度/加速度轨迹为主要观测方向。**主终点、阈值、持续时间、误差容差和比较窗口尚未冻结**。下表是独立测量量，不加权成综合分数。

| 候选量 | 对象/单位 | 优点 | 局限 | 建议定位/状态 |
|---|---|---|---|---|
| 有符号 Δv=v_treat−v_base | 运动响应，m/s | 直观，现有状态可读 | 积累效应，不能独自定位制动过程 | 优先报告的轨迹量；主终点待决 |
| 有符号 Δa | 纵向动态响应，m/s² | 直接描述加减速过程 | 微分噪声/采样/仿真积分法敏感 | 与Δv并列观测，阈值待决 |
| Δ位置、Δ累计距离 | 轨迹偏离，m | 描述累积位移 | 路网坐标/时间误差、不同route影响 | 辅助；先定义相同坐标和路径 |
| lane/heading变化 | 横向/方向响应，标识/rad | 适用于多车道交互 | lane字符串不可相减；当前P7无换道策略 | 辅助分类量，不扩展控制算法 |
| net gap/closing speed差 | 跟驰交互，m、m/s | 连到TTC输入 | 依赖leader身份，切换后不是同一交互对 | 分leader段辅助报告 |
| leader关系持续时间 | 交互结构，s | 说明暴露与关系变化 | 出入场/观测缺口影响 | 辅助，不与风险重复计数 |
| 差异候选起点/确认时间 | 时间，s或区间 | 可连接信息与物理时间轴 | 阈值、持续性及覆盖依赖 | 两个时间分存，均Proposal |

推荐保留完整有符号轨迹、绝对差摘要、共同支持数量及缺失时间。最大差值不是预先定义的Action主效应。P7数值误差1e−9仅为该确定性工程比较，不是正式Action阈值。

### 2.1 合格配对与时间对齐（Proposal）

1. pair_manifest预先绑定两run、assignment、条件、交通初始化、网络/route及版本。跨run车辆通过显式角色/初始化映射，不要求两run的incarnation字符串相同，也不以相同vehicle_id自行认定同一实体。
2. 每run内以(run_id, incarnation_id, clock_id, step, phase, sequence)或受治理的state_id唯一定位；同phase重复键先报错，不多对多自动merge。同一时刻不同phase可合法共存。
3. 先检查时钟映射及误差、单位、采样率、观测支持，再比较。默认只报告已确认可比的实际共同观测；不同采样率无共同点时Unknown，不能记零差异。
4. 若未来允许重采样/插值，需单独批准方法、最大缺口、误差和保留原始引用；不对lane/leader标识线性插值。不得把估计值冒充实际readback。
5. leader/lane/route/incarnation变化均分段标注；车辆退出、缺测或未知支持不能靠删除行跨越。未观察不等于未变化。
6. 持续性只能在合格连续观测段内累计，记录候选起点区间、实际确认时间和覆盖；不使用最后点后的虚拟时长。无法确认持续性时右删失/Unknown，不返回“无响应”。

### 2.2 现有函数的使用边界（Fact）

[compare_paired_action](../../../code/src/riskprop/stage_i_mechanism.py)只精确匹配vehicle_id/time_s，比较绝对速度差。无incarnation/run/clock约束，不比较加速度或gap，不自动重采样。重复键触发多对多merge，通常在下游严格递增检查报错，而非明确的重复身份诊断。

其[first_sustained_divergence](../../../code/src/riskprop/prelock_metrics.py)使用中位步长延长末点，未设置最大缺口；删去NaN后可跨缺口确认持续性。离线例子已复现这些限制。因此 first_action_change_time_s **只是该工程规则下的候选起点**，不是完整Action Effect Estimator，不足以确认科学T_U。此次不改核心实现；未来消费者需上游验证和经批准的比较器修正。

### 2.3 五类时间分别保存

| 时间对象 | 提议字段 | 依据/限制 |
|---|---|---|
| Adoption实际消费（本任务表中称T_A） | adoption_consumption_time_lower/upper_s | POLICY_INPUT_INCLUDED→decision/input；不与统一符号中其他A类到达混用 |
| 首次改变命令T_C | command_issued_time、command_change_time | 命令内容变化，不是接收/采用时间 |
| 首次实际执行见证 | execution_observed_time及支持区间 | getter/step/phase；不回填到命令时刻 |
| 实际差异与持续响应候选T_U | first_observed_difference、onset_lower/upper、confirmation_time | 配对运动学，测量误差和缺失显式记录 |
| 总体风险起点T_R / 物理到达T_P | 外部结果引用或Unknown | TR须P5/P6总体同时置信带/持续性；TP来自独立物理链，非Action或首个risk样本下降 |

P7的2.8s命令、2.9s首个差异是历史工程事实，不能作为所有任务的处理起点。比较中的treatment_start_s必须来自预先声明的处理时间定义与具体证据，不按观察到差异反选。

## 3. Vehicle-level Formal Risk

### 3.1 正式计算路径与参数事实

可靠后向跟驰条件下，c=v_f−v_l，g为净间距。当前SUMO适配器要求g>0、c>1e−3 m/s且leader可靠，计算TTC=g/c（s）、DRAC=c²/(2g)（m/s²）。1e−3是现有实现条件，不在本任务推广为跨数据源正式阈值。

Formal rho(TTC)=exp(−TTC/τ)，可靠valid且有限正TTC才有点值；τ=15.364279197080283s。事件P2使用TTC<2.0s、持续0.2s、最大间隔0.11s（具体不等号及连续性以源码为准）；**P2事件阈值不是rho截断值**，TTC=5s也可有正rho。

来源：[Formal源码](../../../code/src/riskprop/formal_risk_measurement.py)、[现有配置](../../../code/configs/stage_0_2_formal_risk_measurement_p2_v1.json)。schema=stage_0_2.formal_risk_measurement.config.v1，algorithm=stage_0_2.formal_risk_measurement.v2。配置明确scientific_defaults_frozen=false，Region/qualification/window/dedup=null。代码/配置存在这些数值是Fact，不证明完整科学参数已冻结；本任务未重新校准τ，也未独立重新验证其原始校准样本。

### 3.2 点贡献与质量矩阵

| 空间/质量条件 | 点贡献[lower,upper] | 解释 |
|---|---|---|
| 区域外且区域位置可靠 | [0,0] | 对指定区域的贡献为零，非该车无风险 |
| 区域归属未知/位置不可靠 | [0,1] | 即使TTC有效也保留成员资格不确定性 |
| 区域内但测量不可靠 | [0,1] | 不因默认TTC或标志补零 |
| 区域内、可靠valid正TTC | [rho,rho] | 可计算点值 |
| 区域内、可靠not_applicable | [0,0] | 仅后向跟驰风险投影，不是全部交通风险为零 |
| missing / invalid / not_measurable / Unknown | [0,1] | 原状态与原因保留，绝不合并成零 |

not_applicable需要可信的“不存在该后向闭合关系”证据。传感器未观测到leader与确定没有leader必须区分；SUMO可在已知观测机制内给出no_observed_leader，现实数据不能直接照搬。碰撞/负间距在SUMO测量中invalid，不用分析真值函数的TTC=0/DRAC=∞替换Formal输出。

状态分轴：测量(valid/invalid/missing/not_applicable/not_measurable)、质量(reliable/uncertain/unobservable)、空间(inside/outside/unknown)、生命周期(present/exited)、时间删失(right_censored)、结果识别(point/interval/Unknown)。Unknown不应成为把其他信息抹平的单一字符串。

## 4. 固定时间积分与固定车辆聚合

### 4.1 现有积分语义（Fact）

对W=[s,e)，L=e−s>0，现有integrate_fixed_window完整保留L。仅经continuity_is_valid证明的相邻观测段可使用左端贡献保持；时间边界可在两真实夹持观测之间裁切。首点前、末点后和缺口不外推；未知段贡献上下界保持[0,1]。重复时间戳拒绝，不静默均值。

连续性依赖source成员/period/site/window、trajectory/leader trajectory、统一clock anchor、实际frame/ms/time及可靠leader匹配。默认0.1s、frame差1可显式配置，但不能只改参数绕过丢帧审计。leader切换或无leader段可能点值为零但无法证明跨时段连续性，仍得未知区间。该保守性是当前能力限制，不应伪造leader来压窄结果。

输出lower/upper_integral单位s；lower/upper_mean无量纲；known/unknown_time_s和observed_pair_time_s为不同量，观测对覆盖不保证点贡献已识别。积分函数只做**时间裁切**，不执行区域几何裁切、出入界定位或完整名单核验。

### 4.2 最终Y仍待定的候选链（Proposal）

沿P1候选式：Y_e(a)=N_e^−1 Σ_{i∈C_e} L_e^−1 ∫_{W_e} b_ie(t;a)dt。

若研究者批准该标准化等车方案，则先对每辆预定车形成同一W的积分界，再以固定N分别平均上下界。可靠区域外段贡献零；位置未知为[0,1]；整车无观测也需保留全窗[0,1]记录。退出不删车、不补新车，不把分母改成当时可见车辆数。区域外的风险贡献零与“区域cohort平均速度在退出后结构性未定义”是不同对象，遵守统一定义Rules B，不能互相套用。

**equal_vehicle_average仅平均传入列表，不核验名单、唯一身份、run或同窗。** 因此可用的数值原语尚不等于可用的事件级区域汇总器。未来需预处理名单完整性、同窗同区域、原始哈希、去重和显式失败行；未实现前不能直接声称已得到正式Y。

依据：统一账本 **Task6/E61**（非同名Task7/E61）只确认rho/均值[0,1]及积分[0,L]有源码依据，最终Y聚合及变换仍Awaiting。条件性的数学范围为：若采用上述Y，则Y∈[0,1]，两臂差∈[−1,1]，四格差∈[−2,2]。did_interval只做区间算术，不提供随机化估计/置信区间/因果识别。不得据此冻结主结局或统计方法。

### 4.3 小型离线例子（已验证软件语义）

所有例子只是确定性数学检验，非交通运行、非科学参数选择。完整27项见[实际结果](../../../evidence/research/P4_TASK1_20261103/deterministic_examples.json)。

- 全窗0.4s，点0/0.1/0.3s，点界均0.2，仅首段连续：积分界[0.02,0.32]s，均值界[0.05,0.8]；缺口和右尾共0.3s保留未知。
- 两个固定成员：一车全窗均值0.2，另一车完全缺失[0,1]，等车界[0.1,0.6]。删除后一车会错误得到点值0.2，现有均值函数不会自行阻止。
- 全部四格界[0,1]，差的界[−2,2]；不能解释为已观察到效应。
- no-leader可靠点贡献0不能直接推出无leader整段可积分为0；现有连续性守卫将该段保留未知。

区间过宽时报告“在给定支持和界下未能点识别”，并保留宽度/缺失组成；不得截窄、补零或只报告完整样本子集。

## 5. 区域、Cohort与完整计算链

DEF-COHORT-001 / DEF-REGION-001要求处理前确定名单及空间支持；DEF-TIME-002要求总体风险时间不同于单次曲线；DEF-PHY-007/009/010分别约束cohort、同域macro及三层物理证据。具体区域/人数/窗口本任务不选定。

固定cohort只测该组车在区域中的贡献，不自动代表该区域全部交通/全部冲突。若目标为“区域总体”，需处理前定义的全体资格/需求角色集合和覆盖说明，不能按各处理下实际进入者动态改分母。区域其他车辆变化不被固定cohort阴性排除；macro变化不证明指定源微观路径。

| 步骤 | 必要输入 → 输出 | 时间/空间/单位 | 质量/缺失/版本责任 |
|---|---|---|---|
| 原始轨迹 | source_ref/hash/row → 原始观测ID | 原生clock/坐标/SI转换 | 源数据及解析版本，不补缺测 |
| 身份时间QC | run/vehicle/incarnation/frame/phase → state_id与QC | 时钟映射区间、坐标系 | 唯一键、断轨、重复和时钟误差分列 |
| 实际状态 | speed/accel/position/lane/leader/gap | 实际post-step支持，m/s、m/s²、m | 不使用target reference当actual |
| 运动学风险 | 合格follower/leader、gap、closing → TTC/DRAC/status | 同一时刻/交互对，s、m/s² | 切leader/lane段，缺失/invalid不补0 |
| Formal点贡献 | TTC/status/reliability → rho/bounds | 相同状态支持，无量纲 | Formula/config hash；测量与空间可靠性独立 |
| 空间裁切 | region geometry/version、车辆位置/出入界 → membership/interval | 固定坐标、边界规则、lane集合 | 未实现通用clip；边界不确定保持界 |
| 时间积分 | 同一车连续样本、固定W/cadence → J_i、均值界 | 固定L，积分s/均值无量纲 | 缺口/首尾/右删失保留全分母 |
| 固定名单组装 | cohort manifest、每车同窗积分 → 完整N行 | 处理前固定支持 | 缺整车显式[0,1]，拒重复/异窗 |
| 区域结局 | 完整N行、待批准聚合版本 → Y界/quality | 单run/event/assignment/unit | 当前Proposal；覆盖不足标scope-limited |
| 下游接口 | 结局+时间序列+缺失+hash → P5/P6 | 独立分配单位，全部assignment | 不按Adoption/动作/完整性筛选主ITT |

出入界需要域内轨迹片段。两点跨界时若没有可信交点/时钟支持，不能把左点inside任意延长整个步长；应保留不确定区段并提出边界操作方案，不能擅自修改Formal积分原语。多车道分别登记lane和区域版本；多leader/多冲突不重复叠加同一车Formal后向贡献，若扩展风险对象须另行科研批准。

## 6. 宏观交通与辅助指标

Edie-type同域A中D=Σd_i(A)、V=Σt_i(A)，q=D/|A|、k=V/|A|、u=D/V。单lane时|A|为空间长度×时间，单位分别veh/s、veh/m、m/s；V=0时u未定义，不填0。部分进入/退出按域内片段，多lane优先分lane报告，跨lane归一化需版本。q=ku是构造恒等式，不是三份独立证据。抽样轨迹不能无权重依据外推全域。宏观量描述交通状态，不是Formal rho，不将Micro/Macro/Cohort合并成OR/AND到达标签。

| 量 | 数学语义/单位 | 职责与限制 |
|---|---|---|
| Formal rho/P2 | 指数风险映射/事件识别，无量纲/事件 | D8沿用；仍需合法质量和scope |
| TTC | gap/closing，s | 后向闭合基础量，不适用时不伪造有限数 |
| DRAC | closing²/(2gap)，m/s² | 辅助运动学；无界，不任意截断，不替rho |
| Integrated TTC Exposure | valid-time加权分段线性TTC暴露，无量纲 | 历史/辅助；不是全窗指数rho；缺测分母不同 |
| PET | 同一冲突区两占用区间间隔，s；重叠为0 | 需要冲突区几何，当前P7不具备该支持 |

prelock_metrics的valid=True而TTC=NaN可产生暴露0，是已复现输入一致性风险；未来使用前必须拒绝/标Unknown不一致输入。本任务记录问题、不修改辅助核心函数。TTC/DRAC共享gap/closing，不作为相互独立的确认。

## 7. Action–Risk关联、数据可信度与下游

P3 Action引用execution，Risk可引用多Action。P7现在只有一个run级risk附件，指向per-state TTC/质量CSV，未计算rho/区域Y，region/cohort/window为空、风险效应Unknown。P4提议用外部规范化明细表与明确state/action/execution桥接，不修改P3正式schema。

每个风险样本或汇总需明确run/assignment/event、实体/角色/incarnation、动作与执行ID、state_id、源字节/hash/行、原生和统一时间支持、region/cohort/window版本、measurement/config/derivation版本、分质量轴及上下界。不允许仅凭“时间接近”关联。区域汇总可跨多车，但需成员映射；不强迫每个原生运动样本都有消息命令。

数据源边界：NGSIM支持高速后向跟驰参考，身份/leader误差仍受QC约束；pNEUMA当前仅城市运动学/组成，无可靠leader与Formal TTC能力；SPMD只支持通信观测边界；SUMO支持模型内实际状态与受控工程验证，不能代替现实测量验证。跨源时钟/坐标/噪声不可默认相同。

P5/P6接口是每个独立run/分配单位的测量结局、固定支持、时间化结局界、缺失和失败状态及哈希。车辆/采样点不是自动增加的随机化样本量。TA/TC/TU只支持机制时间账本；TR/TP与同时带、持续性/统计规划须后续决定。本文的Proposal经过研究者确认后才可进入实现/正式参数登记，不在本任务自动启动后续实验。
