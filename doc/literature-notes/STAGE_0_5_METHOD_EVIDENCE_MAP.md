# Stage 0.5 文献—方法—实验—结论边界映射表

日期：2026-10-20（见文末日期勘误）。
结果：`RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1`。
机器可读索引：`doc/literature-notes/stage_0_5_method_index.json`。

**阅读范围声明**：本表区分「原文全文已读」「仅元数据（Crossref）核验」两类。未读全文的文献**不**记录其公式、指标或阈值，只记录书目事实与"本任务未据此采用方法"。任何"作者认为"式的表述都只出现在全文已读的条目中。

---

## 1. 原文全文已读

### L1. Duan, Zeng, Serok, Li, Blumenfeld-Lieberthal, Huang, Havlin (2023)

- 题名：Spatiotemporal dynamics of traffic bottlenecks yields an early signal of heavy congestions
- 出处：Nature Communications **14**:8111（2023-12-04），开放获取
- DOI：10.1038/s41467-023-43591-7 · Zotero `5DE6L9RS`
- 研究问题与数据：北京、深圳 2015 年 10 月各 30 天、1 分钟分辨率的浮动车速度；分析在 5 分钟窗口上进行。
- 实测方法（Methods "Bottlenecks and their associated congestions"）：
  - Eq. 9：`W_e(t) = U_e(t) / U_e95`，其中 `U_e95` 为该路段速度记录的 95 分位（"approximates the standard maximal velocity on this road"）；**`W_e(t) < 0.5` 判为拥堵**。
  - 拥堵组件的识别用 jam tree（ref. 24）：瓶颈 = 组件下游侧连续拥堵时间最长的路段；上游相邻路段在新拥堵后不超过 `θ = 10 min` 内连接算作同一组件。
  - 增长速度：Eq. 7 `V_A = S_P / T_G`；Eq. 8 `V_TI = S_TI / T_I`，单位为"每 5 分钟新增拥堵路段数"。
- 作者报告的主要结果：初始增长速度在早期（≤15 min）即可预测后续拥堵规模。
- 作者承认的限制（本任务所见范围内）：原始速度数据因隐私不可公开。
- **本项目借鉴**：低速连通组件的"规模—持续时间—起始位置—增长方向"描述，以及**相对速度**而非绝对速度的状态定义。
- **迁移时必须修改**：本文是城市路网（有向图 + jam tree），本项目是单走廊纵向单元；本文的 `U_e95` 来自 30 天记录，本项目只有 12–16 分钟窗口，因此参考速度只能取自同一窗口并在报告中披露这一差异。
- **不能推出的结论**：不能把 15 分钟预测模型、`θ = 10 min` 的窗口参数或 `V_TI` 的数值迁移为本高速走廊的验收条件。

### L2. Saberi, Hamedmoghadam, Ashfaq, Hosseini, Gu, Shafiei, Nair, Dixit, Gardner, Waller, González (2020)

- 题名：A simple contagion process describes spreading of traffic jams in urban networks
- 出处：Nature Communications **11**:1619（2020），开放获取
- DOI：10.1038/s41467-020-15353-2 · Zotero `YA2ACMZV`
- 数据：2018-06-27 的 Google 路网速度，六个城市（Melbourne、Sydney、London、Paris、Chicago、Montreal）。
- 实测方法：
  - Eq. 1：`λ_i(t) = v_i(t) / v_max_i`；Methods 明确 `v_max_i` 取"该 link 在一天 24 h 周期内观测到的最大速度"。
  - Eq. 2：`s_i(t) = 1 if λ_i(t) < ρ else 0`；**`ρ` 是预先设定的阈值**，论文图示用 ρ = 0.1–0.7，**没有给出唯一固定阈值**。
  - 拥堵簇：某一有向 link 的 "congested upstream cluster" = 可通过**完全由拥堵 link 组成**的有向路径到达该 link 源点的节点集合。
  - 零模型（原文）："For each time step t, we generate a null model by randomly drawing `λ_i(t)` of each link i from the same distribution of the link relative speeds as in the simulated data at the same time step."
- **本项目借鉴**：相对速度定义；**逐时间片保留边际分布、打乱空间排列**的零模型，用来检验真实低速连通结构是否强于随机排列。
- **迁移时必须修改**：本文的 `v_max_i` 是 24 h 周期最大值，本项目窗口只有十几分钟；零模型的置换次数论文未规定，本项目取 1000 次并声明为工程选择；走廊是 1 维（14 个纵向单元 × 时间片），置换在列方向进行。
- **不能推出的结论**：不能声称已拟合或验证了 SIR 类拥堵传播机制。

