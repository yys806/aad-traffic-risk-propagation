# P2 Task8 — 参数候选建议

统一定义仍为[Task6 v0.4、27项](../definitions/README.md)。Task7原575完成/1失败、truth v2与359/47/0历史记录不改。所有Task8结果为校准/补充支持，Independent V种子消耗0；不是现实交通验证或AAD核心假设证据。

Formal A=0，独立Qualified=0，F0/总体TR-TP Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS；Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock BLOCKED；StageI READY_ENGINEERING_ONLY；Stage1.1 NOT_AUTHORIZED。

## 参数候选和容差

三层保留Task7中心：W9s、constant、θ1m/s、h1s、q.05s，Cohort coverage1/full-N、Macro w2s；仅重算中心、θ.5邻居、h2邻居，未重搜83配置。中心只可作为有限状态候选；每密度/源设计的有效检出、早报警、miss、Unknown和延迟见cell_metrics.csv。θ下降可能早于固定a1 truth，h增加可能损失短b1事件；不能只比较报警数。

R2固定MAX中，Micro三密度各24/24及时、High Cohort24/24、Medium/High Macro各24/24；Low Cohort/Macro与Medium Cohort没有真阳性分母。High LOCAL4的Micro24/24，而完整Cohort与Macro均24/24真阴性。中心在全部已实现阳性中没有及时漏检，各层逐轮负样本无FP；这是校准描述，不是参数认证。单个同质格24/24的点态单侧95%灵敏度下界也仅约88.3%，达不到95%规划要求，不能凭零失败通过。

θ=.5邻居在R2已实现MAX阳性与LOCAL4 Micro均出现早于固定a1状态onset的报警，及时有效数0/24；这里“早”相对于有限a1坐标，不等于真实微小物理影响不存在。h=2邻居在Medium MAX Macro和High LOCAL4 Micro均0/24及时（不足持续确认），其他已实现MAX格虽24/24但延迟约增加1s。故保留中心作为待验证候选，不推荐上述邻居全域替代；不能把固定中心的良好描述推成稳定区域。

ε_stab=.01/.025/.05/.1/.2和γ_int=.01/.05/.1/.2/.5仅是概率差容差情景，未冻结。配对差分按run，置信半径保留同质格n；Task7交互336格只复用原结果，不新增n。stability_tolerance_sensitivity/interaction_tolerance_sensitivity给出点估计与同时包络是否落入容差，ε/γ越宽越可能掩盖早检/短时漏检，不能凭不显著证明稳定。

附同一零差/零交互good假设下的Hoeffding充分样本成本（非零失败binomial样本量）：稳定差范围[-1,1]用8 log(2K/.05)/ε²，交互[-2,2]用32 log(2K/.05)/γ²；分配type-II边界也覆盖90%规划功效。无科学损失或独立物理误差依据，无法推荐唯一ε/γ，稳定区域Not established。

| 轮 | 层 | 密度 | 及时/真阳性 | FP/真阴性 | Unknown/分母 | 已检出delay中位上端s |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | cohort | low | 0/0 | 0/28 | 0/28 | Unknown |
| 1 | cohort | medium | 0/0 | 0/27 | 1/28 | Unknown |
| 1 | cohort | high | 28/28 | 0/16 | 0/44 | 1.10 |
| 1 | macro | low | 0/0 | 0/28 | 0/28 | Unknown |
| 1 | macro | medium | 11/11 | 0/16 | 1/28 | 2.10 |
| 1 | macro | high | 20/20 | 0/24 | 0/44 | 2.10 |
| 1 | micro | low | 12/12 | 0/16 | 0/28 | 1.05 |
| 1 | micro | medium | 19/19 | 0/8 | 1/28 | 1.05 |
| 1 | micro | high | 36/36 | 0/8 | 0/44 | 1.05 |
| 2 | cohort | low | 0/0 | 0/48 | 0/48 | Unknown |
| 2 | cohort | medium | 0/0 | 0/48 | 0/48 | Unknown |
| 2 | cohort | high | 32/32 | 0/40 | 0/72 | 1.05 |
| 2 | macro | low | 0/0 | 0/48 | 0/48 | Unknown |
| 2 | macro | medium | 32/32 | 0/16 | 0/48 | 2.10 |
| 2 | macro | high | 32/32 | 0/40 | 0/72 | 2.10 |
| 2 | micro | low | 32/32 | 0/16 | 0/48 | 1.05 |
| 2 | micro | medium | 32/32 | 0/16 | 0/48 | 1.05 |
| 2 | micro | high | 56/56 | 0/16 | 0/72 | 1.05 |

Cohort：中心仅适用于High已实现状态，Low/Medium不足，不推荐全密度冻结。Macro：Medium/High强长源已有状态支持，Low不足；局部脉冲域不认证。Micro：三密度native状态与High局部状态可审阅，但不是Qualified传播参数。三层都没有独立V，不推荐正式冻结；具体边界失效/延迟与邻域差异见cell_metrics/stability表。

## 源时间日志问题与W1–W9

Task7实际实现把v<源前速度与v!=getSpeedWithoutTraCI同时作为source onset。SUMO受4.5约束减速时两读数可完全相同：C_low_P22_00实际30.05s已减速，旧字段到31.75–31.8s才触发。Task8以命令时间下界及独立的源前加速度包络外原生状态签名上界记录区间，未用planned time代实际onset；签名缺失记Unknown，不称真实模型误差证书。

Documented Intent：actual physical source onset；Actual Implementation：上述AND条件延迟日志；Evidence：raw速度/加速度/native逐帧对照；Affected Files：旧executor及source-time/W6元数据；Conflict：可能错误拒绝首跳严格时序；Status: Awaiting Researcher Decision，仅指是否回溯修正Task7。本任务不改旧truth、旧代码和359/47/0历史统计。相同旧raw的独立诊断把Observed从47变为119，不是新样本、不是Qualified，更不能新增独立证据。

Task8 Potential=159、Observed=151、Qualified=0；native state positive=187是另一对象。witness_levels.csv逐跳保留W1实际leader、W2 ID、W3关系段、W4源区间、W5真实响应、W6严格区间先后、W7质量、W8竞争解释与W9同段连接。固定网络可排除信号/换道/合流/target控制/通信；剩余随机原生制动/共同原因和独立指定源归属金标准尚未认证，W8仍Unknown，未放宽。任何source claim全程弃权，0错误归属只是vacuuous，不证明归属灵敏度。
