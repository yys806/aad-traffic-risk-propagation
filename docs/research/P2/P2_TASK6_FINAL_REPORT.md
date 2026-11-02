# P2 Task6 — 最终科研设计闭环与校准协议定稿

日期：2026-11-02。状态：**DESIGN_COMPLETE_WITH_LIMITATIONS**。协议版本AAD-P2-PARAM-20261102-v1.0；统一定义AAD-SCI-DEF-20261102-P2T6-v0.4（保留27条Definition ID）。这是设计交付，不是科学Gate/Protocol Lock/Stage1.1或实验运行许可。

## 1. 目标、完成内容与直接下一步

问题仍是：来源可追溯且控制器实际采用的远端风险消息，能否通过动作改变而在普通物理影响到区前改变区域总体风险。物理链与信息链各阶段分开，时间先后不是因果识别，完整消息日志也不识别动作中介。

完成了D1–D7正式同步、两臂/四格识别边界、三层测量操作化、SAC与全参数十三字段、11类参数依赖、历史数据能力审计、可执行实验矩阵/单因素/交互/验证/样本量、允许时间集合/CDF界/Risk ITT同时带/联合错误和冻结停止。完整执行入口是[参数确定实验协议](P2_TASK6_PARAMETER_DETERMINATION_EXPERIMENT_PROTOCOL.md)，一次性科学选择是[集中决策](P2_TASK6_RESEARCHER_DECISIONS.md)T6-R1–R6，不拆更多研究设计任务。

**就绪判断：设计已完整；执行有条件就绪。** 研究者一次接受校准启动所需的对象/真值/损失/β_V与资源授权后，下一项直接进入P2 Parameter Determination Experiment。δ/正式H*/η/四格额外支持在正式使用前确定，不因它们未知无限阻塞纯测量校准。本次明确禁止新实验，实际0 SUMO/TraCI/Pilot/校准运行，无自动启动下一项。

## 2. 当前事实与审计依据

按AGENTS顺序读取当前状态、注册表、研究状态/索引/PROJECT_CONTEXT与Git，追加Task6指定AI_CONTEXT/定义六文件、P2 Task1–5最终报告/决策、Task3结果、Task4文献审计、Task5操作化/方法/论文审计，P1因果/DAG/estimand；必要回源码和明确白名单产物。未扫描私人笔记/OB其他目录、上游DRIFT或locked数据。

| 事实 | 本次直接核查及边界 |
|---|---|
| Formal A源=0、独立Qualified source→cohort=0 | 注册表/当前阶段与Task3/5证据保持；不降源阈值改变事实 |
| V2=768面板/42候选/32,256评估 | calibration_runs.csv按split/scenario/panel_seed重核；只有合成正确性/生成器内性能，不是交通参数范围 |
| B=60run/2,520评估/全部无cohort报警 | detector_results/run_audits/measurement_audit重核；峰值mean下降0.01623808–0.02806257m/s，独立目标阳性缺失，不能估交通sensitivity/延迟 |
| B区域中间车响应 | Task3结果和原轨迹关联摘要，不能替完整独立target Physical Arrival真值，不能把没有cohort报警称区域无普通物理影响 |
| Task9/18/19 | T18 primary60+supplementary40，T19同100run/50pairs，非三批独立样本；共享source input/seed，局部Follower响应非区域传播/独立最早onset |
| 正式风险范围 | 当前formal_risk_measurement.py：rho_from_ttc=exp(−TTC/τ)，contribution_bounds/均值[0,1]，定长积分[0,L_Y]；实际最终Y/前后变换仍需版本确认，不截断DRAC |
| 总体科学证据 | F0不可估、TR/TP总体时间优先性未验证；历史工程PASS不能升级 |

[design_evidence.json](../../../evidence/research/P2_TASK6_20261102/design_evidence.json)包含这些计数、显式白名单/hash、部分原manifest选中文件复核、样本量/功效和可行性计算；不含raw轨迹大表/日志/图片/密封键。历史B跨条件复用seed，60记录并不自动iid；计数不证明独立。

