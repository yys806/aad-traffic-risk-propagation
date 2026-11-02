# AAD P2 Task3 最终报告

Physical Arrival Calibration, Scientific Definition Governance and Paper Consistency

日期：2026-11-02；状态：**COMPLETED_WITH_LIMITATIONS**。完成任务不等于科学Gate通过或核心假设成立。

## 1. 完成内容与交付

首先建立`docs/research/definitions/`六文件统一入口，并仅在AGENTS追加已授权科研定义管理章节。CORE覆盖22个定义、每项13字段，另含witness、cohort/region、持续状态、no-message资格和总体统计细则。README规定版本治理、证据类型、新旧映射及论文冲突登记；AI_CONTEXT只导航，不另立定义。

复用P0–P2、Task17–20、Stage0.5/0.6和既有NGSIM/MiTra/pNEUMA结果；不重跑历史工程验证。PAPER-SKILL已使用，核心交通波图预印本、区间删失JSS全文和官方NIST/SUMO方法资料已阅读；RFC5905仅相关章节，其他历史参考和未精读附件如实标注。Zotero新增5条来源，JSS原文与双语附件已导入，不建立仓库PDF库。

独立校准分两域：V2合成测量验证768面板/42候选；SUMO受控B域60运行，均CALIBRATION_ONLY。原V1存在测量缺陷，原输出保留并撤回，无依据的5s/k3/h1/q2dt数值推荐全部撤回。完整结果及来源见`P2_TASK3_CALIBRATION_RESULTS.md`；运行前设计见`P2_TASK3_CALIBRATION_PROTOCOL.md`。

Overleaf main.tex、supplementary.tex、references.bib在本任务先前已完整读取，没有修改。当前无法恢复原文快照，精确原句/行号/hash和提交时新鲜度未复核，因此论文审计是**有限度完成**，不声称全部论文结论已验证一致。逐项对照位于`../definitions/OVERLEAF_ALIGNMENT.md`。

## 2. 当前可推荐定义

物理链推荐用source onset区间；信息生成资格沿用confirmation后约束。两条时基不混用。A/B源、actual/assigned、Potential/Observed/Qualified、micro path/macro front分别登记。

研究者已确认固定cohort持续baseline-relative signed speed decline方向；具体mean算子仍Proposal：

\[
\Delta u^B_{i,t}=u^B_{i,t}-u^{obs}_{i,t},\qquad
\bar{\Delta u}^{B}_{\mathcal T}(t)=\frac1N\sum_{i\in\mathcal C_{\mathcal T}}\Delta u^B_{i,t},\qquad
\phi(t)=\mathbf1[\bar{\Delta u}^{B}_{\mathcal T}(t)\ge\theta_P].
\]

N处理前固定。完整面板可直接计算；observed-subset均值不是上式，低coverage不以删人/补位解决。区域内漏测可在明确界限下部分识别，车辆出区则区域内速度本身不可用，不能借速度界虚构留区。该定义需要预定支持域；动态占用与随车统计只能另列。

持续判定按观测跨度并审计q、恢复和末端待确认；onset、confirmation、observation分别存储。无独立源路径资格只能称速度状态报警，不自动称源归属arrival。g继续net gap，新速度记号推荐复用论文u加B；Task2 g_v和早期Task3 Δv只作历史映射，未擅自宣布正式Deprecated。

## 3. 校准实际结论

V2独立validation显示：稳态null参考配置0/24报警，但Wilson95%上界约0.138；自然趋势null24/24报警。1m/s×3s全体下降三聚合均24/24，0.8s短段均0；半数响应时mean/median与比例差异显著。缺失、q与h存在强耦合；gap-bridged不是真连续。这些是生成器内测量事实，不能转成交通参数。

B域60/60工程PASS，42候选×60共2,520评估全部未报警。固定cohort峰值mean下降0.01624–0.02806m/s，没有阳性目标arrival支撑检测率、延迟或阈值最优化。每validation条件只有6seed，0/6报警上界约0.3903。source命令执行与实际减速观测分开，native follower由控制日志核验；没有完整Qualified路径。

**本轮重要发现：** B域中s1–s4已在固定region内出现顺序速度响应候选，但预定s5–s10 cohort始终未达到任何候选阈值。由此，phi=0不排除普通物理影响已进入几何区域。后续即使证明风险效应早于此phi，也只能先解释为早于指定cohort的指定持续速度状态，不能自动排除较小速度变化、gap/density或非cohort车辆机制。该范围问题影响核心论文主张，已登记Awaiting Researcher Decision；不擅自修改论文或研究目标。

θ/h/q/W/coverage/recovery/clock均没有已验证唯一数值；标准化阈值未测试。停止扩大实验，保留真实Unknown。

## 4. No-message与总体时间判据

\[
F_0(t\mid H,Z_S=1)=P\{\widetilde T_P\le t\mid Z_C=0,Z_S=1,H\}.
\]

No-message是assignment，不是无源或发送失败。ZC=1中delivery/verification/adoption失败保留ITT。通信前盲法源资格Qpre后随机ZC可支持资格子总体ITT，必须写明F0^Q；不能暗中用它替代全部ZS=1的原F0。当前Formal A源0、无适用参考，F0不估数值。相同seed不保证策略分支后逐实体随机流配对。

