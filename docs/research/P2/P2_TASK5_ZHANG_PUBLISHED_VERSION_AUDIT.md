# P2 Task5 — Zhang 正式期刊版本审计

日期：2026-11-02。状态：FULL_TEXT_READ_PUBLISHED：正式原文18页文本已完整读取；正式PDF pp5/6/11/13及预印本PDF p14已视觉复核，正式/旧附件与双语附件均已读回核验。本文是版本证据，不修改任何AAD正式检测器。

## 1. 原文身份

用户提供 D:/下载/1-s2.0-S0191261526001347-main.pdf；18页，10,752,791 bytes，SHA256 1672d0c1bb4207da2f542096bacb4d5e8641993b5768c208d62cec6b2e3627f1。

Tianya Zhang, Xiunan Wang, Pengyuan Sun, Maged Shoman, Benedetto Piccoli, Peter J. Jin. Physics-informed graph modeling for traffic shockwave analysis through optimized change-point detection. Transportation Research Part B: Methodological 211 (2026), 103522. DOI: 10.1016/j.trb.2026.103522。

第一页：Received 2025-12-10；Revised / Accepted 2026-06-01；Available online 2026-06-08。卷期元数据2026-09与online date分开记录。正式条目Q65YUJ89复用；原预印本不删除/覆盖/合并。原件不进入仓库。

## 2. 已证实版本差异

| 项目 | SSRN 5903681 原附件 | 正式期刊版 | 解释 |
|---|---|---|---|
| 身份 | 36页，2025-12-10，四作者，not peer reviewed | 18页，六作者；上述期刊DOI | 不是同一版本，页数本身不证明删减 |
| 图语义 | 引言DAG；方法undirected event graph | 引言仍DAG；§3.2.1 p5明确undirected G；p6 BFS connected components | 同样存在叙述/算子张力，不能把连通分量解释为有向因果路径 |
| 标注单位 | 六个15min US101/I80片段，100 shockwave events（PDF p21–22） | §4.1 p9：120 validated STMaps；描述compression fronts和merged-event共识规则 | 100事件与120 STMaps不是同一计数单位，不能直接说新增20事件；正式文中未重新完整列出六片段分配 |
| 主结果 | Table1 F1 .849；precision .856；recall .860；speed error 1.421 ft/s；Avg IoU .769 | Table1 p11：F1 .875；precision .879；recall .871；temporal/spatial/combined IoU .726/.830/.758 | 作者报告，不是AAD独立复现；数据/评价变化使直接性能提升比较无依据 |
| speed error | 1.421 ft/s | Table2 p13：2.20 ft/s / 18.82% | 两版数值不得混用，不能把旧版更小误差当正式版结果 |
| 标注/评价 | 原Table1 file-level指标 | p11 aggregated TP/FP/FN；combined IoU=.7 temporal+.3 spatial；match >.5；默认70% lane scanline覆盖 | 评价任务偏向显著大波，可能漏小而早的物理响应 |
| 约束参数/车道依据 | 旧版参数与结构按版本分别保留 | p5–6：dt_min=.1s，dt_max=10s；dmax=120ft；wave speed[-25,-5]ft/s；同车道，换道后独立段 | 文献域的经验条件，不能移植为AAD质量门/阈值 |

| 波速Eq9 | PDF p14为(tj−ti)/(xj−xi)，与速度界的量纲不一致 | p6改为(xj−xi)/(tj−ti)，单位ft/s（已视觉核对） | 证实正文公式修正；作者代码未审计，不能声称代码已修复 |
| 第四约束 | 旧方法列表含spatial-deviation约束 | 正式§3.2.1只列时间、距离、传播速度三项，另明示同lane与换道段 | 列表变化已证；不能凭文字推断其代码相同/不同 |
| 消融与敏感性 | 旧版结果/指标依原表 | 正式新增/扩展PELT+Graph消融、约束消融、边数弹性与复杂度 | 不把结构边数敏感性误称物理因果正确率 |

## 3. 正式版实际算法与证据能力

§3.1 pp3–5：CUSUM候选→限制候选集合的PELT递推及pruning→piecewise-linear segment→相邻段速度差。β默认50；segment至少20点@10Hz、R²>.7。Eq5实际是端点位移/时间，但正文称linear regression；不能自行补成已实现OLS。CUSUM在速度序列候选化，拟合轨迹段，必须保留输入层区别。

§3.2 pp5–7：事件节点(t,x)，时间、距离、后向传播速度约束；undirected graph / BFS组件，非逐边核验真实leader identity。§3.3 pp7–9：压缩/恢复点回归、频率/幅度、时空范围；recovery典型16ft/s，是作者域参数。

§4 pp9–13：NGSIM原视频STMap专家标注，比较DP、PELT、CUSUM预筛与图/DBSCAN；去速度约束F1 .393，去时间 .801，去距离 .831。§5 pp13–16：synthetic runtime（不是AAD synthetic），β建议[50,100]仅其域；图边数弹性不是arrival覆盖率或因果正确率。§6 pp16–17：piecewise stationarity局限，建议adaptive speed window及post-hoc speed-phase decomposition。

## 4. 独立判断 / Proposal

事件检测 ≠ 路径关联 ≠ Qualified W1–W9 ≠ 因果识别。可复用成熟变化点候选与lane-segment预处理、物理可行性过滤和波前辅助图；必须补真实leader/follower、身份/关系连续、源归属、区间时间、缺失/竞争解释及独立验证。不能直接搬β、dmax、wave-speed、70% coverage、recovery速度作为AAD参数。

原文p11和p16的causal表述由物理约束和波前标注一致性支撑；没有独立随机信息干预、未观测混杂排除、无消息source-present参考或AAD风险ITT。物理合理的图边不自动识别因果边。引言DAG与无向BFS实现叙述的张力应保留，不能替作者修复。

AAD不能再把变化点+车辆间物理图+波前重建本身当作已证实新颖性；联合消息生命周期、采用/动作、区域风险ITT及独立同总体物理参考仍是待验证贡献候选。Formal A=0、独立Qualified=0、F0和时间优先性Unknown均不因此改变。

## 5. Zotero、字节保真与仍未确认的事项

复用正式parent Q65YUJ89；正式原件9F39AWXN与用户PDF同SHA；双语V72AJRHW，固定标题“双语对照 PDF（机器翻译）”，标签translated:pdf2zh / version:published，21,058,231 bytes，SHA256 10f27b84efdbc0dba95c34817073cca5041a302eb46184a2e0d5e5eeea0eba40。明确以正式附件路径调用翻译，避免既有脚本按parent先选旧预印本。Task5 note DXIKHPDP；历史Task4阅读标签/notes保留。

旧SSRN CLA3GKSX仍29,389,782 bytes，SHA256 047b49c784c49214721aae6021029a3bb3011f9287c23b025adf26fdb41ac253，与任务前相同。用户称已有独立SSRN条目；新增前本地全库281 top-level核查只见正式parent，SSRN实际挂在同parent的独立附件。本轮没有删除/覆盖/移动/合并，也不虚构独立SSRN parent key。版本身份已通过标题、notes和独立原附件保留；是否以后拆parent需另定，非全文获取阻塞。

未核：作者实现代码、原始标注和全部实验复现、两版样本逐一对应、正式新增标注来源独立性。正式版120 STMaps不能与旧100 events直接做差。全文阅读不等于独立复现或因果验证。Task4曾正式全文不可得为历史事实，本轮由用户提供文件解除此项限制，其他识别缺口不随之解除。
