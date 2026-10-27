# Stage 0.5-R0 设计冻结候选包

任务：AAD-S0.5-R0-20261028。标签日期2026-10-28；实际准备始于2026-10-27（Asia/Shanghai），精确时间见entry/validation。仅离线准备，不执行R1、Stage0.6或StageI。

## 审查结论

R0候选包：READY_FOR_RESEARCHER_REVIEW；科学设计冻结：AWAITING_RESEARCHER_DECISION。B10/B01/B11尚未执行，当前不具备直接启动R1的精确冻结条件。Stage0.5科学交互Gate仍blocked，Stage0.6与StageI保持原状态；未写Protocol Lock、授权envelope或ledger reserve。本轮新增SUMO/真实TraCI连接均0。

研究路线仅来自研究者指定的本地Stage0后续路线.md，源路径与SHA见baseline_binding.json；未复制私人笔记或路线图全文。当前任务不沿用此前周任务的仿真授权。

## Verified：精确B00基线

- 进入HEAD与当时origin/main：4a7c204ba6e83296f6fd657cfe4ce82b35a5ec07，进入工作区干净。
- 唯一接受基线：WEEK_0750_B00_IC1_s20261201_A03，正式来源evidence/results/RES-AAD-WEEK-20261027-V1/。A01/A02的420s运行因资源采样覆盖不合格而保留，不能替代A03；更早candidate-v8首步速度冲突失败也保持原样。
- 当时执行源码为基commit e38f5240a6542ceb12ec7325a59899dd834132be加明确dirty闭包。实际旧协调器快照单独绑定；当前CLI不冒充当时执行文件。原A03 ledger拒绝及导入失败日志不改，接受来自独立零启动后验测量。
- US-101 0750；seed20261201；420s、8400原生步、0.05s步长、0.1s记录、评价窗[120,390)。SUMO1.26.0/TraCI协议22直接核对封存getVersion与二进制/TraCI哈希。
- 真实network/routes/run.sumocfg、五种vType、全部route定义、12项原生控制器源、分析器、原始输出与测量parquet均精确绑定；没有使用通用fixture网络。
- 1150声明=117初态+1033非初态；1005插入=857到达+148在网，145native pending；碰撞/teleport/discard均0，来自原完整验收而非日志缺省。18/18共同支持，局部D1=9778.4veh-s，局部P2 onset0。

## Verified：完整轨迹源事件支持

先按原实现local_d1_measurement处理完整610,725行、1005个已观测ID、4200个记录时刻[0,419.9]，再做区域/起始时刻归属；没有先裁切空间。全部raw FCD行与封存measured_state在身份、时刻、native lane/position、速度和映射纵坐标上逐项精确相等。

正式规则保持：可靠TTC严格小于2s，连续观测跨度至少0.2s，最大允许间隔0.11s；现有记录格点0.1s，身份/前车/native lane变化不能跨接，确认时刻为首个满足跨度的实际观测。独立风险序列扫描与正式事件列表一致。

完整可评价上下文确认P2=0、风险点=0；有效可靠TTC最小2.1578783958602834s。短风险/未确认右删失候选均0。事件列表为空，所以不存在可报告的事件ID、源车辆或事件特定物理到达时刻；没有猜测ID或填0。

全域诊断性合格跟驰边523261，按同一双端规则计E=52326.1veh-s；这不另行冻结全域D1估计对象，原局部D1定义与9778.4veh-s结果不变。84,227点缺失（74,611 native lane边界、9,616 internal连接），仍不可评价；不能把已观测P2=0推广为未观测关系没有物理风险。

| 源区域候选（均Proposed） | 实际道路/范围 | [120,390) D1 veh-s | P2 onset |
|---|---|---:|---:|
| S_UPSTREAM_MAIN | main_0、主线1–5、映射y[0,150) | 8457.4 | 0 |
| S_DOWNSTREAM_MAIN | main_2、主线1–5、映射y[399.22,669.18) | 13650.1 | 0 |
| S_ONRAMP | onramp、native onramp_0、映射lane7 | 254.9 | 0 |

这三个候选均由网络结构定义，未依据有利P2/rho挑选车辆。它们与目标主线空间分开；匝道的道路身份独立，不能仅用共用纵坐标判断空间重合。B00没有现成正式源事件支持；也不据此推断尚未运行的三臂必然没有事件。

## Proposed：目标、cohort与物理时间

目标沿用候选主线1–5、映射y[150,350)、t[120,390)，跨main_0末段和main_1部分，排除main_1_0辅助车道。坐标采用封存parse_fcd对mainline边长的逆映射，不把native pos/raw x当作统一真实纵坐标。此区域不是StageI正式冻结。

首选cohort候选C_INPUT_ROUTE：处理前按固定路线是否包含main_0或main_1确定ID资格，实际为1112个ID（79初态+1033非初态）；另38个初态仅走main_2，不经过目标。完整可重建规则、排除ID和排序ID哈希已登记。资格不依赖P2、rho或处理后实际进入。对原1150总体仍保留生命周期核算，没有删除车辆。

