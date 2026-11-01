# P1 Task1 最终报告：P0 收口与理论模型、因果结构正式建立

日期：2026-11-01
任务：P1-TASK1
状态：COMPLETED_WITH_LIMITATIONS

## 1. 本次完成内容

本次任务完成 P0 Task1–3 的正式收口，并把已有双传播审计推进为一套可计算、可审计、可证伪的 P1 理论与因果框架：

- P0 收口与 P1 入口记录；
- Physical Interaction Network 与 Information Propagation Network；
- 联合动态系统、消息生命周期和控制器—命令—实际动作分层；
- 完整时间事件语义 \(T_G,T_S,T_D,T_V,T_A,T_C,T_U,T_R,T_P\)；
- 时间展开的双传播因果 DAG；
- 四格交互、source-present 两臂 ITT、干扰潜在结果和时间优先性对象；
- H1–H4 的数学定义、观测量、识别条件、证伪条件和 Unknown/失败分类；
- P0 Task3 D1–D10 的 P1 依赖登记。

本次没有新增 SUMO/TraCI 运行、现实数据采集、HIL/实车测试、locked holdout 访问、Protocol Lock 或 Stage 1.1。

## 2. P0 收口结论

Task1 已完成文献与创新性审计；Task2 已完成双传播因果可识别性、干扰和证据契约审计；Task3 已完成最小消息干预与独立物理基准的可行性设计。三项工作均保留为 Completed with limitations，不新增 P0 Task4。

已建立的事实包括：信息传播更快、V2X/BLOS 警告改变行为、非局部控制、交通网络传播、TTC/DRAC/PET 风险代理和干扰因果方法均已有先行。AAD 潜在的独立增量是：在同源源事件、固定目标区域和独立物理基准下，审计生成—传输—送达—验证—采用—动作链，估计干扰感知的区域风险效应，并比较风险效应与普通物理到达分布。该增量仍是 Proposal。

Task3 的建议是封闭测试场整场事件随机化、独立路侧测量和随机 no-message 事件；当前现实确认性启动仍是 NO-GO，现实资源、控制器/车辆接口、物理 witness、SESOI、方差和正式样本量为 Unknown。SUMO 只能承担模型内机制和接口准备，HIL 可作为人类响应路线，二者都不能替代现实因果证据。

## 3. 核心理论模型

物理网络和信息网络分别定义为

\[
G_P(t)=(V,E_P(t)),\qquad G_I(t)=(V,E_I(t)).
\]

两张网络可以共享节点，但物理边和通信边分开记录。联合系统为

\[
x_{t+1}=F_P(x_t,u_t,G_P(t),\xi_t;H,S),
\]

\[
m_{t+1}=F_I(m_t,x_t,G_I(t),A,\eta_t;H,S),
\]

\[
d_{i,t}=\pi_i(x_{i,t},m_{i,t},q_{i,t};\theta_i),
\quad
u^{cmd}_{i,t}=g_i(d_{i,t},x_{i,t},m_{i,t}),
\quad
u_{i,t}=\mathcal E_i(u^{cmd}_{i,t},b_{i,t},\omega_{i,t}).
\]

其中 \(d\) 是控制器采用/拒绝决策，\(u^{cmd}\) 是命令，\(u\) 是考虑安全覆盖和执行限制后的实际输入。区域风险保持现有 Formal rho/P2 语义，固定目标集合、区域和窗口的候选结果写成

\[
Y_e(a)=\frac{1}{|C_e|}\sum_{i\in C_e}\frac{1}{|W_e|}
\int_{W_e} b_{ie}(t;a)\,dt.
\]

本次没有改变 rho=exp(-TTC/tau)、Formal P2 阈值、固定窗口积分、未知贡献上下界或车辆等权聚合实现。

## 4. 因果识别结论

四格对象为

\[
\tau_{SC}
=E[Y(1,1)-Y(1,0)]-E[Y(0,1)-Y(0,0)].
\]

P0 Task3 的 source-present 两臂对象为

\[
\tau_{\mathrm{ITT}}^{S=1}=E[Y(1,1)-Y(1,0)].
\]

二者满足

\[
\tau_{SC}=\tau_{\mathrm{ITT}}^{S=1}-\tau_{\mathrm{ITT}}^{S=0},
\]

所以两臂结果不能单独识别源×通信交互。网络干扰下潜在结果必须写成 \(Y_i(\mathbf A)\) 或 \(Y_e(\mathbf A_e)\)；整场 policy effect、cluster ITT、direct effect 和 spillover effect 只有在相应随机化单位、干扰域、exposure mapping 和正支持条件下才有定义。

