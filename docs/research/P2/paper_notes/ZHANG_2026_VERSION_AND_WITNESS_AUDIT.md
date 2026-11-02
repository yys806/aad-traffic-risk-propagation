# Zhang 2026：正式版本核查与物理 Witness 审计

日期：2026-11-02。状态：正式期刊版 **PARTIAL_READ / FULL_TEXT_UNAVAILABLE**；SSRN全文精读沿用Task3，Task4复核首页、摘要、引言及方法记录。不能将预印本阅读升级成期刊全文阅读。

## 1. 完整出处与可核验版本

期刊：Tianya Zhang, Xiunan Wang, Pengyuan Sun, Maged Shoman, Benedetto Piccoli, Peter J. Jin. *Physics-informed graph modeling for traffic shockwave analysis through optimized change-point detection*. Transportation Research Part B: Methodological 211 (2026), 103522. DOI：[10.1016/j.trb.2026.103522](https://doi.org/10.1016/j.trb.2026.103522)。Crossref/Elsevier元数据：2026年9月；Zotero Q65YUJ89。

实际附件：CLA3GKSX，SSRN 5903681，2025-12-10提交，36页PDF，题页仅四位作者（Zhang/Wang/Sun/Shoman），明确not peer reviewed。SHA256：047b49c784c49214721aae6021029a3bb3011f9287c23b025adf26fdb41ac253。Task3全文方法、实验、讨论、结论记录见P2_TASK3_LITERATURE_AND_METHOD_AUDIT.md §L8。

获取日志：ScienceDirect正式页HTTP403；已登录浏览器打开正式PII页仍显示captcha，未绕过。Elsevier TDM返回HTTP200但仅1873字节coredata、openaccess=0，无全文。OpenAlex的green OA指向同一SSRN，不能认证为期刊最终稿。PII为S0191261526001347。此限制阻断正式版本实质逐项比对，不阻断其余定义与创新性审计；继续检索同一副本不能补足版本证据。

| 比对项 | SSRN可证内容 | 正式版本可证内容 | 结论 |
|---|---|---|---|
| 作者 | 四人，见PDF题页 | 六人，增加Piccoli/Jin，DOI元数据 | 已验证差异 |
| 题名 | 同题名（大小写差异） | 同题名 | 元数据一致 |
| 日期、载体 | 2025-12-10，not peer reviewed | TRB 211/103522，2026-09 | 已验证版本不同 |
| 数学定义/有向性 | 引言称DAG/causally-linked，方法使用undirected graph | 未取得正文 | 实质变化Unknown |
| 算法与物理约束 | CUSUM→PELT/优化分段线性→图→连通分量 | 未取得正文 | Unknown |
| 数据、标注与评价 | NGSIM六15min片段、100专家STMap标注 | 未取得正文 | Unknown |
| 数值与结论 | 下节所列为预印本作者报告 | 未取得正文 | 禁止转录为journal结果 |

## 2. 研究问题、模型和数学方法（仅预印本）

从车辆位置/速度轨迹识别加速、减速change points，跨车连接事件并聚类交通波，避免仅从粗网格STMap识别形状。候选流程是CUSUM初筛、PELT及优化piecewise-linear拟合确定运动学变化点，再用时空邻近、波速、加速度/轨迹alignment等物理约束构造事件图，连通分量形成波。

节点是轨迹变化事件，不是持续车辆实体。图边代表符合假定约束的候选传播联系；不等同实际同车道leader→follower记录。引言DAG/因果级联措辞与方法无向图之间有语义张力，不能靠有向画箭头修复因果识别。

关键假设：轨迹质量足够、change points可分、阈值/优化惩罚可代表所研究交通波；波速和空间约束排除不合理关联。上游/下游必须按坐标和候选影响方向分别解释，不能把车辆行驶方向当影响方向。

## 3. 数据、结果、作者结论与局限（仅预印本）

NGSIM US101/I80六个15分钟片段；100个人工STMap标注作为评价参考。作者表中报告F1=0.849、波速误差1.421 ft/s；未复算，不能视为AAD验证结果，也不能确认正式版保留这些数值。与轨迹/图像算法比较验证的是检测一致性和波参数精度。

作者摘要将波描述为跨车辆制动/加速因果级联；正文方法提供物理可解释的关联恢复，没有独立信息干预、随机化处理、外生工具变量或可识别反事实。论文使用causal/causation不自动满足AAD的策略因果识别。预印本讨论承认轨迹依赖、参数与更复杂场景泛化问题；此处不把自己的因果质疑冒充作者主动承认，亦不推测期刊版最终措辞。

## 4. 与AAD W1–W9的逐类对照

W1–W9原编号和完整条件仍以Task2规范为准；下表比较证据功能，不重编号。

| 证据功能 | 预印本事件图 | AAD微观Witness | 可复用与边界 |
|---|---|---|---|
| 运动学变化 | 优化change points | 源变化与后续目标响应均须记录 | 候选提取可参考，参数不可迁移 |
| 身份/关系 | 以事件节点关联 | 连续车辆ID、实际leader/follower、同车道分段 | 时空邻近不能替代真实交互关系 |
| 方向/时序 | 物理约束候选联系；图语义待澄清 | source→response时间区间顺序可审计 | 不按区间中点强制排序 |
| 多跳 | 图连通/波聚类 | 每跳均需准入，路径time-respecting | connectivity不等于Qualified |
| 替代解释/质量 | 以物理约束提高检测一致性 | 多源、换道、控制命令、缺失、clock与竞争解释独立登记 | 不以算法分数排除未测混杂 |
| 宏观联系 | change points聚类成波 | micro路径与macro状态分别报告 | macro波前不能替代micro身份链 |
| 因果层 | 检测算法，无独立干预识别 | Qualified也只是预定义路径证据 | 两者均不得自动称因果证明 |

## 5. AAD独立判断和后续启示

该工作直接威胁“首次用车辆级图表示制动级联/交通波”的创新主张；AAD不能把图、物理约束或多跳本身当独创。可区分的候选是同源事件下完整消息生命周期、实际采用/动作证据、资格子总体随机化风险效应与独立no-message物理参考的联合证据契约，尚未被AAD实证实现。

不将检测图直接导入生产Witness，不冻结θ/h/q，不宣布其因果措辞错误已在正式版复核。下一步只需合法取得正式全文后按本表复核变化；当前版本缺口保留，不因此新增实验。


正式版补充primary metadata/摘要来源：Rutgers机构出版记录 https://www.researchwithrutgers.org/en/publications/physics-informed-graph-modeling-for-traffic-shockwave-analysis-th/ （本轮读取摘要与六作者/卷号/DOI）。摘要继续使用因果级联/微观图的表述，但摘要不能证明最终Methods包含独立因果识别；本审计不据此填补正式数学/实验的Unknown。
