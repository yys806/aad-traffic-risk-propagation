# AAD Symbol Register

版本：AAD-SCI-DEF-20261102-P2T5-v0.3。以下是当前入口及映射；新记号是Proposal。论文采用情况以OVERLEAF_ALIGNMENT.md为准。

| 符号 | 中文含义 | English | 单位 | 首次定义位置 | 当前定义来源 | 状态 |
|---|---|---|---|---|---|---|
| \(Z_S,S^*,Z_C,C^*\) | 源/通信分配与实际状态 | assignments and actual states | binary/status | P1 DAG/Estimand | P1、DEF-SRC-001/REF-001 | Agreed方向 |
| \(\eta^{src}_\omega\) | 论文指定源风险事件 | source-risk event | event | Overleaf main.tex source-event/lifecycle | Overleaf；不同于assignment | Paper notation |
| \(u_{v,t},a_{v,t}\) | 车辆速度、加速度 | vehicle speed/acceleration | m/s, m/s² | Overleaf Stage II | 论文；代码speed/acceleration显式映射 | 既有语义 |
| \(g_t^{(v'\to v)}\) | 净间距 | net gap | m | Overleaf Stage II | 论文；代码net_gap | Reserved |
| \(\Delta u_t^{(v'\to v)}\) | pair闭合速度 | pair closing speed | m/s | Overleaf Stage II | 论文；leader/follower符号不得省略 | Reserved |
| \(\rho,\mathrm{TTC},\mathrm{DRAC}\) | 正式风险、碰撞时间、减速度需求 | formal risk, time to collision, required deceleration | 1, s, m/s² | 既有论文/正式测量规范 | formal_risk_measurement.py与正式配置 | 不改既有定义 |
| \(t_{S,onset},[L_S,U_S]\) | 源物理起点与界 | source onset/bounds | s | P2 Task1/2 | DEF-SRC-002 | Proposal |
| \(t_{S,confirm}\) | 源确认 | source confirmation | s | P2 Task1 | event_confirm_s；DEF-SRC-003 | 实现事实 |
| \(T_{G,eligible}\) | 消息生成资格 | generation eligibility | s | P2 Task1 | DEF-INF-001；不是actual generation | 设计约束 |
| \(t_E\) | 物理传播起点 | physical origin | s/interval | P2 Task1 | 推荐onset，非confirmation | Awaiting |
| \(G_P(t),G_I(t)\) | 物理/信息网络 | physical/information graph | graph | P1/P2 | 论文G^phy/G^info为映射，非新增网络 | 方向Agreed |
| \(\pi,\Pi_{qualified}\) | 路径及合格路径集合 | path/qualified paths | path/set | P2 Task1 | DEF-PHY-002–004 | Proposal |
| \(\mathcal T,\mathcal C_{\mathcal T},N\) | 固定区域、cohort、人数 | region/cohort/size | set/set/count | P1 D4/P2 | DEF-REGION/COHORT；paper V^tgt映射 | 原则Agreed，边界待定 |
| \(B_{\mathcal T},u^B_{i,t}\) | 物理baseline及每车参考速度 | physical baseline/reference speed | state, m/s | P2 Task2 | DEF-PHY-005 | Proposal |
| \(\Delta u^B_{i,t}\) | 单车baseline减实际速度 | baseline-relative decline | m/s | 本轮修订Proposal | DEF-PHY-006；B上标必留，不同于pair closing speed | Proposal |
| \(\bar{\Delta u}^B_{\mathcal T}(t)\) | 等车全cohort平均下降 | full-cohort mean decline | m/s | 本轮修订Proposal | DEF-PHY-007 | Proposal |
| \(\widehat{\bar{\Delta u}}_{obs}(t)\) | 观测子集估计量 | observed-subset estimate | m/s | 本轮修订 | 不自动等于全cohort量 | Proposal |
| \(M_i(t),c(t),c_P\) | 可用掩码、固定分母覆盖、门槛 | mask/coverage/gate | binary/proportion | P2 Task2/3 | 固定N，无动态补位 | Proposal |
| \(\phi,\theta_P,h_P,q_P\) | 状态函数、强度、持续、最大缺口 | state/threshold/span/gap | 1,m/s,s,s | P2 Task1/2 | DEF-PHY-008；主均值尺度 | Proposal；数值Unknown |
| \(T_P,\widetilde T_P\) | 理论与可观测物理到达 | physical arrival/random observation | s/interval | P1/P2 | DEF-TIME-001/REF-002 | 非总体常数 |
| \([L_A,U_A],T_{A,confirm},T_{A,obs}\) | 到达onset界、确认、采样 | arrival interval/confirmation/observation | s | P2 Task1/2 | DEF-TIME-001/CENS-001 | 操作Proposal |
| \(T_U,T_R,\widehat T_R\) | 动作时间、真风险效应起点、统计检测 | action/risk onset/estimator | s | P1 | P1 §7；DEF-TIME-002 | 不得互换 |
| \(\tau_R(t),\delta,\mathcal H,U_{sim}\) | 策略风险曲线、SESOI、网格、同时上带 | policy curve/SESOI/grid/band | risk,risk,s,risk | P1 §7.1.1 | 不新增风险体系 | 参数待定 |
| \(F_0(t\mid H,Z_S=1)\) | 无消息arrivalCDF | no-message arrival CDF | probability | P1 §7.2 | DEF-REF-002 | 有定义，无可估数据 |
| \(Q_{pre},F_0^Q\) | 通信分配前资格及其子总体CDF | prequalification/subpopulation CDF | binary/CDF | 本轮识别审计 | 不与原F0悄然等同 | Agreed资格方向；记号/实施细则Proposal |
| \(H,H^\star,\eta,\alpha\) | 处理前背景、预定早窗、到达比例容许、错误率 | context/horizon/arrival allowance/error | mixed,s,probability,probability | P1 §7.2 | H不是h_P；均未冻结 | Awaiting |
| \(T_R^{upper},T_P^{lower}\) | 总体时间比较界 | population comparison bounds | s | P1 §7 | TP下界须说明分位数/早窗对象 | 概念Agreed，构造Proposal |
| \(\hat b(t),e(t)\) | offset校正及误差界 | clock correction/error bound | s | 本轮时钟契约 | DEF-CLOCK-001 | Proposal；值Unknown |

## 历史映射与治理

Task2的g_v^mean(t)是速度偏差的临时通用函数名，与论文net-gap g存在阅读混淆，但不是已证明同一完整记号的数学重定义。建议后续统一为上述Δu^B族，优先复用论文u表示速度；B上标区分pair闭合速度。早期Task3草稿的Δv^B族对应同一候选量。本次保留两者历史映射，**未将旧符号正式Deprecated，也未更改论文**。映射及未来弃用均Awaiting Researcher Decision。

论文t_ω^phy-resp是行为层物理响应候选，与区域状态TP对象不同，不擅自重命名为新的正式论文变量。论文risk baseline R^tgt,base与B_T物理基线用途不同，不因都叫baseline就认定数学冲突。代码既有speed、net_gap、closing_speed、event_confirm_s及Formal rho tau语义不变；tau标定值不复用于θP。

操作细则G的W、t_B,end、n_i,B为基线窗长/窗末/逐车有效样本数；b(t)是local相对reference的offset，e_offset/d_max/e_phase分别为offset、drift上界及step-phase界（s、s/s、s），只为误差传播辅助记号，均Proposal，值Unknown。


## Task4增量（不修改Overleaf符号）

| 符号 | 中文 / English | 单位 | 首次 / 当前来源 | 状态与旧映射 |
|---|---|---|---|---|
| Q(1), τQ, τ非Q, p | 源存在时潜在通信前资格、两类效应、资格比例 / potential eligibility, conditional effects, share | binary,risk,probability | DEF-POP-001/细则I | Agreed资格设计；推导辅助记号Proposal，不替代τSC |
| A, d_i(A), t_i(A), q_A,k_A,u_A | lane时空域、域内距离/驻留、宏观流/密度/速度 / space-time domain and traffic measures | m·s,m,s,veh/s,veh/m,m/s | DEF-PHY-009 | Proposal；复用u速度；q_A不是最大采样间隔q_P，k_A不是统计候选k |
| O_P, M, W, Q, ν（带O_P上下文） | 观测域、机制、窗口、质量、版本 / observation scope components | sets/version | DEF-SCOPE-001 | Proposal；排版使用花体集合，W为窗口集合时不得与标量baseline W混用；Q不是Qpre资格 |
| E_P, E_micro,E_macro,E_cohort | 双层及cohort证据记录 / evidence vector | structured record | DEF-PHY-010 | Proposal；不定义新二值到达 |

Qpre/F0^Q的设计方向现为Task4 C Agreed；v0.1表中Proposal只保留给符号和具体估计实施。新增宏观符号服务不同测量对象而有必要；不得把u_A与固定cohort平均下降、g净间距或ρ风险混用。


## Task5增量（v0.3，新增记号均Proposal）

| 符号 | 中文 / English | 单位 | 首次/当前来源与创建理由 | 状态 / 旧映射 |
|---|---|---|---|---|
| \(\mathbf T_P,T_P^{micro},T_P^{macro},T_P^{cohort}\) | 分层时间族 / layer-specific arrival times | s / allowed set | DEF-TIME-004 / CORE J；区分三个物理问题 | Proposal；旧φ的TP仅映射cohort，未改论文phy-resp |
| \(F_{0,\ell}^Q\) | 分层资格无消息CDF / endpoint-specific eligible no-message CDF | probability | CORE J/O；确保endpoint/总体不混 | Proposal；原全体F0不被覆盖 |
| \(A_{lj},L_l,w_M,D_A,V_A,\mathbf m_A\) | lane时空域、长度、macro窗、车距/车时总量、状态向量 | m·s,m,s,veh·m,veh·s,vector | CORE K；复用q_A/k_A/u_A族而非新造速度符号 | Proposal；w_M不是baseline W；V_A为总车时非车辆集合 |
| \(\mathcal S_{i\ell},a_{i\ell}(t),b_{i\ell}(t)\) | 允许时间集合与CDF测量界指标 / allowed-time set and bound indicators | set,binary,binary | CORE N/O；Unknown需显式上下界 | Proposal；b_iℓ不是clock offset b(t)，a_iℓ不是单车加速度a_v,t |
| \(K_P,J_R,n_z,\epsilon_P,e_z\) | 预定界限族规模、风险族规模、独立臂单位数、浓缩半径 / family sizes, units, margins | count/count/count/probability/risk | CORE O；给出可执行同时覆盖充分条件 | Proposal；n不是车辆或帧数 |
| \(A_R,B_R,Y_i^L,Y_i^U\) | 有依据风险范围及测量包络 / validated outcome range and observation envelope | risk | CORE O；不对DRAC假设任意上限 | Proposal；非采用A*、非physical baseline B_T |
| \(\alpha_R,\alpha_P,\alpha_{clock},\alpha_{measure}\) | 联合错误分配 / joint error allocation | probability | CORE P，细化P1 α | Proposal，数值未定；确定性误差界不耗概率预算 |
| \(H_0\) | 跨源分配前共同背景 / pre-source background | mixed | CORE M；区别已受源影响的pre-ZC背景H | Proposal辅助记号，不改P1既有H含义 |

上述上标/下标不可省略导致重名。t_E推荐onset interval仍非Agreed；物理baseline与F0不同；g净间距、pair闭合速度及Formal rho/P2全部保留既有语义。
