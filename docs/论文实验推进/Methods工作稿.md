# Methods

本文的模型、识别规则、控制目标、指标、统计方法和复现条件按投稿正文表述。只有需要由校准或正式实验确定的数值参数保留为符号，不在实验前填入结果。

## System model and two-stage framework

本文研究由车辆运动、物理交互和显式消息传递共同构成的联网交通系统。设车辆集合为 $\mathcal V=\{1,\ldots,N\}$，全体车辆状态和实际控制输入分别为 $X_t=\{x_{i,t}:i\in\mathcal V\}$ 和 $U_t=\{u_{i,t}:i\in\mathcal V\}$，物理交通图和显式信息图分别为 $G^{\mathsf P}(t)$ 和 $G^{\mathsf I}(t)$，截至时刻 $t$ 已生成且尚在协议生命周期内的消息集合为 $M_t$。共同系统模型写为

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

车辆 $i$ 的状态写为 $x_{i,t}=(\mathbf p_{i,t},v_{i,t},a_{i,t},\ell_{i,t})$，其中 $\mathbf p_{i,t}$、$v_{i,t}$、$a_{i,t}$ 和 $\ell_{i,t}$ 分别表示二维位置、速度、实际纵向加速度以及车道和道路边状态。$u_{i,t}^{\mathsf{cmd}}$ 为控制器请求命令，$u_{i,t}$ 为经过执行器和安全约束后实际施加的输入，$\xi_{i,t}$ 为外生随机输入。离散状态更新为

$$
x_{i,t+1}=f_i^{\mathsf{dyn}}\!\left(x_{i,t},u_{i,t},\xi_{i,t};G^{\mathsf P}(t)\right).
$$

仿真使用统一时钟 $t=n\Delta t$。每个时间步依次读取车辆状态和物理邻接关系，判定源风险事件，更新消息的生成、发送、交付、校验和采用状态，计算控制输入，再推进车辆运动。状态、消息、控制和风险记录共享运行标识、时间步和时间原点。$\Delta t$ 在数值收敛校准后固定。

每条消息记为 $m_{q,i,j,t}$，其中 $q$、$i$ 和 $j$ 分别为消息、来源车辆和目标车辆索引。协议允许发往目标车辆的候选消息集合为

$$
M_{j,t}^{\mathsf{cand}}=\{m_{q,i,j,t}\in M_t:(i,j)\in\mathcal E^{\mathsf I}(t)\}.
$$

候选集合表示消息已经生成且协议允许通信，不表示消息已经发送、交付或可供控制器使用。消息载荷包含消息标识、源事件标识、源车辆和目标车辆标识、风险类型、风险摘要及生成时间。指定远端消息只构成目标自动驾驶车辆的附加输入，不关闭本地感知、基础控制器或安全约束。

源区域和目标区域分别记为道路状态空间中的 $\mathcal R^{\mathsf S}$ 和 $\mathcal R^{\mathsf T}$，并满足 $\mathcal R^{\mathsf S}\cap\mathcal R^{\mathsf T}=\varnothing$。源车辆 $i$ 的合格风险事件必须在 $\mathcal R^{\mathsf S}$ 内触发，目标车辆 $j$ 在处理前基线和结果窗口内必须属于 $\mathcal R^{\mathsf T}$。各场景的道路边、车道、纵向坐标、路线组件、拓扑距离和车辆资格在实验设计中固定。

物理传播采用时间展开图审计。图中同时保留同一车辆相邻时间步之间的运动延续关系，以及跟驰、合流或冲突产生的车辆间直接作用关系。$\tau_j^{\mathsf P}$ 表示物理影响可能到达目标的最早保守边界，而不是事后观察到的实际传播时刻。双走廊只有在道路拓扑断开、无跨走廊车辆转移、无共享控制状态且无合格时间路径时，才允许取 $\tau_j^{\mathsf P}=+\infty$；物理连通场景使用独立校准后的保守下界。

