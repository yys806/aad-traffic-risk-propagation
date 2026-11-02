# P2 Task8 — Independent V决策

统一定义仍为[Task6 v0.4、27项](../definitions/README.md)。Task7原575完成/1失败、truth v2与359/47/0历史记录不改。所有Task8结果为校准/补充支持，Independent V种子消耗0；不是现实交通验证或AAD核心假设证据。

Formal A=0，独立Qualified=0，F0/总体TR-TP Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS；Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock BLOCKED；StageI READY_ENGINEERING_ONLY；Stage1.1 NOT_AUTHORIZED。

## 固定候选Independent V决策

**NOT_EXECUTED_TRUTH_SUPPORT_INSUFFICIENT**。V实际Positive=0、Negative=0、seeds=0，不执行部分验证，不把R2或旧Task7重新命名V。

固定配置验证的科学缩域：每层一组中心参数、每密度一档固定MAX源条件，保留全部三层/三密度和N0/N1/A0；不认证完整剂量范围、局部脉冲或稳定邻域。局部脉冲另作补充诊断，不能用该狭域认证替代局部性能。J=78完整登记：state63（N0/N1 FPR18、主阳性及时miss9、四来源场景Unknown36）；归属15（FAR9、source Unknown3、Qualified timely miss3，其中金标准缺失）。延迟上界4s和及时灵敏/漏检共用同一个二项成功谓词，不重复计信息。

βV=.05，good FPR/FAR=.002对.01、good miss/Unknown=.01对.05，分配单项power=1−.1/J，exact逐n搜索。完整78声明的90%功效仍未建立，因3个Qualified真值端点不可检验。即使假设所有阳性可实现，negative需3197/同质格、positive需633/格，合计至少30672新run；理想4-worker 7.95h、已采用串行31.81h、仅raw约41.49GiB。只做state63仍需28965run、理想7.51h/39.18GiB。不是沿用Task7 J765的成本，也不是零失败最有利n冒充power。

缺失状态支持：[{"layer": "cohort", "density": "low", "reason": "no a1b1 positive under either bounded source design"}, {"layer": "cohort", "density": "medium", "reason": "no a1b1 positive under either bounded source design"}, {"layer": "macro", "density": "low", "reason": "no a1b1 positive under either bounded source design"}]。源归属truth不足、现有候选边界/局部性能、资源和必要独立样本共同阻断；不能由增加seed假定阳性产率1。当前剩余资源详见decision JSON，已完成工作仍计在2h/10GiB总预算内。

| η情景 | 及时检出目标 | 证书Positive n/格 | Negative n/格 | 理想运行下界 | 4-worker理想h/串行h | raw GiB | CDF Hoeffding n/格 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.01 | 0.9975 | 15571 | 15571 | 186852 | 48.4/193.8 | 252.8 | 154374 |
| 0.05 | 0.9875 | 3106 | 3885 | 44283 | 11.5/45.9 | 59.9 | 6175 |

η仅情景，miss/Unknown各η/4，正式αmeasure未冻结，另以.005/J规划，绝不等同βV=.05。CDF K45来自本次更窄的单源条件×3层×3密度×5时点，不是Task7五设计层的K225；仅描述有限状态proxy，非F0。finite_state_cdf_budget.csv按R2同质格分别列detected-early、Unknown和采样余量，n0的格保持Unknown。

完整式detected-early + Unknown + εsampling + mdelay + εtruth/clock/measurement <η。独立V的及时检出/FPR/FAR、真实任意最早物理onset/独立延迟界、Formal A/Qpre/F0、正式H*仍缺失，完整预算不可求值；两个η情景均Not established/Unknown。上述样本成本也建立在极有利假设上，不能代表已达到桥接。

成本复核留痕：首次η=1%估算仅给对照格分配FPR所需n，未同时覆盖更严格Unknown端点；最终表已取二者最大值15571/格，原估算与修订原因保留于initial_statistical_plan/和analysis_revision.json。无truth、detector输出或候选评价改动，不把首次估算伪称正确。

## 复现、验证及Context Consistency Check

268计划单位、267完成、1失败/未执行，804分层标签，2412离线参数评价。完整运行碰撞0、teleport0、target setters 0。目前新增输出0.369GiB；预算计时30.5分钟，硬上限2小时/10GiB。每单位raw/truth/audit、旧源输入、代码/配置、seed/split均有hash和Git baseline/dirty记录。

定向测试覆盖源onset陷阱、b1时间跨度、identity不拼接、seed分离和Unknown失败；复用Task7算子/精确二项定向测试，不跑无关全量pytest/compileall。独立复算核查全部新run/label hash、Task7原hash、中心指标和16份exact计划；文档strict-git、evidence exporter/verify及纯Git字节保真实际结果见[verification_record](../../../evidence/research/P2_TASK8_20261102/verification_record.json)。启动原失败与一次工程续跑完整保留，不伪称首次通过。

统一定义v0.4/27项不变；AI_CONTEXT/状态/索引/注册/参数证据账本按真实结果同步。旧账本E61–64在Task6/Task7重复，历史表不改，本任务用Task命名空间注明歧义且新增E66以后。无生产模块/正式配置、AGENTS、论文、locked holdout或上游DRIFT变动。Formal A=0，独立Qualified=0，F0/总体TR-TP Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS；Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock BLOCKED；StageI READY_ENGINEERING_ONLY；Stage1.1 NOT_AUTHORIZED。

本地输出code/outputs/calibration/p2_task8_20261102_v1/；[便携证据](../../../evidence/research/P2_TASK8_20261102/README.md)仅元数据/小表/运行摘要/原hash与必要源快照，无raw大表、日志、图片或密封键。最终Commit/Push以Git核对为准，不写循环自指SHA。
