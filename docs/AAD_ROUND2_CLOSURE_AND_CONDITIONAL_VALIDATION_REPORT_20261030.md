# AAD_ROUND2_CLOSURE_AND_CONDITIONAL_VALIDATION_REPORT

日期：2026-10-30（Asia/Shanghai）。项目：AAD。状态：**已完成立即可交付工作；条件阶段保留 Blocked，未降低准入标准。** 科研决策权归研究者。

## A. 完成内容

### WP1：Round2 关闭与正式决策

已将原 minGap=1.0 源区候选登记为 `CLOSED_FAILED_ORIGINAL_SOURCE_CONDITION`。它只执行过一次 seed20261201、420 s；Rule A PASS、源区 Formal P2=0、目标诊断1保留，原始失败、配置、日志及证据未改。不得以另一 seed、窗口、source/target/cohort、阈值、时长或扰动挽救原分支。独立固定前车对照中的 minGap1.0 属新条件任务。

研究者已批准 C 作为一般 Formal P2，D1 保持独立 same-native-lane 局部分母；物理路径另按 B 的五项真实时间化见证判断。当前正式 C 已实现，无需修改生产代码。新增 B 完备性检查只核查是否提供五类带出处的记录，不能替代实际物理审查；现有路径仍 Unknown。决策详见 [正式决策记录](AAD_ROUND2_RESEARCH_DECISIONS_20261030.md)。

直接读取封存 B00 A03/Round2 XML，核实只存在五个 vType 的 minGap2.5→1.0 差别；异质 tau、sigma、车辆/路线/到达记录其余字段一致，network.net.xml 与 run.sumocfg 字节相同。审计不代表固定前车工程可行性已经通过。

### WP2：Simulator–NGSIM Formal Comparability Matrix

完成8维矩阵、16个原Task2合成案例及8个新探针；Task2–7.2的8个历史包95项列载荷原SHA通过且前后不变。C资格、正常可靠正gap/closing域的数学测量及D1独立性有明确工程证据；一般科学等价性仍 Unknown，`formal_equivalence_accepted=false`。

保留三类 C 以外冲突并停止相关语义修改：显式中断两端处理不同；formal projection重建原始frame/clock；预计算TTC/Unknown标记及leader自身观测支持不同。三者均附 Documented Intent、Actual Implementation、Evidence、Affected Files、Conflict、Status: Awaiting Researcher Decision。详见 [比较矩阵](SIMULATOR_NGSIM_FORMAL_COMPARABILITY_MATRIX_20261030.md)。

### WP3：官方英文询问信

发送授权已 Agreed，拟收件人为 data.itsjpo@dot.gov；实际状态 **Blocked / Not Sent**，没有compose/send动作、实际收件人或发送回执。读取已有Edge窗口返回原文 `Computer Use app approval timed out`，无法核验已认证发信会话；这是应用访问授权超时，不是自动审核拒绝或邮件服务失败回执。原稿位于Task7.2便携目录而非登记工作目录，SHA212d3f2299138061d6ee5a60dfb0be0fab8f95d8403197e3b620ab5359c981ee未变。署名占位保留，本地未发送EML已备妥。详见 [独立发送报告](AAD_ROUND2_PROVIDER_INQUIRY_DISPATCH_20261030.md)。

### 条件工作包

[VIDEO_ACQUISITION_GO_NO_GO](VIDEO_ACQUISITION_GO_NO_GO_20261030.md) 为 **NO_GO**：许可、时间锚、空间覆盖均未通过。磁盘容量快照足以容纳约2.497 GB基础压缩+解压占用，但最终临时空间、获取方式和校验流程仍未验证。没有下载任何视频、整包或新相机，没有实际预注册名单、片段、Review ID身份映射或人工真实性结论。

