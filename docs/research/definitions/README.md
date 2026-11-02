# AAD 统一科研定义事实源

状态：`Active / Proposal-with-limitations`
当前版本：`AAD-SCI-DEF-20261102-P2T3-v0.1`
更新日期：2026-11-02

`docs/research/definitions/` 是 AAD 当前科研定义、符号、参数、假设和证据状态的唯一统一入口。它承载当前定义，不替代源码、配置、实验产物、Overleaf 正文或研究者决策；这些事实源分别负责实现事实、运行事实和论文表述。其他 Task 报告可以保留历史记录，但不能另立一个与本目录冲突的最新定义版本。

## 文件职责

- `CORE_SCIENTIFIC_DEFINITIONS.md`：定义、公式、输入、判定方法、证据、适用范围和局限。
- `SYMBOL_REGISTER.md`：全项目符号、单位、首次定义位置、当前来源、旧符号映射和冲突状态。
- `PARAMETER_AND_CALIBRATION_REGISTER.md`：参数推荐值/范围、确定依据、敏感性和冻结状态。
- `EVIDENCE_AND_ASSUMPTION_LEDGER.md`：Fact、Inference、Hypothesis、Proposal、Agreed、Unknown 的证据登记。
- `OVERLEAF_ALIGNMENT.md`：统一定义与 Overleaf `AAD` 项目本任务已读 `main.tex`、`supplementary.tex`、`references.bib` 的有限逐项对照（快照和精确位置限制见审计）。

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

新版正式修订须递增版本并登记接受依据。当前Agreed仅限任务书或既有明确决策中的方向；均值算子、tE、数值参数、子总体转换和claim范围仍Awaiting。定义目录不通过任何科研Gate。
