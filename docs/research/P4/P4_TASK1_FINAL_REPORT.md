# P4 Task1 最终报告

Task ID：AAD-P4-TASK1-20261103。日期：2026-11-03。WP1：Action → Risk → Regional Risk测量审计与操作化。

**最终状态：AUDIT_AND_OPERATIONALIZATION_COMPLETE_WITH_LIMITATIONS。** 本次交付完成源码审计、测量规范、外部数据契约提案、集中待决清单和可核验便携证据。不是完整区域风险生产管线已部署，不是正式效应测量就绪。新增交通/SUMO/TraCI运行、seed、Pilot、Independent V、holdout读取均0。

## 1. 目标、进入状态与范围

先依项目规则核对AI_CONTEXT当前状态、注册表/索引、PROJECT_CONTEXT，再核对统一定义、P1/P2/P3/P7最新有效资料、当前源码/config、已有测试与证据。基线HEAD=f772c860968fd5901894bcfed5475b32fd027b0e，main，工作区干净。P7 Task2.1已ENGINEERING_INTEGRATION_COMPLETE_WITH_LIMITATIONS，v1异常失败保持历史。此次不重复P7复验或P2参数实验。

统一定义仍AAD-SCI-DEF-20261102-P2T6-v0.4 /27项，无Definition ID/公式批准状态变更。P7 D1–D8、Agreed Adoption不变。源码、Formal config、P1模型/estimand、P3schema、历史P2/P7及证据保持原字节；开始时封存535项保护文件hash用于结束比对。

影响判断：只新增P4文档/CSV/JSON、便携离线核验脚本，以及项目状态/索引导航；涉及测量接口说明，不改变生产科研逻辑。六个相关离线测试文件及确定性边界例子足以覆盖本次“事实核验”目的；不跑全仓pytest/compileall。已知可能启动SUMO的旧native测试未选入；进程守卫禁止pytest内任何外部进程。

## 2. 主要发现

| 发现 | 已验证事实 | 研究含义/处理 |
|---|---|---|
| 动作对象分层 | Decision、Command、ACK/getter、post-step状态分别存在 | 运动学v/a是响应观测，不自动等同全部真实执行器输入U*或因果效应 |
| A01/A02动作比较限制 | 仅按vehicle/time匹配速度；无incarnation/clock检查，可跨缺口和外延末点确认 | 当前first_action_change_time_s不能作为完整Action Effect Estimator；缺陷与建议已登记，未修改科学核心 |
| Formal点贡献 | 指数rho、质量界及固定窗积分有真实实现 | P2事件TTC阈值不截断rho；Unknown不补零 |
| R01名单守卫缺失 | equal_vehicle_average只平均输入列表，无外部完整N/同窗核验 | 缺成员被删会改变分母；尚无已验证完整区域汇总器 |
| R02支持限制 | 积分仅时间裁切；no-leader/切leader可使区段保守Unknown | 几何区域边界和连续性需上游证明，不伪造输入压窄界 |
| R03辅助暴露输入不一致 | valid=True但TTC=NaN可得到暴露0 | 明确需一致性阻断；不是Formal rho缺陷，不在本任务改算法 |
| L01/L02风险接线边界 | P7Risk只引用target TTC/quality；P3允许区域Risk引用多车Action | 需外部规范化state/Action/Execution/Risk支持表；P3图合法不等区域Y有效 |
| 最终Y未批准 | Task6/E61仍将最终聚合/变换置于待决 | P1候选式和数值原语不能自动升级为Agreed |

详细函数、行号、输入输出、实际调用链和数据能力见[源码审计](P4_IMPLEMENTATION_AND_DATA_LINEAGE_AUDIT.md)及[18项机器追溯](p4_measurement_traceability.csv)。

## 3. 形成的测量体系

1. **Action**：完整保存实际v/a/位置/车道/leader/gap；通过明确pair角色、incarnation、clock和连续支持比较；首次命令、执行、实际差异、持续响应候选起点和确认时间分存。不造加权Action Score。
2. **单车Formal Risk**：可靠后向闭合TTC→现有rho；可靠区域外为0、成员或测量未知保留[0,1]；不适用只限当前后向风险投影，非全交通风险无风险声明。
3. **区域Risk**：固定空间/时间/处理前名单；每车全窗积分界→完整N名单组装→待批准聚合算子。未知整车保留全窗界，退出不删车。当前提出可实现规则，未声称已部署。
4. **Action–Risk**：以run/assignment/event/entity/incarnation和state/action/execution显式ID桥接，加时空支持、版本及源hash，不以相近时间自动关联。
5. **P5/P6接口**：全部assignment单位的测量结局/界、固定支持、时间化记录、缺失/失败/删失、版本/hash；不按Adoption或Action成功筛选ITT，不把车辆/采样点当独立分配样本。

具体计算阶段、字段/单位/缺失及状态规则见[测量规范](P4_ACTION_AND_RISK_MEASUREMENT_SPEC.md)和[数据契约](P4_MEASUREMENT_DATA_CONTRACT.md)。契约aad.p4.measurement.proposed.v0.1含12表、247字段，均标PROPOSAL_NOT_DEPLOYED，不扩P3正式schema。

## 4. 既有工程结果与风险指标定位