固定前车输入和独立物理审查均 **Blocked / Not Run**。已核查历史324次重放的确切三seed、随机性与适用边界，提交 [最小配对矩阵提案](FIXED_LEADER_PAIRED_EXPERIMENT_PROPOSAL_20261030.md)：20261101/20261102/20261103，3重复/臂/合格片段、共6N次；N及物理输入未定，精确方案尚需研究者确认。未自动执行。

[ROUND3_CANDIDATE_READINESS_REPORT](ROUND3_CANDIDATE_READINESS_REPORT_20261030.md) 为 **NOT_READY**；缺独立物理参考及配对观测，不能诚实宣布形成了经机制证据支持的新候选。候选方向仅保留已批准的机制判别问题，不引入新模型或参数搜索。

## B. 修改文件

完整逐文件清单及原因保存在本轮主证据包 `modified_files.json`；不把本地原始日志或媒体纳入Git。主要分组：

| 文件/范围 | 修改原因 |
|---|---|
| code/scripts/prepare_stage_0_5_round2_closure.py、对应定向测试 | 封存XML、历史seed随机性、B记录完整性和条件状态的离线可复现审计 |
| code/scripts/audit_stage_0_5_round2_closure_comparability.py、对应定向测试 | 有界接口比较、成员/onset反例、历史证据验证 |
| 本总报告、正式决策、比较矩阵、官方发送、视频NO_GO、固定前车提案、Round3就绪报告 | 分开登记已批准决定、工程事实、未知量与条件阻断 |
| AI_CONTEXT/00、04、05、06、07、08 | 同步当前状态、工具导航、实验、Agreed决策、问题及变更 |
| docs/PROJECT_REGISTRY.json、RESEARCH_STATUS、PROJECT_INDEX、RESULTS_INDEX、STAGE_INDEX、HISTORY_INDEX、CHANGELOG | 正式注册关闭状态、新工作包及保留历史入口 |
| .gitattributes（仅11个本轮新文件） | 固定被哈希绑定文件的原有LF/CRLF字节，做小型Git对象检出核验，不改历史换行 |
| 三个本轮 evidence/results/RES-AAD-ROUND2-* 包、evidence/EVIDENCE_MANIFEST.json | 输入/代码/config哈希、命令、环境、失败与条件状态的便携证据 |

AGENTS.md、生产 code/src/riskprop、正式config、历史实验与证据包、私人物料均无修改。

## C. 验证结果

| 状态 | 内容与范围 |
|---|---|
| Passed | WP1独立7项定向测试（0.14s）、两个新增Python文件py_compile；仅覆盖元数据/配置与B记录守卫 |
| Passed | WP2新增13项全部通过；最终5文件定向范围100 passed、3 deselected（16.38s）；新脚本/测试AST语法通过 |
| Passed | 16个原Task2合成案例和8新探针已执行；8历史包95项SHA及不变性验证 |
| Failed（保留） | WP2首次100 passed/3 failed，第二次Windows --deselect路径未匹配仍100/3；完整原始日志仅保留本地，便携test_attempts记录原失败 |
| Blocked / Not Passed | 三个既有Parquet读写测试缺pyarrow/fastparquet；一次有据环境检查后不安装依赖、不修历史测试；第三次仅排除这三项 |
| Passed | PROJECT_DOCS_OK；三个新RID受限export/verify均通过；38个本轮小型Git检出对象逐字节相等；保护范围和Context Consistency Check通过，最终暂存版本再次复核 |
| Not Run | SUMO/TraCI、新真实/仿真轨迹、第三窗口、locked holdout、视频获取、实际盲审/固定前车实验、全量pytest、全仓compileall |
| Not Applicable | 确定性合成/元数据审计的新随机seed、实验重复、机制效应区间及物理真值认证 |

未把三项被排除测试写成通过；未把工程通过写成科学等价。初始schannel远端查询、Python输出编码、默认沙箱Git索引写权限导致的首次strict-git未追踪、Windows文本模式checkout-index清单错误均保留；Git已获必要索引写授权，文档检查和NUL清单检出随后通过。前者用GitHub API及命令级openssl只读查询核实，未修改全局Git设置。