阶段保持Stage0.5 CLOSED_WITH_LIMITATIONS、Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS、Protocol Lock BLOCKED、StageI READY_ENGINEERING_ONLY、Stage1.1 NOT_AUTHORIZED。

## 3. D1–D7同步与接受粒度

| 决定 | 同步位置与结果 | 未自动冻结 |
|---|---|---|
| D1 三层分别报 | CORE当前Q、TIME-004/PHY-004/008–010、E54、符号/决策 | 层内算子/阈值/质量/范围数值；不造OR/AND标量 |
| D2 Edie-type主要候选 | CORE K/Q、参数M01–10、E55、协议6.1 | window/网格/阈值/抽样/检测域验证 |
| D3 两臂与四格定位 | CORE I/M/R、E56、协议11、T6-R5 | 共同资格/非Q政策/额外识别假设；不改矩阵 |
| D4 onset/confirmation均记 | CORE N/R、E57、协议12/15、时间符号 | t_E最终映射及误差/反应窗数值；Formal确认不改 |
| D5 科学下限后逐项/交互/V | SAC/十三字段/依赖矩阵、E58、协议5–10 | 科学损失、a*/b*/d*、参考具体值、最终n与冻结 |
| D6 P1保守总体方向 | CORE O/P/T、E59、协议8/12/13 | 估计器/族/预算具体数值；真实到达桥接证书 |
| D7 本次不改论文 | OVERLEAF_ALIGNMENT、E60、集中决策 | 后续论文文字仅另授权，当前在线版未重读 |

旧v0.1–v0.3与Task报告保留；方向Proposal由本次Agreed覆盖，算法/数字不一键升级。统一定义是唯一当前科研定义入口，AI_CONTEXT只摘要导航。

## 4. 两臂与四格：可以回答什么

合格两臂：有源、communication-blind Qpre确认后随机ZC，估τ_Q(t)=E[Y(1,t)−Y(0,t)|ZS=1,Qpre=1]及同资格/同H权重/同域F0,ℓ^Q。需要真实分配时刻/正概率、无提前暴露、稳定政策、适当独立簇/干扰与结果质量。ITT保留失败/缺失/拒绝/未采用/未Qualified及确认前已到达；实际消息各阶段成功不是纳入条件。

四格：τSC=(μ11−μ10)−(μ01−μ00)，在共同源前总体/政策/结果/clock和四格随机支持成立时回答source×communication交互，不是采用者效应或τ_Q。Qpre对ZC是前变量，对ZS可能后变量；无源Q(1)成员不可见，即使Q(0)=0、随机ZS或同seed也不填补。Principal stratification定义有效对象，通常仍需额外模型/假设/界才估计；本次不加假设。

同源前总体下τSC=pτ_Q+(1−p)τ_nonQ−τ_S0为全期望恒等式；未随机非Q/未定义S0政策的项不可识别，不能填0。两臂外推全部有源需非Q支持/已接受运输条件。源前共同opportunity可提供另一共同四格资格，但改变资格对象，须研究者决定。当前formal_design只核配置/生命周期/共享前缀契约，不证明实际随机性/positivity；这些历史校准不是合格因果数据。

后续分析先审实际资格/分配/干扰，再合格两臂ITT与分层F0和生命周期失败，最后各层早窗；四格自身支持通过后另报。单位为独立run/最大依赖block，非车/帧/同seed四次运行；共同输入有限时结果只对该支持域。

## 5. 三层测量与时间语义

Micro真实leader/follower逐跳W1–W9，源/响应区间、ID/关系/quality/竞争解释和同响应段连接。Potential/Observed/Qualified分层，不因图连通或时间相似合格，Qualified也非无混杂因果证明。缺链且覆盖不够是Unknown，不是无到达。

