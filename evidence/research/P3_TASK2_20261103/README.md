# P3 Task2 — 控制器证据接口便携包

Task ID：AAD-P3-TASK2-20261103；日期：2026-11-03；仅工程合成验证。所有fixture均fixture_only=true、scientific_claim_eligible=false；候选采用边界PROPOSED，未接入真实控制器。

- schema.json：14类事件的字段、身份、状态和时间别名库存，独立版本aad.p3.controller-evidence.v1。
- fixture_A/B/C/D/E/G/H.json：七个有效确定性合成capture；F七种错误由构造器独立重建。
- linkage_results.json：显式图、Unknown、候选策略输入和F异常结果；不能解释为科学资格。
- provenance.json与synthetic_SHA256SUMS：原runner执行版本、dirty快照、环境及实现/合成文件hash。
- input_provenance.json：179项选定历史输入的运行时hash与可用的基线Git blob hash；不是Task7/8全原始大数据重审。
- output_bindings.json：本任务实现、测试、报告、context/registry和冻结状态绑定。
- test_results.json：50项最终新增测试与42项旧回归、各次执行摘要和原XML hash；首次失败不隐藏。完整XML仅本机输出保留，不复制原始日志。
- validation.json：验收范围、实际验证记录及限制；SHA256SUMS封装本包成员（不含自身）。
- verify_evidence.py：只读校验hash、固定状态、Task20本机旧manifest，以及七fixture关联/重建与七异常复算；无SUMO、无seed、无holdout。

~~~powershell
python -X utf8 evidence/research/P3_TASK2_20261103/verify_evidence.py --repo-root .
python -X utf8 evidence/research/P3_TASK2_20261103/verify_evidence.py --repo-root <git-snapshot-root> --portable
~~~

portable模式仅跳过未随Git携带的历史code/outputs小文件，接受预先登记的历史运行时或基线Git blob字节；其余缺失/变更仍失败。新代码固定LF，本包固定字节。包校验前先检查实现绑定，再导入执行离线复算。命令PASS只覆盖这些条件，不认证外部producer真实性、实际采用或因果效应。

完整本机输出：code/outputs/analysis/p3_task2_20261103_v1/。报告：[P3_TASK2_FINAL_REPORT.md](../../../docs/research/P3/P3_TASK2_FINAL_REPORT.md)；[字段与P7接入](../../../docs/research/P3/CONTROLLER_EVIDENCE_IMPLEMENTATION.md)。原Task1三契约、Task7/8/20输出与统一定义不改；正式科学状态不升级。
