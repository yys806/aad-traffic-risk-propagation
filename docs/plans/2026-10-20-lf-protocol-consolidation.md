# AAD-0.5-LF-PROTOCOL-CONSOLIDATION 执行计划

日期：2026-10-20。起点 main/origin `d700f158496545ed76dfd7aba9956737926a8ca6`。
独立结果 `RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1`；本地批次 `code/outputs/formal/calibration/stage_0_5_lf_protocol_v1`。

1. 核对原LF调用链和SHA，仅复制LF3必要工程点态、事件、交通/队列摘要及两个批准校准窗口的既有轻量摘要；建立独立Python -S胶囊、角色白名单、拒绝路径测试与冻结分析计划。原始真实轨迹/第三窗口/holdout/历史全源事件表/旧B1 C完整状态均不读。
2. 在新增独立分析模块中先建立合成预期测试：开始/确认/结束归属差异、确认前/全事件包含差异、身份/时钟/质量中断、同edge换道、边界窗口截断、共同可评价边分母、未知/零暴露、计划SHA与角色拒绝。核心P2和旧LF模块不改。
3. 冻结代码和输入后，逐事件复算266个原正式核心工程事件，重建86/87/83；新增“开始至确认全程在域”作为不同候选，逐事件位置/时间/成员/排除原因均留证。用全网前车上下文，连续边分母继承Stage0.2，两端在域是候选空间归属，不批准新规则。
4. 仅LF3独立轨迹作初始化诊断：1s观测序列、30/60s分段、60s信号相位配准、局部通量与全网pending分账、固定0/60/120/180/240窗口敏感性。暖机候选先用交通指标，风险结果仅事后描述影响，不用于选择。统计不确定性与可接受模型偏差分开。
5. 整合五层必要条件、两参考窗口差异、需求可识别性、量纲/空间/样本支持、容差与样本精度候选公式；没有获批margin/窗口/归属时返回Awaiting Researcher Decision，不产生Gate pass。
6. 新SUMO运行默认0次，保留5/8余额。离线审计后只有新运行能区分关键解释才另冻结具体运行；不使用既耗尽的接入预算，不启动ABCD或校准。若不需要运行，记录Not Attempted和理由。离线worker墙钟900s、进程树3GiB、输出1GiB，禁止无限重试或阈值搜索。
7. 输出统一报告/候选协议/逐事件CSV/分母及窗口审计/五层准入表/问题与研究者决策矩阵。便携文件每项≤256KiB，大型状态/图保留本地；历史目录不改。定向受控回归、纯Git全量、compileall、严格文档、SHA/便携语义复核、Context Consistency Check、commit/push和远端新克隆。

科学决定仅Proposed/Awaiting Researcher Decision；已有局部方案A为Agreed；复算为Verified工程事实。1e-6m、TTC<2s、.2s确认、100ms连续性及原分母不变。C完整回溢Evidence Insufficient；Gate pending_simulation_sample；正式局部P2 Unresolved/Not Calculated；科学容差Tolerance Not Yet Justified、ED上界Not Identifiable；不解锁后续阶段。根工作区五项文献删除和AGENTS不处理。

复现准备补记：v1先prepare基础LF3/两窗口摘要，随后按source_manifest的pre_freeze_revision补入A+ diagnostics/unified_strata，再tests→freeze→analyse。收口新增prepare_stage_0_5_lf_protocol_summaries.py封装该补入步骤并测试SHA/已冻结/重复拒绝；它未被伪称为原v1已执行代码。只允许在新的独立目录复现，不能重用本轮冻结目录。无原LF3本地工程产物的纯Git克隆只能验证便携事件/分母/候选规则与入口，不能重演大型状态分析；这种范围差异必须报告。
