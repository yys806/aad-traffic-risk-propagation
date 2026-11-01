# AAD P1 因果估计对象与识别条件

日期：2026-11-01
状态：**P1_TASK2_REFINED_ESTIMANDS**。研究者已确认 SUMO 优先、source-present 两臂当前主分析、最终四格、单跳通信和自动控制器；操作参数与正式统计准入仍待决定。

## 1. 结果和潜在结果的共同定义

令 \(\mathcal T=(C,R,W)\) 表示处理前预先定义的目标车辆集合、道路区域和观察窗口。对策略分配 \(a\)，令

\[
Y_e(a)=Y_{\mathcal T,e}(a)
\]

为事件 \(e\) 的区域风险结果。候选主结果沿用现有 Formal rho/P2 语义：固定窗口内按现有贡献边界积分，再对预列目标车辆等权聚合。未知测量保留上下界；不能把缺失、未观测或不可靠贡献补成零。

在网络干扰下，完整写法是

\[
Y_e(\mathbf A_e),\qquad
Y_{i,e}(\mathbf A_e),
\]

其中 \(\mathbf A_e\) 是同一事件/簇/整网的处理向量。只有在明确干扰域和 exposure mapping 后，才可写成 \(Y_i(a_i,g_i)\)。

当前首版把分配和实际状态分开：

\[
Z_S\to S^*,\qquad Z_C\to C^*\to (D^*,V^*,A^*,U^{cmd,*},U^*).
\]

SUMO 只读 Observer 产生 \(\widetilde X,\widetilde R,\widetilde T_P\) 等模型观测；它不成为消息策略或控制器的处理变量，也不等同现实路侧 witness。

## 2. 长期规划的四格交互效应

令 \(s\in\{0,1\}\) 表示源事件是否存在，\(c\in\{0,1\}\) 表示通信策略是否启用：

\[
Y_{\mathcal T}(s,c).
\]

四格交互效应为

\[
\begin{aligned}
\tau_{SC}
={}&E[Y_{\mathcal T}(1,1)-Y_{\mathcal T}(1,0)]\\
&-E[Y_{\mathcal T}(0,1)-Y_{\mathcal T}(0,0)].
\end{aligned}
\]

它表示源事件和通信策略之间的因果交互，而不是“采用者的效应”或消息传播速度。如果风险越低越好，\(\tau_{SC}<0\) 只表示方向上与风险下降一致；显著性、SESOI、适用域和科学意义仍需独立判断。

四格设计在以下条件下有额外信息：

- \(S=0\) 提供通信策略在无源事件背景下的基线效应；
- \(S=1\) 提供消息策略在源事件存在时的效应；
- 两者之差检验源事件是否改变消息策略的效果。

四格设计要求四个 cell 共享处理前配置、稳定的 pair/event 关系和已知分配概率。formal_design.py 的配置校验只证明工程契约，不证明真实科学识别。

## 3. P0 Task3 的 source-present 两臂 ITT

在只随机化通信策略且固定 \(S=1\) 的设计中：

\[
\tau_{\mathrm{ITT}}^{S=1}
=E[Y_{\mathcal T}(1,1)-Y_{\mathcal T}(1,0)].
\]

它能回答：在预先定义的源事件总体中，启用与不启用通信策略的 assignment-level 区域结果差异。它不要求所有消息都成功送达或被采用，安全覆盖、处理失败和链路失败都应保留在 ITT 中。

两臂与四格的关系是

\[
\tau_{SC}
=\tau_{\mathrm{ITT}}^{S=1}-\tau_{\mathrm{ITT}}^{S=0},
\quad
\tau_{\mathrm{ITT}}^{S=0}=E[Y(0,1)-Y(0,0)].
\]

因此，两臂结果等于四格交互只有在额外假设 \(\tau_{\mathrm{ITT}}^{S=0}=0\) 或该项已由独立设计证明时才成立。两臂不能单独识别源×通信交互，也不能推出 source-absent 下没有通信效应。

## 4. 干扰下的候选效应对象

