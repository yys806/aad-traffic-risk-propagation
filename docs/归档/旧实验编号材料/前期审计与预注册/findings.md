# Findings & Decisions

## Requirements

- 完整梳理 AAD 前期所有实验及其证据状态。
- 不因已有代码或结果而默认实验有效，需判断其是否达到 NC 级证据强度。
- 系统调研 Nature Communications 相关论文，重点查看原文、Methods、Extended Data 或 Supplementary Information。
- 列出需保留、复算、重做、补强和新增的全部实验。
- 设计可靠完整的主实验、对照、消融、鲁棒性、统计与复现体系。
- GPU 可用，时间成本不作为删减实验的理由，但避免无科学价值的算力堆量。
- DRIFT 仅作为上游交通流机制参考，不修改。
- 本轮需把路线图升级为可冻结的预注册执行方案；每项实验必须有科学预测、量化或结构化门槛、失败后理论处置，之后严格顺次执行。
- “达不到就不行”解释为预先冻结的 go/no-go 和理论证伪，不解释为必须得到正结果；不得为通过门槛而事后换阈值、窗口、种子或结局。

## Expert Perspectives

1. **因果识别审稿人**：替代解释、反事实设计、负对照、时间顺序与效应量。
2. **交通仿真与安全审稿人**：场景代表性、交通需求、控制器、安全替代指标和仿真可信度。
3. **车联网与控制审稿人**：消息生命周期、时延/丢包/老化、控制采用和闭环稳定性。
4. **统计与可复现性审稿人**：样本量、种子、配对设计、不确定性、多重比较、失败试验与开放产物。
5. **NC 综合编辑视角**：概念新颖性、证据广度、跨条件一般性、现实锚定和领域影响。

本轮预注册修订继续沿用上述五种视角，并增加“软件独立复现者”作为第六视角，专门审查 runner、时间对齐、状态隔离、路径匹配和统计复算是否可能共同制造主效应。

## Preregistration Principles

- 采用 paper-blind 预承诺思路：先写验收维度、主要终点、门槛和失败处理，再允许正式结果进入分析。
- 每个正文主张必须由论文自身数据或已核实文献支持；预期结果必须区分科学预测、工程完整性要求和正向效应门槛。
- 无法达到正向门槛时，不修改门槛追求通过；应按预先规则缩小理论适用域、降级 Result 或终止相应路线。
- 文献检索与计划修订采用六视角综合，避免只模仿某一篇控制论文的实验规模。

## Theory-to-Protocol Audit

- 理论的最小不可分割链为 `S_A → M_A → delivery → adoption → U_B → R_B`；E02 的负向风险效应只有与 E05 的链条闭合和 E06 的负对照等效同时通过，才允许解释为信息介导作用。
- 双走廊的理论优势是 `tau_P=+infinity`，但仍必须排除共享控制输入、跨走廊状态泄漏和通道计算副作用；结构断开本身不替代四格交互。
- 合流必须同时满足 `t_adopt ≤ t_action < tau_P` 与整个结果窗结束早于 `tau_P`；只证明动作先行不足以归因整个风险窗口。
- 理论稿末尾“现有双走廊和合流实验完成第一阶段仿真验证”与当前证据状态冲突：关键代码和原始包缺失，因此冻结方案必须将其改为“历史记录候选，待 E00–E10 重新验证”，不能把旧结论作为新实验前提。
- 当前 AAD 代码已有事件、局部传播、Pilot 汇总和真实轨迹解析测试，但缺少正式双走廊、合流、物理到达、第二控制器和预注册统计实现；E00 是科学门槛，不只是工程整理。

## Research Findings

