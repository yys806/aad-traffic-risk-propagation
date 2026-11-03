# P3 Task2 — 控制器消费回执与事件关联最终报告

Task ID：AAD-P3-TASK2-20261103；执行日期：2026-11-03；状态：COMPLETED_ENGINEERING_INTERFACE_SYNTHETIC_ONLY。基线Git：6bf45cdccd8a7628f5d737fb66e8dbc79fe65c1b。实现时存在本任务未提交新增文件，具体dirty快照见fixture provenance。

## 1. 解决的问题和结论边界

Task1确认旧adopted主要来自fixture条件/工程时程，缺策略消费和Message–Decision–Command–Execution关联。Task2新增独立版本化证据接口、关联校验和最小合成验证，让P7可以直接接真实producer边界。现在能够表达并审计“哪个消息进入哪个策略决策、决策形成什么命令、经过何种安全处理、读回何种实际状态”，不再依赖单个adopted布尔。

**实际控制器仍未接线，未得到真实策略消费证据。** Proposed采用边界未升级，日志关联不证明采用引起动作或风险效应。P3基础接口可阶段性收口，下一步交P7真实接入；P5继续负责机制因果识别。

Formal A=0；Independent Qualified Witness=0；F0/Overall TR–TP=Unknown；Stage0.5=CLOSED_WITH_LIMITATIONS；Stage0.6=PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock=BLOCKED；Stage I=READY_ENGINEERING_ONLY；Stage1.1=NOT_AUTHORIZED。统一定义仍为[27项v0.4](../definitions/README.md)。

## 2. 既有能力复用与工程范围

复核Task1报告/三契约及formal_design、stage_i_mechanism、formal_artifacts、formal_runner、communication_observability、stage_0_1_sumo及相关测试。旧Formal schema/生命周期和八列联合轴不能无损承载新外键，因此采用独立JSON sidecar；未改变旧公共接口、生产SUMO控制路径或Formal Parquet schema。

新增[controller_evidence.py](../../../code/src/riskprop/controller_evidence.py)、[合成构造器](../../../code/scripts/p3_controller_evidence_fixtures.py)、[隔离runner](../../../code/scripts/run_p3_task2_controller_evidence_fixture.py)、[定向测试](../../../code/tests/test_controller_evidence.py)。没有重复实现旧风险测量或旧四格设计。完整字段/接口/P7插入点见[实现说明](CONTROLLER_EVIDENCE_IMPLEMENTATION.md)。

## 3. 实现与科研语义

独立schema aad.p3.controller-evidence.v1覆盖14类记录：Source、Message、Send、Delivery、Validation、Controller Instance、Input、Consumption、Decision、Command、Safety、Execution、Action Observation、Risk Observation。record/message/decision/command/execution ID分开；run/pair/block/cell/assignment及vehicle incarnation明确关联。

输入回执来自接收端controller_input角色；消费回执由policy角色在实际策略边界append。本任务只有合成调用，不把角色字符串当成真实性鉴定。CONSIDERED只是过滤/评估，POLICY_INPUT_INCLUDED关联具体decision、策略版本和snapshot；候选纳入清单还检查关键hash/引用完整性，仍为 aad.p3.policy-input-adoption.proposed.v0.1 / PROPOSED。历史adopted=True adapter只注释原字段，创建新回执数为0。

关系支持一决策多消息、同消息多决策、一决策零/多命令、一命令多安全处理/执行区间。显式外键、双向消费清单、payload及版本一致性、run/车辆生命周期和环检查不靠最近时间补齐。已确认结构错误抛EvidenceError；未观察到消费、预期命令/执行缺失、时钟/读回缺失保留Unknown。

安全记录区分未观察、确认无、修改、拒绝、未知。安全修改不会删除消费；实际状态和命令值分开。UNCHANGED决策可保留消费但不发新命令；无动作不能推无风险效应。赋值/P5模式只记录中立metadata，不实现未经批准的Enabled/Disabled语义，不按实际采用筛ITT样本。

时间保留native、映射区间、step/phase/sequence、observed/available。严格区间U<L与同step调用顺序分开；重叠/未知不制造epsilon或填零。比较和事件图都不是因果认证，physical_arrival_status继续UNKNOWN。

## 4. 八类合成验证

全部fixture_only=true、scientific_claim_eligible=false；无真实通信或SUMO。