| 对象 | 定义/直觉 | 需要的设计条件 | 当前定位 |
|---|---|---|---|
| Individual treatment effect | \(Y_i(a_i=1)-Y_i(a_i=0)\) | SUTVA 或可证明的局部干扰域 | 通常不适用于开放交通网络 |
| Direct effect | 固定邻域 exposure \(g\) 下 \(Y_i(1,g)-Y_i(0,g)\) | 预定义 exposure mapping、正支持、域内分配可见 | 候选，留给 P5 |
| Spillover effect | 固定自身处理下 \(Y_i(a,g_1)-Y_i(a,g_0)\) | 两阶段/整网随机化与可测物理/信息 exposure | 候选，不能从未采用车差异直接得出 |
| Total policy effect | 整场策略 \(a=\pi_1\) 与 \(\pi_0\) 的 \(E[Y_e(\pi_1)-Y_e(\pi_0)]\) | 事件/簇/整网 assignment，域外泄漏可界定 | 最适合作为首版区域 ITT 的一般表述 |
| Cluster-level ITT | \(E[Y_g(1)-Y_g(0)]\) | cluster 是随机化和独立性单位；簇间干扰受限 | 可用于封闭场/session 设计 |

车辆数不等于独立样本数。若一个事件内多车共享状态、驾驶者或消息，推断至少按事件/session/簇聚类。

## 5. 网络随机化与 exposure mapping

三类方案有不同识别对象：

1. **整场事件随机化**：识别整场 policy ITT，保留网络内所有 direct 与 spillover 的总和；最少依赖车辆级 SUTVA。
2. **车辆级随机化**：只有在干扰域、处理向量和 exposure mapping 完整可见时，才能估计 direct/spillover；未知域外影响会破坏普通 A/B 解释。
3. **两阶段随机化**：先随机簇/场景策略，再随机簇内鼓励或接收资格；可为 exposure-specific 或 adoption/complier 对象提供支持，但需要每个联合分配有正概率。

对事件 \(e\)，可定义信息 exposure \(g_I\)（可达、送达、消息版本）和物理 exposure \(g_P\)（路径连接、邻车动作、物理前沿）。两者不能用同一标签代替。

## 6. 消息采用与中介对象

Delivery \(D\)、Verification \(V\)、Adoption \(A\)、Command \(U^{cmd}\) 和实际动作 \(U\) 都是处理后的变量。观察到

\[
D=1\;\not\Rightarrow\;A=1,\qquad
A=1\;\not\Rightarrow\;U\text{ 改变}.
\]

直接比较 adopted 与 not-adopted 车辆会选择处理后状态；即使日志完整，也只证明事件可观测，不自动识别自然中介效应。可考虑的额外对象包括：

- 随机 adoption encouragement 的 ITT；
- 在有效 IV 和排除限制下的 complier effect；
- 预定义 principal strata；
- 有时间顺序和中介混杂控制的 interventional indirect effect。

这些对象均需新的设计、假设和正支持，不能在 P1 把 adopted 子集平均差写成机制因果效应。

### 6.1 Adoption encouragement、reduced form 与 IV/LATE

若未来增加随机化的 adoption encouragement 或工具变量 \(Z_A\)，机制链写成

\[
Z_A\longrightarrow A^*\longrightarrow U^{cmd,*}\longrightarrow U^*.
\]

需要区分三个对象：

1. **Adoption rate**：在已送达/已验证消息中，\(P(A^*=1\mid D^*=1,V^*=1)\)。这是链路描述量，不是采用的因果效应。
2. **Reduced-form effect**：鼓励对实际动作的 assignment-level ITT，
\[
\tau_{\mathrm{RF}}
=E[U^*\mid Z_A=1]-E[U^*\mid Z_A=0].
\]
3. **IV/LATE**：在工具变量条件成立时，采用对动作的局部平均因果效应，
\[
\tau_{\mathrm{IV}}
=\frac{E[U^*\mid Z_A=1]-E[U^*\mid Z_A=0]}
{E[A^*\mid Z_A=1]-E[A^*\mid Z_A=0]}.
\]

\(\tau_{\mathrm{IV}}\) 需要随机分配/独立性、相关性（第一阶段非零）、排除限制、单调性、well-defined adoption 和正支持。网络干扰下还需要对整场分配向量、信息/物理 exposure 和域外泄漏作相应限制；普通车辆级 Wald 比值不能自动解决干扰。

