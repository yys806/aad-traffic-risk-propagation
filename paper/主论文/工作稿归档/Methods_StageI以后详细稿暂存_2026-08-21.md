# Methods Stage I 以后详细稿暂存

> 归档时间：2026-08-21。该版本保存 Stage I 及后续 Methods 的详细备选内容，不代表当前主稿进度；当前正文以 `paper/主论文/main.tex` 为准。

## System model and two-stage framework

本文研究由车辆运动、物理交互和显式消息传递共同构成的联网交通系统。设车辆集合为 $\mathcal V=\{1,\ldots,N\}$，全体车辆状态和控制输入分别为 $X_t=\{x_{i,t}:i\in\mathcal V\}$ 和 $U_t=\{u_{i,t}:i\in\mathcal V\}$，物理交通图和显式信息图分别为 $G^{\mathsf P}(t)$ 和 $G^{\mathsf I}(t)$，系统消息集合为 $M_t$。共同系统模型写为

$$
\Sigma_t=\left(X_t,U_t,G^{\mathsf P}(t),G^{\mathsf I}(t),M_t\right).
$$

Stage I 在给定系统和控制逻辑下识别指定消息的增量因果效应；仅当该作用达到预设证据门槛后，Stage II 才优化消息采用和车辆动作。两阶段共享状态、图、消息和风险测量，但具有不同的问题、约束和评价标准。

车辆类型记为 $\kappa_i\in\{\mathsf{AV},\mathsf{HV}\}$。对时刻 $t$，$\mathcal N_i^{\mathsf P}(t)$ 表示能够通过跟驰、合流或冲突直接影响车辆 $i$ 的物理邻居，$\mathcal N_i^{\mathsf I}(t)$ 表示通信协议允许向车辆 $i$ 提供消息的来源集合。由有向序对 $(k,i)$ 表示从车辆 $k$ 指向车辆 $i$，两类图定义为

$$
\begin{aligned}
\mathcal E^{\mathsf P}(t)&=\{(k,i):k\in\mathcal N_i^{\mathsf P}(t),\ k\neq i\},\\
\mathcal E^{\mathsf I}(t)&=\{(k,i):k\in\mathcal N_i^{\mathsf I}(t),\ k\neq i\},\\
G^{\mathsf P}(t)&=(\mathcal V,\mathcal E^{\mathsf P}(t)),\qquad
G^{\mathsf I}(t)=(\mathcal V,\mathcal E^{\mathsf I}(t)).
\end{aligned}
$$

物理边表示车辆运动上的直接作用，沿连续物理边形成的逐跳链属于物理传播。信息边只表示协议允许通信，不表示消息已经生成、发送、交付或被控制器采用。是否存在物理传播必须通过时序可达性审计，不能由欧氏距离或单个时刻的邻接关系代替。

车辆 $i$ 的状态写为 $x_{i,t}=(\mathbf p_{i,t},v_{i,t},a_{i,t},\ell_{i,t})$，其中 $\mathbf p_{i,t}$、$v_{i,t}$、$a_{i,t}$ 和 $\ell_{i,t}$ 分别表示二维位置、速度、实际纵向加速度以及车道和道路边状态。$u_{i,t}$ 为控制器输出，$\xi_{i,t}$ 为外生随机输入。离散状态更新为

$$
x_{i,t+1}=f_i^{\mathsf{dyn}}\!\left(x_{i,t},u_{i,t},\xi_{i,t};G^{\mathsf P}(t)\right).
$$

仿真使用统一时钟 $t=n\Delta t$。每个时间步依次读取车辆状态和物理邻接关系，判定源风险事件，更新消息的生成、发送、交付、校验和采用状态，计算控制输入，再推进车辆运动。状态、消息、控制和风险记录共享运行标识、时间步和时间原点。$\Delta t$ 在数值收敛校准后固定。

每条消息记为 $m_{q,i,j,t}$，其中 $q$、$i$ 和 $j$ 分别为消息、来源车辆和目标车辆索引。目标车辆可观测的消息集合为

$$
M_{j,t}=\{m_{q,i,j,t}:(i,j)\in\mathcal E^{\mathsf I}(t)\}.
$$

消息载荷包含消息标识、源事件标识、源车辆和目标车辆标识、风险类型、风险摘要及生成时间。指定远端消息只构成目标自动驾驶车辆的附加输入，不关闭本地感知、基础控制器或安全约束。

源区域和目标区域分别记为道路状态空间中的 $\mathcal R^{\mathsf S}$ 和 $\mathcal R^{\mathsf T}$，并满足 $\mathcal R^{\mathsf S}\cap\mathcal R^{\mathsf T}=\varnothing$。源车辆 $i$ 的合格风险事件必须在 $\mathcal R^{\mathsf S}$ 内触发，目标车辆 $j$ 在处理前基线和结果窗口内必须属于 $\mathcal R^{\mathsf T}$。各场景的道路边、车道、纵向坐标、路线组件、拓扑距离和车辆资格在实验设计中固定。