位置、速度和加速度分别使用米、米每秒和米每二次方秒。不存在有效前车或字段不可观测时，派生量记为缺失，不以零值替代。每辆车在单次运行中使用唯一身份；车辆离开后不得继续被物理边、消息或风险记录引用。四格由同一冻结快照分别启动，消息缓存和运行状态互不共享。主随机种子按背景交通、人类驾驶扰动、通信和控制器等子系统派生为命名随机流；四格使用相同的对应随机流，处理触发的额外调用不得推进其他子系统的随机序列。

## Stage I: causal identification

Stage I 检验本文定义的“类超距作用”：开放指定消息通道是否使来源可追溯的远端风险信息在普通物理影响到达前改变目标车辆的实际动作和风险负担。主效应使用全部预先登记的四格配对单元，不按消息采用或动作分化筛选；后两者用于机制审计。

本文通过物理图与信息图分离、消息生命周期审计、四格反事实配对和时间先行判定共同检验 $\mathcal P_1$。物理图审计源扰动是否能够沿道路和车辆交互逐跳到达目标；信息图记录消息是否生成、发送、交付、通过来源、目标和时效校验并被采用；四格配对只改变源风险和指定消息通道，保持处理前交通状态、背景输入和非处理控制逻辑一致；时间审计比较消息采用、目标动作分化和物理影响到达的先后顺序。错误来源、错误目标、过期消息、仅交付未采用消息和等计算量虚假消息用于检验替代解释。

设 $S\in\{0,1\}$ 表示指定源风险是否存在，$C\in\{0,1\}$ 表示指定消息通道是否开放。$C=0$ 只屏蔽指定消息，不改变目标车辆的本地感知、基础控制器、安全约束或无关通信。对消息 $q$，$D_{q,j}(t)$、$Q_{q,j}(t)$ 和 $Z_{q,j}(t)$ 分别表示对目标车辆 $j$ 的交付、联合校验和采用状态，三者均属于 $\{0,1\}$，并满足 $Z_{q,j}(t)\leq D_{q,j}(t)Q_{q,j}(t)$。有效消息链满足

$$t_0\leq t_q^{\mathsf{gen}}\leq t_q^{\mathsf{send}}\leq t_{q,j}^{\mathsf{del}}\leq t_{q,j}^{\mathsf{adopt}}.$$

对完整四格配对单元 $\omega$，令 $R_{j,\omega}(s,c)$ 表示目标车辆 $j$ 在处理条件 $(S=s,C=c)$ 下的窗口风险负担。单元交互效应和总体效应为

$$\delta_{\omega}^{\mathsf{NL}}=[R_{j,\omega}(1,1)-R_{j,\omega}(1,0)]-[R_{j,\omega}(0,1)-R_{j,\omega}(0,0)],\qquad \Delta^{\mathsf{NL}}=\mathbb E_{\omega}[\delta_{\omega}^{\mathsf{NL}}].$$

这是开放指定通道的意向运行效应：消息未采用或动作未分化的正式运行仍保留在分母中。令 $\delta^{\mathsf{eq}}$ 表示可视为零效应的最大容许偏差，令 $\delta^{\mathsf R}$ 表示具有实际意义的最小风险变化幅度，并要求 $0\leq\delta^{\mathsf{eq}}<\delta^{\mathsf R}$。对于数值越大表示风险越高的终点，负值表示风险下降，正值表示风险增加。

令 $t_0$ 为共同触发时刻，$t_q^{\mathsf{gen}}$、$t_q^{\mathsf{send}}$、$t_{q,j}^{\mathsf{del}}$ 和 $t_{q,j}^{\mathsf{adopt}}$ 分别表示消息生成、发送、交付和采用时刻。令 $\varepsilon^{\mathsf u}>0$ 和 $\varepsilon^{\mathsf x}>0$ 分别为实际输入差异和状态差异的判定容差。$t_j^{\mathsf u}$ 表示目标实际输入首次明显分化的时刻，$t_j^{\mathsf x}$ 只用于校核物理传播估计。未在观察期内检测到分化时，时间分析记为右删失，固定窗口机制判定记为尚未通过，但运行仍保留在主效应中。