- 仓库中可见的历史输出系列包括：`pilot_20260714`、`drift_qualification_20260716`、`risk_event_dataset_20260716`、两套局部传播基线、`nonlocal_pilot_a_20260726`、`nonlocal_pilot_b_20260802` 及两个定向修正输出。
- README 明确将 DRIFT 当前定位为数据与闭环重仿真的基础，而非已经完成正式反事实因果验证的平台。
- Pilot A 仅有 p60/p80、on/off、单一 seed 的 4 次冒烟仿真；历史文档明确禁止把它解释为正式因果结果。
- Pilot B 的本地输出支持 32 个有效通信原型运行及通道状态审计，但其运行矩阵规模仍偏小，且采用次数不能替代风险效应。
- 历史计划文档记录过 20 个正式种子、80 次四格运行和显著负向效应，但当前 `docs/项目导航.md` 明确指出决定性双走廊原始输出在本地缺失，因此这些数字目前只能视为“项目记录中的主张”，不能视为已独立复算的本地证据。
- 早期局部传播工作包含正式事件数据集、单跳/多跳基线、置换空模型、敏感性表和图，但它属于观察性物理传播基线，不能直接证明指定消息的非局部因果效应。
- **Pilot A（2026-07-26）**：p60/p80 × on/shadow-off，仅一个配置种子（实际 SUMO seed 13269），共4次、每次120步；验证首次采用9.6 s、首次轨迹分化9.8 s、处理前完全一致和开关有效，但安全指标方向混合，明确属于机制冒烟。
- **Pilot B / 真实风险通信（2026-08-02至08-06）**：通信 Pilot B 有32个有效 cell、仅2个种子；真实风险实验共46次（2 preflight、32主矩阵、8门控、4独立核验）。四个上下文主效应均为0，p60门控效应区间跨0，正式160次扩展因目标风险不足而主动停止。它证明协议与负对照可以工作，不证明稳定风险收益。
- **决定性双走廊（记录）**：20种子×4格=80次，记录的 `Delta_NL=-0.1312075`、20/20负、零碰撞、拓扑零路径，并有36次独立通信核验；但完整原始包目前不在 AAD Windows 树中，因此先按“待回收、待独立复算”处理。
- **合流迁移 v1（记录）**：20种子×4格=80次，均值为负但只有12/20形成合格源事件并产生负效应，未达到预注册16/20及逐种子采用门槛，正式结论是不支持迁移。
- **合流迁移 v2（记录）**：6个独立资格种子冻结速度/剩余距离门槛，20个全新正式种子×4格=80次；记录的 `Delta_NL=-0.0102834`、18/20负、0碰撞、14项门槛通过。原始产物同样需要统一回收与复算。
- **局部物理传播基线**：2,057个合格 episode、2,315条候选局部边、1,294条选定直接边、763条链和214条多跳链；100次循环时间移位空模型与阈值敏感性已做，能作为普通物理传播竞争基线，但当前边选择每个目标至多一个父节点，仍是观察性简化模型。
- 已发现的重要实现历史风险包括：Pilot B 曾有渗透率解析和跨运行通道状态污染；时间锚点曾错一仿真步；合流曾有 `sims_per_step=5` 导致机制日志与 state 行错位；这些问题已有回归测试记录，但正式重做时仍需从当前统一代码版本重新生成，而不能只信旧摘要。
- 当前 AAD `code/` 只包含风险事件、局部传播、Pilot A/B 汇总和真实轨迹/SPMD 管线；`code/configs/` 仅有 `feasibility_week_smoke.json`。项目内没有决定性双走廊和两版合流的 runner、network、正式配置、统计分析器、专用测试或输出目录。
- 当前 `code/outputs/` 的10个系列均早于或属于 Pilot B；未发现 `decisive_dual_corridor_20260807`、早期正式合流、资格种子或修正版合流目录。这意味着最关键的论文主效应目前不能在 AAD 仓库内一键重跑。
- 本地 Pilot B 输出较完整（原始 emissions、mechanism logs、run logs、cell/paired/factorial/communication tables），但其核心规模仅32个有效 cell、2个种子，适合作为协议原型证据，不适合作为 NC 主结果。
- Pilot A 本地包含4个 emissions、机制日志、配置、配对一致性和区域尺度汇总，证据链可审计，但只有单一随机种子。
- `code/README.md` 仍将当前代码定位为“first-pass skeleton”，并把反事实包装器列为后续扩展；当前模块没有支撑论文核心非局部主张的一体化正式 runner。
- 结构化复核确认：风险事件数据集含270个文件、1,609,149行、6,933个事件和4,131个 episode；主局部基线使用2,057个 episode、1,294条直接边、214条多跳链和100次置换，DRIFT-only 基线仅382个 episode、196条直接边、33条多跳链和100次置换。
- Pilot B 审计为32/32有效运行、零碰撞、off零采用、oracle/理想通信/受损通信采用次数分别为4,711/5,018/2,809，受损通信观测丢包率19.24%。这些是协议执行量与完整性指标，不等同于风险改善证据。
- 早期 DRIFT qualification 虽通过 candidate fit 与 formal evidence 字段，但最终决策仍为 `HOLD`，原因是极端减速度和长时低 TTC 需要逐条区分真实冲突、控制急变和离散伪影；因此不应把“formal_evidence_passed”孤立解释为数据已充分验证。
- 既有 NC 证据映射已经给出合理的结果链条“定义→断开拓扑识别→机制证伪→连通合流迁移→现实层级锚定→一般性”，但其“五篇共同做法”尚未附逐篇实验设计证据，本轮必须以原文和补充材料重新核实，不能直接把旧总结当成 NC 标准。
- 历史 Windows 外部工作树 `C:\Users\Lenovo\.config\superpowers\worktrees\code\nonlocal-pilot-a` 已不存在；WSL `mixed_autonomy_lab` 目录仍存在但不是 Git 仓库，顶层时间和文件搜索主要止于 Pilot B/旧版合流配置，未发现决定性双走廊命名资产。这进一步说明关键正式代码和输出不能假定仍可恢复。
- 待填：NC 文献实验标准。
- 待填：Result 1–6 主张—证据差距。