物理传播采用时间展开图审计。图中同时保留同一车辆相邻时间步之间的运动延续关系，以及跟驰、合流或冲突产生的车辆间直接作用关系。若源扰动可沿时间单调的合格物理路径到达 $j$，记录最早物理到达时刻 $\tau_j^{\mathsf P}$；若不存在可达路径，则令 $\tau_j^{\mathsf P}=+\infty$；观察期内无法判定时保留为不确定或右删失。双走廊只有在道路拓扑断开、无跨走廊车辆转移、无共享控制状态且无合格时间路径时，才允许取 $\tau_j^{\mathsf P}=+\infty$。

位置、速度和加速度分别使用米、米每秒和米每二次方秒。不存在有效前车或字段不可观测时，派生量记为缺失，不以零值替代。每辆车在单次运行中使用唯一身份；车辆离开后不得继续被物理边、消息或风险记录引用。四格运行共享初始交通状态、背景输入和随机种子，但分别初始化车辆状态、消息缓存和随机数流，避免跨运行状态泄漏。

## Stage I: causal identification

Stage I 检验来源可追溯的指定远端消息，是否在源风险的物理影响到达目标之前改变目标车辆的动作和风险负担。设 $S\in\{0,1\}$ 表示指定源风险是否存在，$C\in\{0,1\}$ 表示指定消息通道是否开放。$C=0$ 只屏蔽指定消息，不改变目标车辆的本地感知、安全约束、基础控制器或无关通信。

对消息 $q$，$D_{q,j}(t)$、$Q_{q,j}(t)$ 和 $Z_{q,j}(t)$ 分别表示消息是否已交付、是否通过来源/目标/类型/时效校验以及是否被目标控制器采用，并满足

$$
Z_{q,j}(t)\leq D_{q,j}(t)Q_{q,j}(t).
$$

令 $t_0$ 为试验触发时刻，$t_q^{\mathsf{gen}}$、$t_q^{\mathsf{send}}$、$t_{q,j}^{\mathsf{del}}$ 和 $t_{q,j}^{\mathsf{adopt}}$ 分别为消息生成、发送、交付和采用时刻。被采用消息必须满足

$$
t_0\leq t_q^{\mathsf{gen}}\leq t_q^{\mathsf{send}}
\leq t_{q,j}^{\mathsf{del}}\leq t_{q,j}^{\mathsf{adopt}}.
$$

令 $\varepsilon^{\mathsf u}>0$ 和 $\varepsilon^{\mathsf x}>0$ 分别为动作与状态容差，$t_j^{\mathsf u}$ 为目标动作相对配对基线首次超过 $\varepsilon^{\mathsf u}$ 的时刻，$\tau_j^{\mathsf P}$ 为屏蔽指定消息时源扰动经纯物理通道首次使目标状态差异超过 $\varepsilon^{\mathsf x}$ 的时刻。信息先行要求

$$
t_{q,j}^{\mathsf{adopt}}\leq t_j^{\mathsf u}<\tau_j^{\mathsf P}.
$$

对结果窗口 $\mathcal W=[t^{\mathsf{win}},t^{\mathsf{win}}+H)$，还要求

$$
t_{q,j}^{\mathsf{adopt}}\leq t^{\mathsf{win}}
<t^{\mathsf{win}}+H\leq\tau_j^{\mathsf P},
\qquad t_j^{\mathsf u}\in\mathcal W.
$$

设 $\omega$ 为完整四格配对单元，$R_{j,\omega}(s,c)$ 为目标车辆在处理条件 $(S=s,C=c)$ 下的窗口风险负担。单配对交互效应和总体效应定义为

$$
\begin{aligned}
\delta_{\omega}^{\mathsf{NL}}
&=[R_{j,\omega}(1,1)-R_{j,\omega}(1,0)]\\
&\quad-[R_{j,\omega}(0,1)-R_{j,\omega}(0,0)],\\
\Delta^{\mathsf{NL}}&=\mathbb E_{\omega}[\delta_{\omega}^{\mathsf{NL}}].
\end{aligned}
$$

对于数值越大表示风险越高的终点，负的 $\Delta^{\mathsf{NL}}$ 表示平均风险下降，正值表示上升。效应是否支持主张由预设实际重要效应边界和不确定性区间决定，不能只依据符号或显著性。