排除限制尤其需要审查：\(Z_A\) 只能通过 \(A^*\) 影响 \(U^*\)，不能同时改变消息内容、延迟、安全覆盖、控制器其他模式或物理邻车动作。完整 adoption 日志不能证明排除限制。若条件不能辩护，只报告 adoption rate、日志审计和鼓励 reduced form，不声称 LATE。本任务不新增 adoption encouragement 实验。

### 6.2 Action–Risk 的候选识别对象

动作机制的理论路径为

\[
U^*\longrightarrow X^*_{\mathcal T}\longrightarrow Y^*_{\mathcal T}.
\]

普通动作—风险回归或 adopted/not-adopted 比较不识别动作介导因果效应，因为动作受处理前状态、控制器状态、网络邻车动作和时间变化暴露影响。候选方法和条件如下：

| 方法 | 目标对象 | 关键识别条件 | 当前定位 |
|---|---|---|---|
| 随机化动作干预/鼓励 | 动作 assignment effect 或动作 ITT | 动作鼓励有正支持，排除限制可辩护，区域结果固定 | 候选；本任务不运行 |
| 有效 IV | \(U^*\) 对 \(Y^*\) 的 complier effect | 相关性、排除限制、单调性、干扰域和稳定处理 | 候选；不能假定 |
| longitudinal g-formula | 时间变化动作策略下的风险结果 | 顺序可交换性、时间变化混杂可测、正支持、正确模型/稳健估计 | 候选；需 P4–P6 |
| interventional indirect effect | 通过动作分布改变的风险效应 | 中介混杂条件、干预性中介定义、干扰和时间顺序明确 | 候选；不等于自然中介 |

H1 的区域 ITT 可以在 H2/H3 机制尚未完全识别时独立报告。不能把 H1 ITT 代数拆成 H2 与 H3 两个因果效应，也不能把命令日志或动作差异自动升级为中介因果证据。

### 6.3 测量误差、Observer 与缺失

对真实结果 \(Y^*\) 和观测结果 \(\widetilde Y\)，报告

\[
\widetilde Y=h_Y(Y^*,Q,\varepsilon).
\]

Observer、控制器日志和风险提取各自保留 quality、clock、identity、missing_reason 和 derivation_version。误差可能造成 attenuation、身份错配、时间区间和信息性缺失；不能默认它只增加独立同分布噪声。缺失/Invalid/Unobservable/Unknown 保留上下界或删失，不补零。

## 7. 时间优先性对象

### 7.1 事件级时间变量

\(T_U\) 是配对轨迹/执行记录中的实际动作变化时间，\(T_R\) 是消息策略引起的总体区域风险因果效应 onset，\(T_P\) 是普通物理状态的独立到达时间。三者不能互相替代。stage_i_mechanism.py 的 first_action_change_time_s 只对应 \(T_U\) 的工程候选。

\[
T_R<T_P.
\]

考虑检测、时钟和统计不确定性，实际判定应采用

\[
T_R^{upper}<T_P^{lower}.
\]

\(T_R\) 必须来自预定早期风险曲线、同时置信带和持续性规则；第一次观察到风险下降、第一次命令变化、第一次 \(T_U\) 或消息生成时间都不能直接替代它。\(T_P\) 必须由独立时间化物理 witness 或当前 SUMO 只读 Observer 的模型内记录给出，并明确适用域。

### 7.1.1 \(T_R\) 的统计定义

在当前 source-present 两臂设计中，先对预先定义的时间网格估计

\[
\tau_R(t)
=E[\widetilde R_{\mathcal T}(t)\mid Z_C=1,Z_S=1]
-E[\widetilde R_{\mathcal T}(t)\mid Z_C=0,Z_S=1].
\]

风险越低越好。给定未来由研究者确定的 SESOI \(\delta\)，总体风险效应 onset 的一般定义为

\[
\widehat T_R
=\inf\left\{t\in\mathcal H:
UCB_{\mathrm{sim}}\bigl(\widehat\tau_R(t)\bigr)<-\delta
\ \text{并在预定持续性规则下保持}\right\}.
\]