## Technical Decisions

| Decision | Rationale |
|---|---|
| 将“运行成功”与“科研证据有效”分开评定 | smoke test、原型日志和主效应实验的证据等级不同 |
| 每项主张至少对应主效应、机制审计和替代解释控制 | 防止用单一风险下降替代完整因果链 |
| 预注册冻结种子、门槛、失败处理和统计脚本版本 | 降低结果导向调整和选择性报告风险 |
| 理论字段先于 runner 冻结 | 确保 source→message→adoption→action→risk 与 `tauP` 可由原始表复算，不因实现困难删减理论链 |
| artifact smoke 明确不具科学资格 | 基础设施成功不能被误报为交通风险或因果效应证据 |
| 正式 run ID 不允许覆盖 | 修正、重跑和失败必须保留版本历史，避免同名目录静默改变结果 |
| 当前混合环境仅作 primary evidence | Miniconda + 用户级 PyArrow 不是第二干净环境，E00 仍需 clean-room 复算 |

## E00 Implementation Findings

### Evidence correction — 2026-08-18

- 用户提供的当前 DRIFT 工作树已只读核验：决定性双走廊网络、纯状态机、Flow runner、分析器和专用测试均被 Git 跟踪，DRIFT HEAD 为 `58397fb2834e238d5d4d5e72d0307f1d09674b48`。
- 因此，“决定性双走廊代码完全缺失”只适用于此前 AAD 独立工作树/旧外部路径审计，不适用于 DRIFT 当前上游。历史候选数字仍不自动升级为 AAD 正式证据：还没有迁移到 AAD 的五表 schema、manifest、provenance、独立 analyzer 和双环境真实交通复算。
- AAD 当前环境没有 DRIFT runner 假设的 `~/shen/paper_repos/flow`，且 `import flow` 不可用；SUMO 1.26.0、`traci` 和 `sumolib` 可用。下一步选择是显式迁移/适配 DRIFT 逻辑，或按同一理论直接建立 SUMO adapter，不能静默依赖不存在的 Flow 路径。