$$
\begin{aligned}
t_j^{\mathsf u}&=\inf\{t\geq t_0:\|u_{j,t}(1,1)-u_{j,t}(1,0)\|>\varepsilon^{\mathsf u}\},\\
t_j^{\mathsf x}&=\inf\{t\geq t_0:\|x_{j,t}(1,0)-x_{j,t}(0,0)\|>\varepsilon^{\mathsf x}\}.
\end{aligned}
$$

令 $\mathcal W=[t^{\mathsf{win}},t^{\mathsf{win}}+H)$ 为风险窗口。令 $\operatorname{Reach}_{G^{\mathsf P}}(i,j;I)$ 表示区间 $I$ 内是否存在时间单调物理路径。$\Sigma_{\omega}^{\mathsf{pre}}(s,c)$ 为处理前冻结状态，$\doteq_{\varepsilon^{\mathsf{pre}}}$ 表示离散字段和身份映射完全一致、连续状态差异不超过冻结容差。令 $e_\omega$ 为指定源风险事件，$\mathcal M_{\omega}^{\mathsf{src}}$ 为与该事件、源车、目标车和处理版本绑定的消息标识集合。$\mathcal K^{\mathsf{NC}}$ 和 $\Delta_k^{\mathsf{NC}}$ 分别为负对照集合及其同类效应。Stage I 分别检验效应是否存在和是否形成安全收益：

$$
\begin{aligned}
\mathcal P_1:\quad
&\text{估计 }\Delta^{\mathsf{NL}}=\mathbb E_\omega[\delta_\omega^{\mathsf{NL}}];\\
&\mathsf{NLE}^{\mathsf{exist}}:\ |\Delta^{\mathsf{NL}}|\geq\delta^{\mathsf R};\\
&\mathsf{NLE}^{\mathsf{safe}}:\ \Delta^{\mathsf{NL}}\leq-\delta^{\mathsf R};\\
\mathrm{s.t.}\quad
\text{(9a)}\quad &\mathcal R^{\mathsf S}\cap\mathcal R^{\mathsf T}=\varnothing;\\
\text{(9b)}\quad &\operatorname{Reach}_{G^{\mathsf P}}(i,j;[t_0,t^{\mathsf{win}}+H])=0;\\
\text{(9c)}\quad &\Sigma_{\omega}^{\mathsf{pre}}(s,c)\doteq_{\varepsilon^{\mathsf{pre}}}\Sigma_{\omega}^{\mathsf{pre}}(s',c')\\
&\hspace{2.1em}\forall(s,c),(s',c')\in\{0,1\}^{2};\\
\text{(9d)}\quad &\exists q\in\mathcal M_{\omega}^{\mathsf{src}}:\ Z_{q,j}(t_{q,j}^{\mathsf{adopt}})=1;\\
\text{(9e)}\quad &Z_{q,j}(t)=1\Rightarrow D_{q,j}(t)=1\quad\forall t;\\
\text{(9f)}\quad &Z_{q,j}(t)=1\Rightarrow Q_{q,j}(t)=1\quad\forall t;\\
\text{(9g)}\quad &t_0\leq t_q^{\mathsf{gen}}\leq t_q^{\mathsf{send}};\\
\text{(9h)}\quad &t_q^{\mathsf{send}}\leq t_{q,j}^{\mathsf{del}};\\
\text{(9i)}\quad &t_{q,j}^{\mathsf{del}}\leq t_{q,j}^{\mathsf{adopt}};\\
\text{(9j)}\quad &t_{q,j}^{\mathsf{adopt}}\leq t_j^{\mathsf u};\\
\text{(9k)}\quad &t_j^{\mathsf u}<\tau_j^{\mathsf P};\\
\text{(9l)}\quad &t_{q,j}^{\mathsf{adopt}}\leq t^{\mathsf{win}};\\
\text{(9m)}\quad &t^{\mathsf{win}}+H\leq\tau_j^{\mathsf P};\\
\text{(9n)}\quad &\left|\Delta_{k}^{\mathsf{NC}}\right|\leq\delta^{\mathsf{eq}}
\quad\forall k\in\mathcal K^{\mathsf{NC}}.
\end{aligned}
$$

约束 (9a)--(9c) 是设计与处理前可比性条件；(9d) 将被归因消息绑定到指定源事件、源车、目标车和处理版本；(9e)--(9i) 审计交付、校验和生命周期；(9j)--(9m) 检查采用、实际输入和完整风险窗口是否先于物理到达边界；(9n) 在确认性实验层面逐类检验负对照等效性。