信息介导解释还要求四格处理前等效，指定消息完成生成、发送、交付、校验和采用链，采用后出现动作分化，动作和整个结果窗口早于物理影响，且错误来源、错误目标、错误类型、过期消息、仅交付未采用消息和虚假消息不产生同类作用链。源风险资格、消息生成、目标集合、采用规则、主要终点、容差、结果窗口、效应边界、样本量、排除规则和统计脚本均在确认性结果解锁前固定。Stage I 是受约束的因果识别，不包含控制策略优化。

## Stage II: safety-constrained control

Stage II 只在 Stage I 的主要效应、消息链和负对照同时达到预设门槛后启动。令 $\widetilde M_{j,t}\subseteq M_{j,t}$ 为通过来源、目标、类型和新鲜度校验的消息集合，$z_{j,t}=\pi^{\mathsf Z}(x_{j,t},\widetilde M_{j,t})$ 为采用策略形成的信息输入，$u_{j,t}=\pi^{\mathsf u}(x_{j,t},z_{j,t})$ 为动作策略，联合策略为 $\pi=(\pi^{\mathsf Z},\pi^{\mathsf u})$。

分别以 $J^{\mathsf{risk}}(\pi)$、$J^{\mathsf{act}}(\pi)$ 和 $J^{\mathsf{eff}}(\pi)$ 表示标准化风险、动作代价和效率代价。令 $\Pi^{\mathsf{safe}}$ 为满足车辆动力学、道路边界、碰撞规避、控制上下界以及消息来源和新鲜度约束的策略集合，则

$$
\pi^\star=\arg\min_{\pi\in\Pi^{\mathsf{safe}}}
\mathbb E\left[J^{\mathsf{risk}}(\pi)
+\lambda^{\mathsf u}J^{\mathsf{act}}(\pi)
+\lambda^{\mathsf e}J^{\mathsf{eff}}(\pi)\right].
$$

候选策略包括透明规则控制器、安全约束预测控制器和带独立安全过滤器的学习控制器。local-only、always-cautious 和 oracle 分别作为无远端消息、固定保守响应和完整先验信息参照。训练和超参数选择只使用开发场景与独立尾部风险发现集；Pareto 选择规则、代价权重和安全过滤器在留出场景解锁前固定。最终策略须相对 local-only 降低风险，相对 always-cautious 保持安全非劣并降低效率或舒适性代价，同时不恶化碰撞和尾部风险。

## Experimental design and data sources

仿真实验分为物理隔离识别、物理连通迁移和控制优化。物理隔离层使用两条拓扑不连通的走廊，指定消息是两条走廊之间唯一允许的信息输入。物理连通层使用具有明确跟驰、汇入和冲突关系的合流路网，并以消息屏蔽反事实、已知冲击响应和时序可达图共同估计 $\tau_j^{\mathsf P}$ 的保守下界。控制优化层改变消息采用和动作策略，不重新选择核心终点。

场景覆盖自由流、临界和拥堵状态，并改变风险类型、物理与信息拓扑、通信时延、抖动、丢包、消息年龄、交通需求和人类驾驶参数。核心风险族包括追尾制动、cut-in 或换道、合流让行和队列尾风险。至少一个场景族、一个风险类型和一组通信压力条件完整留出。

数据分为 calibration、confirmatory 和 locked holdout。Calibration 只用于数值误差、容差、效应边界、样本量、通信范围和场景覆盖，不进入正式效应估计。Confirmatory 数据在代码、配置、随机种子、主要终点和统计脚本冻结后生成。Locked holdout 在全部开发决策结束后解锁一次。仿真按场景族和随机种子分层，真实数据按地点、日期、行程或完整场景分层。

每个确认性单元运行完整的 $S\times C$ 四格。错误来源、错误目标、错误类型、过期消息、仅交付未采用消息和等计算量虚假消息构成负对照，本地预测、固定保守驾驶和 oracle 构成竞争基线。所有已启动运行进入 intention-to-run 分母，排除只依据处理分配前冻结的资格规则。

NGSIM、pNEUMA 和 INTERACTION 轨迹数据用于校核车辆匹配、风险事件提取和交通状态覆盖；Safety Pilot Model Deployment 数据用于校核发送机会、消息接收、时延、丢包和连续性。缺少消息采用或动作响应字段的数据不用于推断真实闭环因果效应。硬件在环或同步混合现实平台若被采用，则沿用同一消息生命周期和时钟审计，并与真实道路实证明确区分。

## Risk, action and temporal metrics

纵向追尾场景的主要终点为目标车辆在 $\mathcal W$ 内的积分 TTC 风险负担。令 $\varphi(j,t)$ 为目标车辆 $j$ 的有效前车映射，$h_{j,t}>0$ 为净间距，$\Delta v_{j,t}=v_{j,t}-v_{\varphi(j,t),t}$ 为闭合速度，则