## D. 科研结果分层

- **Observation**：源区Formal P2仍为NGSIM167/159、SUMO B00/Round2为0/0；目标1只作诊断。当前C已实现；成员/时钟/质量支持存在可复现接口反例。
- **Interpretation**：当前接口只有受限可比范围；这不是零源区事件的因果解释，也不是科学等价裁决。
- **Hypothesis**：网络内部扰动生成不足与相同leader输入下响应不足仍不能区分；Task6换道/leader现象不指定因果机制。
- **Proposal**：先满足独立许可/时空/物理质量条件，再确认有限配对实验矩阵。三seed不构成统计功效保证；不自动增加重复或选有利seed。

## E. 条件授权状态

| 条件任务 | 当前状态 | 原因 |
|---|---|---|
| 官方许可 | Blocked | 缺逐文件适用条款与人审访问权限澄清 |
| 时间映射 | Blocked | 缺PTS/time base/FPS/原点、多点锚、offset及drift |
| 空间覆盖 | Blocked | Camera7/8仅地理候选，完整source/车道覆盖未认证 |
| 视频获取 | Blocked | 前三项未过；0文件 |
| 盲审 | Blocked | 无合格媒体，0案例/0判断；上限36及预注册要求保留 |
| 固定前车输入 | Blocked | 物理输入、公平初态、实际工程可行性及精确重复批准未齐 |

这些任务拥有条件授权但条件未满足；“Blocked”不表示研究者从未批准方向，也不表示风险事件为假。

## F. 未解决问题

1. 官方信尚未发送：需可访问的已认证正式发信渠道及核实署名；已有发送授权持续有效，无需重复批准发送方向。三类C外接口契约冲突需研究者明确决定；未在本轮自行改变连续性、身份或时钟语义。
2. 视频逐文件许可、时间、空间与人审访问资格仍Unknown；任何费用、协议或机构授权需新决定。
3. 新配对seed/重复矩阵为Proposal；合格片段数、初态、horizon、可实现leader跟踪误差及wall-time成本仍Unknown。
4. 三个历史Parquet测试依赖缺失；本轮不安装或修改无关历史输入。
5. Task6行级对照不等于唯一后车独立、旧METHOD-EXPANSION元数据SHA不符/缺件等历史限制保留，不启动扩展分析。
6. 未形成已获物理与机制支持的Round3候选；不推进Stage0.6、Protocol Lock或StageI。

## G. AI_CONTEXT 更新与一致性

实际更新00_PROJECT_STATE、04_MODULE_MAP、05_EXPERIMENTS、06_DECISIONS、07_KNOWN_ISSUES、08_CHANGELOG。01研究背景、02生产架构、03生产数据流无变化理由明确，不为数量更新。历史段落原文保留，新增当前入口明确A/B/C及获取授权的旧pending描述已被本次Agreed决策前瞻替代。注册表、阶段/结果/历史索引与机器结果对应，保护已有76条便携登记和全部既有result内容；52个本轮Git改动逐文件列在modified_files.json。

## H. Git与复现

入场工作区clean、main=`80abab044063803219f6ceadfeb3562c3939aaa1`；GitHub get_commit(main)与命令级openssl ls-remote一致，故没有新增远端提交需要迁移。每个独立工作包分别采用Conventional Commit，验证后推送main。最终commit列表、push回执、远端SHA与clean状态由发布完成后的本地 `code/outputs/formal/calibration/aad_round2_closure_20261030/git_delivery_receipt.json` 及最终回复记录；本报告不自称包含自身尚未生成的Git SHA。

可复现命令、解释器、输入/源码/config SHA和执行时dirty状态见各包source_bindings及validation_record。本轮完整输出位于code/outputs/formal/calibration/aad_round2_closure_20261030/及比较审计的独立目录；原始失败日志、邮件交接稿与UI截图（如有）仅留本地。便携证据不含原媒体、原轨迹、HTML、图片、日志或密封身份键。
