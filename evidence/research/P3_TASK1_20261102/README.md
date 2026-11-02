# P3 Task1便携审计证据

任务AAD-P3-TASK1-20261102；实际执行跨日至2026-11-03。审计基线4932cf08c46b2e95fdc2fdae63214fd25fbc39d8，开始clean。本包是只读实现审计和文档契约证据，不是SUMO运行结果、控制器采用凭证或因果证据。

## 内容与口径

| 文件 | 含义 |
|---|---|
| input_provenance.json | 基线、不可变源码/测试/定义/历史报告/fixture与通信勘误SHA；唯一授权OB原文SHA及本地备份引用 |
| audit_summary.json | 九阶段状态、输入版本、关键接口缺口、无新实验/权限边界 |
| planning_revision.json | OB规划原/新SHA、2525→2302行、WP映射、12公式/42准入保留检查 |
| test_execution.json | 四个定向测试的命令、42通过、初次tmp权限失败和一次有限重试 |
| validation.json | 文档/链接/字段/状态、hash、既有fixture、证据导出及Git检出核验结果 |
| output_bindings.json | 本次P3文档与同步入口的最终SHA，不循环绑定本包自身 |
| verify_evidence.py | 标准库只读核验器；portable模式不访问本机OB/历史运行目录 |
| SHA256SUMS | 本目录全部小型证据文件（除自身）的SHA256 |

原始日志、pytest临时目录、原OB逐字节备份在本机code/outputs/analysis/p3_task1_20261102_v1/；不复制进便携证据。原Task20 fixture仅核验原有manifest/SHA，未重跑。未复制大型轨迹、密封键、图片或OB全文。

## 复核

在仓库根目录执行：

    python -X utf8 evidence/research/P3_TASK1_20261102/verify_evidence.py --repo-root . --portable

本机完整核验可省略--portable，额外验证已绑定Task20输出及唯一授权OB规划；没有这些本机材料时不应冒称本机核验完成。portable复核证明Git小型证据及绑定源码/文档的字节完整性，不证明消息事件真实发生。

历史受保护文件有9项原生CRLF与Git blob字节不同。本包分别登记两套精确SHA：本机模式只接受原始runtime字节，portable模式接受已登记runtime或baseline Git blob字节，不做模糊规范化，也不为此修改历史文件或AGENTS。

本次Git-only复核固定使用git -c core.autocrlf=false archive导出索引树，并遵循已登记eol属性。第一次默认core.autocrlf=true导出产生其他CRLF转换，校验如实失败；此失败与修复范围登记在validation.json，没有重写历史SHA或源文件。任意不同换行配置的检出不自动在本包精确字节保证内。

项目既有证据仍使用export_project_evidence.py导出/验证；本P3包通过项目注册表research_audits和P3/项目索引关联，独立SHA256SUMS管理，不伪造实验result_id。

## 科学状态

三契约Proposed v0.1 / Awaiting Researcher Ratification；规划v1.1 Revised Proposal。生产代码/config、统一27定义v0.4、Gate/Lock、原实验/回溯数据均保持。Formal A=0，Independent Qualified=0，F0/Overall TR–TP=Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS，Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS，Lock BLOCKED，Stage I READY_ENGINEERING_ONLY，Stage1.1 NOT_AUTHORIZED。