Macro同向lane的固定弧长×过去窗口，域内实际片段积分D/V/A，q=D/A、k=V/A、u=D/V仅V>0，单位与部分穿越/入离域/换道裁切明确。完整普查主候选，稀疏p_i已知才考虑设计权重，p未知只observed traffic；比值非有限样本无偏。lane分别报，不用可见均速冒充区域速度。窗口末端/crossing不等真实最早响应，不减一个w_M伪修delay。Edie原文仍未取得，复用Hall测量依据，不假称原文精读。

Cohort固定N/region/window与signed baseline decline方向保留，均值具体算子推荐而非最优事实；出区/缺失不补位。三层不一致按局部/稀释/其他源/缺链/不同支持解释，不投票、不OR/AND、不用一层填Unknown。Task3 B已说明cohort阴性不能排除区域物理响应。

时间契约分别记录planned、actual source onset、first positive、confirmation、message eligibility/generation/send/delivery/validation/adoption、actual action、regional risk-state onset与population causal T_R、physical onset/confirmation/observation/available。保留exact/left/interval/right/Unknown及区间并集；计划不替实际，确认不反推精确onset，采样/offset/drift/phase均进入两侧误差。source对齐建议[L_S,U_S]而非确认，待最终科学接受，不改Formal P2确认。

## 6. 科学下限、参数与依赖结论

统一[SAC与参数登记](../definitions/PARAMETER_AND_CALIBRATION_REGISTER.md)分别登记δ、η、H*、α、FPR、Sensitivity/Miss、Delay、Unknown、Power和独立n，另补truth a*/b*/误差及FAR。每项有定义/现有证据/推荐替代/影响/冻结点；风险意义、物理到达比例、coverage、FPR/显著性和检测/物理时间不混淆。

十三字段登记C01–09、U01–09、M01–10、T01–10：名称符号、数学、单位、对象、域、候选/经验区分、实验、文献、依赖、偏差后果、校准、独立V、状态。所有交通经验数值Unknown；候选按pre跨度、独立truth/误差和科学预算生成，不恢复V1 5s/k3/h1s/q2dt，不将V2/B或Formal源规则迁为arrival经验。

11类依赖覆盖W×model、θ×h、h×q、coverage×missing、recovery×hysteresis、macro window×θ、Δx×Δt、density×θ、reaction×clock、identity×missing、H*×η×α×n。恒等式/积分实现可独立检查；检测参数需条件逐项+重点联合，身份/真onset/归属/抽样概率/漏检界需独立truth。更换region/cohort/资格/truth scope/主算子/阈值状态版本可能改变estimand，不能当纯调参。

最佳数值仍Unknown的原因不是少一轮综述，而是缺独立交通null、目标positive/onset/归属标签、损失价值/真实独立单位和域迁移证据；这些由下一参数实验按本协议测量，不再增加设计任务。

## 7. 最终实验协议的执行性

协议18节给出：目的/范围、历史数据白名单、N0/N1/positive/归属对照、独立truth先封存、有限因素/水平/控制、参考网格、单因素、11依赖交互、robustness、独立单位/seed/split、精确样本量与power、明确分母指标、一次V、稳定区域/冻结、停止、复现和报告。

示例探索矩阵三密度×（两类null+五positive设计点+一归属对照）×24=≤576计划单位，大量参数只重算同raw；这不是有功效样本量，也不保证目标实际阳性。V独立n按actual标签/误差族精确计算；同轨迹/seed不拆帧分set，旧V不复用为新独立V，locked不读。

精确二项限独立同质Bernoulli：单项单侧95%、零FP达到1%上界最少299，5%需59；全检出达到95%下界需59，90%需29。全零最有利n不等90%验收power，脚本另枚举good FPR=.2%对1%、good miss=1%对5%的验收power；J_V扩大/α_measure=.005时另算，不能隐藏成本。delay用timely有效检出下界，Unknown/miss计不成功；每run同参数交互差分用独立block误差，不用detector行数作n。

完整顺序：一次科学启动项→manifest/独立truth/SAC/split/resources→网格/参考→null/positive/归属C→逐项→关键交互/robustness→按power定V n→hash冻结→一次新V→稳定区域/Unknown与推荐冻结。无可行组合/阳性缺失/cap不足则按预定停止保留失败，不追阳性不调科学标准。