- 仅检查 `.parquet` 扩展名无法防止伪表；正式 seal 现在必须由 PyArrow 读取 metadata，JSON 也必须可解析为 object。
- 理论链所需的最小表不是单一 emissions：至少要分别保留 state、normalized emission、protocol lifecycle、applied action 和 risk/attribution；否则无法审计消息是否在动作前到达、动作是否真实分化及风险是否正确归因。
- Pilot B 的字段可以作为 protocol 原型，但缺少完整 validation reason、独立 action/risk 表和统一正式 schema，不能直接晋升为 confirmatory runner。
- 四格配置不能靠人工肉眼比较。当前 validator 要求四格集合精确、S/C 真值正确、run ID 唯一，且公共配置 canonical JSON 完全一致；后续真实 config 必须保存相同 diff audit。
- 消息“交付”不等于“采用”。当前 lifecycle validator 明确区分 generated、sent、delivered、validated、adopted，并要求时间单调、source/target/freshness 全部有效；该契约与论文机制链一致。
- 完整 provenance 必须记录真实执行 argv。第一次 smoke 实现使用合成命令，新增测试后已纠正；这说明 provenance 本身也必须被测试，不能只检查字段存在。
- 失败输出同样是科学分母。重复 run ID 的预期失败现在进入 append-only JSONL，且不会覆盖已 seal 的首次 run；后续所有 runner stage 需要复用这一约束。
- `e00_artifact_smoke_20260818_v2` 只包含五张零行表，用来验证 schema、Parquet、manifest、checksum 和 CLI；manifest 明确 `scientific_claim_eligible=false`，不得进入 Result 数字。
- `run_contract_fixture` 已把四格和五表串成非空解析链：每个 cell 均有 state/emission/protocol/action/risk，s1c1 具有完整 generated→sent→delivered→validated→adopted 链，处理前 target prefix 一致，处理后仅 fixture 动作分化；它使用占位风险值且永久标记 `fixture_only`，不能当作交通结果。
- 主环境与隔离 venv 的非空 fixture 每 cell 行数一致（s0c0/s0c1：3/3/1/3/1；s1c0/s1c1：6/6/1/3/1），四格/前缀/隔离/时间/ID 审计结果一致；这证明 contract 可复算，不证明 SUMO 理论效应。
- 当前主环境 PyArrow 25.0.1、pandas 2.2.3、Python 3.13.5、SUMO 1.26.0 已可运行；SUMO executable SHA-256 为 `dcdbf4fe1f8268816cda2d0631d407fd8e63b0cad5f3e57fe9cf235d9dece926`。第二干净环境尚未执行，因此 E00 尚未通过。

## Issues Encountered

| Issue | Resolution |
|---|---|
| 全仓库关键词检索输出过长并被截断 | 后续按文档、代码、配置和输出分组审计，不再一次性读取全仓库命中 |
| 历史计划、进度和最新交接的完成状态不完全一致 | 按项目证据权威顺序，以原始产物和当前可复算链为准；无原始包的正式数字一律降级为待核验记录 |
| AAD 当前缺少决定性实验实现与输出 | 下一步先核查外部只读工作树/WSL线索，随后决定迁移当前版本还是在 AAD 中干净重建 |
| 多个摘要文件一次性输出被截断 | 后续逐文件用结构化字段读取，只保留审计所需键和值 |

## Resources

- AAD 主论文：`paper/主论文/main.tex`
- 最新交接：`docs/归档/项目记录/交接/新对话完整交接_2026-08-15.md`
- 周推进：`docs/归档/项目记录/8.12-8.18推进.md`
- 上游 DRIFT：`D:\shen\TJU\DRIFT`（只读）

## Browser Findings

