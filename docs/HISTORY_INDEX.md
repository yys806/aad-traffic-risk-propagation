# AAD 历史资产索引

> 历史资产保留是为了追溯“曾经做过什么、为何被替代”，不是为了给当前结论补证据。代码位于 `legacy/`，原始记录位于 `记录/` 与 `docs/归档/`，本地旧输出仍按原目录保留。

## HIST-DRIFT-QUALIFICATION

- 用途：早期上游 DRIFT 资产资格筛查和适配审计。
- 代码：`code/src/riskprop/legacy/drift_qualification.py`、`code/scripts/legacy/audit_drift_qualification.py`。
- 为何不是当前路径：它只回答上游资产是否可参考，不能替代 AAD 正式实验 Gate。
- 可验证摘要：阶段 0 E00 的《上游DRIFT资产核验》；边界为历史参考。

## HIST-RISK-EVENT-DATASET

- 用途：早期风险事件抽取与可视化。
- 代码：`legacy/risk_event_dataset.py` 与对应旧脚本。
- 为何不是当前路径：形成于预注册和校准门禁之前，口径未与当前协议绑定。
- 边界：可作代码考古，不能直接进入当前论文 Results。

## HIST-LOCAL-PROPAGATION

- 用途：早期局部传播指标和可视化探索。
- 代码：`legacy/local_propagation_baseline.py` 与对应旧脚本。
- 为何不是当前路径：符号、指标与冻结规则早于现行 E01/E02 体系。
- 边界：只作方法演化对照，不能混用口径。

## HIST-NONLOCAL-PILOTS

- 用途：保存非局部传播 Pilot A/B 及修正版的早期探索。
- 代码：`legacy/nonlocal_pilot_summary.py` 与 A/B 汇总脚本。
- 为何不是当前路径：未在现行真实校准、意向运行分母与协议锁 Gate 下执行。
- 边界：只能证明做过探索，不能证明核心效应存在。

## HIST-FEASIBILITY-PIPELINE

- 用途：保存最初可行性周、区域化、传播与通用 CLI 管线。
- 代码：`legacy/pipeline.py`、`legacy/cli.py`、旧 feasibility 脚本。
- 为何不是当前路径：它是正式科研路线和证据门禁建立前的原型。
- 边界：用于复现历史决策，不得覆盖当前正式模块。

## 归档完整性

2026-09-08 的物理迁移与保留清单位于 `docs/maintenance/`。它们记录迁移前后路径、Git blob 或哈希，用于证明整理是保留式归档而不是删除。任何人恢复历史入口时，应先读清单和 `code/src/riskprop/legacy/README.md`，再决定是否建立新分支；不得把 legacy 默认接回正式路径。
