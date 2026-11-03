# P4 Task1 便携审计证据

Task：AAD-P4-TASK1-20261103。状态：AUDIT_AND_OPERATIONALIZATION_COMPLETE_WITH_LIMITATIONS。

[最终报告](../../../docs/research/P4/P4_TASK1_FINAL_REPORT.md) · [规范](../../../docs/research/P4/P4_ACTION_AND_RISK_MEASUREMENT_SPEC.md) · [数据契约](../../../docs/research/P4/P4_MEASUREMENT_DATA_CONTRACT.md) · [待决](../../../docs/research/P4/P4_RESEARCHER_DECISIONS.md)。统一定义仍[v0.4/27项](../../../docs/research/definitions/README.md)。

本包是源码/定义/既有证据的只读审计和离线软件语义验证，不是新的交通实验或独立验证结果。不复制完整轨迹、大型数据、PDF或原始日志，不重命名历史实验充作新增样本。

## 文件清单与用途

| 文件 | 内容 |
|---|---|
| source_manifest.json | 基线HEAD、实际源码/config/定义/历史证据与P4交付文档hash；工作区与Git规范化视图分别登记 |
| review_scope.json | 本次实际审计范围、关键函数/调用链搜索、未读取/未启动边界 |
| method_sources.json | 既有P2方法审计与本次只读Zotero元数据核验范围；不冒充新全文阅读 |
| environment.json | 当前离线解释器/库/OS与原P7环境引用，SUMO本次未启动 |
| tests.json | 当前84项定向测试分项/命令/hash、27例子计数及进程守卫结果 |
| offline_no_process.py | 实际使用的pytest审计钩子原字节；禁止外部进程创建 |
| deterministic_examples.json | 27项已运行的确定性边界例子；含已知限制的复现，不是修复通过 |
| protected_byte_check.json | 开始封存535项保护文件的结束原字节比对结果 |
| context_consistency.json | AI_CONTEXT00–08/索引/注册表同步和正式状态不变检查 |
| validation.json | 本次阶段性验收范围、事实/Proposal/Unknown和关键结果 |
| project_checks.json | 严格文档、evidence exporter、定向语法、Git字节与最小Git视图检查的实际记录 |
| verify_evidence.py | 不启动SUMO的独立核验脚本：全包hash、源版本、27例子、字典、追溯及文档链接 |
| SHA256SUMS | 除自身及__pycache__外本包所有文件原始字节SHA256 |

## 复核命令

在具备现有Python/pandas/numpy依赖的仓库根目录执行：

    python evidence/research/P4_TASK1_20261103/verify_evidence.py --repo-root .

仅复现数学/软件语义（不生成交通数据）：

    python evidence/research/P4_TASK1_20261103/verify_evidence.py --repo-root . --probe-only

完整原始测试XML/log、启动前工作区/hash及临时核验文件在本机code/outputs/audits/p4_task1_20261103/，便携核验不依赖这些本机日志。tests.json含真实日志hash，不将历史P7的143项计入本次。7个旧native SUMO测试未选择，不能计通过。

source_manifest对已知CRLF/LF视图差异显式登记工作区字节、Git blob及LF字节hash；只有已登记且归一后完全一致的视图允许兼容，不放宽内容校验。新包用限定路径属性保字节，不清理历史换行。

## 有限结论

已Verified：实际代码语义及18项追溯，84项相关离线测试、27项语义复现。Proposal：12表247字段契约、Action规则、完整名单/空间支持组装、最终区域Y算子。Unknown：正式风险因果效应、F0/总体TR–TP及真实来源资格。P7已有工程验收不变，历史v1失败不改。

此验证器通过表示包、源码绑定和已记录语义可复核，**不表示Action缺陷已修复、最终Y已批准或生产区域风险链已部署**。不改变P1、P3schema、Formal算法/config、Gate、Protocol Lock或Stage1.1授权。
