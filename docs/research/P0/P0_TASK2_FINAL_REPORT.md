# P0 Task 2：双传播因果链可识别性与证据契约审计

状态：**COMPLETED_WITH_LIMITATIONS**
日期：2026-11-01
承接：P0 Task 1；Task1 文献、报告、结论和历史状态均保留。

## 1. 最终判断

AAD 最有价值的科学问题不是“信息传播比车辆扰动快”或“远端警告能改变驾驶行为”。这些内容已经分别由 Schönhof et al. (2006)、Wang et al. (2019)、Jerath et al. (2024) 和 Peng et al. (2026) 覆盖。当前真正可区分的问题是：

> 在同一源事件、同一目标 cohort 和独立 no-message 物理基准下，消息策略是否通过可审计的送达、验证、控制器采用和实际动作，改变个体及区域风险；该效应何时被物理传播、通信失败或控制器不采用遮蔽。

这个问题具有潜在创新性，但截至本任务完成仍是 Proposal。现有 AAD 数据不能识别 C1–C3。

## 2. 六个必须回答的问题

### 2.1 AAD 当前最有价值的科学问题是什么？

双传播链在同源事件上的可识别比较：信息到达、验证和动作变化是否在物理状态到达之前发生，并能否在固定区域窗口内产生可归因风险差异。重点是可审计的 causal chain 和 failure boundary，而不是信息传播速度的重新命名。

### 2.2 真正可能成立的创新点是什么？

只有以下条件同时满足，才可能形成实质增量：

1. 事件级 message lifecycle 从 generation 到 action 全部有时间戳和失败状态；
2. assignment 是随机或有可信外生设计；
3. Tinformation 和 Tphys 来自同一事件、同一 cohort、统一时钟；
4. no-message physical reference 具有独立性依据；
5. network interference 由预定义 exposure mapping 处理；
6. 个体动作和区域风险结果均按固定规则测量。

这可以是“可审计的信息介导风险因果机制”，但还不是已证明的创新。

### 2.3 哪些主张必须放弃或收窄？

- 放弃“首次提出信息—物理传播耦合”：Schönhof 已明确建立；
- 放弃“首次提出信息传播波/信息早到”：Schönhof、Wang 已覆盖；
- 放弃“首次证明远端警告改变驾驶动作”：Peng 已有随机化模拟器因果证据；
- 放弃“作用边界是首次发现”：Jerath 已定义 ZOI、event horizon 和 null horizon；
- 收窄“类超距作用”为待检验的 information-mediated early risk effect；
- 不把 TTC/DRAC/PET 的变化直接写成事故概率变化；
- 不把 SUMO no-message 轨迹当作现实独立物理真值。

### 2.4 最值得继续发展的研究方向是什么？

优先级最高的是最小 ITT/policy effect 设计：道路区段—时间簇随机 message availability、同源 no-message control、固定 cohort/window、完整消息生命周期、双 exposure mapping 和物理 witness。Adoption/mediation 作为次级扩展，只有在随机鼓励、IV 条件和中介混杂得到证据后才执行。

### 2.5 达到 NC 级别还缺什么不可替代的证据？

- 多个独立源事件/网络簇，而不是单条仿真轨迹；
- 可验证的随机 assignment 和正概率；
- 消息生成、发送、送达、验证、采用、命令、动作的完整关联；
- 同源 no-message 物理传播参考；
- 统一时钟和身份连续性；
- 个体到区域风险的固定 cohort/region/window 证据；
- 干扰和跨簇泄漏审计；
- 现实或可信现场数据的适用域验证；
- 对 null effect、adoption failure、physical masking 和 measurement loss 的预注册解释。

### 2.6 下一步最值得解决什么问题？

建议 P0 Task 3 先解决“最小消息实验和独立物理 witness 是否可执行”的证据问题：冻结处理单位、物理到达操作定义、时钟/身份契约和最小 pilot 数据需求；不启动正式 Stage 1.1。若研究者不批准消息实验或无法获得 witness，应把主线收窄为可识别性/失败边界研究。

