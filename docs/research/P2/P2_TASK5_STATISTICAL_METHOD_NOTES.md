# P2 Task5 — 定向方法阅读笔记

日期2026-11-02；阅读版本和推断分别登记。本文不冒称所有文献全文精读。

## M1. Frangakis–Rubin 2002：资格不是自动可识别的共同总体

出处：Constantine E. Frangakis; Donald B. Rubin. Principal stratification in causal inference. Biometrics 58(1),21–29. DOI10.1111/j.0006-341X.2002.00021.x。Zotero TVEZQ3UT，note NEVZT5FQ。已读PMC作者手稿HTML的完整article，包括§1–6和例子/参考文献；FULL_TEXT_READ_HTML，不冒称出版PDF逐页阅读。地址https://pmc.ncbi.nlm.nih.gov/articles/PMC4137767/。PDF端点返回HTML而非PDF，未导入假附件。

研究问题：如何在有处理后变量时定义具有因果含义的效应，而不把观察到的不同组直接比较。基本分层由潜在中间变量对(S(1),S(0))决定；principal effects在同一不受实际分配改变的潜在成员层比较潜在结局。§3 Eq3.2的似然同时积分缺失潜在结局和缺失层成员，作者明确没有附加假设通常不存在唯一最大似然估计。§4依从、缺失和死亡截断例子；§5–6讨论替代结局与科学知识/敏感性，未承诺普适无假设点识别。

方法假设：潜在处理定义、实际assignment机制、成员/结果模型及具体科学限制。本文是方法论与已有例子，不是交通数据，不提供AAD阈值或功效数值。作者的well-defined principal effect与能够从实际观测识别是不同命题。

AAD推断：Qpre先于ZC，故可用于通信随机试验的纳入；但它受ZS源条件影响，source-absent的Q(1)未知。即使约定Q(0)=0也没有显示Q(1)成员。不能用两个臂各自观察到的资格拼一个相同人群，也不能仅以“principal stratification”名称声称已解决。可复用定义/敏感性框架，不复用为现有四格识别证明。替代是源前共同opportunity，仍需研究者决定与额外支持。

## M2. Hoeffding 1963：保守同时界的可执行后备

出处：Wassily Hoeffding. Probability inequalities for sums of bounded random variables. Journal of the American Statistical Association 58(301),13–30. DOI10.1080/01621459.1963.10500830。Zotero ASAGL6D9 / 原始PDF42JXM756 / note3DCQPWE5。来源RPI课程公开原始扫描，SHA256 3021bcc097ef23a99a84d0eef8dcce2fd835c71df79a105727d3e03f8f0b8930，19 PDF页含封面。PARTIAL_READ：视觉核对印刷pp13–15、28（PDF2/3/4/17），没有OCR全文，不标FULL_TEXT_READ。

问题：独立有界变量和的尾概率。已核Theorem1 Eq2.3：变量在[0,1]时，P(mean−Emean≥t)≤exp(−2nt²)；§6说明有限总体简单无放回取样可用相应独立抽样界。没有要求不同时点彼此独立；逐点有效界再union可得有限预定族的同时控制。

AAD推导（不是原文交通结论）：先以允许集合给a≤真实arrival指标≤b，再对固定目标的b均值/有限总体取样上界加sqrt(log(K/α)/(2n))。n是独立run/簇或SRS抽样单元，不是帧；预定族K覆盖所有时点/endpoint/H。风险侧若已有真实有限范围，可逐臂同理上包络差并控族错误。自适应选窗、未知簇依赖、不均匀分配直接套SRS、无界DRAC截断都不受此证明支持。

局限：该后备很保守，可能样本量不可行；无有效范围就不能使用，Unknown可能使上界恒为1。只展示有效构造，不宣称已在AAD验证覆盖或估F0。正态bootstrap/cluster max-t是另行设计与验证的效率备选，不由该文保证。

## M3. 复用的观察与交通测量来源

Hall, Traffic Stream Characteristics, FHWA Traffic Flow Theory Chapter2，Zotero26RQQ7EE / XBQFKNWX；本轮补核§2.1–2.2的点/空间/时空支持、space/time-mean及部分穿越。仍PARTIAL_READ，不称整章或Edie原文全文读完。Edie原文一次定向搜索未取得合法可核版本；1963会议/1965出版差异不擅定，继续记录缺口。宏观公式是有官方测量依据的Edie型Proposal，不是新声称的AAD实证结果。

区间删失复用Task3 L14 Fay–Shaw (2010), Exact and Asymptotic Weighted Logrank Tests for Interval Censored Data: The interval R Package, JSS36(2),1–34, DOI10.18637/jss.v036.i02，Zotero QUH3LUP3 / TIWGTN2S的已审计来源和P1统计方案，不重复建立文献库。Turnbull须正确first-event历史及可辩护inspection/coarsening机制；可恢复状态的长缺口不能直接视作不可逆failure inspection。KM不处理一般区间删失。上述适用边界与允许集合保守界分别说明，不用估计软件掩盖观察机制不识别。

Hudgens–Halloran2008、Aronow–Samii2017复用P0已经审计条目H8GFNS8U、T6SFNY5I，不重读为“新增成果”。实际分配单位、partial interference、exposure positivity与HT权重条件继续适用；同seed共享背景不能增加独立样本量。

## 阅读和归档限制

新增两条先查全库281个top-level条目，未按标题反查Crossref。正式DOI元数据逐一核对，归现有06_类超距与因果理论QPEI5PQP并保留AAD根集合。期刊指标用现有easyScholar按正式刊名返回；缺失指标Unknown，CCF未核验不得写不在目录。Crossref简称返回全名时保留返回值、不手造简称，官方标准短名仍待补核。Principal无合法PDF，Hoeffding为扫描且本环境无OCR，未生成其双语PDF；Zhang正式版已另有双语附件。机器翻译不是原文或方法正确性证据。
