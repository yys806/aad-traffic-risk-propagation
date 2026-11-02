# P2 Task7 — 实际执行协议

Task ID: AAD-P2-TASK7-PARAMETER-DETERMINATION-EXPERIMENT-20261102。状态：EXPLORATION_COMPLETE_WITH_LIMITATIONS / V_NOT_EXECUTED。
继承 [Task6 v1.0](P2_TASK6_PARAMETER_DETERMINATION_EXPERIMENT_PROTOCOL.md) 和 [统一定义 v0.4](../definitions/README.md)，不增加或替换27项 Definition ID。授权来源为研究者 Task7 任务书；Task6 当时无运行授权的历史记录保持。

## 有限域和冻结顺序

Windows 原生 SUMO，独立双车道直路，仅 lane 0 为主要测量域；lane 1 的断开跟驰链源为归属对照。通信关闭。lane 0 native Krauss 跟驰，禁止换道；仅源车辆接收速度控制，目标车辆无动态速度 setter。正式网络、config、生产代码和 locked holdout 均不进入此实验。

固定 Region=[1600,3080] m，Cohort=s14–s17，源计划干预30 s，原始步长0.05 s；基线支持[10,28) s，监测[30,46] s，额外随访至50 s。源位于区域下游边界之外；实际源 onset 必须由状态读回确定。低/中/高是输入密度设计层，实际 Edie k 另报，不冒称现实交通覆盖。每层车辆数24/40/64、初始间距35/23/15 m，初速/上限10 m/s。

有限 truth 范围候选 a*=1 m/s、b*=1 s；另记录2a*、2b*层。它们是本次构造测量域的 Proposal，独立于 detector θ/h，不是普适物理下限。truth 使用完整高频原始状态、固定已知速度上限10 m/s和固定 oracle 时间支持；不使用拟合 baseline 或候选 detector。真实任意微小物理 onset 的界仍 Unknown。校准绝对延迟规划 d*=4 s、H_cal=16 s，均不冻结正式 H*。

所有计划单位、seed、truth规则、源命令、区域和群体先生成 manifest/hash，再运行；全部 truth/hash 先封存，之后才运行 detector。完整状态 truth 与指定源归属 truth 分开：单次速度变化和同 seed 不自动证明因果归属；W8不能排除竞争解释时为 Unknown。Micro W1–W9 不放宽。

## 有限矩阵与资源

N0/N1/P11/P21/P12/P22/局部非cohort/A0 × 3密度 ×24预列新seed，共576计划依赖单位。P11等为源命令设计点，实际标签只由真实目标响应决定；无响应不补跑、不挑seed。首先执行矩阵内六个固定单位作成本评估，不另增样本。所有参数/交互/压力测试优先离线复用raw。原始、truth、detector、audit分目录保存。

Calibration 与 Independent V 用不同 SeedSequence 命名空间；同一run的三层、参数和mask共享 dependency_block。历史V2/B60和Task9/18/19仅审计，不算新的独立样本。

单机规划：4 workers，探索576单位；独立V最多约2小时墙钟、10 GiB输出和同机资源安全余量，实际是否运行以准确样本量、试跑成本及有效truth支持共同决定。此上限是执行预算，不是科学验收标准。资源或truth不足时不运行伪充分V，保留未完成状态。运行前记录可用CPU/内存/磁盘，预计raw与临时空间，至少保留20 GiB磁盘安全余量。

## 参数及验收

按Task6 C01–C09、U01–U09、M01–M10和T08/T09逐项比较，候选依Task6规则由pre支持、原始采样和独立误差生成。11类交互分别登记；恢复/滞回用事件寿命及重入检查，不能只看首次报警。压力层含降采样、MCAR/块/MNAR缺失、噪声、identity与leader断裂。

有限域 Proposal：FPR≤1%、FAR≤1%、timely recall≥95%、Unknown≤5%，β_V=.05、power=.90；good坏率分别采用 .002/.002/.01/.01 作规划假设，不是观测事实。实际 J_V 枚举检测层、端点、密度、冻结候选与邻域；采用保守同时控制及真实run/最大依赖block。无足够独立V时参数不可标记 Recommended-for-freeze。

η=.01/.05分别规划及时漏检/Unknown上限η/4；完整早窗质量需加入detected early mass、Unknown、CDF抽样上带、delay/truth/clock误差。β_V≠α_measure；另算.005证书成本。正式η/δ/H*/风险网格、Protocol Lock和Stage1.1均不改变。

## 停止与复现

碰撞、teleport、目标速度控制、版本/hash漂移或数据越界硬停止；真值/阳性/稳定域缺失则对应层 Unknown/Not established，不降标准、不补零、不增加运行追求通过。脚本、manifest、truth、seed/split、版本、dirty状态与所有产物SHA写入独立输出；日志仅留本地，不复制进便携证据。实际偏离和失败进入最终报告。

## 实际执行增量与偏离（2026-11-02）

575完成/1启动失败，576 planned attempts全部保留；没有重跑历史或补seed。实际source剂量4/8 m/s×4/8 s、local2×1，与目标a*/b*分开。target等级实现详情见planned_signal_realization；特别是Macro 2a*格未实现，不将source命令当真值。本次primary truth仅a=1,b=1；其他目标强度/持续以描述性实现审计报告，不另造事后主标签。

独立truth v2在首次detector前冻结；初版v1完整保留，48个cohort恢复区间按原随访要求延到50s，不改变主状态/onset。失败产生3个Unknown。候选25/36/22，离线逐项/交互/压力完成。J_V=765，source/scene/seed/run block完整登记；独立V因资源和真值支持不足NOT_EXECUTED，seed消耗0。科学ε_stab/γ_int、Formal H*/η/δ/α和真实物理误差仍Unknown。

CDF规划225项包含固定5设计层，初版45项规划留档；β_V=.05与α_measure=.005分别计算。原始执行manifest及当时协议/代码字节快照不可用最终报告版本替换；源执行m-v1、独立truth修复m-v2和detector版本分别有hash。最终脚本/文档版本另见便携证据。

复算与输出契约见[最终报告](P2_TASK7_FINAL_REPORT.md)。Formal A/Qualified/F0、Stage/Gate/Lock和论文未改变。
