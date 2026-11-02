# P2 Task4 — Overleaf只读一致性审计

日期：2026-11-02。状态：COMPLETED_WITH_LIMITATIONS。正式逐项差异事实源为[统一定义OVERLEAF_ALIGNMENT](../definitions/OVERLEAF_ALIGNMENT.md)的Current P2 Task4表；本报告只摘要证据、影响与修订优先级，不另立定义。

## 1. 实际读取与证据

读取最新版main.tex 1759行、supplementary.tex 254行、references.bib 217行的活动内容及相关注释。通过既有Edge合法登录下载AAD.zip，获取时间2026-11-02T08:20:35.613795Z；三个文件与ZIP的字节/hash已完整登记于统一对照表。源文只在被Git排除的本地只读快照，不在仓库创建活动.tex，不修改Overleaf。行号属于这次快照，后续版本需重取。

Task3受工具切换影响没有可恢复快照；本轮已解除该限制。Task3称物理多跳主要位于注释的说法已纠正：main323–367是活动正文，确有动态图、实际变化/响应及时间顺序。不能将旧误读作为新增方法缺口。

## 2. 必须优先处理的三项冲突

1. **范围**：main87/90/96的ordinary physical propagation排除表述须改成研究者A接受的预定可观测机制范围。Task3区域内非cohort响应反例使“cohort未触发⇒区域任何物理影响未到”不成立。论文拟议设计不是已证明错误的实证结果，但强解释不受当前测量支持。
2. **总体与筛选**：main676以通信两运行的源匹配及全部四格有效性决定整组纳入，存在处理后选择和目标总体改变风险。预先规定QC仍不能自动保证不受处理影响。Task4 C接受的是Qpre在ZC分配前、通信盲资格筛选后ITT，失败保留。
3. **主要时间对象**：main1033–1036主检验是同处理运行(1,1)内的两个行为响应，no-message仅敏感性；P1/Task4 D主对象是总体区域风险效应和匹配F0。二者不是同一数学量。行为配对可作机制描述，不能代TR、独立无消息到达或个体反事实提前。

## 3. 可保留内容与缺项

有向physical graph、真实运动变化/响应、assignment与event区分、正式确认后消息资格、预固定cohort、gen/send/del/adopt、command/actuation/motion层次、行为不代风险、提前物理失败不事后删窗/删例均可保留。g净间距及TTC/DRAC既有语义未发现本次新增定义导致的同公式冲突。

需补：onset interval、双层macro/微观独立质量、verification、Qpre/F0^Q、共同支持域、持续φ的限定用途、删失/Unknown/clock、预定H*及全网格同时带/联合错误。风险baseline和物理baseline是不同对象；不能仅因名称相同判为数学冲突。

## 4. 最近邻与引文

references.bib已有Saberi/Duan；缺Jerath/Zhang。main84的“尚未建立直接可归因联系”须限定为本次联合证据契约，而非泛称信息→车辆动作→宏观交通尚无先例。Jerath已经给出该链和ZOI，Peng随机BLOS动作效应与既有信息波工作也必须纳入。Zhang正式方法全文未取得，未来引文须区分SSRN和期刊，不把预印本数值放在正式期刊归属下。

## 5. 审计限制与后续

未更改正文、公式、参考文献或论文结论。快照下载不是版本历史锁；不声称获取时刻以后没有并行编辑。未审校所有历史中文注释，也未逐篇重新验证全部bib。下一次论文修改需研究者另行授权；当前已接受的A–D不需再次确认，具体正文修订与主要endpoint仍待决定。
