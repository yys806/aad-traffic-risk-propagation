# P7 Task2 工程证据 — 2026-11-03

Task ID: AAD-P7-TASK2-20261103。

**ENGINEERING_IMPLEMENTED_SUMO_ACCEPTANCE_BLOCKED。此包不是正式科研结果，也不是已通过的完整工程验收。**

No Message、Disabled、Enabled各一次SUMO 1.26.0运行，seed=20261103。前两者工程检查通过且实际轨迹一致；Enabled v1产生真实消费、决策、命令与状态读回，但2.80 s出现9.00 m/s² emergency braking。原运行结束后才发现；原摘要误报PASS原样保留，独立派生验收明确BLOCKED_ABNORMAL_BRAKING。此后SUMO运行=0。

当前v1.1/v2配置增加策略内参考下降率约束和异常停止检查，仅离线测试，不冒称已经SUMO验证。不增加独立Safety Layer。正式A=0、Qualified=0；区域风险效应Unknown；不启动Pilot/V/holdout，Stage1.1仍NOT_AUTHORIZED。

## 内容与范围

- validation.json：真实任务状态、停止边界、正式科研资格及Git限制。
- controller_config.json与captured_controller_config_v1.json：当前离线修正版与原失败版，均ENGINEERING_CANDIDATE_NOT_FORMAL。
- conditions/：三条件原配置/摘要/provenance/命令区间及压缩完整P3 sidecar、完整关联audit。旧PASS不作验收依据。
- association_validation.json、controller_evidence_manifest.json：本机全外部字节验证、完整图、Payload和snapshot字节样本；不以样本声称全原始数据可便携复算。
- source_manifest.json、captured_source_v1.json.gz：当前源码hash与原捕获9个入口/直接依赖源码字节，不声称捕获完整传递依赖闭包。
- trajectory_summary.json：ENGINEERING_DIAGNOSTIC_ONLY实际轨迹描述，不证明Adoption-induced Action Effect。
- test_results.json、historical_protection.json、official_sumo_api_sources.json、schema_versions.json及SHA256SUMS：失败历史、定向测试、205文件保护及版本来源。
- verify_evidence.py：只读检查本包所有字节、完整图、旧捕获源码字节及选定Payload/snapshot；不启动SUMO。

完整原始轨迹、逐步外部JSON、CSV、SUMO和测试日志仅保留在本机code/outputs/engineering/p7_task2_20261103_v1，不进入便携证据。不存在正式Region/Cohort/Window，风险引用保持Unknown。

## 复核

仓库根目录运行 python evidence/research/P7_TASK2_20261103/verify_evidence.py。
本机完整外部字节复核加 --local-output code/outputs/engineering/p7_task2_20261103_v1。
复核通过只证明声明范围的完整性/关联，不使Enabled烟测通过。

[最终报告](../../../docs/research/P7/P7_TASK2_FINAL_REPORT.md)；[控制器规格](../../../docs/research/P7/P7_LONGITUDINAL_CONTROLLER_SPEC.md)；[接口接线](../../../docs/research/P7/P7_CONTROLLER_EVIDENCE_INTEGRATION.md)。