令 $E_{\omega}^{\mathsf{tech}}=1$ 表示四格均按冻结配置完成且主要结局可重建。运行完整性和机制状态分别为

$$
\begin{aligned}
A_{\omega}^{\mathsf{run}}=\mathsf{valid}&\Longleftrightarrow E_{\omega}^{\mathsf{tech}}=1\text{ 且 (9a)--(9c) 成立},\\
A_{\omega}^{\mathsf{mech}}=\mathsf{pass}&\Longleftrightarrow\text{(9d)--(9m) 成立}.
\end{aligned}
$$

全部预先登记的正式单元构成意向运行集合 $\Omega^{\mathsf{ITR}}$。$A_{\omega}^{\mathsf{mech}}$ 和任何处理后风险结果不得用于移出该集合；工程失败和结局缺失按预先指定的缺失数据与界限分析处理。只有效应界限、设计条件、机制审计和负对照均达到门槛时，才支持相应的 $\mathsf{NLE}^{\mathsf{exist}}$ 或 $\mathsf{NLE}^{\mathsf{safe}}$ 主张。

## Stage II: safety-constrained control

Stage II 仅在 $\mathcal P_1$ 的主要效应、消息链和负对照均达到门槛后启动。它回答控制器如何使用经 Stage I 验证的信息，并限制由此产生的安全、舒适性、效率和尾部代价；其结果不能反过来证明 $\mathcal P_1$。

物理连通场景使用领先裕度 $L_{\omega}^{\mathsf P}=\tau_j^{\mathsf P}-(t^{\mathsf{win}}+H)$。绑定指定源事件的消息在实际输入分化前被采用且 $L_{\omega}^{\mathsf P}>0$ 时，该运行通过信息先行审计。未通过的正式运行仍进入意向运行分析，只是不支持信息先行归因。

消息 $q$ 的年龄为 $t-t_q^{\mathsf{gen}}$，$T^{\mathsf{fresh}}$ 为最大允许年龄。合格消息集合为

$$
\widetilde M_{j,t}=\{m_{q,i,j,t}\in M_{j,t}^{\mathsf{cand}}:D_{q,j}(t)=1,Q_{q,j}(t)=1,0\leq t-t_q^{\mathsf{gen}}\leq T^{\mathsf{fresh}}\}.
$$

采用策略 $\pi^{\mathsf Z}$ 对每条合格消息给出二元采用决定；已采用消息组成 $M_{j,t}^{\mathsf{adopt}}$ 并聚合为 $z_{j,t}$。动作策略 $\pi^{\mathsf u}$ 生成请求命令 $u_{j,t}^{\mathsf{cmd}}$，安全执行映射 $g_j^{\mathsf{safe}}$ 再形成实际输入 $u_{j,t}$。联合策略为 $\pi=(\pi^{\mathsf Z},\pi^{\mathsf u})$。

对运行 $\omega$，$J_\omega^{\mathsf{risk}}(\pi)$、$J_\omega^{\mathsf{act}}(\pi)$ 和 $J_\omega^{\mathsf{eff}}(\pi)$ 分别表示风险、动作与舒适性以及通行效率代价。令 $\mathbb P^{\mathsf{eval}}$ 为正式评估前冻结的运行分布。总体代价和完整向量定义为

$$\mathbf J(\pi)=\bigl(J^{\mathsf{risk}}(\pi),J^{\mathsf{act}}(\pi),J^{\mathsf{eff}}(\pi),J^{\mathsf{tail}}(\pi)\bigr),\qquad
J^{\mathsf r}(\pi)=\mathbb E_{\omega\sim\mathbb P^{\mathsf{eval}}}\!\left[J_\omega^{\mathsf r}(\pi)\right].$$

这里先说明四类代价在 $\mathcal P_2$ 中的作用；具体数学定义和缺失处理在后文展开，尾部风险采用 CVaR 聚合。