### L3. Brockfeld, Kühne & Wagner (2004)

- 题名：Calibration and Validation of Microscopic Traffic Flow Models
- 出处：Transportation Research Record **1876**(1): 62–70
- DOI：10.3141/1876-07 · Zotero `GMF4LZDC` · 全文：https://elib.dlr.de/6652/1/TRB2004-001743.pdf
- 数据：2001 年 10 月日本试验场 DGPS 车队试验，4 次试验 × 9 个前后车对 = 36 个数据对，0.1 s 分辨率。
- 实测方法：**把记录的前车（leading car）数据输入模型，由模型计算后车的车头间距时间序列**，用实测与模拟车头间距的偏差标定/验证模型；时间步 0.1 s；优化用 downhill simplex（多次不同初值）。
- 误差度量：Eq. 2
  `e = Σ_{t=0}^{T} |g_sim(t) − g_obs(t)| / Σ_{t=0}^{T} g_obs(t)`，`t ∈ {0, 0.1, …, T}`，以百分比表示。
- 作者报告：标定误差 12–17%，验证 17–22%；个别数据集验证误差达 40–60%（"overfitting"）；模型之间的差异小于驾驶员之间的差异。
- 作者承认的限制：试验场驾驶比真实道路更谨慎（试验场车头时距约 2.5 s，真实高速约 1.0–1.5 s）；不同模型难分优劣。
- **本项目借鉴**：前车轨迹驱动 + **Brockfeld Eq. 2 归一化间距误差**作为主指标；按"对"为单位报告而不是把逐帧记录当独立样本。
- **迁移时必须修改**：本项目使用自然交通（存在换道、异质驾驶员、非合作前车），误差水平不可与论文的 12–17% 直接比较；论文的优化流程本任务**不使用**。
- **不能推出的结论**：不能把 12–17% 当作本项目的验收阈值或科学容差。

### L4. Schrader, Karnik, Hainen & Bittle (2024)

- 题名：Calibrating Car-Following Models Using SUMO-in-the-Loop and Vehicle Trajectories From Roadside Radar
- 出处：SUMO Conference Proceedings **5**: 209–233（2024-07-17），开放获取
- DOI：10.52825/scp.v5i.1127 · Zotero `LIUYDEMK`
- 数据：1.5 km 信号控制城市走廊的路侧雷达轨迹，含 track-level 关联与融合。
- 实测方法（§3.3.1）：SUMO 网络为**单条 1.8 km 边**，限速 22.35 m/s（对应 50 mph）；**每个前后车对通过 TraCI 进入仿真，TraCI 全程控制前车的位置与速度**；后车参数经 `vType` 设置。
- 度量（§3.3.2）：
  - Eq. 5：`NRMSE(s,v,a) = NRMSE(s) + NRMSE(v) + NRMSE(a)`
  - Eq. 6：`NRMSE(X) = RMSE(X, X̂) / sqrt((1/n) Σ_i X_i²)`
  - 车头时距数据限定在 0–10 s，并剔除低速情形以抑制车头时距膨胀；速度用 6 阶 Butterworth 低通（截止 0.25 Hz）平滑。
- **本项目借鉴**：TraCI 控制前车、单边长直网络、`NRMSE` 定义；分指标报告（间距、速度）而不合并为单一加权分数。
- **迁移时必须修改**：本项目**不评分加速度**（观测加速度为差分派生量，噪声处理未在本任务验证），因此只报 `NRMSE(gap)` 与 `NRMSE(speed)`；前车轨迹来自 NGSIM 而非雷达，存在身份/时钟契约（Stage 0.2）的继承限制。
- **不能推出的结论**：不能因为采用了该文的 SUMO-in-the-loop 方式就声称达到了该文的精度。

### L5. FHWA (2019), Traffic Analysis Toolbox Volume III

