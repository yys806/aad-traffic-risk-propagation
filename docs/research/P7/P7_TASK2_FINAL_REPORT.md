# P7 Task2 — 消息驱动控制器与端到端证据链

Task ID：AAD-P7-TASK2-20261103；WP3；2026-11-03。

**状态：ENGINEERING_IMPLEMENTED_SUMO_ACCEPTANCE_BLOCKED。未达到 ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS 验收条件。**

## 1. 已实现与未完成

已新增独立纵向策略、版本化工程 Payload、单跳实际收发/验证、运行级固定 Adoption gate、真实策略消费/决策、setMaxSpeed命令、post-step状态/生命周期、P3证据与P4动作/测量状态引用。D1–D8及Agreed Adoption amendment已登记，旧Proposed保持。

三种条件各一次，单一工程seed=20261103。A/B完成工程检查；C形成真实消息消费→决策→命令→SUMO动作链，但发生emergency braking，不可判烟测通过。原v1源码/config/输出/log保留；v2参考值变化约束与停止检查已实现，仅离线测试，未重跑SUMO。整体工程验收未完成。

## 2. 影响判断与保护

新增独立P7模块、执行/封装脚本、两版工程config、定向测试、文档/证据；P3公共模块仅双版本兼容及严格匹配，历史fixture源显式选择legacy。涉及控制输入/身份/时间/证据接口，采用新策略/P3及旧Stage0.1非启动接口、fixed Follower拒绝接口、Stage0.5纯测量/接口回归。

不改Formal科研测量、正式config、四格/P1 ITT、定义v0.4/27项、Gate/Lock、Stage1.1、历史Task7/8/16/20输出。未运行全仓pytest/compileall。7个会启动SUMO的旧测试明确deselect，不伪称通过。选定205个历史小文件逐字节保护，不重读历史大轨迹。

## 3. 控制器如何工作

[D1–D8](P7_RESEARCHER_DECISIONS_20261103.md)是Agreed方向，具体参数仍工程候选。消息只有生成时可知的source/risk/target/空间/有效期信息，无未来轨迹或加速度命令。接收端逐周期验证，门控后组装实际PolicyInput，策略结合本地速度、位置、lane/road、限速、leader/gap计算目标速度参考。详见[规格](P7_LONGITUDINAL_CONTROLLER_SPEC.md)。

只有合成源生成时刻取自工程config；命令由真实消息有效性、门控、本地状态及策略决定，不是固定时程命令。Disabled仍接收/验证/记录，策略messages=[]，有效消息REJECTED/ADOPTION_DISABLED关联实际decision；Enabled真正传入策略才记录POLICY_INPUT_INCLUDED。adoption_mode/assignment显式、稳定、缺失fail-closed；无正式随机化器/概率冻结，不根据动作反推Adoption。

## 4. 原生跟驰、API与动作

复用原dual-corridor网络构建，不运行Stage0.1固定时程。两车Krauss，原生目标max=20 m/s、leader max=12 m/s，均为工程参数。唯一目标setter为traci.vehicle.setMaxSpeed；无setSpeed/setAcceleration/setSpeedMode/moveTo驱动轨迹。

command_id在API边界产生，issue/ack/getter与实际动作分开。simulationStep后读实际x/v/a/leader/gap并关联active command。同一参考不发新命令，旧命令可跨多步；消息失效写回原20 m/s，v1在8.0 s实际释放/回读。车辆实际step3进入后至退出连续观察，退出后不再控制。

三条件speedMode全31，actual speed与getSpeedWithoutTraCI最大绝对差均0，存在前车约束下低于单车上限的样本，支持原生参与；这不保证任意上限突降均正常，不可代替异常检查。

## 5. 必须保留的失败 P7-T2-ENG-001

Enabled v1在SUMO time=2.80 s报告emergency braking：decel=9.00 m/s²、wished=4.50 m/s²；实际轨迹保留对应减速度。原入口只检查碰撞/teleport，漏查emergency warning，原run_summary.status误报PASS。

**该运行结束后才发现，不能声称在2.80 s已即时停止。** 两日志复制同一warning，独立audit去重。原PASS不改写，派生acceptance=BLOCKED_ABNORMAL_BRAKING。发现后新增SUMO=0，不挑seed、不追加条件/参数搜索或循环重跑。

原因：maxSpeed突降至10 m/s可触发SUMO emergency braking，mode=31不能保证只使用常规减速度。v2在策略内按实际当前速度约束参考值下降，并加入emergency getter、实际减速度/日志停止检查；不增加Safety Layer。当前入口拒绝无参考变化约束的v1配置。

v2仅单元验证，能否消除异常、真实SUMO执行及整体验收均Unknown/NOT_EXECUTED。本任务不在停止后追加SUMO来取得通过。

## 6. 三条件结果

| 项目 | No Message | Disabled | Enabled v1 |
|---|---:|---:|---:|
| 消息生成/接收 | 0/0 | 1/1 | 1/1 |
| Validation / Input / Consumption | 0/0/0 | 334/334/334 | 334/334/334 |
| POLICY_INPUT_INCLUDED | 0 | 0 | 52 |
| Decision / Command | 351/0 | 351/0 | 351/2 |
| Execution | 0（无命令） | 0（无命令） | 326 |
| Action / Risk reference | 352/1 | 352/1 | 352/1 |
| 在场轨迹行/退出行 | 351/1 | 351/1 | 351/1 |
| 碰撞/teleport | 0/0 | 0/0 | 0/0 |
| 独立Safety记录 | 0 | 0 | 0 |
| P3结构 | VALID | VALID_WITH_UNKNOWNS | VALID_WITH_UNKNOWNS |
| 工程验收 | PASS | PASS | BLOCKED_ABNORMAL_BRAKING |