主问题最小化 $J^{\mathsf{risk}}(\pi)$，约束限制 $J^{\mathsf{act}}(\pi)$、$J^{\mathsf{eff}}(\pi)$ 和 $J^{\mathsf{tail}}(\pi)$。在一组冻结的代价上界上重复求解 $\mathcal P_2$ 得到 Pareto 前沿，即不能继续改善某一目标而不使至少另一目标恶化的候选边界。最终选择规则在锁定留出集解锁前固定。

$$
\begin{aligned}
\mathcal P_2:\quad
&\pi^\star\in\arg\min_{\pi}
J^{\mathsf{risk}}(\pi);\\
\mathrm{s.t.}\quad
\text{(11a)}\quad &x_{j,t+1}=f_j^{\mathsf{dyn}}(x_{j,t},u_{j,t},\xi_{j,t};\\
&\hspace{7.2em}G^{\mathsf P}(t)),\\
\text{(11b)}\quad &u_{j,t}^{\mathsf{cmd}}=\pi^{\mathsf u}(x_{j,t},z_{j,t})\quad\forall t;\\
\text{(11c)}\quad &Z_{q,j}(t)=\pi_q^{\mathsf Z}(x_{j,t},m_{q,i,j,t})\in\{0,1\};\\
\text{(11d)}\quad &M_{j,t}^{\mathsf{adopt}}=\{m_{q,i,j,t}\in\widetilde M_{j,t}:Z_{q,j}(t)=1\};\\
\text{(11e)}\quad &z_{j,t}=\operatorname{Agg}^{\mathsf{msg}}(M_{j,t}^{\mathsf{adopt}}),\quad\operatorname{Agg}^{\mathsf{msg}}(\varnothing)=\mathbf 0;\\
\text{(11f)}\quad &Z_{q,j}(t)=1\Rightarrow D_{q,j}(t)=1;\\
\text{(11g)}\quad &Z_{q,j}(t)=1\Rightarrow Q_{q,j}(t)=1;\\
\text{(11h)}\quad &Z_{q,j}(t)=1\Rightarrow0\leq t-t_q^{\mathsf{gen}}\leq T^{\mathsf{fresh}};\\
\text{(11i)}\quad &u_{j,t}=g_j^{\mathsf{safe}}(x_{j,t},u_{j,t}^{\mathsf{cmd}})\in\mathcal U_j;\\
\text{(11j)}\quad &x_{j,t}\in\mathcal X_j^{\mathsf{safe}}\quad\forall t;\\
\text{(11k)}\quad &J^{\mathsf{act}}(\pi)\leq\overline J^{\mathsf{act}},\\
\text{(11l)}\quad &J^{\mathsf{eff}}(\pi)\leq\overline J^{\mathsf{eff}},\\
\text{(11m)}\quad &J^{\mathsf{tail}}(\pi)\leq\overline J^{\mathsf{tail}}.
\end{aligned}
$$

约束 (11a)--(11e) 连接动力学、逐消息采用、已采用集合、控制信息和请求命令；(11f)--(11h) 要求采用消息已经交付、校验且未过期；(11i)--(11j) 将请求命令转为安全的实际输入；(11k)--(11m) 限制动作、效率和尾部风险代价。

仅本地、固定保守和理想信息控制器分别提供无远端消息基线、整体保守解释和不可部署上界。吞吐、排放、误报警和不必要采用作为预先指定的次要运行指标报告，不替代四类核心代价或硬安全判定。若 $\mathcal P_2$ 未通过，只收缩控制价值主张，不推翻 $\mathcal P_1$。

## Experimental design and data sources

独立重复单位是预先登记的“场景族 $\times$ 主随机种子”完整四格配对。四格从同一快照启动并使用一一对应的命名随机流，只改变 $S$ 和 $C$。$S=1$ 触发指定源风险事件，$S=0$ 不触发；$C=1$ 开放指定协议栈，在 $S=1$ 时允许事件绑定风险消息，在 $S=0$ 时只运行等负载无风险占位消息；$C=0$ 屏蔽指定消息但保留本地感知、安全约束和无关通信。

正式运行前冻结校准集、开发集、确认集和锁定留出集。校准集确定测量规则和阈值，开发集用于调参，确认集只执行预注册 Stage I 分析，锁定留出集在全部规则固定后只解锁一次。

