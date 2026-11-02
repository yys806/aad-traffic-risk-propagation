# P2 Task8 — 阳性支持补充结果

统一定义仍为[Task6 v0.4、27项](../definitions/README.md)。Task7原575完成/1失败、truth v2与359/47/0历史记录不改。所有Task8结果为校准/补充支持，Independent V种子消耗0；不是现实交通验证或AAD核心假设证据。

Formal A=0，独立Qualified=0，F0/总体TR-TP Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS；Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock BLOCKED；StageI READY_ENGINEERING_ONLY；Stage1.1 NOT_AUTHORIZED。

## Task7不足的原始证据与三层差异

audit/task7_support_audit.csv逐单位复核全部575完成轨迹并核对原1728标签；一启动失败仍Unknown。planned C-P机会每密度120（四等级96+局部24），不是保证阳性；固定Cohort局部点原本要求阴性，A0状态阳性另列，不能把总192当计划真阳性。

- Low P22源速度确实降到2 m/s，最低加速度−4.5 m/s²，不能归为“源未执行”。代表run s1/s2/s3到a=1的时刻32.95/36.25/39.55s、位置3093.17/3091.15/3089.07m，均在Region上界3080m之外；固定域内最大下降约.0325，完整Cohort约.027–.031。表明当前剂量下响应与固定支持错位，不是观测缺失。此为已测试域限制，不证明所有可能源曲线都不行。
- Medium P22固定域内原生响应可达s8，峰值约5.94–6.08m/s；尚未到s14–s17，Cohort下降约.026–.031。Macro峰值仅.275–.279，车时权重下局部响应不足以使全域降1。Micro有阳性不要求其他层有阳性。
- High P22 Cohort下降7.78–7.86，Macro仅1.508–1.521，未达2a目标。task7_macro_dilution_decomposition.csv给出逐车D/V及车时权重，贡献和严格等于同域速度下降；.1s truth窗口与2s detector窗口分别保存，空间稀释与时间平滑不是三个独立证据。
- 原Plocal源2m/s×1s在High目标Micro峰值仅.358–.468，低于a*=1；没有可用b*=1状态，而非探测器漏检。Local pulse4m/s×1s与8m/s×1s是预列新设计，不改变Region/cohort。N0/N1完整原生面板中未出现a1b1状态，不能推出任意微小影响不存在。

实际leader和身份在完整运行中连续、目标setter=0。源端剂量、衰减、传播时间/域位置、全群体覆盖和Macro聚合共同影响支持；不把所有缺失都解释为“再加大强度”。因果归属仍需W8，以上是轨迹事实及有限工程解释。

| 缺失条件 | 补充前轨迹依据 | 本次核查问题 | 预列允许调整 |
|---|---|---|---|
| Low Cohort | 原固定群体下降约.03，前车a1响应越过Region | 固定群体能否在原Window响应 | LONG/MAX源条件 |
| Medium Cohort | 原a1响应到s8，未到s14–17 | 更长/强源是否传到完整群体 | LONG/MAX源条件 |
| Low Micro | 原首批a1响应位置大于3080m | 同域原生响应能否形成 | LONG/MAX源条件 |
| Low/Medium Macro | 局部响应的车时权重不足 | 同域平均能否达到a1b1 | LONG/MAX源条件 |
| High Macro 2a | 原峰值约1.51，小于2 | 更强源能否增大原域累计减速 | LONG/MAX源条件 |
| Local non-Cohort | 原局部2×1脉冲峰值低于a1 | 原域局部变化能否不改变完整Cohort | LOCAL4/LOCAL8源脉冲 |

以上均不改变Region、Cohort、Window、原生模型或a1b1；实际实现与失败见分设计结果表，未实现条件作为本次测试域限制停止。

## 一次有界补充及停止

