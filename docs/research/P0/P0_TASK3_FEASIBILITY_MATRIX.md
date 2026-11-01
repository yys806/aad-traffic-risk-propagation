# P0 Task 3：实验平台可行性比较矩阵

日期：2026-11-01。状态：**Proposal + cited Fact**，不构成实验授权。总报告与来源编号见 [P0_TASK3_FINAL_REPORT.md](P0_TASK3_FINAL_REPORT.md)；逐项理由/限制见 [p0_task3_feasibility_matrix.csv](p0_task3_feasibility_matrix.csv)（4 平台×12 维=48 条）。来源原文定位/URL/hash 见 [p0_task3_source_register.json](p0_task3_source_register.json)。

## 1. 判级含义

- **Feasible**：给定列明适用域，已有源码/既有工程证据或官方接口直接支持该能力；不表示 AAD 已获得资源或完成新实验。
- **Conditionally Feasible**：能力可构建，但需新增集成、质量验证、安全/伦理或识别条件；依赖写在相应行。
- **Not Feasible**：该路线在本次审查限定下不能提供相应证据；不是断言未来任何变体都不可能。
- **Unknown**：当前证据不足以核实，尤其是 AAD 访问权、设备、费用和场地权限。

`Verified` 指被引用的技术/本地事实已核验；推荐属于 `Proposed`。不用等级相加或主观打分。SUMO 与 HIL 的 no-message reference 是**模型环境内**参考，封闭场路线才以现实物理测量为目标。每项能力等级与“本项目实际可获得性”是两个字段。

## 2. 统一 12 维矩阵