## 3. 当前研究设计

### 最小设计

- 处理：随机 message availability/strategy；
- 对照：同源 no-message；
- 单位：事件—道路簇—时间窗口；
- 结果：固定个体或区域 risk burden；
- 机制：message lifecycle、controller adoption、vehicle action；
- 物理基准：独立 witness 或 no-message arm；
- 估计：ITT/policy effect；按事件/簇聚类不确定性。

### 扩展设计

在道路簇内增加随机鼓励，估计 adoption/complier effect；使用 Aronow–Samii exposure mapping 区分 message exposure 和 physical exposure；在满足处理后混杂要求时估计 interventional mediation；报告跨簇泄漏、未知到达时间和代理指标适用域。

## 4. 当前数据结论

| 数据/结果 | 能做到 | 不能做到 |
|---|---|---|
| NGSIM | 轨迹和部分风险代理的工程核查 | 消息链、同源物理反事实、区域因果 |
| MiTra T1 | 高频轨迹、条件 Leader/Follower 派生 | 消息/采用、独立 witness、现实区域效应 |
| SPMD | RV_RX 接收状态连续性边界 | 逐包 delivery、verification、adoption、动作 |
| SUMO | 机制 fixture、字段和 no-message 工程路径 | 现实因果、现实物理真值、Stage 1.1 科学结论 |
| Task9/19 | 局部 fixed Leader–Follower 响应描述 | AAD 核心信息效应、物理传播、区域风险 |

## 5. 文献更新

本任务补齐了六篇指定核心最近邻：

- Schönhof et al. (2006)：全文；Poisson 车辆网络、longitudinal/transversal hopping、消息到达分布和微观仿真；
- Wang et al. (2019)：全文；队列—LWR 两层信息波模型和 NS-3 校准；
- Jerath et al. (2024)：全文；LWR 瓶颈、ZOI、event horizon、null horizon；
- Peng et al. (2026)：全文；40 人、239 个有效试次、随机 BLOS warning、DML/CausalForestDML、ORS/RT 因果效应；
- Hudgens & Halloran (2008)：PMC 全文；partial interference 和两阶段随机化；
- Aronow & Samii (2017)：全文；assignment、exposure mapping、HT/IPW 和局部依赖方差。

## 6. 项目状态和限制

项目状态保持：

- Stage 0.5：CLOSED_WITH_LIMITATIONS；
- Stage 0.6：PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；
- Protocol Lock：BLOCKED；
- Stage I：READY_ENGINEERING_ONLY；
- Stage 1.1：NOT AUTHORIZED。

本任务未启动新 SUMO、未访问 locked holdout、未修改正式风险指标、未修改固定主线规划文件。报告结论受到现实消息链、物理 witness、区域结果和数据组合不可识别性的限制。

## 7. 交付物索引

- P0_TASK2_CAUSAL_IDENTIFIABILITY_AUDIT.md
- P0_TASK2_DUAL_PROPAGATION_CAUSAL_MODEL.md
- P0_TASK2_ESTIMAND_AND_INTERFERENCE_SPEC.md
- P0_TASK2_PHYSICAL_COUNTERFACTUAL_AUDIT.md
- P0_TASK2_REGIONAL_RISK_MEDIATION.md
- P0_TASK2_DATA_SOURCE_CAPABILITY_AUDIT.md
- P0_TASK2_EVIDENCE_CONTRACT.md
- P0_TASK2_RESEARCH_DESIGN.md
- P0_TASK2_RESEARCHER_DECISIONS.md
- p0_task2_evidence_contract.json
- p0_task2_variable_dictionary.csv

逐篇精读记录、注册表、Task1 矩阵和 NC 风险评估已同步更新；Task1 历史内容未覆盖。