R1预列100单位：三密度×LONG(8m/s×12s)/MAX(10m/s×12s)各8；N0/N1/A0各4/密度；High LOCAL4/LOCAL8(4/8m/s×1s)各8。速度下界0，不加第三档。仍用原Task7网络/vType、Krauss、禁换道、区域[1600,3080]、cohort s14–17、30–46监测和50s随访。请求1s slowDown不是实际1s完成；SUMO原生速度模式限制实际decel4.5、accel2.6，逐run核实，恢复按原曲线释放，不做target setter。

一次R1 TraCI启动失败S1_medium_MAX_01，0帧、0执行；失败seed119947188不重跑。45完成后停机，54个从未启动单位先留Unknown；原partial freeze/零帧占位完整存档。核查唯一归属本任务的orphan SUMO无监听socket后终止。根因Unverified，单进程为有限工程缓解；只首次执行原54个未用seed，无换seed/科学条件变化。后续不再修复迭代。该工程续跑不增加第三轮；原停止记录不抹除。

R1全部truth先封存，再按预注册的truth-only规则冻结R2：三密度MAX各24，High LOCAL4再24，三密度N0/N1/A0各8，共168。LOCAL8已使Cohort改变，不能当局部非Cohort阳性；选LOCAL4依据独立状态而非detector。R2全新namespace，以单进程执行，全部结果保留。R1/R2/可能V分别命名空间[20261102,8,101/202/303]；相同run跨层/参数仍同依赖block。

最大扰动后Low Cohort/Macro及Medium Cohort仍无阳性，已停止这些格；不移动Region/cohort、不延长监测域、不降a*/b*，不继续加seed或更强源。源恢复与目标恢复分别记录，50s前未恢复者right-censored，不外推恢复时刻。扰动较极端，不代表现实交通代表性。

| 轮 | 层 | 密度 | 计划分母 | Positive | Negative | Unknown | 2a*/b* |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | cohort | low | 28 | 0 | 28 | 0 | 0 |
| 1 | cohort | medium | 28 | 0 | 27 | 1 | 0 |
| 1 | cohort | high | 44 | 28 | 16 | 0 | 20 |
| 1 | macro | low | 28 | 0 | 28 | 0 | 0 |
| 1 | macro | medium | 28 | 11 | 16 | 1 | 0 |
| 1 | macro | high | 44 | 20 | 24 | 0 | 12 |
| 1 | micro | low | 28 | 12 | 16 | 0 | 12 |
| 1 | micro | medium | 28 | 19 | 8 | 1 | 19 |
| 1 | micro | high | 44 | 36 | 8 | 0 | 28 |
| 2 | cohort | low | 48 | 0 | 48 | 0 | 0 |
| 2 | cohort | medium | 48 | 0 | 48 | 0 | 0 |
| 2 | cohort | high | 72 | 32 | 40 | 0 | 32 |
| 2 | macro | low | 48 | 0 | 48 | 0 | 0 |
| 2 | macro | medium | 48 | 32 | 16 | 0 | 0 |
| 2 | macro | high | 72 | 32 | 40 | 0 | 32 |
| 2 | micro | low | 48 | 32 | 16 | 0 | 32 |
| 2 | micro | medium | 48 | 32 | 16 | 0 | 32 |
| 2 | micro | high | 72 | 56 | 16 | 0 | 32 |

## 各源设计实际实现

