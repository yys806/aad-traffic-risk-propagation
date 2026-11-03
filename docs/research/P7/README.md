## Current — P7 Task2.1工程验收 (2026-11-03)

ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS。唯一Enabled v2复验通过（1次、seed20261103），基准未重跑。最大实际减速度1.0 m/s²，无emergency/碰撞/teleport；52次实际采用、39命令、326执行、352动作。首次命令2.8 s、首个实际差异2.9 s；8.0 s过期恢复20 m/s且后续无消息输入。共同351点比较有效，最大速度差2.649473720 m/s、加速度差2.719870887 m/s²，仅ENGINEERING_DIAGNOSTIC_ONLY。 v1失败不改，正式科研资格/阶段不升级。

[复验报告](../../../docs/research/P7/P7_TASK2_1_FINAL_REPORT.md) · [证据](../../../evidence/research/P7_TASK2_1_20261103/README.md)。后续P5等不在本任务启动；下方保留历史状态。

# P7 端到端工程集成

当前：[Task2报告](P7_TASK2_FINAL_REPORT.md)、[研究者D1–D8](P7_RESEARCHER_DECISIONS_20261103.md)、[控制器规格](P7_LONGITUDINAL_CONTROLLER_SPEC.md)、[P3/P4接线](P7_CONTROLLER_EVIDENCE_INTEGRATION.md)、[便携证据](../../../evidence/research/P7_TASK2_20261103/README.md)。

状态：ENGINEERING_IMPLEMENTED_SUMO_ACCEPTANCE_BLOCKED。真实消息驱动代码路径存在；v1 Enabled发生emergency braking，v2仅离线验证。不得宣称整体验收完成。

历史：[Task1审计](P7_TASK1_FINAL_REPORT.md)、[控制路径清单](P7_REAL_CONTROL_PATH_AUDIT.md)、[集成蓝图](P7_INTEGRATION_BLUEPRINT.md)。Task1当时不存在策略/边界待决的记录保留；Task2授权和实现是后续增量。统一定义仍[v0.4/27项](../definitions/README.md)。