TP是事件随机时间，总体由F0表示；TR为总体风险策略效应时间。严格沿用P1 `7预定H*：风险曲线的同时上界低于负SESOI并持续，且同一资格总体/H标准化下F0(H*)上界<η。TR upper<TP lower仅在明确总体界的构造后使用；可选η分位数反演下界仍Proposal，不是所有事件的最早物理时间。

风险/arrival/clock联合错误预算可用αR+αP+αclock保守控制，不要求独立；扫描须同时覆盖，不用pointwise CI冒充。右删失需完整可判定窗口，末端未满足h的阳性段单列；区间删失和Unknown不混用。KM/Turnbull须相应独立删失/inspection假设；信息性缺失用界限/敏感性。可恢复速度段不能照搬不可逆医学事件的观测假设。时间区间含钟差后重叠则temporal precedence not established。

## 5. 对11项科研问题的独立判断

| 问题 | 判断及依据 |
|---|---|
| 1 物理意义 | 有明确持续减速状态含义；不是任意物理影响首次进入region的充分测量 |
| 2 与Formal P2/rho关系 | 可分层共存，未改风险定义；未证明风险与速度状态等价，也不要求等价 |
| 3 主指标优越性 | mean与平均幅度目标相容，方向明确；无普遍经验优胜证据。median漏少数，比例多一阈值，需辅助 |
| 4 参数依据 | 有方法、合成和B运动学证据；无A标签、B目标阳性或交通null充分样本，数值不可冻结 |
| 5 参数依赖 | W/趋势/θ相关；q/coverage/h共同决定有效段；恢复改变复发，联合选择而非逐项拍定 |
| 6 交通适用域 | 当前仅合成与单车道Krauss局部B域；排队、换道、密度变化及现实域迁移未知 |
| 7 Witness | W1–W9使关系、方向、顺序及竞争解释可审计；不把相关性变因果，当前合格路径0 |
| 8 F0意义 | 明确的source-present no-message总体分布；预资格子总体需另标，当前不能估计 |
| 9 时间优先性 | 现有数据不支持；没有合格A源、F0或TR风险因果曲线 |
| 10 可推荐/不可定 | 推荐分层契约、持续计时、固定分母、符号映射、保守统计方案；核心claim范围、参数和实现顺序待决定 |
| 11 NC级重大漏洞 | 有：阈值cohort状态不足以排除其他普通物理机制；风险/arrival总体和支持域需一致；源0、Qualified0、F0/因果风险链缺失；论文审计快照粒度不足。这些阻止强结论，不等于假设已被证伪 |

## 6. 文献、论文与任务限制

文献全文/章节/摘要/历史复用状态逐篇见文献审计。新增Zotero条目和附件key可追溯；不把他文阈值当AAD验证值。当前资料足以支持方法边界和停止选择，继续扩大综述不能解决缺目标阳性和识别问题。

论文对照分CONSISTENT、NOT_YET_IN_PAPER、NOTATION_CONFLICT及待原文复核的claim风险；不把新Proposal说成论文已采纳，也不把行为响应记号直接判作数学冲突。需要后续读取可复核版本才能完成精确逐句审计。

本轮未执行：正式确认性科研实验、历史Task9/19重跑、Formal P2/rho/正式配置修改、locked holdout读取、Gate/Lock/Stage变更、Overleaf修改、长期路线修改、现实采集/HIL/实车。执行过独立CALIBRATION_ONLY SUMO/TraCI，不能再写“未运行SUMO”。

## 7. 验证、上下文与下一步

影响范围限治理文档、独立测量/绘图/B校准/后处理脚本及定向测试、校准便携摘要；不接入生产科研模块。验证采用脚本语法、测量定向测试、60run集成审计、SHA/JSON/文档严格验证、scope与控制字符检查；不运行全量pytest或compileall。实际命令和最终结果追加于本节末。

AI_CONTEXT00–08、PROJECT_INDEX、RESEARCH_STATUS、STAGE_INDEX、PROJECT_REGISTRY及结果/证据导航按本轮事实同步，历史和阶段状态保持。便携包不含日志、图、PDF、原始轨迹大表；本地输出完整保留。

下一步由研究者审核P2_TASK3_RESEARCHER_DECISIONS.md，特别是claim范围、风险/arrival支持域、Qpre目标总体和完整面板适用范围。数值校准还需独立目标阳性/交通null及质量证据。没有自动启动后续任务、Protocol Lock或Stage1.1。

### 已完成验证记录

- 定向测量/位置证据测试：9 passed；五个新增Python文件py_compile通过。
- B集成记录：60/60工程PASS，零collision/teleport/region支持失败；无额外仿真重跑。
- SHA256逐项复核：V1原manifest 5文件、V2 9文件、B 497文件、便携包14文件全部匹配。仅表示完整性，不证明科学有效性。
- exporter：PORTABLE_EVIDENCE_EXPORTED results=92 files=1391；verify=PORTABLE_EVIDENCE_OK。研究校准单独research_audits登记，不增加正式result数量。
- 最终暂存后文档严格验证返回PROJECT_DOCS_OK，git diff --cached --check通过。初次diff check发现新README两行Markdown尾空格，已修复；原V1失败不隐藏。
- 注册表结构对照确认除Task3导航/audit外历史状态不变；AGENTS diff仅授权新增章节。原SUMO XSD警告和Overleaf快照限制保留。

交付Git信息：分支main，Task3运行前父提交d1b731c；提交信息为feat(research): govern physical arrival definitions and calibration。最终commit SHA、push与远端HEAD核对结果见本任务完成回复及Git记录，不在提交自身写入自指SHA。提交前仅有本任务46个暂存文件；全文工作产物按本机exclude保留，未进入Git。

补充验证记录：最终AGENTS范围审计首次读取Git中文输出遇到Windows默认GBK解码错误；显式UTF-8后46文件范围及便携SHA核验通过，未改科研内容或环境依赖。