| 轮 | 密度 | 源设计 | 计划run | Cohort+ | Macro+ | Micro+ | Macro 2a+ | 失败/未知run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | high | A0 | 4 | 4 | 4 | 4 | 4 | 0 |
| 1 | high | LOCAL4 | 8 | 0 | 0 | 8 | 0 | 0 |
| 1 | high | LOCAL8 | 8 | 8 | 0 | 8 | 0 | 0 |
| 1 | high | LONG | 8 | 8 | 8 | 8 | 0 | 0 |
| 1 | high | MAX | 8 | 8 | 8 | 8 | 8 | 0 |
| 1 | high | N0 | 4 | 0 | 0 | 0 | 0 | 0 |
| 1 | high | N1 | 4 | 0 | 0 | 0 | 0 | 0 |
| 1 | low | A0 | 4 | 0 | 0 | 4 | 0 | 0 |
| 1 | low | LONG | 8 | 0 | 0 | 0 | 0 | 0 |
| 1 | low | MAX | 8 | 0 | 0 | 8 | 0 | 0 |
| 1 | low | N0 | 4 | 0 | 0 | 0 | 0 | 0 |
| 1 | low | N1 | 4 | 0 | 0 | 0 | 0 | 0 |
| 1 | medium | A0 | 4 | 0 | 4 | 4 | 0 | 0 |
| 1 | medium | LONG | 8 | 0 | 0 | 8 | 0 | 0 |
| 1 | medium | MAX | 8 | 0 | 7 | 7 | 0 | 1 |
| 1 | medium | N0 | 4 | 0 | 0 | 0 | 0 | 0 |
| 1 | medium | N1 | 4 | 0 | 0 | 0 | 0 | 0 |
| 2 | high | A0 | 8 | 8 | 8 | 8 | 8 | 0 |
| 2 | high | LOCAL4 | 24 | 0 | 0 | 24 | 0 | 0 |
| 2 | high | MAX | 24 | 24 | 24 | 24 | 24 | 0 |
| 2 | high | N0 | 8 | 0 | 0 | 0 | 0 | 0 |
| 2 | high | N1 | 8 | 0 | 0 | 0 | 0 | 0 |
| 2 | low | A0 | 8 | 0 | 0 | 8 | 0 | 0 |
| 2 | low | MAX | 24 | 0 | 0 | 24 | 0 | 0 |
| 2 | low | N0 | 8 | 0 | 0 | 0 | 0 | 0 |
| 2 | low | N1 | 8 | 0 | 0 | 0 | 0 | 0 |
| 2 | medium | A0 | 8 | 0 | 8 | 8 | 0 | 0 |
| 2 | medium | MAX | 24 | 0 | 24 | 24 | 0 | 0 |
| 2 | medium | N0 | 8 | 0 | 0 | 0 | 0 | 0 |
| 2 | medium | N1 | 8 | 0 | 0 | 0 | 0 | 0 |

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

完整分母/阴性/Unknown/恢复区间、源状态、a1/a2实际连续跨度、leader证据见support_realization与witness_levels。固定代表S2各密度MAX_00时间序列图位于本地outputs的figures/fixed_representative_state_traces.png，不作为额外独立样本。全局聚合只作描述，不把R1适应选择后R2合成独立V。

## 源时间日志问题与W1–W9

Task7实际实现把v<源前速度与v!=getSpeedWithoutTraCI同时作为source onset。SUMO受4.5约束减速时两读数可完全相同：C_low_P22_00实际30.05s已减速，旧字段到31.75–31.8s才触发。Task8以命令时间下界及独立的源前加速度包络外原生状态签名上界记录区间，未用planned time代实际onset；签名缺失记Unknown，不称真实模型误差证书。

Documented Intent：actual physical source onset；Actual Implementation：上述AND条件延迟日志；Evidence：raw速度/加速度/native逐帧对照；Affected Files：旧executor及source-time/W6元数据；Conflict：可能错误拒绝首跳严格时序；Status: Awaiting Researcher Decision，仅指是否回溯修正Task7。本任务不改旧truth、旧代码和359/47/0历史统计。相同旧raw的独立诊断把Observed从47变为119，不是新样本、不是Qualified，更不能新增独立证据。

Task8 Potential=159、Observed=151、Qualified=0；native state positive=187是另一对象。witness_levels.csv逐跳保留W1实际leader、W2 ID、W3关系段、W4源区间、W5真实响应、W6严格区间先后、W7质量、W8竞争解释与W9同段连接。固定网络可排除信号/换道/合流/target控制/通信；剩余随机原生制动/共同原因和独立指定源归属金标准尚未认证，W8仍Unknown，未放宽。任何source claim全程弃权，0错误归属只是vacuuous，不证明归属灵敏度。