- 题名：Traffic Analysis Toolbox Volume III: Guidelines for Applying Traffic Microsimulation Modeling Software — 2019 Update to the 2004 Version
- 编号：FHWA-HOP-18-036，2019 年 4 月，FHWA Office of Operations
- Zotero `IQR7YZBZ` · 第 5 章：https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter5.htm
- 实测要求（第 5 章）：
  - 至少两个关键性能指标：其一为沿关键路径的行程时间或速度剖面，其二为**瓶颈动态**（瓶颈通行能力或持续时间）。
  - 拥堵速度阈值经验法则：**取观测自由流速度的三分之一**，且必须低于"速度-通行能力"对应速度。
  - 拥堵起始/消散按 ≥15 分钟时间间隔识别；须针对**单一代表性日**标定，不推荐对多日平均的合成日标定。
  - 四条可接受性准则：Criterion I（95% 的模拟输出落在 `c_r(t) ± 1.96σ(t)`）；Criterion II（2/3 的输出及两个关键时段落在 `c_r(t) ± σ(t)`）；Criterion III（BDAE，平均绝对误差 ≤ 该交通条件内各日相对代表性日的平均偏差）；Criterion IV（`|平均系统误差| ≤ (1/3) × BDAE 阈值`）。
  - 明确说明：标定是"每个交通条件一次运行"，不需要用不同随机种子多次运行来标定。
- **本项目借鉴**：把微观行为诊断与整场景状态诊断分开；同时评价时变状态与瓶颈动态；阈值取自由流速度的 1/3 作为文献锚点。
- **迁移时必须修改**：上述四条准则需要**同一交通条件下的多日样本**来构造 `σ(t)` 与 BDAE 阈值。本项目只有两个不同交通条件的 15 分钟窗口，**无法计算** `σ(t)` 与 BDAE，因此本任务**未**使用这四条准则，也未把"1/3 自由流速度"当作观测真值（工程配置的 27.78 m/s 不是实测自由流速度）。
- **不能推出的结论**：不能把 FHWA 的包络或准则当作本项目的科学容差 δ。

### L6. SUMO 1.26 官方源码（软件实现依据，不是文献）

- 位置：`code/outputs/formal/calibration/stage_0_5_final_candidate_v1/official_source/`（封存于最终收口任务，SHA 已登记）
- 关键事实：
  - `MSCFModel::maximumSafeFollowSpeed()`（`src_microsim_cfmodels_MSCFModel.cpp` L947 起）以 `myHeadwayTime`（即 `tau`）作为车头时距进入安全停车速度计算，因此**平衡态要求 `v·tau` 加上最小间隔**。
  - `MSCFModel_Krauss::dawdle2()`（`src_microsim_cfmodels_MSCFModel_Krauss.cpp` L129 起）实现 `sigma` 驾驶不完美：`speed -= ACCEL2SPEED(sigma * speed * random)`（低速分支）或 `sigma * myAccel * random`（高速分支）。
  - `libsumo::Vehicle::setSpeed()`（`libsumo_Vehicle.cpp` L1907 起）在 `speed >= 0` 时写入**一直持续到 `SUMOTime_MAX`** 的速度时间线——即 TraCI 的 `setSpeed` 是**持续覆盖**，要解除必须再调用 `setSpeed(-1)`。本任务的轨迹重放因此**不对后车调用 `setSpeed`**（早期实现因这一点产生过后车速度被冻结的缺陷，已在实现记录中披露）。
- 用于核对的版本：SUMO 1.26.0，二进制 SHA 记录在冻结计划中。

---

## 2. 仅元数据核验（Crossref），全文未读

以下条目的书目信息经 Crossref DOI 记录核验；**本任务未据其采用任何公式、指标或阈值**。

