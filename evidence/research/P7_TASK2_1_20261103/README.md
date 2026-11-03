# P7 Task2.1 单次v2 SUMO复验证据

Task ID：AAD-P7-TASK2.1-20261103；2026-11-03。状态：ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS。

仅新启动一次Enabled v2：SUMO1.26.0、seed20261103、dt0.1；历史No Message/Disabled复用未重跑。最大实际减速度1.0 m/s²，无emergency/碰撞/teleport；52次采用、39命令、326执行、352动作。首次命令2.8 s、首个实际差异2.9 s；8.0 s过期恢复20 m/s，上限读回及后续空消息输入正确。

validation.json逐项验收，comparison.json覆盖全部351共同在场时刻。完整P3 sidecar/audit压缩保存；command_bytes含全部实际API/getter字节，readback_samples与byte_samples为选定字节样本。artifact_manifest绑定全本机输出；source_bytes保存实际v2闭包及Task2结束时源码，source_manifest区分历史/当前。controller_config保留实际原字节，SHA与运行一致。

完整原始轨迹、逐步状态、CSV和日志仅在本机code/outputs/engineering/p7_task2_20261103_v2_revalidation。便携复核可重验完整P3图和39条API字节，不能脱离本机轨迹重算全部动作差异；加--local-output可复算。

运行：python evidence/research/P7_TASK2_1_20261103/verify_evidence.py；本机复核加 --local-output code/outputs/engineering/p7_task2_20261103_v2_revalidation。均不启动SUMO。

首次108 passed/42临时目录setup错误保留，最终143 passed/7 deselected。v1异常9 m/s²与原误报PASS、Task2便携包保持不变。旧包current-source verifier需用preflight/task_start_sources作为--repo-root；本包也保存那些源码字节。

限制：合成源、进程内单跳、工程候选参数；不是正式资格、采用因果效应或区域风险证明；风险Unknown，无独立Safety Layer，正式定义/Gate/Stage1.1不变。SUMO_HOME/XML schema validation环境warning保留，未为此增加运行。

[最终报告](../../../docs/research/P7/P7_TASK2_1_FINAL_REPORT.md)。
