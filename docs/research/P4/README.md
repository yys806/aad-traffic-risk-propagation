# P4 — 动作与区域风险测量

Task ID：AAD-P4-TASK1-20261103。状态：**AUDIT_AND_OPERATIONALIZATION_COMPLETE_WITH_LIMITATIONS**。文档审计与操作化完成；契约Proposal，尚非完整区域风险生产管线。新增SUMO/TraCI/seed/V/holdout读取均0。

唯一科研定义入口：[统一定义 v0.4 / 27项](../definitions/README.md)。本目录不冻结科学参数，不替代 P1/P2/P3 正式契约。

## 导航

- [最终报告](P4_TASK1_FINAL_REPORT.md)：结果、验收范围和后续接口。
- [测量规范](P4_ACTION_AND_RISK_MEASUREMENT_SPEC.md)：Action/单车风险/区域风险、质量界与时间支持。
- [源码与血缘审计](P4_IMPLEMENTATION_AND_DATA_LINEAGE_AUDIT.md)：实际实现、缺陷及适用边界。
- [外部测量契约](P4_MEASUREMENT_DATA_CONTRACT.md)：aad.p4.measurement.proposed.v0.1，未修改P3schema。
- [研究者待决](P4_RESEARCHER_DECISIONS.md)：8组具体选择，推荐不等Agreed。
- [字段字典](p4_measurement_variable_dictionary.csv) · [源码追溯](p4_measurement_traceability.csv) · [机器审计](p4_implementation_audit.json)。
- [便携证据与核验](../../../evidence/research/P4_TASK1_20261103/README.md)。

已验证84项定向测试及27项离线语义例子；动作持续性跨缺口、等车平均无名单守卫、辅助暴露valid/NaN问题均保留并报告，未擅自改科学逻辑。P7工程验收保持通过；正式Y聚合/范围/阈值与总体风险因果效应仍待决或Unknown。
