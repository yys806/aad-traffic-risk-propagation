# P4 Task2 portable evidence (2026-11-04)

Task AAD-P4-TASK2-20261104，IMPLEMENTATION_COMPLETE_WITH_LIMITATIONS。D01–D08 Agreed；工程契约aad.p4.measurement.v1。所有examples仅SYNTHETIC_VALIDATION_ONLY，不是交通实验/校准/独立样本。

## 内容及复核

- examples/：版本化Action/区域输入输出、完整点、部分缺失、UNKNOWN_SCOPE、同N错身份拒绝；synthetic_source.json真实字节来源。
- mathematics.json + verify_mathematics.py：15项独立Fraction复算，三车区间[7/36,3/4]、点5/12；不导入生产函数。
- tests.json：最终172通过（88新+84历史），两轮开发期失败原始log/JUnit hash与修正，最终进程guard无阻断尝试。
- protected_bytes.json：554既有文件原字节及四定义append-only原前缀；v0.4/27项不变。
- environment.json / source_manifest.json：基线Git SHA、环境、代码/测试/文档/配置SHA；交付commit由包含本包的Git revision确定，避免自引用。
- existing_p7_scope.json：只读复用真实P7；352行单target，无完整scope，不能提供区域Y。
- context_consistency.json / project_checks.json：上下文、文档、exporter和Git字节检查。
- SHA256SUMS / verify_evidence.py：包内全清单及源绑定核验。完整原始pytest日志留本机code/outputs/audits/p4_task2_20261104，不复制大表/日志。

标准库独立复核：python evidence/research/P4_TASK2_20261104/verify_evidence.py --repo-root .

只随包核验（无仓库也可）：python verify_evidence.py；python verify_mathematics.py examples

重新生成工程例子：python code/scripts/validate_p4_measurement.py --examples --output <新的独立目录>。实际JSON输入使用--input和--output；来源字节核验调用validate_bundle(..., artifact_root=...)。这些命令不会启动SUMO。

独立hash证明文件一致性，不能自动证明真实名单覆盖完整。P3schema/原Formal/config/历史证据不改；新合成例不含正式region/window数值。无Action科学阈值/T_U，风险因果/T_R Unknown，Gate/Lock/Stage1.1不升级。

Task1旧包绑定基线58c7e68861b283d7f31e7bafb860cea03dc2e76d；四定义本次经授权append后应在该历史revision核验Task1旧source_manifest，不能篡改历史包适配新字节。

字节视图：默认核验原工作区字节；--byte-profile git-blob用于从Git索引/提交直接提取的blob视图。source_manifest与保护表分别记录两种SHA，4处既有换行差异不通过改写原文件消除。定义旧前缀亦各自绑定，保持历史语义及原始工作区字节。