## 8. 总体统计与结论边界

逐层允许时间集合S给a=1{S完全在t前}、b=1{S与t前相交}，a≤真arrival指标≤b；Unknown为[0,1]，样本识别界不是CI。不要求删失独立；Hoeffding上带另要求底层独立/有限总体SRS或适用设计，n为真实单位。多时点/endpoint/region/层union，未知簇不能套iid；n0=0为Unknown。

Risk ITT用原assignment和测量上下包络；双侧全网格带两臂两方向用4J_R常数（旧2J仅上带）。按当前正式有界贡献/定长积分推Y范围，不任意截断DRAC，不将pointwise称同时。cluster max-t/bootstrap效率备选仍需设计/矩/覆盖审核；随机化sharp-null不代异质ATE/SESOI带。

detector阴性不等真实物理未到达；真实CDF需独立同域延迟/漏检证书桥接F_true(t)≤F_det,available(t+d*)+m_delay及足够随访，或真onset允许集本身覆盖；不能把B证书无证外推A。预算αR+αP+αclock+αmeasure≤α，确定性误差不机械分配，估计证书的joint失败必须匹配。校准.05证书不能自动抵.005测量项。

固定H*/SESOI、risk持续全网格上带、同资格各层真arrival上界<η、clock/measurement均满足才逐层Supported；可评估未达标Not established；关键识别/测量不足Unknown。不机械复合三层、不推出个体跨世界提前秒数。

## 9. 一次性决策与论文一致性

T6-R1对象/算子/边界/onset；R2科学损失、a*/b*/d*/稳定标准；R3统计/β_V/族与正式联合预算；R4正式δ/H*/η/风险网格持续；R5四格共同资格/非Q政策支持；R6校准域/资源与下一实验授权。每项集中记录推荐、依据、反对、未知、替代/后果、冻结时点；D1–D7不重复请求。R4/R5非纯测量校准启动阻塞项。

论文只复用Task5于2026-11-02T10:07:46.887013Z的字节/行号审计，Task6未重读在线当前版，不宣称此后最新版相同。OVERLEAF_ALIGNMENT保存Documented Intent/Actual Implementation/Evidence/Affected Files/Conflict/Status: Awaiting Researcher Decision。未来Methods处理纳入/双estimand/三层/clock/统计，Results只真证据，Discussion有限机制/迁移/个体限制；不改main/supplementary/bib，不把Proposal写成结果。

## 10. 影响范围、验证和Context Consistency Check

修改范围限三核心报告、六统一定义、项目研究导航/注册/AI_CONTEXT和文档专用设计计算脚本/小JSON证据；不改code/src、生产code/scripts、正式配置、科研逻辑/接口、Formal定义、Gate/锁、Stage1.1、AGENTS、论文或历史产物。设计计算脚本位于docs/research/P2/task6_support/，非实验执行器。

最小充分验证：该脚本语法与内置数学边界断言/历史计数/原选中文件SHA；本次文档的本地链接/13字段/符号/版本/JSON/禁用状态；validate_project_docs.py --strict-git；研究audit登记变化后按AGENTS运行evidence exporter及verify；Git差异/远端HEAD。无全量pytest/compileall/交通实验。实际验证结果见下表；只证明所列工程覆盖，不证明科研假设或实验已完成。

Context Consistency Check：研究方向/定义/方法/下一实验和未决边界受影响，更新AI_CONTEXT00/01/05/06/07/08、RESEARCH_STATUS/PROJECT_INDEX和PROJECT_REGISTRY；没有实现/架构/数据流变化，不重写02/03/04。阶段/正式result计数/历史失败保持，research audit不新增正式结果。

原始失败记录保留：一次协议写入因命令行反斜杠字符串SyntaxError未执行写入，改直接补丁；一次读取脚本同类转义失败，改无反斜杠字面量；一次CORE增量脚本变量名错误在版本头更新后停止，随后补入正确当前细则；一次历史读取输出编码失败，改显式UTF-8。都未运行交通/访问locked或改生产逻辑，不伪称首次通过。