P7既有Enabled v2的351共同点、首命令2.8s/首实际差异2.9s、8.0s过期恢复及真实消费/执行证据可作工程链参考。它们不是新实验，不证明正式消息资格、Adoption因果效应或区域风险效应。P7Risk附件无正式Region/Cohort/Window、未计算rho/Y，风险仍Unknown。

TTC为后向跟驰基础量；DRAC是辅助所需减速度，不能替rho/截断求有界；Integrated TTC Exposure是valid-time归一化历史辅助量；PET需同一冲突区；Edie-type交通状态需要同域D/V/A。上述不合成新主风险分数，不将q=ku或TTC/DRAC当独立多份证据。Macro、Micro、Cohort保持不同测量对象。

NGSIM只支持其高速跟驰域；pNEUMA当前无可靠leader/Formal TTC，SPMD不是行为/风险真值；SUMO模型内通过不等现实测量通过。方法调研复用P2已有审计；只读核对四项Zotero元数据，未声称新精读未取得原文的Edie或SSAM材料，未新增论文/数据集。

## 5. 验证结果与保留失败

| 验证 | 结果 | 范围 |
|---|---|---|
| 六文件定向pytest | **84 passed，0 failed，0 errors**，44.61s | Formal7、prelock8、P7 evidence7、P3 evidence50、P7 Task2.1守卫7、stage_i5 |
| 进程创建守卫 | guard_active=true，blocked_attempts=[] | pytest无外部进程启动尝试，新SUMO=0 |
| 小型确定性语义例子 | **27通过，0失败** | 空窗/缺口/右尾/界传播/动作缺陷/NaN辅助风险复现，非交通实验 |
| 文档、字典、源码追溯、portable hash及Git字节 | 见[validation.json](../../../evidence/research/P4_TASK1_20261103/validation.json)与project_checks | 独立验证器、strict docs、exporter/verify、Git视图核验 |

P7历史143项不计入本次数量。复现缺陷的例子通过不代表缺陷已修复。首次便携核验因Python tuple与JSON list容器直接比较触发AssertionError；已修正为JSON容器归一后逐值比较，不放宽数值或hash标准，保留在project_checks中。84项pytest及27个语义检查本身无失败。只读检索的转义/Windows通配路径错误随后以固定字符串/精确路径核对；无实验/资料影响。完整测试XML/log和task_start在code/outputs/audits/p4_task1_20261103/，便携包只含摘要/hash，不复制大表或日志。

最小Git视图前两次分别遗漏riskprop包入口的legacy传递依赖和formal_design相对导入，发生导入失败；已补齐真实绝对/相对导入闭包，第三次通过，未修改生产代码。两份原失败视图/输出均保留，属于便携构建验证失败，不是84项pytest或SUMO失败；最终封包还执行最终Git视图复核，结果见project_checks及本机封口记录。

## 6. 研究者待决与仍Unknown

[集中清单](P4_RESEARCHER_DECISIONS.md)包含8组决策：Action主测量与连续确认；对齐/插值；区域总体覆盖；最终Y/标准化/权重；几何边界/无leader连续性；源特定质量准入；固定窗口/网格；外部契约与最小实现授权。推荐不自动成为Agreed，未给出正式数值。

仍Unknown：真实来源资格、区域风险效应、F0、总体T_R–T_P；P7单次工程差异不能填补。T_A（实际消费）、T_C、工程T_U候选与总体T_R/独立T_P明确分开。当前未访问在线Overleaf，既有对齐差异保留，不改论文。

## 7. 验收与后续接口

| 验收组 | 本任务结论 |
|---|---|
| 科研定义 | 通过审计：对象/风险/空间时间/因果边界清楚；不新冻结定义/参数 |
| 实现审计 | 通过：按源码区分implemented/partial/interface-only/missing并有复现 |
| 测量体系 | 文档与Proposal完成：计算输入输出、固定分母/界和P5/P6接口具体；生产全链未部署 |
| 科研可靠性 | 通过边界检查：缺失不补零，不将工程/风险变化声称因果效应 |
| 工程交付 | 文档/字典/证据可核验、上下文同步；实际验证结果见便携记录 |

本任务可阶段性收口。后续不需重复控制器基础接口建设或再设计一套测量目录；研究者确认上述选择后，可直接据本契约实施最小缺失组装/QC。P5负责资格/assignment/干扰与识别，P6负责统计规划，P8必要独立验证、P9准入均需另行授权。Formal A/独立Qualified仍0；Stage0.5 CLOSED_WITH_LIMITATIONS、Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS、Protocol Lock BLOCKED、Stage I READY_ENGINEERING_ONLY、Stage1.1 NOT_AUTHORIZED保持不变。

## 8. Context Consistency Check与Git

AI_CONTEXT 00–08按各自职责更新审计结论/模块边界/缺失/待决/零新实验及导航；PROJECT_CONTEXT、PROJECT_INDEX、RESEARCH_STATUS、RESULTS_INDEX和PROJECT_REGISTRY登记文档审计，不登记新交通实验。统一定义目录仅链接，不改字节。

完成验证后使用一个逻辑完整P4提交推送origin/main，实际Commit/Push结果及SHA以Git和最终回复为准，避免自引用hash。未将本机忽略的完整日志/临时生成器纳入提交。