源事件和目标车辆分别按 $\mathcal R^{\mathsf S}$、$\mathcal R^{\mathsf T}$ 及冻结资格规则确定。每个场景在运行登记表中固定道路和车道范围、区域边界、拓扑距离、交通需求、车辆进入与退出、源扰动、背景驾驶模型、目标控制器、通信模型、仿真步长、观察期和风险窗口，不依据确认性结果改写。

每次运行至少产生五类逻辑记录：车辆状态、源事件与标准化发射量、消息生命周期、控制器实际采用的输入与输出、风险和安全结果。每条记录带有运行标识、场景标识、随机种子、车辆或消息标识和仿真时间戳，并由 manifest、provenance 和失败账本关联。消息的生成、发送、交付、字段校验、采用和失效分别记录；$C=0$ 只屏蔽指定消息，不关闭本地感知、基础控制器、安全约束或无关通信。负对照包括错误来源、错误目标、错误风险类型、过期消息、仅交付未采用消息、等计算量的虚假消息和 sham channel。真实轨迹与通信数据只用于其字段直接支持的测量、分布或可观测性校核；缺少消息采用和动作响应字段时，不推断真实闭环因果效应。

## Risk, action and temporal metrics

风险终点按冲突类型预先选择。追尾风险的确认性主终点使用归一化积分 TTC 负担；交叉、合流、换道和队列尾场景分别在校准阶段冻结适配指标、方向、阈值、观测掩码和结果窗口。不同物理含义的原始 TTC、PET 或冲突量不直接相加，也不在结果解锁后更换主要指标。以下给出 TTC 主终点的正式定义。令 $\varphi(j,t)$ 为时刻 $t$ 目标车辆 $j$ 的有效前车，$h_{j,t}>0$ 为净间距，$\Delta v_{j,t}=v_{j,t}-v_{\varphi(j,t),t}$ 为闭合速度；当不存在有效前车、间距或速度不可观测时，设观测掩码 $m_{j,t}^{\mathsf{TTC}}=0$，不以零替代。对有效观测，

$$
\operatorname{TTC}_{j,t}=
\begin{cases}
h_{j,t}/\Delta v_{j,t},&\Delta v_{j,t}>0,\\
+\infty,&\Delta v_{j,t}\leq 0.
\end{cases}
$$

令 $\theta^{\mathsf{TTC}}>0$ 为校准后冻结的风险阈值，令 $[y]_+=\max(y,0)$。单个时间步的归一化风险负担为

$$
\rho_{j,t}^{\mathsf{TTC}}=
\begin{cases}
1,&\text{发生碰撞或 }\operatorname{TTC}_{j,t}=0,\\
1-\operatorname{TTC}_{j,t}/\theta^{\mathsf{TTC}},
&0<\operatorname{TTC}_{j,t}<\theta^{\mathsf{TTC}},\\
0,&\operatorname{TTC}_{j,t}\geq\theta^{\mathsf{TTC}}.
\end{cases}
$$

在采用 TTC 主终点的运行中，$R_{j,\omega}(s,c)$ 就是对应处理格下的 $I_{j,\omega}^{\mathsf{TTC}}$；其他风险类型只在预先指定的指标替换后同步替换 $R$。若结果窗口内有效观测时长大于零，则

$$
J_{\omega}^{\mathsf{risk}}(\pi)=I_{j,\omega}^{\mathsf{TTC}}(\pi)
=\frac{\sum_{t\in\mathcal W_\omega}m_{j,t}^{\mathsf{TTC}}
\rho_{j,t}^{\mathsf{TTC}}\Delta t}
{\sum_{t\in\mathcal W_\omega}m_{j,t}^{\mathsf{TTC}}\Delta t}.
$$

无有效观测的运行记为不确定，不赋予零风险。碰撞、越界和不可恢复的安全事件同时作为硬安全结果记录，不因风险负担的平均值下降而被抵消。其他风险类型使用相同的“有效观测掩码—单位内归一化—预先冻结聚合”结构，并在跨类型比较前只比较标准化效应。

