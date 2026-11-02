# AAD 统一科研定义事实源

状态：`Active / Proposal-with-limitations`
当前版本：`AAD-SCI-DEF-20261102-P2T6-v0.4`
更新日期：2026-11-02

`docs/research/definitions/` 是 AAD 当前科研定义、符号、参数、假设和证据状态的唯一统一入口。它承载当前定义，不替代源码、配置、实验产物、Overleaf 正文或研究者决策；这些事实源分别负责实现事实、运行事实和论文表述。其他 Task 报告可以保留历史记录，但不能另立一个与本目录冲突的最新定义版本。

## 文件职责

- `CORE_SCIENTIFIC_DEFINITIONS.md`：定义、公式、输入、判定方法、证据、适用范围和局限。
- `SYMBOL_REGISTER.md`：全项目符号、单位、首次定义位置、当前来源、旧符号映射和冲突状态。
- `PARAMETER_AND_CALIBRATION_REGISTER.md`：参数推荐值/范围、确定依据、敏感性和冻结状态。
- `EVIDENCE_AND_ASSUMPTION_LEDGER.md`：Fact、Inference、Hypothesis、Proposal、Agreed、Unknown 的证据登记。
- `OVERLEAF_ALIGNMENT.md`：统一定义与 Overleaf `AAD` 项目本任务已读 `main.tex`、`supplementary.tex`、`references.bib` 的当前字节级快照逐项对照；Task3有限读取记录保留为历史。

## 状态含义

`Verified` 表示当前源码、配置、产物或全文材料直接支持；`Agreed` 表示研究者明确接受；`Proposed` 表示可审计推荐但未接受；`Hypothesis` 表示待验证科学假设；`Inference` 表示由已登记事实推得的判断；`Unknown` 表示当前证据不足。Codex 完成文档或校准任务不会自动把 `Proposal` 升级为 `Agreed`。

## 更新规则

1. 开始科研任务前先读本 README 及相关定义、符号和参数登记。
2. 新增、修改或废弃定义时，同一任务同步更新本目录和证据登记。
3. 修改符号时同步更新 `SYMBOL_REGISTER.md`，并记录旧符号映射。
4. 修改参数时同步更新 `PARAMETER_AND_CALIBRATION_REGISTER.md`，同时保留合理范围、敏感性和未决状态。
5. 旧定义不得无痕删除；使用版本、变更原因、替代关系和影响文件登记。
6. `AI_CONTEXT/` 只摘要和导航，不形成第二套定义事实源；出现差异时登记冲突。
7. Overleaf 是论文正文事实源，本目录是当前科研定义事实源。二者冲突时更新 `OVERLEAF_ALIGNMENT.md`，不得擅自覆盖任一方或修改 Overleaf 正文。
8. Formal P2、Formal rho/P2、Gate、Protocol Lock 和 Stage 1.1 规则仍以既有事实源和研究者决定为准；本目录的 Proposal 不改变它们。

## 当前入口

- Task6 当前：[最终报告](../P2/P2_TASK6_FINAL_REPORT.md)、[参数确定实验协议 v1.0](../P2/P2_TASK6_PARAMETER_DETERMINATION_EXPERIMENT_PROTOCOL.md)、[集中科研决策](../P2/P2_TASK6_RESEARCHER_DECISIONS.md)。
- D1–D7方向已Agreed，27条Definition ID保留；具体数值/算子/估计器与执行授权分层登记。科学下限、参数十三字段和依赖矩阵见参数登记Task6；下一项直接为Parameter Determination Experiment，不增设计任务。


- Task5历史[完整报告](../P2/P2_TASK5_FINAL_REPORT.md)、[操作化方案](../P2/P2_TASK5_MEASUREMENT_AND_IDENTIFICATION_PROPOSAL.md)、[集中决策](../P2/P2_TASK5_RESEARCHER_DECISIONS.md)。

- 当前核心定义：[CORE_SCIENTIFIC_DEFINITIONS.md](CORE_SCIENTIFIC_DEFINITIONS.md)
- 当前符号登记：[SYMBOL_REGISTER.md](SYMBOL_REGISTER.md)
- 当前参数和校准：[PARAMETER_AND_CALIBRATION_REGISTER.md](PARAMETER_AND_CALIBRATION_REGISTER.md)
- 证据账本：[EVIDENCE_AND_ASSUMPTION_LEDGER.md](EVIDENCE_AND_ASSUMPTION_LEDGER.md)
- 论文对照：[OVERLEAF_ALIGNMENT.md](OVERLEAF_ALIGNMENT.md)
- P2 Task3 专项报告：[../P2/P2_TASK3_FINAL_REPORT.md](../P2/P2_TASK3_FINAL_REPORT.md)

## 版本关系

`P2 Task1/Task2` 的历史报告保留原始定义和当时状态；本目录在不改变研究者已确认方向的前提下，将符号、定义和参数状态统一成当前入口。当前 Physical Arrival 的数值参数仍为 `Proposal / Awaiting Researcher Decision`，不能写成论文已采用或正式 Protocol Lock。

## 本版变更记录与重要限制