其中 \(UCB_{\mathrm{sim}}\) 是覆盖整个时间网格的同时上置信带。当前不冻结 \(\delta\)、\(\alpha\)、时间网格、持续时长、基线风险、horizon 或多重检验规则。若没有通过预定质量和持续性条件，\(\widehat T_R\) 为 Unknown，而不是把第一次下降当成 onset。

### 7.2 总体层面可识别的时间对象

在无消息随机事件中，可估计总体物理到达分布

\[
F_0(t\mid H,Z_S=1)
=P\{\widetilde T_P\le t\mid Z_C=0,Z_S=1,H\},
\]

其中 \(H\) 是处理前分层，\(\widetilde T_P\) 的质量、区间删失和 witness 类型必须一起报告。若使用 \(T_P(0)\) 记号，它表示该无消息总体下的潜在到达分布，不表示已观察到同一处理事件的反事实路径。早期窗口效应可写成

\[
\tau_R(H)=E[Y_{\mathcal T}(Z_C=1;H)-Y_{\mathcal T}(Z_C=0;H)\mid Z_S=1]
\]

或对每个 \(h\) 的时间曲线差 \(\tau_R(h,t)\)。若预注册 horizon \(H^\star\) 内的 \(F_0(H^\star)\) 上界低于允许的物理到达比例 \(\eta\)，且 \(\widehat\tau_R(h,t)\) 的同时置信带/持续性判定支持早期差异，只能表述为“在总体上物理状态通常尚未达到的窗口存在策略效应”。这仍是总体层面的 early-window effect，不是每个处理事件的提前秒数。

### 7.3 个体事件的反事实限制

单个处理事件的 \(T_P(0)\) 没有被同时观察。随机化识别边际的处理效应和到达分布，但不自动识别

\[
T_P(0)\text{ for the treated event},\quad
P\{T_R(1)<T_P(0)\},\quad
T_P(0)-T_R(1).
\]

两个 arm 的边际分布不能配成同一事件的跨世界提前秒数。区间重叠、删失或跨世界联合分布不可辨识时，时间优先性必须报告 Unknown / 未分离。

## 8. 缺失和界限

对每个 arm 保存有效、未知、删失、安全中止和泄漏记录。若 \(Y\) 只有区间 \([L,U]\)，策略效应的识别区间可写为

\[
[\;L_1-U_0,\;U_1-L_0\;],
\]

再另行报告随机化抽样不确定性。识别区间不等同置信区间；区间跨越零表示在当前测量质量下不能排除方向差异。

物理到达的完整观测、右删失和区间删失需要分别使用相应方法；信息性缺失不能机械套用普通生存估计。缺少物理 witness 时，\(T_P\) 相关对象保持 Unknown。

## 9. 估计对象与后续阶段的对应关系

| P1 对象 | 所需后续阶段 | P1 只规定的内容 |
|---|---|---|
| 四格 \(\tau_{SC}\) | P5 | 变量语义、关系和额外基线需求 |
| source-present \(\tau_{\mathrm{ITT}}^{S=1}\) | P4/P5 | assignment-level 区域效应，不把它升级为交互 |
| direct/spillover/total policy | P5 | 干扰域、mapping、正支持条件 |
| adoption/action 机制效应 | P3/P5 | 处理后变量限制和所需鼓励/IV |
| \(F_0(t)\)、总体早期效应 | P2/P5 | 物理 witness、删失和共同时间框架 |
| \(T_R^{upper}<T_P^{lower}\) | P2–P6 | 时间判定条件，不冻结阈值/置信水平 |

## 10. 当前不冻结的事项

SUMO 优先、当前 source-present 两臂 ITT、最终四格、单跳通信、自动控制器、固定 cohort/region/window 原则和总体时间优先性已经确认。仍未冻结的是 Source Event 的具体实例、Target Cohort/Region/Window 的数值边界、物理到达 \(\phi\)、随机化概率、interference exposure mapping、Adoption IV 是否实际部署、SESOI、样本量和多重比较规则。P1 只提供可复用的定义和识别边界。