动作代价使用实际加速度和 jerk。令 $m_{j,t}^{\mathsf a}$ 为二者同时可观测的掩码，$\bar a^{+}$ 和 $\bar a^{-}$ 为加速和减速边界，$e_{j,t}^{+}=[a_{j,t}-\bar a^{+}]_+$、$e_{j,t}^{-}=[-a_{j,t}-\bar a^{-}]_+$。令 $\dot a_{j,t}=(a_{j,t}-a_{j,t-1})/\Delta t$，$\bar a^{\mathsf{jerk}}$ 为其参考尺度。给定非负且和为一的权重 $w_{+}^{\mathsf a},w_{-}^{\mathsf a},w^{\mathsf{jerk}}$，时刻动作代价为

$$
c_{j,t}^{\mathsf a}=
w_{+}^{\mathsf a}\left(\frac{e_{j,t}^{+}}{\bar a^{+}}\right)^2+
w_{-}^{\mathsf a}\left(\frac{e_{j,t}^{-}}{\bar a^{-}}\right)^2+
w^{\mathsf{jerk}}\left(\frac{\dot a_{j,t}}{\bar a^{\mathsf{jerk}}}\right)^2.
$$

动作与舒适性总体代价为

$$
J_{\omega}^{\mathsf{act}}(\pi)=
\frac{\sum_{t\in\mathcal W_\omega}m_{j,t}^{\mathsf a}
c_{j,t}^{\mathsf a}\Delta t}
{\sum_{t\in\mathcal W_\omega}m_{j,t}^{\mathsf a}\Delta t}.
$$

边界、参考尺度、权重和动作缺失规则在校准锁定前确定，确认性结果不得按策略表现重新调整。

效率代价记录旅行时间、停车时间、平均速度损失和任务未完成。令 $T_{\omega}^{\mathsf{obs}}(\pi)$ 为实际旅行时间；未在观察期内完成时取冻结上限 $T^{\mathsf{max}}$，并令 $F_{\omega}^{\mathsf{inc}}(\pi)=1$。$T_{\omega}^{\mathsf{ref}}$ 为冻结参考旅行时间，$T_{\omega}^{\mathsf{stop}}(\pi)$ 为停车时长，$\bar v_{\omega}(\pi)$ 和 $\bar v_{\omega}^{\mathsf{ref}}$ 为策略与参考平均速度。给定和为一的非负权重 $w^{\mathsf{time}},w^{\mathsf{stop}},w^{\mathsf{speed}},w^{\mathsf{inc}}$，

$$
\begin{aligned}
J_{\omega}^{\mathsf{eff}}(\pi)
={}&w^{\mathsf{time}}\left[
\frac{T_{\omega}^{\mathsf{obs}}(\pi)-T_{\omega}^{\mathsf{ref}}}
{T_{\omega}^{\mathsf{ref}}}\right]_+\\
&+w^{\mathsf{stop}}\frac{T_{\omega}^{\mathsf{stop}}(\pi)}
{T_{\omega}^{\mathsf{obs}}(\pi)}
+w^{\mathsf{speed}}\left[
1-\frac{\bar v_{\omega}(\pi)}{\bar v_{\omega}^{\mathsf{ref}}}\right]_+
+w^{\mathsf{inc}}F_{\omega}^{\mathsf{inc}}(\pi).
\end{aligned}
$$

候选策略未完成任务不能作为缺失排除；冻结参考运行不可重建时，整个配对进入预设缺失数据界限分析。

尾部风险不以平均值代替。令 $\alpha\in(0,1)$ 为 CVaR 置信水平，对应上尾概率为 $1-\alpha$；$\eta$ 为阈值变量。则

$$
J^{\mathsf{tail}}(\pi)=
\inf_{\eta\in\mathbb R}
\left\{\eta+\frac{1}{1-\alpha}
\mathbb E_{\omega\sim\mathbb P^{\mathsf{eval}}}\!\left[\left[J_{\omega}^{\mathsf{risk}}(\pi)-\eta\right]_+\right]\right\}.
$$

四类代价均在同一冻结评估分布 $\mathbb P^{\mathsf{eval}}$ 上计算并按“越小越好”解释。$\alpha$、参考运行、权重、阈值和评估分布在正式评估前冻结。