- 联网检索工具本身发生解码错误后，已按 web-access 流程切换到本机 Chrome CDP；只把搜索页用于发现论文，不把摘要当作证据。
- 第一轮官方 Nature 检索定位到《Knowledge-guided self-learning control strategy for mixed traffic flow under connected and automated vehicles》和《Effect of adaptive cruise control on fuel consumption in real-world driving》；前者适合审视多场景/多控制器仿真与实车或硬件验证，后者适合审视真实道路外部验证和效应异质性。
- 2025 NC 混合车队控制论文不是只报一个最优场景：以4个替代控制器（PPO/DDPG/AC/CVDS-IDM）为基线，20个 NGSIM 数据集做平均，报告振荡、舒适、能耗、稳定性四类指标；另测4档通信时延、CAV渗透率、车队规模、人驾参数噪声和换道扰动，并公开 Code Ocean 代码、数据、Source Data 和补充材料。其限制也明确承认尚待真实车队验证。对 AAD 的启示是：主效应、算法基线、通信剂量、交通异质性、突发扰动与开放产物必须同时存在。
- 2024 NC 真实 ACC 研究使用157辆车、95名驾驶员、40,356次行程、1,094,215 km、16,389小时、60余个1 Hz信号；做持续 QA/QC、地图匹配、车型/驾驶员/环境控制、trip 与 situation 两层分析及交互项。该案例说明“真实数据锚定”不是抽取少量 TTC 片段，而是要有大覆盖、测量链、混杂控制和情境异质性；同时其数据/代码受隐私限制，NC 并非绝对要求公开原始数据，但要求明确可用性与限制。
- 第二轮官方论文集覆盖四类证据架构：交通拥堵传染模型用多城市经验数据+微观仿真+局部传播/需求关系；瓶颈早期信号用大规模城市速度数据+时空相关+预测性能；异质流渗流用理论证明+多套大型真实交通网络+干预改善+一般性分析；network isolator 用严格理论+合成网络+真实电网+非线性/扰动敏感性。共同点不是统一样本量，而是“机理/识别核心 + 独立现实系统 + 扰动或一般性检验”。
- Saberi 等的拥堵传染研究跨 Melbourne/Sydney/London/Paris/Chicago/Montreal 六城，并用已校准 AIMSUN Melbourne 动态交通分配模型、不同拥堵阈值、1h/4h需求加载、逐时空 null model 和局部上游簇验证；其弱点是经验数据仅一天，论文主动列为未来多日扩展。AAD 应至少跨场景/多日或多交通实现，而不能把单日或单 seed 说成普适。
- Duan 等的瓶颈论文使用北京52,000路段/27,000节点、深圳22,000路段/12,000节点、30天1-min速度；用某工作日训练、另一工作日测试，并在两城17个工作日上报告 ROC/AUC、误差条和5/10/15/20 min早期窗口。这给 AAD 的直接标准是：机制阈值需跨城市/日期或仿真分布外测试，并把早期预测时间—准确率权衡显式报告。
- Hamedmoghadam 等用 Melbourne 61天与 Brisbane 月度公交网络、Melbourne 工作日约212万/日和周末91.2万/日交易；将方法与 EB/需求加权 EB/传统渗流临界性比较，做 top-2%瓶颈干预，并在100个随机几何图×3种流需求分布上验证一般性。Kaiser 等则用三个真实电网、级联故障触发分布、非线性 Kuramoto 扩展、权重扰动和 N−1 设计权衡。对 AAD 而言，必须有竞争基线、反事实干预、合成受控系统和现实网络/场景的互补证据。
- Kolekar 等的 DRF 风险模型把一个统一原理同时推到7类道路/交通情境，并优先选择自然驾驶文献作外部对照；但其自身参数实验只有1名参与者×两种风格各10次，说明 NC 也会接受小样本“参数示范”，前提是核心贡献有跨情境公开证据，且不把小样本个体实验外推为群体结论。AAD 的 Pilot A/B 可以保留为机制/参数示范，但不能升级为主证据。
- 2026 NC 主动推断碰撞规避模型以两类场景调参、第三类加拿大路口场景完全留出检验；正面追尾场景有896次模拟，并对元分析、美国 SHRP2、非洲 ANNEXT 和两项驾驶模拟研究。它对7个逐机制消融、13个调参量逐一近一数量级敏感性分析，并用10,000次贝叶斯/非参数抽样表达不确定性。AAD 需要同等逻辑：留出场景、逐模块消融、参数敏感性和独立经验基准，而非只做 on/off。
- 2026 GA2AD 摘要与官方附录入口显示：训练涵盖 cut-in、hard braking、speeding 对抗行为，报告碰撞率、95%绝对 jerk 和平均速度，并在自动驾驶试验场用同步虚拟交通做闭环轨道测试。AAD 若要明显提升投稿竞争力，HIL/同步虚实闭环应列为高价值增强实验；但当前在线正文未完整呈现，具体样本规模不能凭摘要猜测。
- 2026 dense learning NC 是当前最强安全实验参照：4类 base AV、highway/roundabout/urban 三环境、数百万次自然驾驶环境测试、7项技术消融、nuPlan 1200小时/四城留出基准，并把同一 SafeDriver 无额外微调用到 Autoware；最后在 Mcity Lincoln MKZ + SUMO/Autoware 同步混合现实闭环验证，显式校正延迟、道路坡度和 sim-to-real gap。训练用400 CPU核/2.8 TB内存，每迭代50,000步；关键不是 GPU 数量而是稀有事件采样、跨栈复用和物理闭环。
- NC 作者指南没有规定“达到 NC 必须多少 seed/多少场景”的统一数值门槛。后续样本量必须由效应方差、最小实际重要差异和功效/精度目标决定；所谓“NC 标准”应表述为从代表性论文归纳出的证据架构，而不是虚构期刊硬指标。
- NC 官方定位是“对特定研究共同体有意义的高质量原创研究”，初投格式灵活；因此是否过审主要取决于科学问题和证据，而非把主文堆到某个固定篇幅或运行次数。
- NC/Nature Portfolio 的硬性可复现要求与本项目当前状态直接冲突：发表主张所需的最小数据集、代码和协议必须可供验证/扩展，核心自定义代码须在审稿中提供，发表时最佳实践是带 DOI 的 Zenodo/Code Ocean；限制必须在投稿时明确。决定性双走廊和合流代码/原始包缺失不是“整理问题”，而是投稿阻断项。