备选C_PRE_PULSE_STATE：在两项操纵前的同一预定时刻/区域固定ID，时刻和区域仍待决定；它排除晚进入车辆、改变估计对象，不能静默替换首选。两种方案都必须区分声明出发、实际插入、未到目标、pending、缺失跟驰与右删失；无合格观测不是零风险。

物理路径使用真实network connections核对，见topology_candidate_audit.json。main_0可沿同边/下游main_1到目标；onramp的道路路径可到main_1，但先进入辅助lane0，必须有实际换道/跟驰见证才可到目标车道；main_2没有逆向道路旅行路径到目标，这不证明上游leader→follower影响不可能。

### 物理路径实现边界：Awaiting Researcher Decision

- Documented Intent：物理到达必须来自实际有向物理路径，区分身份/链路缺失、不可达及不确定，不能用消息到达替代。
- Actual Implementation：归档helper先检查前向道路拓扑，再接同车前进时间边与同时刻leader→follower边；没有最大时间缺口或incarnation质量守卫。tau_p是绝对目标时刻，不是传播时长。
- Evidence：离线单元测试复核1s缺口仍可被helper跨接，及下游源被前向道路预检早拒；源事件审计为0，因此本轮不计算事件特定tau_p。
- Affected Files：code/src/riskprop/stage_0_1_sumo.py::analyze_physical_path_from_archived_tables、正式到达资格候选；未修改该实现或宣称其为科学效应估计器。
- Conflict：道路旅行可达性不能自动替代风险影响可达性，helper输出不能直接作已验收的科学物理到达。
- Status：Awaiting Researcher Decision。候选规则为有身份质量、连续观测及实际车道连接见证的时间化leader→follower图；缺失路径标uncertain，只有指定图的可靠断连才可标不可达。起始物理时钟与可检测确认时钟分别保留。

## Proposed：B10/B01/B11精确输入

arm_input_candidates.json是不可执行的候选描述，所有execution_allowed=false，没有新授权或envelope。B00直接复用已接受证据。

- B10首选候选复用现有准备器与NativeBackend语义：仅main_2_0..4道路lane限速，零阶保持[0,180)10、[180,240)5、[240,420)10m/s；t180/t240先set再执行下一0.05s步，逐lane立即get回读。不是逐车setSpeed，不强迫车辆瞬时达到该速度。进入/离开/换道后遵循所在lane的当前限速及原车模；未来须同时保存set/get和实际车速轨迹。高层脉冲已确定，精确scope/边界语义仍为待冻结候选。
- B01仅60辆非初态entering车：原block=floor(depart/60)，块内按(original_depart,ID)稳定排序；n>1用t=60b+20+5r/(n-1)，单车20s；按原实现Python ties-to-even舍入到0.05s、输出两位小数。块内排序、ID、路线、车型、其他属性均不变；XML车辆元素按(new declared depart,ID)全局重排，明确披露这一序列化变化。候选算法不因代码已存在就视为批准。
- 7块数量为9/8/9/8/9/9/8，共60，逐车映射见CSV。每个候选时间在本块[20,25]且总窗内，全部对齐原生格点；与现有pulse_routes独立对照。候选depart只表示声明时刻，不代表插入成功。
- B11严格组合两项，不能加入其他干预。网络、1150个ID、117初态/DS38/IC1、车型/行为、seed、所有窗口与停止语义不变；实际差异逐项见scenario_diff_matrix.json。

## 待研究者决定与放行条件

decision_register.json逐项记录来源、首选/备选、影响及空的approved_value。需要明确：源区域/源集合、物理源时钟与确认时钟用途、目标空间定义、cohort规则、合格物理路径/缺失语义、B10精确操纵、B01确定性压缩算法、实际插入/pending的诊断判读。既定三臂预算、seed和全无源事件停止规则不重新寻求授权；不自动采用旧90%门槛，不搜索新seed/强度。

R1须先完成这些范围明确的冻结，并为新的精确输入/源码/运行时/policy建立独立准入。R0审查就绪不提升科学Gate，不替代R1操纵生效、源支持及后续交互验证。

## 证据与离线复核

- 便携包：evidence/results/RES-STAGE-0.5-R0-DESIGN-PACKET-20261028/；manifest/SHA256SUMS绑定全部包文件、候选输入和相关源码。
- 新候选route：evidence/admission/AAD-S0.5-R0-20261028/candidate-v1/ramp_routes.rou.xml。B10用原route，B01/B11共用这份精确候选；不修改B00文件。
- 封存全轨迹仍只在原A03本地产物目录；不把raw轨迹、大逐车表、日志、holdout或私人资料复制进便携证据。
- docs/audits/stage_0_5_r0_20261028_v1/final_validation.json记录最终定向/全量软件、compileall、文档、哈希和无数据检出结果。初次配置键读取错误在写候选前退出，原日志保留；首版未导出草稿保留并明确登记cohort计数修正，没有新仿真或历史改写。
- Context Consistency Check：仅更新本任务入口、实验/结果索引和待决问题；Stage0.5科学Gate、Stage0.6、StageI、旧失败和Not Accepted均保持不变。