消息采用、实际输入分化和完整风险窗口均早于 $\tau_j^{\mathsf P}$ 时，运行通过信息先行审计；未通过的正式运行仍保留在意向运行分母中。

## Statistical analysis and uncertainty

四格配对单元 $\omega$ 是最小分析单位。令 $\mathcal G$ 为预先登记的场景族集合，$\Omega_g\subseteq\Omega^{\mathsf{ITR}}$ 为场景族 $g$ 的全部正式单元，$n_g=|\Omega_g|$，$w_g^{\mathsf{scn}}\geq0$ 为冻结权重且和为一。主要效应估计为

$$
\begin{aligned}
\widehat{\Delta}^{\mathsf{NL}}&=
\sum_{g\in\mathcal G}w_g^{\mathsf{scn}}
\left(\frac{1}{n_g}\sum_{\omega\in\Omega_g}\widehat{\delta}_{\omega}^{\mathsf{NL}}\right),\\
\widehat{\delta}_{\omega}^{\mathsf{NL}}&=
\bigl[\widehat R_{j,\omega}(1,1)-\widehat R_{j,\omega}(1,0)\bigr]\\
&\quad-\bigl[\widehat R_{j,\omega}(0,1)-\widehat R_{j,\omega}(0,0)\bigr].
\end{aligned}
$$

场景权重在确认集解锁前固定。置信区间按场景族分层重采样完整四格单元；共享主随机种子的跨场景单元作为同一簇重采样。主要效应同时报告点估计、95\%置信区间、场景分母、工程失败、机制失败和右删失数量。

95\% 置信区间整体低于 $-\delta^{\mathsf R}$ 或高于 $+\delta^{\mathsf R}$ 时支持 $\mathsf{NLE}^{\mathsf{exist}}$；只有单侧 95\% 上界低于 $-\delta^{\mathsf R}$ 时才支持 $\mathsf{NLE}^{\mathsf{safe}}$。正向越界必须报告为风险增加。每类负对照须独立落入 $[-\delta^{\mathsf{eq}},\delta^{\mathsf{eq}}]$；不把不显著当作等效。

缺失观测不作零值填补。碰撞、越界、控制器中止或任务未完成按冻结失败终点或最不利可实现界限计入；日志损坏等工程故障仍保留在意向运行分母，并同时给出预设缺失数据模型和保守界限。若结论依赖排除这些单元，确认性判定不通过。

Stage II 只使用开发集和预先指定的稀有事件发现集选择策略。候选策略必须满足 (11a)--(11m)，并相对仅本地控制器达到风险改善，相对固定保守控制器在安全和尾部风险上不劣，且在动作或效率至少一项越过实际意义边界。锁定留出集只用于一次性验证。

## Calibration, validation and reproducibility

校准阶段只确定测量规则、容差、参考尺度、代价权重、CVaR 置信水平、效应边界、样本量和运行器参数，不估计确认性主效应。风险测量在解析轨迹上验证 TTC、DRAC、PET 或适配指标、碰撞判定和缺失掩码；真实轨迹校准集只校核测量与分布。

时间展开物理路径算法使用独立实现或解析图例校验最早到达时刻，覆盖无路径、单路径、多路径、车辆离开、跨走廊隔离和右删失情形。消息状态机分别测试生成、发送、丢弃、延迟、交付、校验失败、采用和过期；控制器日志必须能由消息状态和车辆状态重建实际采用与动作输出。离散时间步 $\Delta t$ 通过数值收敛检查后固定，改变 $\Delta t$ 不得改变主要路径、消息链和结论方向。

每个运行保存代码提交标识、环境锁、配置和数据/随机种子 manifest、开始与结束时间、退出码、五类逻辑表、审计摘要、原始产物校验和及失败原因。修复 bug 后生成新版本并重跑全部受影响运行；不得用修复后的结果静默替换旧产物。分析脚本从只读原始表重建状态、消息生命周期、动作、风险和主估计量，并在结果解锁前通过一份独立实现或人工可审计样例复核。Results 报告验证结果、适用域和失败账本，Methods 只规定规则和复现条件。
