# P5 Task1 最终报告

Task ID：AAD-P5-TASK1-20261104。日期：2026-11-04。

状态：DESIGN_COMPLETE_WITH_OPEN_IDENTIFICATION_DECISIONS。完成因果识别方案审计与文档设计；该状态不代表已估计因果效应、研究者已批准新方案、实验准入或 Protocol Lock。

## 1. 完成内容

交付[完整设计](P5_TASK1_CAUSAL_IDENTIFICATION_DESIGN.md)、[研究者决策登记](P5_TASK1_RESEARCHER_DECISION_REGISTER.md)与[便携证据](../../../evidence/research/P5_TASK1_20261104/README.md)。覆盖任务 A–F：三种估计对象、Qpre/四格 A–C 方案、网络干扰与单位、Adoption、Action–Risk、总体时间优先性。设计包含时间展开图、H1–H4 表、随机单位/干扰表和现有/未来证据表。

先核对 Git HEAD/clean 工作区、最新 P1–P4/P7 决定、统一定义及相关源码/证据，未重做 P4 测量设计。基线 3682de08c411e941dd4340474ae7c7702b3fd2e1；36 个来源绑定基线版本。没有修改生产代码、正式配置、P3/P4接口、P7策略、统一定义 v0.4 /27 IDs、历史报告/证据、Overleaf、Gate 或 Stage1.1 授权。

## 2. 核心发现与推荐

1. **Inference：τQ、全部 source-present ITT 与 τSC 是不同对象，不能一般等同。** Qpre 对 ZC 是处理前，但可能受 ZS 影响。全期望分解需要非Q及无源通信效应；不能补零。随机 ZS 不揭示无源单元的潜在 Q(1)。独立反例给出相同可观测边际、不同 principal-stratum 交互。
2. **Proposal：当前 A + 最终 B 候选 + C 备选。** 当前保留 Qpre=1、有源的资格两臂主入口；最终四格在研究者确认的共同源前机会总体上设计。Principal stratification 需要额外假设或部分识别，未批准点识别。最终四格方向保持，具体共同总体、源机制、四格正支持和无源通信策略尚缺。
3. **Proposal：完整 run / 可审计 matched-block 优先。** P7 运行固定模式是工程路径，不是随机器；车辆、帧、消息和同 run 后续事件不是独立样本。同 seed 配对保留 block 依赖。分别审查信息域和物理域，当前整场策略支持不能拆 direct/spillover。
4. **Fact / Unknown：采用事实已接通，采用因果效果未识别。** 继承正式 Adoption 定义和 Enabled/Disabled 方向；采用率、开关 reduced form 与 IV/LATE 分开。排除限制、动态单调性和网络条件不能由日志齐全证明。No Message 与 Disabled 的对照映射也是独立待决事项。
5. **Proposal：H1 与机制分层报告。** Action–Risk 的随机动作策略、IV、纵向 g-formula、interventional effects 各需自己的条件。P4的测量点/区间状态不代表因果识别；普通动作回归与 adopted 分组不能替代机制设计。
6. **Unknown：H4 尚不能经验判断。** T_U、T_R、三层 T_P 分开；同资格/单位/时间/H权重和独立物理参考是前提。Detector CDF 不等于真实到达 F0，缺同域延迟/漏检桥接不能宣布真实物理提前。总体早窗不识别单例反事实提前秒数。

以上推荐未升级为 Agreed。既有确认内容和 11 组新增待决问题、Unknown/对象级 Blocked 见决策登记；无需在本任务中逐项重新请求批准。

## 3. 当前证据支持范围

|层次|已验证事实 / 允许使用|仍缺失 / 禁止升级|
|---|---|---|
|P3/P7 消息链|实际输入消费、decision、command、execution及目标状态可追溯|唯一 Enabled v2及历史基准非随机因果实验；52次采用不等于52独立样本|
|P4 测量|固定完整资格名单、固定N同窗Y界、严格Δv/Δa和版本化外桥已实现；引用历史172测试/15数学检查|当前真实完整区域Y无合格输入；P7单目标352行不能替代全区域样本|
|P2 物理|三层定义、B类有限校准与Unknown规则可复用|Formal A=0、Independent Qualified=0；B不等FormalA/独立V，F0及总体T_R–T_P Unknown|
|方法|复用P1/P2与Zotero历史索引；定向核对6组原始方法来源|本机Zotero只读API失败，未称live库已核验；NBER扫描正文未精读；复杂纵向网络中介尚无识别证书|