| 场景 | 实际验证 | 结果 |
|---|---|---|
| A 正常完整链 | 14类记录、完整引用、1个候选策略输入回执、独立实际状态引用 | PASS |
| B 验证后未观察消费 | 验证/输入保留；无虚假回执，不能由缺记录推永久未采用 | PASS，消费Unknown保留 |
| C 过滤器读取 | CONSIDERED不计入候选采用，不要求捏造decision | PASS |
| D 已消费但无新命令 | POLICY_INPUT_INCLUDED与UNCHANGED共存，command_disposition=NONE | PASS |
| E 安全修改 | 原命令、修改命令、实际加速度分别记录；消费和决策仍保留 | PASS |
| F 结构错误 | 孤儿消息、不存在decision、跨run/车辆生命周期、payload冲突、missing command、重复ID七变体 | 全部捕获预期错误 |
| G 重复/过期/多次消费 | 重发、重复送达、多接收者、过期状态、一决策多消息及同消息多周期 | PASS |
| H 时间与缺失 | 同step不同phase/sequence、区间重叠、未知clock、缺读回、右删失 | PASS，Unknown保留 |

关联结果的VALID_WITH_UNKNOWNS是结构验证结果，不是科研PASS。额外测试覆盖幂等、深拷贝、反序列化、拒绝历史升级、非有限数/字符串布尔、无安全记录、失败决策、命令有效期、错误policy/可选message引用、倒序capture悬空决策、非法引用容器等。

## 5. 验证执行及失败记录

影响范围：新增独立身份/时间/记录验证器和合成工具；旧共享接口、科研算子、生产执行与配置未变。采用新增定向测试加四组旧回归，不运行无关全量pytest或全仓compileall。

最终新增测试 **50 passed**（new_tests_sealed.xml）；此前四组原有测试 **42 passed**，在targeted_final.xml的86项运行中与当时44项新增测试一起通过。最终覆盖为50新增+42旧回归=92项，**不是声称一次运行92项**。最终合成runner七个有效场景与F七异常全通过。

首次新增测试保留34 passed / 1 failed / 1 setup error：测试预期将14条完整链误写13，以及Windows临时目录父路径未建好；修正测试预期、使用存在的本任务输出父目录及新basetemp后通过。后续加约束后按受影响新模块复测，未改无关旧测试；所有执行摘要和XML SHA见[test_results.json](../../../evidence/research/P3_TASK2_20261103/test_results.json)。

语法、文档严格验证、证据导出/核验、历史hash、窄Git快照复算及diff检查结果以[validation.json](../../../evidence/research/P3_TASK2_20261103/validation.json)实际记录为准。Git提交/push另由任务收尾核验，不用运行时基线SHA假称最终提交。

## 6. 历史保护和可复算证据

179个选定历史输入绑定包含旧生产模块/测试、统一定义、Task1文档、Task7/8/时间回溯便携证据及Task20原fixture小文件，未修改。Task20原SHA256SUMS另外逐文件核验。没有重新读取/重哈希全部Task7/8原始大轨迹，本任务没有访问或写入这些输出；不把选定输入hash检查夸大成全原始数据重审。

新增[便携证据](../../../evidence/research/P3_TASK2_20261103/README.md)保存schema、7个合成fixture、关联结果、F异常复算、实现/输入/输出hash、测试摘要、只读复核器。原始测试XML及开发输出留本机code/outputs/analysis/p3_task2_20261103_v1，不复制大型数据或整个项目。便携检出允许已登记的历史运行时/Git blob两种字节表示，不改旧历史文件；当前新实现和合成包使用明确LF/二进制字节规则。

## 7. 研究者待决事项与最高价值下一步

仍待决定：Proposed策略输入采用边界是否正式批准；P5 Enabled/Disabled如何切断路径及随机化/资格总体；P4动作比较与阈值；真实日志可信边界和时间映射/误差资格。未冻结通信TTL、动作阈值或任何新科学参数。

建议下一项是**有限P7真实控制路径接线与证据读回**：复用本接口，把真实接收端、策略输入/决策、命令API、安全层、simulationStep后状态和P4观测引用逐点接入。生产接入/先导运行须取得对应授权，本任务没有自动开始。P3无需再设计另一套基础数据结构；真实采用、普通物理到达、区域风险和机制因果证据仍分别建立。

本次新增SUMO/TraCI运行=0、seed=0、Independent V=0、locked holdout读取=0；未改论文、正式config、Gate、Protocol Lock及统一定义。P2既有359/47/0与版本化359/119/0、Qualified=0及双η结论全部保持。
