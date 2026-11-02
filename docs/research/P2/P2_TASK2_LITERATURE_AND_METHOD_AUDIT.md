# P2 Task2 文献与方法审计

日期：2026-11-02
状态：`COMPLETED_WITH_LIMITATIONS`
范围：只调研直接影响 P2 Task2 方法选择的交通波方向、车辆轨迹状态识别、轨迹完整性和时间删失资料；不做大规模综述，不把文献方法直接升级成 AAD 因果判据。

## 1. 调研口径与停止依据

本轮先检查 AAD Zotero 现有索引和项目内方法审计，再对用户给出的四个起始来源
和两个补充来源做有界公开核查。Zotero 索引显示项目已有轨迹标定、轨迹完整性、
交通波和时空传播主题；本任务复用其主题定位，不在仓库建立 PDF 文献库。

检索同义词包括：`kinematic wave`、`traffic shockwave`、`shock wave direction`、
`vehicle trajectory perturbation`、`speed state change`、`trajectory completeness`、
`interval-censored event time` 和 `right censoring`。公开核查以 DOI、出版社/机构
页面和项目已有全文笔记为依据。六个来源已经覆盖本任务的三个直接问题：

1. 微观交互和宏观波前的数学对象与方向；
2. 车辆轨迹上的状态变化和波前候选识别；
3. 采样间隔、轨迹完整性和区间删失对时间估计的影响。

继续扩大检索不会为 AAD 当前选择提供新的直接证据，因为现有资料已经共同支持
“分层记录、方向由数据确定、不能把轨迹算法当作因果 witness、区间不能取中点”
这些方法边界；数值阈值、区域定义、时钟容差和路径准入仍是 AAD 内部的研究者决策。
因此本轮在六个来源后停止。

## 2. 来源总表