## Supplementary Findings for Preregistration

- Wang 2025 Supplement 明确给出2000个训练 episode、0.1 s时间步和完整 SAC/仿真参数，但正文的统计比较仍依赖20个 NGSIM 数据集与多类扩展场景；因此 AAD 的学习控制器必须把“训练预算”和“独立评估重复”分开，不能把训练 episode 当统计样本。
- Schumann 2026 Supplement 将正面追尾初始条件分解为多个 time-gap×速度组合，并把侧向侵入、路口场景独立实现；其参数敏感性逐一改变关键规划参数。AAD 应把场景条件作为有科学含义的分层而非只随机采 seed，并为时间步、动作容差、物理到达估计和控制参数设置独立敏感性。
- Feng 2026 Supplement 的官方下载未完整完成；损坏副本已明确排除，后续只引用已从官方正文核实的数百万测试、跨环境/控制栈、7项消融和 Mcity 混合现实信息，不引用未读附录中的具体数字。

## Official Reporting Implications

- NC 官方报告政策明确支持 preregistration，并要求核心自定义代码在审稿时可提供、发表时给出可访问方式；冻结文件必须包含 commit、环境、处理版本、分析脚本和最小验证数据，而不仅是自然语言计划。
- NC 报告政策把统计资源链接到 Nature 的统计专题集合；本轮将从中只选对本项目直接相关的一手统计文章，重点核对样本量、重复、区间和多重比较，而不机械套用生命科学 reporting form。
- Nature 统计专题强调统计设计必须在实验完成前确定，并单列 power/sample size、comparative design、replication、nested design、two-factor design 和 multilevel analysis。对 AAD 的直接含义是：seed×scenario 才是主要重复层级，frame/message/vehicle-step 属于嵌套观测；四格 `S×C` 必须直接检验交互，而不是比较“一个显著、另一个不显著”。
- Nature Methods 的统计材料强调低功效会削弱可检测性、复现质量比单纯重复数量更重要、有层级噪声必须用 nested/multilevel 分析、两因素设计应直接建模 interaction。Aarts 等进一步显示忽略嵌套依赖可把名义5%的 I 类错误显著放大，并指出提升真正独立对象数量通常优于增加同一对象内观测。AAD 因此将 seed×scenario family 视为独立重复，run 内 frame/message/vehicle 只用于计算该 trial 的结局或层级辅助模型。
- 方法文献检索定位三条可直接纳入冻结方案的原则：Lipsitch 等的 negative control 用于检测混杂/偏差；Lakens 的 equivalence test 要求先定义可忽略效应区间而非用“不显著”证明无效；Morris、White 与 Crowther 的 ADEMP 框架要求仿真研究预先写清 Aims、Data-generating mechanisms、Estimands、Methods 和 Performance measures。E06 将采用等效门槛，整套 SUMO 计划按 ADEMP 扩展格式记录。
- 开放原文进一步确认：negative control 应在理论机制不可能产生效应的条件下复现实验，以暴露污染、分析错误或未预见的共同原因；因此 wrong-source、expired、delivery-only、shuffled pairing 必须覆盖不同故障层，而非重复同一种“空消息”。
- Lakens 明确指出 `p>0.05` 不能证明无效，TOST 的上下界必须由 SESOI 预先定义；AAD 的负对照通过条件将采用“区间完全落入等效带”，而非“没有显著性”。Morris 等明确给出 ADEMP，且要求报告 Monte Carlo 性能；本项目将额外冻结 Monte Carlo standard error/区间精度停止条件，避免把任意100 seeds当作期刊标准。
- FHWA 的 SSAM/替代安全指标官方材料同时使用 TTC、PET、最大速度/相对速度、减速度等冲突表征，并专门进行仿真模型与冲突观测验证。AAD 不应让 `I_TTC` 单独承担所有风险类型：追尾主指标可用积分 TTC 并以 DRAC/碰撞核验，合流/cut-in 必须加入 PET 或二维冲突指标；跨风险只比较预先标准化的效应，不直接混合原始量纲。