| 维度 | SUMO 配对模型实验 | 驾驶模拟器 / HIL | 封闭测试场联网车 | 当前已审计现实数据 / 自然观测 |
|---|---|---|---|---|
| Source Event | **Feasible**：外生扰动可脚本化；Formal P2 资格仍需测量，不能保证命中 [L2–L4] | **Conditionally Feasible**：场景引擎可安排事件；人类响应不能精确复现，需许可/接口 [S5、S8；L8] | **Conditionally Feasible**：安全包络内源扰动；场地、安全和控制权限未知，不能保证安全地产生 Formal P2 [S7；L0] | **Not Feasible**：存档事件可描述，不能在原事件中重新随机施加/重复 [L5] |
| Randomization | **Feasible**：外置脚本可分配策略/运行，当前 fixture 非生产实验 [L2、L4] | **Conditionally Feasible**：warning/no-warning 分配有先行例；参与者/运行/顺序与 carryover 需设计 [L8–L9] | **Conditionally Feasible**：整场事件随机路由风险消息，须控制域/复位与源端一致 [L9；S7] | **Not Feasible**：NGSIM/MiTra/SPMD 已审范围无已验证随机 message assignment [L5] |
| Message Lifecycle | **Conditionally Feasible**：Task20 合成字段/校验可复用；缺生产发送—receipt—验证链 [L2、L4] | **Conditionally Feasible**：自建消息层、HMI/接收器日志；recorder 不自动含消息 [S6、S9] | **Conditionally Feasible**：源端、接收端、验证端可联合记录；日志导出权限 Unknown [S7；L6] | **Not Feasible**：缺同源稳定 message_id 完整链；RV_RX 不是逐包 [L5] |
| Adoption | **Conditionally Feasible**：须在真实执行的 controller tick 插入决策回执，fixture adopted 布尔不够 [L2、L4] | **Conditionally Feasible**：自动控制器可适配；人类心理采用 **Unknown**，按钮/眼动仅 proxy [S8–S9；L6、L8] | **Conditionally Feasible**：实际控制软件采用/拒绝/覆盖日志；能否接入 Unknown [L6；S7] | **Not Feasible**：当前三类存档没有控制器采用回执 [L5] |
| Action | **Feasible**：TraCI/FCD、原生响应已有工程证据；消息因果仍待实验 [L3；S3–S4] | **Conditionally Feasible**：踏板/方向盘、control/虚拟轨迹接口可记录，需整合与延迟校准 [S8–S9] | **Conditionally Feasible**：CAN/反馈和独立实车轨迹需标定关联，现资源 Unknown [L6；S7] | **Conditionally Feasible**：NGSIM/MiTra 部分轨迹可派生；没有可归因消息命令 [L3、L5] |
| Physical Witness | **Not Feasible**（现实独立）：只有模型状态；模型内全状态可作结构见证 [S4；L5] | **Not Feasible**（现实交通独立）：真实驾驶者+虚拟交通不等于现实道路物理；可取虚拟状态 [S5–S6；L8] | **Conditionally Feasible**：独立路侧覆盖源/路径/R/边界；不能由 RTK/V2X 存在推定完成覆盖 [S7；L6] | **Unknown**：NGSIM 视频时空绑定、MiTra 参考点/原视频等未闭合；无已认证同源路径 [L5] |
| No-Message Reference | **Feasible**（结构模型内）：同初态/RNG 保存并配对；相同 seed 不保证相同逐车随机量 [S1–S2] | **Conditionally Feasible**（模拟环境）：随机无警告试次，处理学习/顺序；不是现实道路对照 [L8；S5–S6] | **Conditionally Feasible**（现实群体）：其他独立事件随机 π0+独立 witness；不恢复个体反事实 [L5、L9] | **Not Feasible**：未采用车/另一个数据集不提供随机 π0 同源群体 [L5] |
| Regional Risk | **Conditionally Feasible**：全状态可接正式分析器；固定 R/C/W 和源支持未冻结 [L2、L4；S4] | **Conditionally Feasible**：全虚拟交通可计算；单驾驶者轨迹不足，周车模型必须披露 [S6；L7–L8] | **Conditionally Feasible**：全车队/全区域观测、net gap/连续性通过后用现有 rho [L4、L6；S7] | **Not Feasible**（区域消息因果）：局部风险可测不等于固定同源区域 policy outcome [L5、L7] |
| Interference | **Conditionally Feasible**：整网一次分配包含运行内干扰；跨运行状态/RNG和接入层需审计 [L4、L9] | **Conditionally Feasible**：周车与人类序列相关需保留；多真人座舱联网能力 Unknown [L8–L9；S8] | **Conditionally Feasible**：整场控制域、边界/迁移/复位审计；域外未知不能靠聚类 SE 修复 [L9；S7] | **Not Feasible**（当前消息因果）：缺完整 assignment/exposure 与正概率支持 [L5、L9] |
| Clock | **Feasible**（模型）：统一仿真 tick/状态时间；外接硬件需另校准 [L2、L4；S4] | **Conditionally Feasible**：固定步/同步世界+I/O/HMI延迟桥接；不能只用 wall-clock [S5、S9] | **Conditionally Feasible**：PPS/PTP/GNSS 桥接和残差上界；设备有时钟不等于已经同步 [L6；S7] | **Unknown**（双链）：部分轨迹有时间，跨消息/采用/独立 witness 统一时钟未验证 [L5] |
| External Validity | **Conditionally Feasible**：仅固定模型/场景内效应，现实外推不合格 [L2；S1–S4] | **Conditionally Feasible**：真实驾驶者在模拟任务中的响应；驾驶者选择/虚拟周车/预期限制 [L8；S8] | **Conditionally Feasible**：受控真实车辆和场地内政策效应；自然交通/事故风险/一般性仍需独立验证 [L0、L7；S7] | **Not Feasible**（核心主张）：可描述自然交通，不凭自然性获得消息因果/时间优先性 [L5] |
| Cost and Access | **Feasible**（已有底座）：已有 SUMO/TraCI 审计；新闭环开发工时/算力待估 [L2–L3] | **Unknown**：座舱、许可/多客户端、参与者/伦理、排期和费用未核实 [S8；L8] | **Unknown**：场地、车辆、改装/日志/路侧权限、审批、预算未核实 [S7] | **Conditionally Feasible**（只读复用）：已有审计和部分本地轨迹；新平台完整实验数据访问 Unknown [L5] |

