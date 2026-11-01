# AAD P1 Task2 最终报告：研究决策同步与双传播因果模型深化

日期：2026-11-01
任务：AAD-P1-TASK2
状态：COMPLETED_WITH_LIMITATIONS

## 1. 完成内容

本次任务完成了：

1. 将研究者已确认的 D1–D10 方向同步为 Agreed，并把操作参数、阈值、精度和样本量继续标记为 Awaiting Researcher Decision；
2. 区分源事件分配 \(Z_S\)、通信策略分配 \(Z_C\)、实际源事件 \(S^*\) 和实际策略执行 \(C^*\)；
3. 将真实过程与观测过程分层，增加 SUMO 只读 Observer、日志、时钟、身份、测量误差和缺失机制；
4. 深化 Adoption encouragement、reduced form、IV/LATE 和 Action–Risk 候选识别框架；
5. 严格定义总体 \(T_R\)、\(T_P\)、\(T_U\) 关系和早期区域风险曲线的统计 onset；
6. 统一 H1–H4、D1–D10、DAG、estimand 与现有 Formal rho/P2/工程接口。

本次没有运行 SUMO、Pilot、Task9/18/19、现实数据采集、HIL/实车测试或 locked holdout，也没有修改生产代码和正式风险配置。

## 2. D1–D10 同步结果

研究者已确认的方向如下：

- D1：当前优先 SUMO，研究结论限定模型内；
- D2：当前 source-present 两臂区域风险 ITT，最终必须完成四格；
- D3：Formal P2 是优先源事件；安全受控扰动是独立机制域；
- D4：固定 cohort、region、window，使用区域总体 Formal rho/P2 风险；
- D5：SUMO 只读 Observer；现实扩展使用独立路侧观测；
- D6：首版只研究总体时间优先性；
- D7：单跳直达、不转发，同时保留物理网络干扰；
- D8：自动控制器，不纳入人类驾驶者心理采用；
- D9：先 Pilot，再规划 SESOI、功效和样本量；本次不运行 Pilot；
- D10：依据证据缺失收窄主张，保留失败边界研究路线。

仍未冻结：场景、车辆、区域和窗口边界，物理状态函数 \(\phi\)、阈值、持续性、路径资格、消息有效期、随机化概率、IV 是否实际部署、SESOI、α、power、ICC、样本量和停止规则。

正式记录见 [P1_TASK2_RESEARCHER_DECISIONS_20261101.md](P1_TASK2_RESEARCHER_DECISIONS_20261101.md)；P1 Task1 依赖登记已同步为“方向已确认、参数待定”。

## 3. DAG 深化结果

更新后的 [CAUSAL_DAG.md](CAUSAL_DAG.md) 现在区分：

- \(Z_S\)：源事件场景/实验分配；
- \(S^*\)：实际源事件状态和 Formal P2 资格；
- \(Z_C\)：通信策略分配；
- \(C^*\)：实际策略执行；
- \(D^*,V^*,A^*,U^{cmd,*},U^*\)：真实送达、验证、采用、命令和实际动作；
- \(\widetilde X,\widetilde D,\widetilde A,\widetilde U,\widetilde R,\widetilde T_P\)：观测或派生记录；
- \(Z_A\)：未来可选的 Adoption encouragement；
- \(Q_t\)：时钟、身份、遮挡、采样和测量质量。

DAG 通过 \(t\rightarrow t+1\) 节点表示物理和信息反馈，未把真实动态反馈画成同一时间层的环。Observer 只从真实过程生成记录，不参与消息处理、Adoption、控制命令或车辆动作。

## 4. Adoption IV 与 Action–Risk 识别

H2 现在明确区分：

\[
Z_A\rightarrow A^*\rightarrow U^{cmd,*}\rightarrow U^*.
\]

分别报告 adoption rate、鼓励 reduced-form ITT 和在条件成立时的 Wald/IV/LATE。IV 需要随机分配/独立性、relevance、exclusion restriction、monotonicity、well-defined treatment、正支持和干扰域条件。完整 adoption 日志不能自动证明排除限制；若条件不可辩护，只报告描述性链路和鼓励 ITT。

H3 现在明确 \(U^*\rightarrow X^*_{\mathcal T}\rightarrow Y^*_{\mathcal T}\)，并列出随机动作干预、有效 IV、longitudinal g-formula 和 interventional indirect effect 四类候选方法。普通回归、adopted/not-adopted 比较和命令日志不能自动得到动作介导因果效应。

## 5. 真实状态、观测误差和缺失

