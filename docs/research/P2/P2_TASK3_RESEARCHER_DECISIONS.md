# P2 Task3 研究者决策记录

日期：2026-11-02；状态：COMPLETED_WITH_LIMITATIONS。以下新方案均未自动成为Agreed。统一事实源：`../definitions/README.md`。

## 1. 已确认方向与事实

- Agreed方向：固定cohort、固定region、预定window；持续baseline-relative signed speed decline为第一版物理状态方向。
- Agreed边界：A/B分离，Formal P2/rho不变；总体层早窗比较，不估处理事件跨世界提前秒数；Overleaf只审计。
- Fact：Formal A合格源0，合格独立source→cohort Witness仍0；V2完成768面板，B完成60 CALIBRATION_ONLY运行，不能升级正式科学证据。
- Fact：Task3没有研究者对具体算子、数值参数、符号迁移或新增识别假设的正式接受记录。

## 2. 推荐、替代和科学后果

| ID / 事项 | 备选与后果 | 推荐及支持证据 | 反对证据 / 不确定性 | 状态 |
|---|---|---|---|---|
| D01 tE | onset保留确认前物理传播；confirmation易漏掉该段 | 物理链用onset区间，信息资格用confirmation；P2时间逻辑 | A无可校准onset标签，缺口可使起点不可识别 | Proposal / Awaiting Researcher Decision |
| D02 速度符号 | 复用u并加B；另造v；延用g会混net gap | Δu^B及区域平均，与论文速度u一致；g仍net gap | pair Δu需保留方向上标；新旧映射仍需接受 | Proposal / Awaiting |
| D03 聚合器 | mean衡量平均幅度；median衡量典型成员；比例衡量受影响人数 | mean首候选、median/比例辅助，三者同面板比较 | 半cohort代理中结果不同，无普遍优胜；异常值及加减速抵消 | Proposal / Awaiting |
| D04 cohort×region | 完整预定支持域；随车指标；动态占用 | 首版限定预定窗口内完整在区cohort；动态占用辅助 | 出区是结构性不可用；不能缺失界虚构留区；普适性受限 | Proposal / Awaiting |
| D05 baseline | 静态源前均值；处理前趋势预测；匹配无源参考 | onset下界前相邻窗口并检验稳定性；有趋势才比较预拟合预测 | V2 trend-null全报警；去趋势也可能吸收真实缓慢变化；W未定 | Proposal / Awaiting |
| D06 θ/h/q/W | 绝对阈值；标准化；顺序检测 | 暂不冻结数值；根据交通null FPR上界和阳性检测联合选择 | B全部无cohort报警；k=3从未测试；V1数值推荐撤回 | Unknown values / Awaiting |
| D07 coverage | 完整面板；可辩护缺失模型/界限 | 固定N、原因分层；无识别依据则Unknown | coverage门槛不解决MNAR；不可事后删车补位 | Proposal / Awaiting |
| D08 recovery | 观测阴性重置；退出持续；hysteresis | 检测段显式重置，恢复另确认；不默认hysteresis | 尚无交通chatter校准；退出规则会改变重复段数 | Proposal / Awaiting |
| D09 witness | 拓扑/邻近；实际关系；关系+顺序响应+竞争审查 | W1–W9逐跳，首版同车道纵向，复杂交互另列 | 反应阈值/时窗未定；B最多4候选边，未成完整链 | Proposal / Awaiting |
| D10 no-message总体 | 全ZS=1 assignment总体；通信前资格Qpre子总体 | 先盲法资格后随机ZC，可解释Qpre子总体ITT；显式F0^Q | F0^Q不自动等于原F0；事后S*=1筛选有选择偏差 | Proposal / Awaiting |
| D11 时间统计 | 固定H*总体早窗；η分位数反演；个体配对 | 优先P1 `7固定H*、风险同时带与F0上界联合覆盖 | η/δ/α/时域未定；KM/Turnbull有观察机制条件；非个体提前秒数 | Proposal / Awaiting |
| D12 clock | 实证offset/drift/phase界；假定零误差 | 分开钟差、采样、统计界并外扩；同钟也审计phase | 本轮没有跨设备钟差数据；不推荐具体容差 | Unknown / Awaiting |
| D13 主张范围 | “早于指定速度状态”或“排除任意普通物理影响” | 明确限定前者；后者需要更广物理机制排除证据 | B中s1–s4已在region响应而cohort未报警；阈值不能消除该逻辑缺口 | **Awaiting Researcher Decision，影响核心claim** |
| D14 论文一致性 | 现在改正文或登记未来修订 | 只保留对照表，研究者决定后另授权修改 | 当前没有可复核原文快照hash/精确行，审计粒度有限 | Task boundary Agreed；后续待定 |

D13是限制解释的推荐，不擅自更改研究目标。任何决定应由研究者明确给出，随后同任务同步CORE、SYMBOL、PARAMETER、LEDGER、Overleaf alignment；历史Task报告保留。

## 3. 数值决策所需证据

交通null稳定窗口、可独立标注的受控目标状态、完整cohort/region支持、噪声与缺失机制、源/响应区间、至少一条独立路径、预定FPR/漏报损失和跨域可迁移依据。现有B没有目标阳性支持，不继续加实验来追求预期答案。

## 4. 本轮不改变的状态

Stage0.5=CLOSED_WITH_LIMITATIONS；Stage0.6=PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock=BLOCKED；StageI=READY_ENGINEERING_ONLY；Stage1.1=NOT_AUTHORIZED。Formal P2/rho、四格设计和长期路线不变，不自动启动P2 Task4或任何后续实验。