| ID | 文献 | 出处 | DOI | Zotero | 在本项目中的角色 |
|---|---|---|---|---|---|
| L7 | Kesting & Treiber (2008), Calibrating Car-Following Models by Using Trajectory Data: Methodological Study | TRR **2088**(1):148–156 | 10.3141/2088-16 | `GSJPFHJK` | 方法背景：轨迹数据标定的稳健性；本任务未采用其优化器 |
| L8 | Punzo, Ciuffo & Montanino (2012), Can Results of Car-Following Model Calibration Based on Trajectory Data be Trusted? | TRR **2315**(1):11–24 | 10.3141/2315-02 | `ZJGB2X68` | 方法背景：校准不确定性与多指标冲突；本任务未使用 cobweb plots |
| L9 | Krauss, Wagner & Gawron (1997), Metastable states in a microscopic model of traffic flow | Phys. Rev. E **55**(5):5597–5602 | 10.1103/PhysRevE.55.5597 | `I4NU8C5G` | 背景：Krauss 模型的亚稳态；实现以 L6 源码为准 |
| L10 | Krauß (1998), Microscopic Modeling of Traffic Flow: Investigation of Collision Free Vehicle Dynamics | DLR-Forschungsbericht 98-08，115 S.，Universität zu Köln 博士论文 | —（DLR elib 8380 / SUMO 全文 PDF） | `XHLWGAC3` | 背景：模型原始推导；实现以 L6 源码为准 |
| L11 | Sharma, Zheng & Bhaskar (2019), Is more always better? The impact of vehicular trajectory completeness on car-following model calibration and validation | TRB Part B **120**:49–75 | 10.1016/j.trb.2018.12.016 | `B8J8W6P2` | 背景：轨迹完整性对校准的影响；本任务的轨迹完整性由 Stage 0.2 契约继承 |
| L12 | Kolekar, de Winter, van Arem (2020), Human-like driving behaviour emerges from a risk-based driver model | Nat. Commun. **11**:4850 | 10.1038/s41467-020-18353-4 | `9XZTIZ2S` | 仅背景：驾驶行为机制，不是本任务的校准方法依据 |

---

## 3. 方法—实验—代码对应

| 实验阶段 | 采用的方法 | 来源 | 代码 | 证据文件 |
|---|---|---|---|---|
| A1 阈值敏感性 | 绝对速度阈值 5/10/15 m/s；`W = U/U95 < 0.5`；`λ = v/v_max < ρ`（ρ=0.3–0.6）；`1/3 × 27.78 m/s` | L1 Eq. 9、L2 Eq. 1–2、L5 第 5 章 | `stage_0_5_jam_definition.py` | `jam_definition_sensitivity.json`、`jam_definition_rules.csv` |
| A2 零模型 | 每个时间片内重排速度（保留边际、破坏空间排列），1000 次，种子冻结 | L2 Methods | `stage_0_5_jam_definition.null_model` | 同上（`null_*` 字段） |
| B1 轨迹重放 | 前车由 TraCI 逐 0.05 s 施加观测位置/速度；后车完全由模型驱动；逐样本核验前车跟随偏差 | L3 §"Simulation setup"、L4 §3.3.1 | `stage_0_5_leader_replay.replay_pair` | `replay_plan.json`、`runs/*/` |
| B2 基准与候选 | `tau = 1.0` vs `tau = 1.6`，其余冻结 | 项目冻结基准 + 本任务候选 | `stage_0_5_leader_replay.configuration` | `replay_plan.json` |
| B3 指标 | Brockfeld Eq. 2；`NRMSE(gap)`、`NRMSE(speed)`；间距/速度偏差与 MAE；车头时距；闭合速度分布 | L3 Eq. 2、L4 Eq. 5–6 | `pair_metrics` | `replay_summary.json` |
| B4 解释规则 | 双窗口改善且核心指标不恶化才算支持；否则报冲突或异质性 | 任务书 §六 B4 | 运行前写入计划 | `replay_plan.json` |
| C 条件供给 | **未执行**（B 阶段未支持行为候选） | 任务书 §七 C4 | — | `phase_c_decision.json` |

---

## 4. 本任务明确不做的推论

1. 不用 Brockfeld 的 12–17% 或 FHWA 的 1σ/2σ 包络作为本项目的科学容差。
2. 不把工程配置的 27.78 m/s 当作实测自由流速度。
3. 不声称已复现 US-101 拥堵、已校准 Krauss 模型或已通过 Stage 0.5。
4. 不声称零模型检验证明了因果传播机制。
5. 不把本任务的 48 次微型重放算作已获授权的正式校准运行。

---

## 日期勘误（2026-10-20）

本文件、`docs/STAGE_0_5_TRAJECTORY_RECONSTRUCTION.md`、`docs/STAGE_0_5_SUMO_SCENE_RECONSTRUCTION.md` 与 `docs/plans/2026-10-21-stage-0-5-trajectory-reconstruction.md` 曾将执行日期标为 2026-10-21。核对提交时间（`afdc3d0` 的 author/committer date 为 2026-10-20 20:20:17 +08:00）与本地时区（Asia/Shanghai，+08:00）后确认：**实际执行日为 2026-10-20**，原标注为撰写时的人工日期错误。文件名与已提交正文按项目惯例保留不改，勘误在此显式登记。