Delivery、Verification、Adoption、Command 和 Actual Action 都是处理后变量。观察到消息送达、采用或动作变化不能自动产生中介因果效应；需要随机鼓励、IV、principal strata 或满足条件的 interventional mediation 设计。

时间优先性使用

\[
T_R<T_P
\]

及不确定性版本

\[
T_R^{upper}<T_P^{lower}.
\]

随机化可以识别总体 policy effect 和 no-message 物理到达分布，但不能自动观察同一个处理事件的 \(T_P(0)\)，也不能直接识别每个事件的提前秒数或跨世界联合概率。因此总体 early-window effect、总体物理到达分布和个体事件 counterfactual precedence 必须分开报告。

## 5. H1–H4

| 假设 | 核心对象 | 支持条件 | 证伪/削弱条件 |
|---|---|---|---|
| H1 信息干预效应 | source-present ITT 或四格交互 | 可审计分配、固定 cohort/region/window、Formal 风险结果和干扰边界 | 识别条件满足且效应小于 SESOI 或方向相反；测量失败则 Unknown |
| H2 控制器采用机制 | 采用鼓励/IV 对命令和实际动作的效应 | 送达、验证、采用、命令、执行全链路；正支持与 IV 条件 | 送达验证充分但采用接近零或采用后无命令/动作差异；日志缺失则不可识别 |
| H3 动作—风险机制 | 有识别支持的 \(Y(U=u_1)-Y(U=u_0)\) 或干预性间接效应 | 动作有外生来源、物理 exposure 和区域结果可测、干扰域明确 | 有效动作干预下区域效应小于 SESOI/方向相反；只有个体动作则 Unknown |
| H4 物理到达前的信息效应 | \(T_R^{upper}<T_P^{lower}\) 或总体 early-window 版本 | 独立时间化物理 witness、预定风险 onset、无消息到达分布、时钟和删失规则 | 时间区间重叠、物理到达不晚于风险效应或缺少 witness；此时为否定/Unknown，不是“没有物理传播” |

“不显著”“证据支持效应小于 SESOI”“处理链失败”和“不可识别”在报告中保持分开。

## 6. 仍需研究者决定的事项

D1–D10 全部保持 Proposed / Awaiting Researcher Decision。P1 只保留一般化方案，不冻结：

- 首版平台与主张层级；
- 两臂与四格主次关系；
- Formal P2 或安全受控扰动的 Source Event；
- Target Cohort、Region、Window 和主要风险终点；
- 物理到达状态函数、阈值、持续性和路径规则；
- 总体时间优先性还是个体事件主张；
- 整场、车辆级或两阶段随机化和干扰处理；
- 自动控制器或人类驾驶者；
- SESOI、α、power、样本量和多重比较；
- 资源或证据失败时的主线收窄。

这些决定的依赖、后果和推荐登记在 [P1_TASK1_DECISION_DEPENDENCY_REGISTER.md](P1_TASK1_DECISION_DEPENDENCY_REGISTER.md)。

## 7. 下一阶段建议

P2–P4 应围绕 P1 定义补齐源事件/物理 witness、消息采用证据和区域风险测量；P5 再冻结随机化和干扰 estimand；P6 依据独立 pilot 参数制定 SESOI、功效和样本量。任何阶段都应保留失败、Unknown、删失和适用域边界。完成这些前，不生成 Protocol Lock 或启动 Stage 1.1。

## 8. 交付文件

- [P0_CLOSEOUT_AND_P1_ENTRY_NOTE.md](../P0/P0_CLOSEOUT_AND_P1_ENTRY_NOTE.md)
- [THEORY_AND_CAUSAL_MODEL.md](THEORY_AND_CAUSAL_MODEL.md)
- [CAUSAL_DAG.md](CAUSAL_DAG.md)
- [ESTIMAND_SPECIFICATION.md](ESTIMAND_SPECIFICATION.md)
- [HYPOTHESIS_AND_FALSIFICATION.md](HYPOTHESIS_AND_FALSIFICATION.md)
- [P1_TASK1_DECISION_DEPENDENCY_REGISTER.md](P1_TASK1_DECISION_DEPENDENCY_REGISTER.md)

## 9. 当前阶段边界

Stage 0.5、Stage 0.6、Protocol Lock、Stage I 和 Stage 1.1 状态未改变。本报告是理论与因果模型交付，不是正式协议、实验授权或科学结果报告。