## FHWA 针对性复核补充

- FHWA SSAM Chapter 2 明确要求轨迹分析保留多次随机种子 replication，并同时计算 TTC、PET、最大速度、相对速度、初始/最大减速度、冲突角和假想 Delta-V；TTC/PET 阈值只是冲突筛选条件，不是完整安全结论。
- FHWA SSAM Chapter 6 的验证包含理论验证、83 个现场路口的 field validation，以及 4 个仿真系统的 sensitivity analysis。不同仿真器在同一设施上可能产生数量级不同的冲突数，安全指标之间也常有 trade-off；这直接支持 AAD 的 E11 第二控制器、E17 sim-real coverage 和多指标联合门槛。
- FHWA 还明确指出模拟冲突与真实 crash 的关系并非确定性等价，模型中意外碰撞和驾驶行为假设会改变结果。因此 AAD 的“零碰撞”只能作为暴露/完整性报告，不能单独证明安全；硬安全事件必须与风险指标、暴露量和上置信界联合报告。

## 预注册方案修订决定

- 旧路线图中的 `max(100, 功效所需N)` 和固定“每类50个负对照 seed”不再作为直接执行口径。新方案先用独立 calibration seeds 锁定 `delta_0`、`delta_R`、`delta_plan`、非劣界和等效检验样本量，再运行 confirmatory；若 calibration 不能给出 `delta_plan>delta_R`，则不启动核心确认性实验，若两者接近则由区分二者所需的精度自动增大样本量。
- 旧路线图把 E07 通信剂量放在真实通信校准之前，存在人为档位与现实数据脱节风险。新方案先做 E16-A 真实 Tx/Rx 配对和经验运行区间，再锁定 E07 的确认性通信条件；E16-B 仍作为留出验证。
- E19 被拆成 discovery（发现现实可实现的失败族）和 locked stress-test（独立评估）两个阶段；若发现集与测试集复用，结果作废。
- FHWA 针对性网页的首次整页提取因输出过大被截断；已改为逐页按术语和标题抽取小段并以官方原文核验，不把截断输出当证据。