| 编号 | 来源 | 资料状态 | 对本任务的角色 |
|---|---|---|---|
| L1 | Lighthill & Whitham (1955), *On Kinematic Waves. II. A Theory of Traffic Flow on Long Crowded Roads*, Proc. Roy. Soc. A 229:317–345. DOI: [10.1098/rspa.1955.0089](https://doi.org/10.1098/rspa.1955.0089) | 公开书目信息与理论来源核查 | 说明宏观 kinematic wave 是空间—时间状态传播对象，不等同车辆身份路径 |
| L2 | Richards (1956), *Shock Waves on the Highway*, Operations Research 4(1):42–51. DOI: [10.1287/opre.4.1.42](https://doi.org/10.1287/opre.4.1.42) | INFORMS 页面与摘要核查 | 说明 shock wave 方向/速度来自宏观流—密度关系，不能替代微观因果边 |
| L3 | Austroads (2015), *Guide to Traffic Management Part 2: Traffic Theory*, AGTM02-15. [官方页面](https://austroads.gov.au/publications/traffic-management/agtm16)；[PDF](https://austroads.gov.au/publications/traffic-management/agtm16/media/AGTM02-15_Guide-to-Traffic-Management-Part-2-Traffic-Theory.pdf) | 官方指南核查；项目 Zotero/主题索引可追溯 | 提供 car following、traffic characteristics、queue、platoon 和 kinematic wave 的方法背景 |
| L4 | Yang, Yang & Du (2024), *A Data-Driven Traffic Shockwave Speed Detection Approach Based on Vehicle Trajectories Data*, Journal of Intelligent Transportation Systems 28(6):971–987. DOI: [10.1080/15472450.2023.2270415](https://doi.org/10.1080/15472450.2023.2270415) | Taylor & Francis/ScienceDirect 页面与公开稿件核查 | 提供从部分轨迹检测宏观波前的可复用流程；不作为 AAD 的路径因果证明 |
| L5 | Lindsey & Ryan (1998), *Tutorial in Biostatistics: Methods for Interval-Censored Data*, Statistics in Medicine 17(2):219–238. DOI: [10.1002/(SICI)1097-0258(19980130)17:2<219::AID-SIM735>3.0.CO;2-O](https://doi.org/10.1002/(SICI)1097-0258(19980130)17:2%3C219::AID-SIM735%3E3.0.CO;2-O)；PubMed [9483730](https://pubmed.ncbi.nlm.nih.gov/9483730/) | PubMed 摘要和方法综述核查 | 支持正确处理 interval censoring，反对把起点/终点/中点当精确事件时刻 |
| L6 | Sharma, Zheng & Bhaskar (2019), *Is More Always Better? The Impact of Vehicular Trajectory Completeness on Car-Following Model Calibration and Validation*, Transportation Research Part B 120:49–75. DOI: [10.1016/j.trb.2018.12.016](https://doi.org/10.1016/j.trb.2018.12.016) | 项目 Zotero 记录和公开摘要核查 | 支持把轨迹完整性、驾驶状态覆盖和缺失原因作为质量门槛；不直接给出 AAD 的传播阈值 |

补充的技术背景还核查了 FHWA 2019 Traffic Analysis Toolbox Volume III 的官方页面
（[FHWA-HOP-18-036](https://ops.fhwa.dot.gov/publications/fhwahop18036/)）。它强调
微观仿真分析的数据密集性、范围和性能指标规划；本轮只把它作为工程规划背景，
没有采用其校准准则或速度阈值，因为 AAD 当前样本和科学目标不满足直接迁移条件。

## 3. 逐篇方法审计

### L1. Lighthill & Whitham (1955)

- **核心方法**：以流量、密度和空间—时间关系描述一维交通的 kinematic wave，
  将状态前沿视为宏观连续介质中的传播对象。
- **关键假设**：一维道路、宏观状态可聚合、流量与密度/速度有适用关系；不以
  车辆身份和单车控制日志为基本对象。
- **数据要求**：空间—时间状态场或足够的流量/密度/速度观测；不是单一车辆
  leader/follower 标签。
- **可复用部分**：AAD 必须把宏观波前定义在道路坐标和时间上，并从数据估计
  前沿方向；它解释了为什么波前方向不应由车辆行驶方向预设。
- **不适用于 AAD 的部分**：不能凭该理论给出某条车辆边的因果资格，不能替代
  source identity、target response、消息分配或 no-message 参考。

### L2. Richards (1956)

- **核心方法**：以连续交通流和经验速度—密度关系推导 shock wave 与其传播。
- **关键假设**：宏观流量关系在目标交通状态适用，状态跳变可用 shock/front
  表达。
- **数据要求**：宏观流、密度、速度或其可靠代理；车辆级 identity 不是必需输入。
- **可复用部分**：宏观波速的正负和大小应从状态场或前沿拟合得到；上下游方向
  不是通用常数。
- **不适用于 AAD 的部分**：不能把宏观 shock wave 直接写成 source→vehicle 的
  Qualified Physical Propagation Witness，也不能解决多源和控制器竞争解释。

### L3. Austroads (2015)

- **核心方法**：交通理论与管理指南，涵盖交通行为、流量—密度—速度、跟驰、
  排队、车队和运动波等对象。
- **关键假设**：指标和模型须匹配道路、交通状态和分析目的，具体应用需要当地
  数据和质量判断。
- **数据要求**：视问题使用速度、流量、密度、车头时距、跟驰和路段状态数据。
- **可复用部分**：支持把微观跟驰、车队/排队和宏观波前作为相关但不同的分析
  层；支持在选择区域状态函数时披露数据覆盖和适用条件。
- **不适用于 AAD 的部分**：指南没有 AAD 的 source event、消息随机化、物理
  witness、\(F_0\) 或时间优先性判据；不能据此冻结 \(\theta_P\) 或 \(h_P\)。

### L4. Yang, Yang & Du (2024)

- **核心方法**：四步轨迹波前检测：对速度轨迹去噪，识别车辆遇到波前的转折点，
  用 DBSCAN 聚类转折点，再用一范数回归估计波前传播速度。方法可使用部分轨迹，
  目标是识别宏观 shockwave 而非车辆级因果。
- **关键假设**：轨迹中的速度变化足以反映波前，去噪和转折点规则在数据上有效，
  聚类出的点属于同一传播前沿。
- **数据要求**：带时间和空间的部分车辆轨迹，足以估计速度变化、转折点和空间
  聚类；阈值和窗口具有数据依赖性。
- **可复用部分**：可作为 AAD 宏观辅助层的候选流程，尤其是固定空间网格、前沿
  方向、采样间隔敏感性和部分覆盖下的诊断。
- **不适用于 AAD 的部分**：不能把其 FFT、DBSCAN、回归或阈值直接作为 \(\phi\)，
  不能取代 micro path 的身份/leader/response 证据，也不能产生 no-message
  counterfactual。论文使用的交通数据和阈值不等于 AAD 的模型配置。

### L5. Lindsey & Ryan (1998)

- **核心方法**：系统比较 interval-censored data 的生存曲线和协变量方法，强调
  区间事件时间不能任意改成精确时间。
- **关键假设**：观察机制、区间边界和删失结构需要被正确声明；不同估计器对
  interval-censoring 的支持不同。
- **数据要求**：事件发生被限制在一个观测区间，或属于右删失/混合删失结构。
- **可复用部分**：AAD 的 onset interval 应直接进入 interval-censored 分析；
  右删失才在适当独立性条件下使用生存方法；需要保留 Unknown 和信息性缺失。
- **不适用于 AAD 的部分**：该综述不是交通传播模型，不能决定物理路径资格、
  状态阈值或时钟校准；其统计假设必须根据 AAD 观察机制重新审查。

### L6. Sharma, Zheng & Bhaskar (2019)

- **核心方法**：研究不同车辆轨迹完整性和驾驶状态覆盖对 car-following 模型
  校准/验证的影响，报告影响具有模型和驾驶状态依赖性。
- **关键假设**：轨迹片段和驾驶状态覆盖会影响可辨识性和误差；完整性不能只用
  行数概括。
- **数据要求**：包含多种驾驶状态、明确缺口和可比较的轨迹片段；需要区分缺失
  类型和状态覆盖。
- **可复用部分**：支持 AAD 保存 coverage、缺失原因、身份连续性和状态分层，
  对固定 cohort 缺失不补零、不由处理后车辆替换提供方法依据。
- **不适用于 AAD 的部分**：研究对象是跟驰模型校准/验证，不提供交通波方向、
  AAD 物理 arrival 或 no-message 分布；不能用其结论估计 AAD 的 \(T_P\)。

## 4. 方法选择矩阵

| AAD 问题 | 文献支持 | 采用方式 | 明确拒绝的直接照搬 |
|---|---|---|---|
| 微观/宏观方向区分 | L1、L2、L3 | 分开记录 vehicle edge 和 macro front，方向由数据估计 | 预设所有波向上游或把 leader→follower 等同 shockwave |
| 轨迹波前检测 | L4 | 作为宏观辅助诊断候选，需固定网格、采样/阈值敏感性和质量记录 | FFT/DBSCAN/回归直接成为 AAD Qualified Witness 或因果判据 |
| 速度状态候选 | L3、L4、L6 | 固定 cohort 上相对 baseline 的有符号速度状态为主候选，median/分位数/比例敏感性 | 把论文阈值、自由流经验值或单次转折点直接冻结为 \(\theta_P\) |
| 轨迹完整性 | L6、FHWA 背景 | 保存覆盖率、状态、身份、缺失和数据来源，低质量时 Unknown/界限 | 以行数、插值或删除缺失车辆制造完整路径 |
| 区间到达时间 | L5 | onset interval、right censoring、interval censoring、Unknown 分开；用相应估计器 | 将区间起点/终点/中点当精确时间，或无条件用 KM |
| 物理因果资格 | 现有 P0/P1/P2 契约 | 用源资格、路径、响应、时钟和竞争解释联合准入 | 把成熟 shockwave 算法当成源→目标的现实因果证据 |

## 5. 对 AAD 的方法结论

### 5.1 方向

交通波理论支持宏观前沿是道路空间—时间对象，车辆交互支持微观边是身份和
关系对象。二者可以互相校验，但不能合并为一条数学路径。AAD 第一版采用微观
纵向交互作为主要 witness，宏观波前只作为辅助方向和一致性记录。

### 5.2 速度状态

轨迹资料足以派生区域速度状态，但阈值、去噪、窗口和覆盖质量决定可重复性。
因此 AAD 采用有符号相对 baseline 速度变化的参数化函数，把平均、median、
分位数和超阈值比例作为预先声明的不同 estimand/敏感性，而不是事后挑选最有利
指标。现有文献没有支持直接冻结数值。

### 5.3 时间删失

观测采样间隔和时钟误差使 onset 通常只能是区间；Lindsey & Ryan 的方法边界
直接支持不取中点和区分右删失/区间删失。Unknown 还包括身份、路径和质量无法
辨识的情形，不能为了套生存分析而把它们统一归入右删失。

## 6. 证据边界与未解决问题

- 文献支持的是方法结构和统计边界，不支持 AAD 的科学效果或现实因果结论。
- Yang 等轨迹波前方法使用的去噪、转折点和聚类阈值需要独立数据校准，不能
  直接成为 AAD 的物理到达阈值。
- 交通波理论不能解决消息分配、controller adoption、source qualification、
  多源竞争或 no-message 反事实。
- 现有 AAD SUMO Formal P2 源事件为零，文献不会改变这一事实。
- 时钟同步精度、区域边界、\(\phi\) 数值参数、删失独立性和 witness 质量仍须
  研究者决定或未来数据支持。

本审计支持 P2 Task2 标记为 `COMPLETED_WITH_LIMITATIONS`；不支持启动实验、
冻结 Protocol Lock 或把模型路径写成现实因果证据。