$$
\operatorname{TTC}_j(t)=
\begin{cases}
h_{j,t}/\Delta v_{j,t}, & \varphi(j,t)\text{ 有效且 }\Delta v_{j,t}>0,\\
+\infty, & \text{其他情况}.
\end{cases}
$$

令 $\theta^{\mathsf{TTC}}>0$ 为经校准冻结的冲突阈值，则

$$
I_{j,\omega}^{\mathsf{TTC}}
=\frac{\Delta t}{H}\sum_{t\in\mathcal W}
\left(1-\frac{\operatorname{TTC}_j(t)}{\theta^{\mathsf{TTC}}}\right)_+.
$$

纵向补充终点包括最小 TTC、冲突持续时间、DRAC 和碰撞。合流、换道和交叉冲突使用 PET 或经解析轨迹验证的二维冲突时间。连续风险帧先合并为事件，再按事件、车辆和场景计量。跨风险类型比较时使用 calibration 数据冻结的尺度标准化，不直接平均不同量纲的指标。

动作分化同时检查控制命令和实际车辆响应。$t_j^{\mathsf u}$ 取动作差异首次超过 $\varepsilon^{\mathsf u}$ 并满足冻结持续时间的时刻，$\tau_j^{\mathsf P}$ 取源扰动沿合格物理时间路径使目标状态差异首次超过 $\varepsilon^{\mathsf x}$ 的时刻。舒适性由加速度、jerk 和控制饱和计量，效率由旅行时间、速度损失、吞吐、排放和队列外溢计量。硬安全终点包括碰撞、道路越界和不可行动力学状态；尾部结果包括预先指定的高分位风险、条件风险价值和暴露归一化的碰撞或近失率。

## Statistical analysis and uncertainty

独立重复单位为随机种子与场景族共同定义的完整四格配对 $\omega$；车辆、事件、消息、帧和车辆时间步是嵌套观测。主要分析估计 $\Delta^{\mathsf{NL}}$，并报告绝对效应、标准化效应、置信区间、每个配对的原始效应及方向比例。区间在 $\omega$ 层通过配对 cluster bootstrap 获得，配对置换或符号翻转检验作少分布假设核验，层级模型用于分离场景族和随机种子变异。

令 $\delta^{\mathsf{eq}}>0$ 为零效应等效边界，$\delta^{\mathsf R}>\delta^{\mathsf{eq}}$ 为风险的最小实际重要效应。前者由数值实现误差、轨迹重建误差和独立分析器差异的上界确定，后者同时受误差上界和最小可执行动作变化约束。有益效应要求 $\Delta^{\mathsf{NL}}$ 的区间越过 $-\delta^{\mathsf R}$。负对照采用双单侧等效检验，只有区间完全位于 $[-\delta^{\mathsf{eq}},\delta^{\mathsf{eq}}]$ 时才判为实际等效于零。

确认性样本量由独立 calibration 配对的方差上界、第一类错误率、目标功效和置信区间精度共同确定。碰撞等稀有事件按暴露量报告发生率和单侧上置信限，零观测不解释为零风险。预设次要终点按层级顺序检验，探索性矩阵使用错误发现率校正。机制完整集只作辅助分析，不能通过处理后排除替代 intention-to-run 主分析。主要结果由冻结分析脚本和独立只读分析器分别复算。

## Calibration, validation and reproducibility

确认性实验前，运行器、风险指标、消息状态机和物理路径算法分别接受解析真值、数值收敛和独立实现验证。解析轨迹覆盖匀速接近、制动、停车、换前车、无效间距、侧向侵入、交叉和合流；物理路径真值集覆盖无路径、单路径、多路径、时变路径和右删失。时间步逐级缩小复算，只有主要指标和到达时刻的差异落入 $\delta^{\mathsf{eq}}$ 且不改变资格分类时才固定 $\Delta t$。解析真值或关键路径分类失败时，不启动主要确认性实验。

稳健性实验保持消息语义和主要估计量不变，分别改变控制器、风险类型、物理与信息拓扑、交通需求、人类驾驶行为和通信条件。边界模型只使用处理前可得变量，并在留出拓扑解锁前生成预测。尾部风险先在开发用发现集中搜索可实现极端事件，再在生成规则、随机流和权重均冻结的独立压力集中评估。

每次正式运行分别记录车辆状态、源风险事件、消息生成与传输、校验与采用、控制命令、实际动作和风险结果，并以唯一运行标识、统一时间原点和配置版本关联。运行同时保存软件与依赖版本、环境锁、冻结配置、随机种子、数据与场景清单、完整命令、原始日志、纳入判定、协议偏离、失败原因及文件校验和。原始产物保持只读；修复或协议修订生成新版本，不覆盖旧批次。最小端到端试验在两个独立环境复算，确认性统计和关键资格分类由第二分析实现复核。
