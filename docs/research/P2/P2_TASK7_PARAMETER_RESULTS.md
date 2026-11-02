# P2 Task7 — 参数结果与稳定区域

状态：Calibration candidates only；三层独立验证性能Unknown；无Recommended-for-freeze。统一定义[入口](../definitions/README.md)仍为v0.4/27项，不在本文件另建定义。

| 层/对象 | 状态阳性及时检出(C) | 真阴性 FP(C) | state Unknown | 有效检出delay中位上端 |
| --- | --- | --- | --- | --- |
| cohort | 119/119 | 0/456 | 1/576 | 1.05 s |
| macro | 48/48 | 0/527 | 1/576 | 2.10 s |
| micro (native finite state) | 167/167 | 0/408 | 1/576 | 1.05 s |

上表包含A0的真实any-source状态阳性，Micro只为native有限状态检测，不是W1–W9的Observed或Qualified计数。任何总比例均为校准描述，不给异质池化exact CI。指定源Qualified=0；每同质N0/N1格n24、0 FP上界11.73%，没有1%FPR证书。

## 28项测量参数与T08/T09

| ID | 参数 | 本次候选/事实 | 局限 |
| --- | --- | --- | --- |
| C01 | baseline W | 9 s calibration center; 4.5/9/13.5 s conditional curves | pre-only fitting; no independent optimality proof |
| C02 | baseline model | constant center; linear compared | only pre-source data |
| C03 | theta_P | 1 m/s calibration candidate | finite a=1 state; not earliest physical onset |
| C04 | h_P | 1 s candidate; 1/2/4 s compared | actual last-first span; available delay <=4 s tested |
| C05 | q_P | 0.05 s clean-grid candidate | clean q grid degenerates; missing-gap domain not calibrated |
| C06 | coverage | 1 center; .6/.8/.9/.95/1 compared | full-N bounds; gate cannot repair MNAR |
| C07 | recovery | negative reset; exit persistence 0/2 s | event lifetime and re-entry recorded |
| C08 | hysteresis | off center; numeric-floor exit delta tested | physical sensor-error scale Unknown |
| C09 | missing | fixed-N [0,10] model-speed bounds or Unknown | no survivor mean; exit/identity missing retained |
| U01 | actual leader relation | same-lane native leader IDs audited | no nearest-neighbor substitution |
| U02 | identity | 0 unresolved switches in complete clean runs | identity stress causes Unknown |
| U03 | relation continuity | complete 50 s relation panel | no cross-leader segment stitching |
| U04 | source interval | actual state/TraCI readback bracket width .05 s | planned 30 s never substitutes actual onset |
| U05 | response candidate | theta=1 m/s,h=1 s Observed-state candidate | not Qualified propagation sensitivity |
| U06 | reaction window | Unknown | threshold-lag/window x clock audit is not true reaction calibration |
| U07 | quality | geometric gap/native equality checks; .05 s grid | external sensor/noise tolerances Unknown |
| U08 | attribution | Unknown for affirmative source claims | 0 claims is abstention, not successful attribution |
| U09 | full witness | Not established; Qualified=0 | W8/independent source-to-cohort evidence absent |
| M01 | region/lane | [1600,3080] m, lane0 fixed | not optimized; other lane is disconnected control |
| M02 | macro window | 2 s center; 1/2/4 s compared | window is part of operator, not onset correction |
| M03 | spatial grid | L/4,L/2,L; primary full region unchanged | partition integral identity checked |
| M04 | temporal grid | .05/.1/.2 s | fixed q causes loss of support after coarsening |
| M05 | Edie operator | D/A,V/A,D/V with clipped segments | V=0 => undefined u; q=ku not independent evidence |
| M06 | coverage/sampling | complete census center; mask stresses | unknown p does not justify full-traffic ratio |
| M07 | macro theta | 1 m/s calibration candidate | target 2a* positive design never realized |
| M08 | macro persistence | 1 s calibration candidate | delay from finite oracle state, not first physical effect |
| M09 | lane aggregation | lane0 separately; no lane union | no multilane/merging mechanism coverage |
| M10 | macro attribution | N/A for any-source endpoint; source-specific Unknown | never inferred from wave or detector state |
| T08 | clock/phase | same simulation clock, .05 s phase bracket | external offset/drift/model numerical-time error Unknown |
| T09 | delay/measurement bound | Unknown for formal physical bridge | independent V absent; no alpha_measure certificate |

## 曲线、交互与可行区域

主要曲线：parameter_curves.csv、conditional_single_parameter_curves.csv；原始逐单位结果仅在本地输出。条件单因素围绕所选候选重算，未用它再次选择V向量。baseline pre预测误差独立列出。实测点估计plateau不是科学稳定/等效区域；ε_stab、γ_int、真实弱信号支持和独立V均不足。

11类依赖的表、分母和限制见最终报告§5。恢复/滞回同时记录事件数、首段结束和重入，不能靠不变的首次报警宣布无影响。Macro空间分区完整普查下D/V可加性应成立；时间降采样仍会改变插值误差与质量。reaction-window记录阈值到阈值lag，不冒称生理反应时间。

missing/identity/噪声/量化压力全部保留Unknown，未降低coverage后把可见均值作为全cohort。宏观已知抽样与未知p的全域恢复没有获得独立证书；本次主结果为完整模型普查。

## 推荐状态

Cohort：Not established；Macro：Not established（目标强度四格未实现）；Micro：native有限状态候选可复算，source-specific Qualified参数Unknown。独立验证每层V n=0。适用仅本次无换道直路platoon和有限a=1,b=1原生响应；不适用真实交通、Formal A、微弱/短暂影响、多源因果归属、换道/横向交互和总体早窗。

本地图：figures/threshold_curves.png、truth_support.png、unknown_stress.png；便携证据仅保存小表和hash，不复制图像或raw。详细成本和结论见[最终报告](P2_TASK7_FINAL_REPORT.md)。
