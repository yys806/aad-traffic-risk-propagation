# Jerath et al. (2024) — ZOI 原文精读

日期：2026-11-02；状态：FULL_TEXT_READ（30页期刊正文，§1–7、图表、作者贡献及书目；外置S1/S2推导附录本轮未全文阅读）。证据类型：作者模型结果，不是AAD数据。

## 出处与版本
Kshitij Jerath, Vikash V. Gayah, Sean N. Brennan. *Mitigating delay due to capacity drop near freeway bottlenecks: Zones of influence of connected vehicles*. PLOS ONE 19(6), e0301188, 2024-06-05. DOI：[10.1371/journal.pone.0301188](https://doi.org/10.1371/journal.pone.0301188)。Zotero ZAHRLZ56 / 原文HSQNJHQL；SHA256 `b33774ece0893cf71b73ea1173e141303792827d12c112e82215f6e2b3ed11c0`。Zhihong (Arry) Yao为editor，不是作者。

## 问题、模型与假设
研究“在何处、向谁发送信息，配合什么车辆控制，才会改善交通宏观状态”。§3将车辆位置/速度的microstate映射到用户选择的macrostate；本研究选单次固定瓶颈的总车辆延误。§4–5单车道、禁止超车/换道、三角基本图/LWR、一次capacity drop、速度瞬时变化。CV1遇到队列后发送警报；CV2假定瞬时接收，按预设策略减速到额定瓶颈状态速度vE，再于下游恢复。控制动作和信息采用是模型规定，不是独立实测生命周期。

## 数学方法与实验设置
§3 Eq(1–3)：车辆延误由virtual arrival/departure时刻定义，宏观状态为受影响车辆延误之和。§5比较无CV控制D0和有CV控制D1，ΔD=D1−D0。Null horizon是适用区间内ΔD=0的边界；event horizon由控制所产生交通状态与原有状态到达瓶颈时序关系给出。ZOI为指定控制使ΔD<0的空间范围；并非任何物理影响的可达边界。

Table2例：qC=1800veh/h、qA=1620、qF=535.5、qG=900、qI=765（15%下降），vF=90km/h，jam density=110veh/km。是代表性参数和解析扫描，不是随机化交通实验。Fig5/6例ZOI为相对CV1距离约0.5–1.7km；特定位置节省5.23veh-h（19.05%），另一位置增加4.30veh-h（15.66%）。这些是作者情境结果，不可迁移为AAD门槛。§6.2–6.5改变qG/qA、qA/qC、qF/qI并讨论300m通信距离/均匀分布下的hopping和最低渗透率。

## 作者结论及明确局限
§7认为信息与事件触发控制可在有限ZOI改善总延误，ZOI随交通状态、控制策略和宏观量而变化；区外动作可能无益甚至有害。§6.1明确单车道、特定控制、单次瓶颈激活、固定参数、三角基本图、瞬时通信、均匀CV分布等强假设；多车/多车道/多策略需后续扩展。没有区域安全风险RCT，没有消息verification/adoption实测，没有同一合格源事件的随机消息开关总体。

## 独立分析与 AAD 重叠
Fact：信息→特定车辆动作→宏观交通结果及空间有效范围已经是明确已有工作。不能把该联系、非局部响应、ZOI概念本身登记为AAD创新。作者的no-CV baseline同时改变控制角色，不能称为AAD source-present随机no-message F0。作者空间horizon依模型/目标而定，不是TP的独立观测真值；“无正延误收益”不等于“无物理影响”。

Inference：这是本轮最接近AAD信息/控制/空间边界的工作，应在未来论文相关工作直接对照。AAD可能区别在同源资格、可审计消息生命周期、实际采用/执行、区域风险ITT及独立普通物理参考的联合识别；此区别目前仅研究设计/Hypothesis，不是已完成结果。

## 可复用与不可照搬
复用micro→macro映射、控制/状态依赖边界、报告不利结果和明示强假设。不可照搬其数值、瞬时接收、全局物理排除、以延误改善代替风险因果效应，亦不能用ZOI替代W1–W9或把解析对照当经验随机识别。