Stage0.5=CLOSED_WITH_LIMITATIONS；Stage0.6=PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock=BLOCKED；Stage I=READY_ENGINEERING_ONLY；Stage1.1=NOT_AUTHORIZED。无新增 SUMO/TraCI、seed、场景、Pilot、V、holdout读取、现实采集或实验样本。

## 4. 验证与验收

影响判断：只新增 P5 设计文档/便携审计和导航索引；未改变正式科研逻辑或共享接口。因此不运行 pytest、SUMO、全仓扫描或 compileall。运行标准库确定性数学反例、保护字节、文档和现有证据导出器检查。

独立 Fraction 复算 **11 项通过**：全期望与交互分解、非Q支持缺失、潜在资格两个不可区分世界、有界子总体均值、两臂/四格测量界的端点枚举。全部标记 DETERMINISTIC_IDENTIFICATION_CHECK_ONLY / SYNTHETIC_VALIDATION_ONLY；不调用项目被测函数、不抽随机数、不估因果效果。

|验收组|设计审计结论|
|---|---|
|A 估计对象|通过：区分三个对象、Q的源后属性、A/B/C与四格缺口|
|B 干扰|通过：单位/块依赖、两干扰域、总政策与direct/spillover及正支持明确；具体方案待决|
|C 机制|通过：采用/命令/实际响应分开；IV和Action–Risk额外条件明列，未批准新模型|
|D 时间|通过：三类时间与三层物理对象分开；共同支持、删失/clock、桥接/多重性和Unknown明确|
|E 工程事实|通过：P3/P4/P7最新能力/限制准确继承，不把合成或单车工程数据当区域因果样本|
|F 文档/证据|通过：严格文档检查、44处内部引用、601文件双字节视图、36来源绑定、既有94结果/1458证据文件核验及最小Git归档（13交付文件SHA/11数学检查）；实际记录见validation.json|

保护集合为601个既有文件；同时登记native与Git blob字节，避免改写历史换行。首次便携Git归档因现有core.autocrlf=true转换CRLF而失败；只给本次archive增加core.autocrlf=false，不改旧文件或持久配置，保留失败归档与验证记录。实际检查命令/结果、便携SHA256和阅读失败保存在证据包。工具过程输出编码/输入语法错误如实记录，未执行额外交通命令。没有隐藏科研失败或重新命名历史证据。

## 5. Context Consistency Check

更新 AI_CONTEXT 00/01/05/06/07/08，PROJECT_CONTEXT、PROJECT_INDEX、RESEARCH_STATUS、RESULTS_INDEX及PROJECT_REGISTRY 的P5研究审计入口。05明确本任务无新增实验；06不把Proposal写Agreed；07登记识别缺口；08保留日期历史。

AI_CONTEXT 02/03/04无需修改：本任务没有实现架构、数据流或模块改动；P5对未来设计字段的需求是文档Proposal，不是现有生产字段。定义入口仅被引用，当前定义/参数/假设状态没有改变；不新增竞争性定义。既有实验/results、Gate与历史research audits保持。

## 6. 对P6及后续的接口

P6得到：明确的τQ/四格分离、候选run/block单位、固定总体Y及缺失界、H4同总体F0和联合错误控制需求。SESOI、ICC、功效、正式n、同时带、δ/η/H*、持续规则与α预算均由后续研究者/P6决定，本任务未计算数值。

需要研究者审阅的优先项：共同源前四格总体；通信与采用开关对照；具体随机化/干扰/index-source；机制识别路线；H4 endpoint与时间支持。已有决定不重新批准，未知数据/假设不补齐。

## 7. Git与停止边界

仅在必要验证全部通过后提交 docs(p5): audit causal identification design，并推送 origin/main、核对远端 HEAD；实际SHA以Git和最终回复为准，避免文档自引用。开始工作区clean，精确暂存本任务文件，不混入其他任务。

本任务完成后停止，等待研究者审阅；不自动启动P6、论文实验同步、组会整理或任何实验。DESIGN_COMPLETE 不代表这些后续事项获准。