| 日期 / 版本 | 原状态 / 变更 | 原因与替代关系 |
|---|---|---|
| 2026-11-02 / v0.1交付 | 新建唯一入口，统一22定义和13字段 | P0/P1/P2历史文档保留，不追溯改写已确认决定 |
| 同版提交前纠错 | V1输出保留并撤回；新增V2独立验证 | 持续时间、检出分类和验证设计缺陷；旧5s/k3/h1/q2dt推荐无依据，全部撤回 |
| 同版符号映射 | Task2 g_v、早期Task3 Δv候选映射为Δu^B Proposal | 复用论文u速度、g保留net gap；不宣布正式Deprecated |
| 同版证据扩展 | V2 768面板；B60 CALIBRATION_ONLY run | 测量验证不等于A源或F0；B全无cohort报警，不推荐数值 |
| 同版科学范围澄清 | CORE细则F、E27–E29 | region内响应可先于cohort阈值状态；更强物理排除主张待研究者 |
| 同版论文审计限制 | 已完整读取，未恢复可复核快照 | 不称提交时逐句/逐公式一致性全部验证；正文未修改 |

历史v0.1状态：当时均值算子、tE、数值参数、子总体转换和claim范围仍Awaiting。v0.2由Task4明确接受A–D方向，覆盖其中claim范围与资格顺序的等待；具体算子、跨总体转换与参数仍未定。定义目录不通过任何科研Gate。

## 历史v0.2 — Task4接受记录（A–D继续有效）（2026-11-02）

研究者已在Task4任务书§四明确接受A有限观测范围主张、B微观/宏观双层物理测量、C通信前盲法Qpre后随机化及资格子总体、D沿用P1总体早窗统计框架，均为Agreed。此记录覆盖v0.1末段对这些方向的Awaiting；tE、均值算子、具体符号映射/质量门/阈值/置信预算、微宏融合仍待定。不得把方向接受写成已有科学证据。详见CORE当前约束及证据账本；历史Task3文件和失败记录保留。


v0.2当时共26定义：v0.1的22条保留，新增DEF-SCOPE-001、DEF-PHY-009/010和DEF-POP-001（13字段齐全）。宏观Edie型算子与证据向量是Proposal；原cohort φ保留公式并限定名称，不再承担全部物理排除。v0.2论文审计：[P2 Task4](../P2/P2_TASK4_OVERLEAF_AUDIT.md)；综合报告：[P2 Task4](../P2/P2_TASK4_FINAL_REPORT.md)。Task4未新增实验、未改论文或AGENTS。

## v0.3 — Task5当前增量（2026-11-02）

当前27定义。DEF-TIME-004与CORE细则J–P具体化分层arrival、Edie型同域裁切、W1–W9候选流水线、Qpre/四格支持、允许时间集合、保守CDF和同时带、联合早窗判定。推荐分别报告三种时间，尚不形成统一标量或微宏融合；全部新具体方案为Proposal。Agreed A–D不变，数值参数Unknown。

Zhang正式18页已全文读取、关键页视觉复核并导入Q65YUJ89/9F39AWXN，覆盖Task4的正式版全文获取限制；Task4当时记录保留。新增Frangakis–Rubin原文HTML、Hoeffding扫描原文关键定理；Edie1963原文仍未取得。完整交付与版本/来源/论文快照见[Task5最终报告](../P2/P2_TASK5_FINAL_REPORT.md)。Overleaf三文件重新下载且逐文件SHA与Task4一致，未改正文。无任何新实验或Gate改变。

| 版本 | 修订理由 / 原定义关系 | 状态 |
|---|---|---|
| AAD-SCI-DEF-20261102-P2T4-v0.2 → v0.3 | 保留26定义，新增时间族；旧TP单一φ限定cohort语义；macro时间与raw物理起点分开；补可执行统计充分条件 | 新方案Proposal，不是协议锁，不追溯改Task3/4 |

## v0.4 — Task6 当前变更与历史映射（2026-11-02）

从v0.3升级，保留全部27定义及旧版本：D1正式接受三层分别报告，D2接受Edie型主要候选基本操作，D3接受两臂/四格不同定位，D4接受onset/confirmation/observation区分，D5先SAC再单因素/交互/独立V，D6接受P1保守总体方向，D7本次不改论文。具体算子/数值/估计器未整体Agreed；E46/47/49等历史Proposal的方向层由E54–60覆盖。

CORE当前细则Q–T、参数SAC/十三字段/11依赖、符号和证据账本同版。原v0.3的2J风险常数仅单侧上带；本版双侧全网格带明确4J。源码已证rho贡献/均值[0,1]、定长积分[0,L_Y]，不是改变正式定义；最终Y聚合仍待接受。Detector到真实物理onset桥接必须有独立同域漏检/延迟证书。

本次0新交通/校准运行、0holdout读取；Formal A0、独立Qualified0、F0/总体TR-TP Unknown，Gate/Lock/Stage1.1不变。Task6只复用Task5论文快照，未重读在线最新版、未改正文；Edie原文仍缺，未虚称精读。协议设计完成，但执行需集中科学启动项与下一实验授权，不要求新前置任务。

## Task7 有限域执行/证据增量（2026-11-02）

Task7当前有限域证据：[最终报告](../P2/P2_TASK7_FINAL_REPORT.md)。v0.4的27项定义保持；575完成/1失败，三层C候选、V0，未建立独立参数认证或严格物理桥接。


## Task8 有限支持与验证决策（2026-11-02）

Task8当前有限支持证据见[最终报告](../P2/P2_TASK8_FINAL_REPORT.md)。v0.4/27项不变，状态与源归属分开，V未执行，无参数/稳定区域/严格桥接认证。


## Task7源时间历史回溯（2026-11-02，独立更正附录）

[Task7源时间独立更正附录](../P2/P2_TASK7_SOURCE_TIMESTAMP_BACKFILL_REPORT.md)：仅修正历史时间overlay及W6派生证据；27定义/v0.4、a1b1、W1–W9、正式参数与阶段不变。