理论模型增加了

\[
\widetilde X_t=h_X(X^*_t,Q_t,\varepsilon_t),
\qquad
\widetilde Y=h_Y(Y^*,Q,\varepsilon).
\]

观测记录必须保留身份、时钟、质量、缺失原因、派生版本和来源哈希。身份错配、时钟偏差、遮挡、采样缺口、信息性缺失和安全中止不能被合并为独立噪声，也不能补零。

SUMO Observer 的“只读”只支持模型内测量独立；它不等同现实路侧传感器，也不提供现实物理真值。

## 6. 总体时间优先性

本次统一：

\[
T_U=\text{实际动作变化时间},\qquad
T_R=\text{总体区域风险因果效应 onset},\qquad
T_P=\text{普通物理状态到达时间}.
\]

在 source-present 两臂设计中，风险曲线差异写成

\[
\tau_R(t)
=E[\widetilde R_{\mathcal T}(t)\mid Z_C=1,Z_S=1]
-E[\widetilde R_{\mathcal T}(t)\mid Z_C=0,Z_S=1].
\]

给定未来确定的 SESOI \(\delta\)，总体 onset 的一般统计定义为

\[
\widehat T_R
=\inf\{t:UCB_{\mathrm{sim}}(\widehat\tau_R(t))<-\delta
\text{ 且在预定持续性下保持}\}.
\]

物理到达仍写成

\[
T_P=\inf\{t:\phi(X^*_{\mathcal T}(t))\text{ 满足预设状态、阈值和持续性}\}.
\]

只有在时间区间、同时置信带、删失和 witness 条件满足时，才可使用 \(T_R^{upper}<T_P^{lower}\)。总体到达分布不能升级为单个处理事件的反事实提前秒数。

## 7. H1–H4 统一结果

- H1 使用 assignment-level source-present ITT 或四格交互；
- H2 区分 Adoption rate、鼓励 ITT 和 IV/LATE；
- H3 区分动作响应与动作介导的区域风险因果效应；
- H4 使用总体 early-window risk effect 与无消息物理到达分布；
- H1 可独立支持，不要求 H2/H3 完全识别；
- H2 支持不自动推出 H3；
- H3 支持不自动推出 H4；
- H4 Unknown 或不成立不等于 H1 不成立。

支持、削弱/否定、处理链失败和 Unknown 继续分开报告。

## 8. 工程接口一致性

现有 formal_design.py 的四格、生命周期和处理前等价性接口继续复用；其配置字段表达实验条件，不是完整的 assignment/actual/observation 生产契约。stage_i_mechanism.py 的 first_action_change_time_s 只属于动作时间候选，不是 \(T_R\) 或 \(T_P\)。formal_risk_measurement.py 的 Formal rho、P2、固定窗口、未知上下界和车辆等权聚合未修改。protocol_lock.py 未调用，Protocol Lock 未生成。

## 9. 对 P2–P6 的影响

- P2：分别操作化 Formal P2、B 机制源事件、物理路径、Observer/witness、\(\phi\)、删失和时钟；
- P3：建立单跳消息链、自动控制器日志、Adoption/Command/Action 字段和可选 \(Z_A\) 评估；
- P4：冻结 cohort/region/window、区域风险时间曲线和动作测量；
- P5：确定四格补充设计、整场/簇随机化、interference mapping 和机制估计；
- P6：用 Pilot 估计方差、相关性、缺失和到达分布，再确定 SESOI、功效和样本量。

## 10. 交付与边界

新增：[P1_TASK2_RESEARCHER_DECISIONS_20261101.md](P1_TASK2_RESEARCHER_DECISIONS_20261101.md) 和本报告。更新：[THEORY_AND_CAUSAL_MODEL.md](THEORY_AND_CAUSAL_MODEL.md)、[CAUSAL_DAG.md](CAUSAL_DAG.md)、[ESTIMAND_SPECIFICATION.md](ESTIMAND_SPECIFICATION.md)、[HYPOTHESIS_AND_FALSIFICATION.md](HYPOTHESIS_AND_FALSIFICATION.md) 和 [P1_TASK1_DECISION_DEPENDENCY_REGISTER.md](P1_TASK1_DECISION_DEPENDENCY_REGISTER.md)，以及项目索引、注册表和 AI_CONTEXT。

Stage 0.5、Stage 0.6、Protocol Lock、Stage I 和 Stage 1.1 状态未改变。本报告不是实验授权、Protocol Lock 或现实交通科学结果。