### 已执行的验证记录（2026-11-02）

| 检查 | 实际结果与覆盖 |
|---|---|
| 文档专用计算脚本语法/内置断言 | builtin compile通过，无pycache；精确二项边界、规划样本量/功效及历史计数断言通过 |
| 设计证据生成及--verify | TASK6_DESIGN_EVIDENCE_OK；34个显式输入哈希、原选中文件SHA和历史审计复核；为当前本机审计读取，完整重算需要所列本地历史产物，不宣称纯Git检出含完整轨迹 |
| 项目文档 | python -X utf8 code/scripts/validate_project_docs.py --strict-git → PROJECT_DOCS_OK |
| 便携证据导出 | export_project_evidence.py --repo-root . → PORTABLE_EVIDENCE_EXPORTED results=92 files=1391；无额外文件差异 |
| 便携证据验证 | 同脚本--verify → PORTABLE_EVIDENCE_OK；该既有导出器范围不替代Task6专用设计证据核验 |
| 定向文档检查 | 18主章节、38参数×13字段、27原Definition ID及各13字段保留；162个本地Markdown链接存在；公式分隔符/六文件版本一致 |
| 注册表/权限范围 | 原canonical条目顺序保留、仅加5入口；历史audit/experiment/result及非授权current字段不变；20个文件仅docs/AI_CONTEXT/evidence，不含生产代码/配置/论文/AGENTS |
| Git格式 | git diff --check及git diff --cached --check通过；既有CRLF/LF提示不扩为全仓库换行清理 |

最终报告记录后重新生成并核验设计证据，再运行strict-git及暂存差异检查后提交。此次没有全量pytest、全仓库compileall或新的交通运行；Git提交SHA与远端核对在最终交付回复记录，不将自身SHA写回产生循环修改。

补充失败及修复记录：首轮差异检查发现CORE末尾多余空行，已修复；一次恢复工作时exec指定目录被拒，默认cwd核实为本项目后继续；一次临时QA把canonical_entries列表当字典路径导致断言停止，改为逐条检查原列表保留及顺序后通过；首次Definition ID临时匹配未覆盖真实粗体字段，改真实格式后确认27条及13字段。它们未造成科研逻辑或历史产物更改。

## 11. 交付物与来源

- 本报告、参数实验协议、集中研究者决策。
- definitions六文件v0.4，27 ID保留，CORE Q–T、SAC/十三字段/依赖表、E54–64/符号/论文对照。
- docs/research/P2/task6_support/calculate_design_evidence.py及evidence/research/P2_TASK6_20261102/design_evidence.json（协议版本/hash、输入证据/设计计算）。
- 历史依据：P1 ESTIMAND/THEORY/DAG；P2 Task1–5报告/决策；Task3原始摘要/原SHA；T18/19run级表；源码formal_risk_measurement.py/formal_design.py；Task5文献/方法/论文有时标审计。来源清单含真实路径/hash，不伪造独立真值。
- 只新增一次NIST官方exact-binomial方法定向核查，链接和阅读范围在协议§17；其数值标准不是交通依据。Edie原文未得，不再无限扩展文献。

**下一项只有P2 Parameter Determination Experiment。** 允许尚未可估参数Unknown，但启动科学项一次裁决后直接照协议运行；不要求再证明理论或再设设计任务。没有把本任务完成解释为AAD假设成立。


### 早窗损失预算的关键可行性结论

真实物理CDF桥接还要求漏检、Unknown、已可能早到质量和抽样余量之和<η。η=1%时，一般95%灵敏度/5%Unknown证书不足。当前推荐待决方案改为m_delay≤η/4、Unknown≤η/4（99.75%及时灵敏度/.25%Unknown只是损失规划，非已达到），为其他质量和统计界留严格余量；一般95%/90%方案只能支持相应测量域，不能升级真实早窗。样本量脚本相应包含严格档和整体验收power，不用普通全零n充足性掩盖成本。