## 3. 三类证据的能力边界

| 平台 | A 独立测量见证 | B 随机 no-message 对照 | C 模型反事实 | 支持结论的最高合理范围（还需有效实验） |
|---|---|---|---|---|
| SUMO | 不提供现实 A；模型全状态可核查 | 只在模型内策略运行 | 可配对，需共初态/版本/外生随机性 | simulator-only policy effect/机制；当前仍 engineering-only |
| HIL | 真实驾驶输入见证；交通物理来自模型 | 人类试次随机化，真实行为+模型交通 | 只能复现模型周车；人类不能精确 counterfactual replay | 模拟情境中的人类响应 ITT；若全交通记录可估模型区域结果 |
| 封闭场 | 可部署现实独立路侧；AAD 设备/覆盖 Unknown | 可在可比独立真实事件中分配 π0 | 可作敏感性补充，但不能顶替 A/B | 受控真实场景的区域 policy ITT；时间优先/采用机制还需额外条件 |
| 当前存档 | 仅条件轨迹/待认证独立源 | 无已验证随机消息对照 | 后续建模也不能恢复现实个体反事实 | 描述、测量工程、有明确假设的观察性研究 |

**A 不等于 B；B 不提供同一事件的两个潜在结果；C 不等于现实物理真值。** 消息组路侧测得的是消息组真实状态；它的测量链可以独立，被测状态仍可能受消息影响。

## 4. 平台的最小接入与现实资源

| 平台 | 最小组件/数据 | 实验簇与参与者 | 当前不可假定具备的条件 |
|---|---|---|---|
| SUMO | 已有执行器+未来消息/控制器适配；全部状态、源/消息/命令/风险和 RNG 审计 | 独立外生运行块；每块两臂只在模型内配对；不需要人类 | 正式源支持、controller 闭环、动态误差/方差/科学 Gate 未完成 |
| 驾驶模拟器 | 场景脚本、警告接口、输入/命令、全周车轨迹、I/O 时钟桥接 | 人类参与；独立驾驶者/组及试次层级；不是轨迹点数；多真人非必备但不能假称已实现 | 硬件、软件许可、伦理、参与者、carryover 可处理性、多座舱接口 |
| 封闭测试场 | 源/中间/目标/后随四种分离车辆角色的原型；消息端点与可记录控制器；完整路侧轨迹；标定/同步/CAN/RTK辅助 | 源事件整场/更大 session 簇；现实重复不能共享 event_id；司机/安全人员可能触发人类伦理要求 | 4 车只是拓扑下限不是科学样本量；更多车辆、独立重复、场地与设备数量均 Unknown |
| 既有数据 | 复用 Task2/Task11–13 审计、已具本地数据；不扩展下载 | 不会因行数大而获得随机单位；新同源实验数据需另审 | message_id、adoption、外生分配、无消息参考、开放权限 |

n 只能由独立事件方差/ICC、SESOI、分配、缺失和时间到达精度决定，当前 Unknown。资源/成本用组件×时间的预算式估计，暂无可靠单价。外部机构公开设施页面不构成访问许可。

## 5. 推荐与停止条件

**现实证据首选：** 封闭场整场事件随机化 + 独立路侧 witness + 跨独立事件随机 π0。**最接近的工程准备：** SUMO，未来另获授权后接生产消息/控制器；不重跑 Task20。**可选行为替代：** HIL，明确驾驶者真实、物理交通模型化的适用域。**现有存档：** 保持测量/描述和边界核验用途。

总体 **CONDITIONAL GO** 仅为设计可继续供研究者选择。任何现实实验、正式 SUMO、Stage 1.1 启动目前均不获本 Task 授权。若无法获得 A+B、足够独立事件和区域覆盖，收窄对应主张；若研究者不接受收窄则保持 NO-GO。详见总报告 §10 和研究者决策清单。