B/C原Payload hash相同。A/B实际连续轨迹和策略输出一致；C策略输入/输出可区分，且有真实setter/post-step readback。描述差异见[轨迹摘要](../../../evidence/research/P7_TASK2_20261103/trajectory_summary.json)，仅ENGINEERING_DIAGNOSTIC_ONLY，不是Adoption-induced Action Effect。

## 7. P3/P4接线、Safety及历史

[接口说明](P7_CONTROLLER_EVIDENCE_INTEGRATION.md)给出14类producer、ID/多对多、phase、Unknown、sidecar/manifest。Enabled实际产生13类，Safety无独立producer因此零记录；manifest登记NOT_INCLUDED_BY_RESEARCHER_DECISION，native约束另作环境事实。

新P7消费使用Agreed v1，旧Proposed契约/输出/证据字节不改，旧sidecar可读且roundtrip保留边界；P3 schema仍v1，旧adopted=True不创建回执。

P4动作引用实际连续轨迹，不用参考值或API参数代替。风险只引用既有compute_sumo_measurements的per-state TTC/quality状态；没有重算正式rho/P2，没有自行指定正式Region/Cohort/Window，risk effect Unknown。v1对既有Formal version的引用不授予正式资格；当前适配器使用自身reference version并单列existing Formal version。

## 8. 测试及所有失败

首次新/P3测试72 passed/1 failed：新journal默认版本拒绝旧直接重放；已修复兼容，旧测试未改。第二次80 passed。首次含实际capture的离线回归127 passed/4 failed/7 deselected：本任务测试错误假定step1已进入，且重复计算两日志同一warning；按实际生命周期/唯一warning修正，不修改轨迹/log。

最终封口：**136 passed / 7 deselected**，覆盖新P7、P3和指定旧接口/测量；实际capture测试只读取已运行SUMO输出，不再启动SUMO。测试通过包含异常拒绝断言，不是把Enabled烟测“测绿”。各次XML SHA/摘要见[test_results.json](../../../evidence/research/P7_TASK2_20261103/test_results.json)，原XML/log全部本机保留。临时命令路径/转义错误无文件改动，保留任务工具记录。

完整外部artifact、Payload/snapshot、decision-command-execution、run mode/incarnation、P3图及captured v1源逐文件核验。文档strict、exporter/verify、12文件定向语法、Git索引字节隔离复核及SHA检查见便携final_checks.json，最终封口后复核日志仅本机保存，不扩大无关历史清理。

便携验证器首次比较原audit时失败：原封装省略冗余timeline，新验证器误作完整JSON相等。已按原投影比较全部其余audit字段，完整sidecar仍重新执行P3验证；原audit与运行记录未改。首次strict文档验证发现便携包ID未在results反向登记；已补齐明确engineering-only的独立分类与双向索引，不改既有研究Gate/阶段。随后strict检查要求legacy paper_locations非空，按已有工程登记惯例仅链接工程报告并注明不是论文。失败与后续复核结果记录于final_checks.json。

## 9. 证据、环境与参数

原始独立输出：code/outputs/engineering/p7_task2_20261103_v1；便携：[P7_TASK2_20261103](../../../evidence/research/P7_TASK2_20261103/README.md)。初始磁盘约202.4 GB可用，工程输出远低于50 MB/条件规划。Windows原生、Python/SUMO/TraCI版本、binary/source/config/input hashes、baseline SHA与dirty状态、seed、实际命令均登记。captured v1的9个入口/直接依赖源已保存，不冒称完整传递依赖闭包；当前补齐登记尚未SUMO验证。

正式风险级语义/资格总体、TTL/通信参数、随机化概率/干扰域、P4阈值/持续/Region/Cohort/Window及P6统计未冻结。factor/headway/参考下降率/工程生成和有效时间/seed/道路范围/原生工程数值仅ENGINEERING_CANDIDATE_NOT_FORMAL，无搜索/优化。

## 10. 科研状态、后续与Git

Formal A=0、独立Qualified=0、F0/总体TR–TP=Unknown。Stage0.5=CLOSED_WITH_LIMITATIONS、Stage0.6=PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS、ProtocolLock=BLOCKED、Stage I=READY_ENGINEERING_ONLY、Stage1.1=NOT_AUTHORIZED。不启动Pilot、Independent V、locked holdout或论文修改。

基础接口无需重复设计。首先需后续授权一次有界v2 SUMO再验收，保留当前失败；通过后P5处理合格消息总体、稳定assignment、Enabled/Disabled、完整assignment-level ITT和Adoption/Action/Risk识别，结合P4/P6/P8。本任务不自动启动后续。

Context Consistency Check同步状态、背景、架构、数据流、模块、实验、决策、问题/changelog及注册表；统一定义仅链接不改。

整体SUMO验收未完成，按AGENTS §8.G不提交/推送未完成或验证失败科研产物：Commit=None、Push=None；保留本地修改与失败证据。
