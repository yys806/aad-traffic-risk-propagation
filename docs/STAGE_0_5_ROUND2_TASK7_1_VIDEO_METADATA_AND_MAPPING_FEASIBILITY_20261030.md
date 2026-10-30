# Stage 0.5 Round2 Task7.1 — 视频元数据与映射可行性

日期：2026-10-30。任务状态：**COMPLETED_WITH_BLOCKERS**。

执行基线：668b88376e0d84c257c4ee7392291a501167add2。开始时本地 main、直接查询的 origin/main 一致，工作区 clean。

## 1. Mainline Check 与结论

本次有界只读科研调查服务于真实源区 Formal P2 的独立物理参考获取，不能证明 AAD 的信息因果效应。Task7 物理审查仍为 BLOCKED_NO_VERIFIED_INDEPENDENT_PHYSICAL_REFERENCE。本次没有下载视频、选择事件或开展视觉审查。

**建议研究者决定是否进入摄像机 7、8 × 两个授权窗口的条件性最小资源申请。** 空间证据足以收敛澄清对象，但没有验证完整可视覆盖、视频时钟或逐文件许可，不能直接获取。

- geographic_candidate_camera_set = [7, 8]。
- minimum_camera_set = null：地理 footprint 不等于全源区、全车道均可审查。
- PTS 映射、具体视频许可、单文件大小和校验码仍 Unknown。
- Coifman & Li (2017) 原文访问阻断，必读全文要求未全部闭合，不标为 Pass。

Formal P2 源区 167/159、Task1–Task7 历史结果、AGENTS.md、06_DECISIONS、Gate、Stage 0.6、Protocol Lock 和 Stage I 均保持原状。没有 SUMO/TraCI、新轨迹、新 seed、第三真实窗口或 holdout 读取。

## 2. Existing Work Reuse

遵循项目进入顺序恢复当前状态、注册表、研究状态/索引、PROJECT_CONTEXT 和 Git；定向核查 AI_CONTEXT 01/02/03/05/06/07、Task7 完整报告及任务指定的五项机器证据。Task1–Task6 通过已登记报告及 Task7 复用索引恢复，不重复计算。

| 问题 | 复用资料 | 本次用途 | 未重复的工作 |
|---|---|---|---|
| 正式事件/onset | Task4/5 已封存统计和唯一归属审计 | 保持 167/159，继承时钟支持 | 不重提取 P2 或重建匹配 |
| 连续性/人工准备 | Task2.1–2.3，经 Task7 复用清单 | 数学连续性不等于物理真实性 | 不重做 447 图册或 48 模板 |
| 微观交互 | Task6 报告和质量边界 | 明确独立物理参考缺口 | 不重跑联合分析或 324 次实验 |
| 本地视频/许可 | Task7 availability/resource/time 审计 | 继承有界目录调查及许可版本差异 | 不扫描私人或无关目录 |
| 摄像机几何 | Task7 八台 GIS 几何及 SHA | 新增 Local_Y 空间桥接 | 不重新开发 GIS 提取流程 |
| 单位与诊断时钟 | real_trajectory.py、ngsim_risk_calibration.py | 核查 0.3048 换算及非 PTS 锚 | 不修改正式数据/身份规则 |

新增计算只针对尚缺的 Global/Local_Y/相机空间对应。另复查官方元数据、指定全文/代码及 Precise NGSIM 两窗的字段和覆盖。完整清单见新证据包 evidence_reuse_matrix.csv。

## 3. Literature & Code Reuse

### 3.1 Coifman & Li (2017)：必读全文仍阻断

A Critical Evaluation of the Next Generation Simulation (NGSIM) Vehicle Trajectory Dataset，TRB 105:362–377，DOI 10.1016/j.trb.2017.09.018。

Crossref 元数据取得；出版商和作者资源访问未取得正文。取得的 .pdf 命名响应为 HTML，不是论文。**没有把摘要、任务说明或 2024 论文转述伪装成已阅读 2017 原文。** I-80 Camera 6、10 fps、Frame_ID 对应仅为待原文核查的方法线索，不能移植至 US-101。该项保留 FULL_TEXT_ACCESS_BLOCKED。

### 3.2 Coifman & Li (2024)：完整 26 页全文已读

Partial Trajectory Method to Align and Validate Successive Video Cameras for Vehicle Tracking，TRC 158:104416，DOI 10.1016/j.trc.2023.104416。

作者实际研究 I-80 七台相机，利用各相机 partial trajectories 检查重叠、缺口及相对比例，并用独立正射图重投影检查空间关系。§3.1/p14 明确先核验相邻相机无时间偏移，再做空间分析：空间和时间同时漂移可互相补偿。其方法不能代替本项目尚缺的 PTS 锚。

可借鉴：逐相机几何验证、相邻视野的共同车辆及多段 partial trajectories 检验、独立道路几何参照。其 I-80 误差不是 US-101 已发生同类错误的证明；其低速排除用于拟合的具体处理不能成为 AAD 事件筛除阈值。没有宣称完整复现其算法或拥有完整公开校准代码。

### 3.3 Zhang et al. (2024)：完整 PMC 正文已读

Deep Spatial-Temporal Embedding for Vehicle Trajectory Validation and Refinement，CA-CIE 39(11):1597–1615，DOI 10.1111/mice.13160。

论文使用沿车道 scanline 的 STMap、embedding 和后处理重建纵向轨迹；以约 100 个图像—原始 NGSIM 坐标对应点及相机重叠进行标定/优化。因此其坐标参考不完全独立于原始轨迹。§6.2 的人工位置参考来自 I-80 单相机材料，不能证明所有 US-101 源区事件的物理真实性。

公开仓库固定 commit：6c8e38ea20458761290327799db1acf676586094。已检查 README、Inference/post_processing.ipynb、Evaluation README 与 CompareWithGroundTruth.m、Consistency.m、JerkAnalysis.m、getTrajectoryPairs.m、platoon_consistency.m。公开内容提供 mask/component 后处理及轨迹/运动学比较，未提供完整训练及全部相机标定/同步链。没有运行这些程序、训练 STDE 或重复实现其标定方法。

### 3.4 文献管理与访问边界

按现有 Zotero AAD 工作流登记三篇：2017 为 7JHH37JY（元数据、无全文附件）；Coifman 2024 为 SZL54NKN（完整 PDF 附件 FDMRDKC3）；Zhang 为 SQYZHHPM（完整 PMC HTML 附件 CZ6DMMXB）。已有指标工具补充可用期刊指标，不臆造缺项。双语翻译本次未启动。忽略的 literature-work 仅为工作产物，不建立新的本地 PDF 文献库。

详见 literature_reuse_assessment.md、alternative_reference_assessment.json 和 source_bindings.json。

## 4. Spatial Mapping：CRS、控制点与道路检查

### 4.1 CRS 与单位

操作性采用 **EPSG:2229，NAD83 / California zone 5，US survey feet**。证据包括官方总体/正射文档、TFW/GIS/Global 坐标重合，以及正射图道路特征。将原生点 (6451175,1873276) 反投影：

| 候选 | 纬度、经度 | 与现场关系 |
|---|---|---|
| EPSG:2229 / zone 5 | 34.139298, −118.365145 | Universal Studios / US-101 现场 |
| EPSG:2227 / zone III | 37.138912, −120.879051 | 不在目标现场 |

EPSG 官方 WKT、候选参数和计算结果均绑定 SHA。这支持采用 zone 5，但**不能证明字典“III”的历史成因就是笔误**，该成因 Unknown；GIS 没有 .prj 的事实不变。

canonical Local_X/Y 按源码既定 0.3048 m/ft；投影残差按 US survey foot = 1200/3937 m 转换。没有改变正式单位语义。

### 4.2 独立于风险的 130 个小型控制点

每窗在 lane 1–5 × 每 50m 纵向格 [0,650)m 中取首条原始记录，65 点/窗；0750 扫描至第 3881 行，0805 至第 3326 行即停止。控制点只有原始行号、lane、Local_X/Y、Global_X/Y，不含车辆 ID 或风险字段，见 spatial_control_points.csv。没有重提取完整轨迹。

canonical 只按这 65 个原始行号/窗读取必要空间字段，65/65 均匹配；Local_X/Y × 0.3048 与 canonical x_m/y_m 最大差 0.0m。接受的历史大文件 SHA 与本次有限交叉检查分别记录，没有重跑所有大 Hash。

拟合：[Global_X,Global_Y] = [1,Local_X_ft,Local_Y_ft] × per-window 3×2 coefficients。

| 窗口 | n | 残差 RMSE(m) | 最大(m) | 交替留出 32 点 RMSE(m) |
|---|---:|---:|---:|---:|
| 0750 | 65 | 2.0883 | 5.4511 | 2.0193 |
| 0805 | 65 | 2.1314 | 5.5750 | 2.0797 |

混合拟合 RMSE 6.4977m；用一窗预测另一窗约 12.47m。故拒绝 pooling，分别映射，不人为平移原数据。差异成因 Unknown，不能称作视频偏移已证实。内部残差和交替留出是模型内一致性检查，不是外部物理精度或置信区间。

### 4.3 正射影像与 CAD

对已有 TIFF 仅读必要条带并裁剪，叠加八台 footprint、控制点及两窗不同颜色的源区边界。已查看主线、中隔带、匝道等静态道路特征，支持几何位于正确道路方向；这是道路检查，不是车辆视频审查。

实际 TIFF 为 17288×16292 RGB，TFW 为 [0.5,0,0,−0.5,6448541.880999999,1877048.179]，即 **0.5 ft/pixel**，与文档 0.25 ft/pixel 不一致。采用实际 TFW，差异成因 Unknown。文档相对精度 2.5ft ≈ 0.762m 仅属于参考图，不是净距/TTC 真值精度。TIFF 无 GeoTIFF CRS tags。

DWG 的 AC1015 文件头及通用制图图例已检查；没有现成 DWG 几何读取器，未安装转换依赖。未声称独立解码 CAD 几何，本次使用任务允许的“独立道路特征”路线。影像、DWG 与大文件留本地。

## 5. Camera Coverage

GIS 为 PolyLine。7–1 号四角可由约 23–25m 的横向边闭合，8 号首尾仅差 0.523m；可作为地理 footprint 解释，但不是逐帧有效视野。每窗对五条代表性 lane 中线与 polygon 求交，再反解 Local_Y。没有把周长当覆盖长度。

下表是五条代表线交集的纵向包络，**不是全车道矩形可见性保证**，均为近似米制范围。

| Camera | 0750 Local_Y(m) | 0805 Local_Y(m) | 源区相交 |
|---|---:|---:|---|
| 1 | 573.39–674.44 | 585.62–686.76 | No（该近似映射下） |
| 2 | 477.86–574.22 | 490.09–586.51 | No |
| 3 | 380.46–479.10 | 392.70–491.39 | No |
| 4 | 299.80–381.43 | 312.04–393.72 | No |
| 5 | 241.01–300.64 | 253.26–312.94 | No |
| 6 | 168.67–241.41 | 180.92–253.70 | No |
| 7 | 83.88–169.52 | 96.19–181.81 | Yes，地理候选 |
| 8 | −18.75–84.34 | −6.38–96.62 | Yes，地理候选 |

US-101 南向行驶、Local_Y 增加时，从北侧 8 号向 7、6…1 号推进；此对应由坐标和道路求得，不按编号直接推断。

camera_localy_coverage.csv 保留 80 个 period/camera/lane 求交段。个别边缘 lane 在 y≈0 不在 footprint 内；代表 lane 的完整可见性也未经视频确认。控制点残差、道路曲线近似及遮挡未知，使操作性 minimum_camera_set 必须继续为 null。

## 6. Time Alignment

复用 Task5/7，两个窗口分别保留：

| 窗口 | Global_Time 范围(ms) | 2005-06-15 Pacific UTC−07 支持 |
|---|---|---|
| 0750 | 1118846979700–1118847932500 | 07:49:39.700–08:05:32.500 |
| 0805 | 1118847843000–1118848842000 | 08:04:03–08:20:42 |

两窗时钟重叠 89.5s，不合并身份、事件或时间块。Global_Time − 100 × Frame_ID 只构造身份诊断时钟，不是视频 PTS 锚。文件名 07:50 不能当第 0 帧 epoch；官方 synchronized 声明也不是验证结果。

当前缺少 raw PTS、实测 fps、文件起始 epoch、Frame_ID↔PTS 锚、相机偏移/漂移及丢帧核验，因此**不能建立可靠视频—轨迹时间映射**。

未来获取批准后，逐 camera 7/8、逐窗用 ffprobe 获取流与逐帧 PTS，检查前/中/后多个可靠锚、offset/rate/drift、重复/丢帧及跨相机一致性。processed ID 只辅助定位。实际 epoch 支持超出名义窗口边界，须向提供方澄清实际文件起止；本次不人为偏移、不下载视频解决这些问题。

## 7. License & Resource

当前 data.gov 视频目录复查成功，视频附件和历史说明复用 Task7 SHA。整包记录为 12,539,460,866 bytes。本次没有请求 ZIP 内容、Range 或中央目录。

| 范围 | 公布表述 | 保留边界 |
|---|---|---|
| 当前视频 catalog | CC BY-SA 4.0 | 不自动覆盖旧条款 |
| 官方视频附件 p2 | CC BY 2.0 | 单独保留差异 |
| 历史轨迹/RDE 元数据 | 署名及不得向第三方复制传播等限制 | 不能混作具体视频新授权 |
| Precise NGSIM 代码 README | 学术/研究非商业 | 不能自动延伸至数据 ZIP |

具体视频/重处理数据文件的适用条款仍 Unknown，不自行裁决新旧条款替代关系，未发邮件或代申请。

资源候选是 raw camera 7/8 × 0750/0805 四个文件，例 raw-video/sb-camera7-0750am-0805am.avi；四个 processed 对应文件仅为可选定位辅助。清单见 license_resource_matrix.csv：相机、窗口、类型、完整 epoch 支持、覆盖限制、大小 Unknown、许可 Unknown、Not Approved。文件名继承官方说明，尚未验证当前 ZIP 实际成员。

没有按整包比例编造子集大小。应先澄清逐文件大小、校验、起止与许可，再由研究者批准提供方单文件或子集获取。Task7 最多 36 例/每例 10s 的预算仍为未批准 Proposal，没有样本名单或视频审查。

## 8. Alternative Reference：Precise NGSIM

只检查固定公开 commit 下两个授权 ZIP（非视频）：

| 窗口 | ZIP bytes | CSV 解析器记录数 | Local_Y 范围(ft) |
|---|---:|---:|---:|
| 0750 | 64,434,905 | 1,033,810 | −32.674–2188.794 |
| 0805 | 64,689,172 | 1,045,913 | −5.782–2216.957 |

原 NGSIM 风格 18 字段有 Vehicle_ID、Frame_ID、Global_Time 并覆盖源区。每窗前 500 行比较：ID、帧、epoch、Local_X、Global_X/Y、尺寸/类别、leader/follower、Space/Time_Hdwy 沿用原数据；Local_Y、速度和加速度变化。不能把沿用字段当独立重算真值，或据此宣称全部事件可一一对应。

两个 CSV 末行（1033811、1045914）出现语义错列：Global_Time≈6452613/6451749、Lane_ID=56.75/36.15，列数虽为 18，语义不正确。原 ZIP 保留，只记录疑点，不修补或建立新正式过滤规则。其余诊断 epoch 支持分别结束于 1118847869500 与 1118848631600，比 canonical 短，不意味着覆盖全部正式事件。

**值得作为后续有界辅助定位/质量对照，不是独立真值或正式替代数据。** 需要先澄清许可、schema 异常及逐事件身份/时空对应，研究者再决定是否单独开展；本次没有提取 P2 或更改 167/159。

## 9. Observation / Interpretation / Unknown / Proposal

Observation：Zone 5 获多源几何支持；130 控制点与 canonical 单位一致；分窗映射将源区定位到 7/8 footprint；TFW 为 0.5ft/pixel；两窗交叉预测约 12.47m 差异；Precise 两窗有沿用字段、较短时钟支持与末行语义疑点。

Interpretation：资料足以收敛资源澄清范围，减少获取全八相机或整包的必要性；不足以验证 167/159 事件的物理真实性。

Unknown：III 字样、TFW 分辨率差异和两窗空间差异的历史成因；PTS/epoch/漂移；全 lane 可见性；逐文件许可/大小/SHA；2017 原文方法细节；Precise 事件级对应。没有将其补零或写成 Pass。

**唯一 Researcher Decision：是否进入 camera 7/8 两窗的许可、时钟、逐文件大小澄清与条件性最小资源申请？** 建议进入该澄清步骤；任何实际视频下载仍须研究者批准。若许可或可信时间锚无法取得，保持物理审查 Blocked，不用重处理轨迹自证真值。

## 10. Files, Validation & Git

新证据包：evidence/results/RES-STAGE-0.5-ROUND2-TASK7.1-VIDEO-METADATA-AND-MAPPING-FEASIBILITY-20261030/。

新增专用离线脚本 code/scripts/audit_stage_0_5_round2_task7_1_video_mapping.py 及合成测试。脚本只读本地资料，无网络、子进程或事件提取；运行方式：python code/scripts/audit_stage_0_5_round2_task7_1_video_mapping.py。使用已有 numpy、Pillow、Shapely；canonical 定向交叉检查使用已有 PyArrow，不安装或修改环境。

仅同步 AI_CONTEXT 00/05/07/08、注册表、结果/项目/研究状态索引、新证据精确导出白名单和本地忽略目录。AGENTS、06_DECISIONS 和历史 Task1–7 包不改。实际定向测试、语法、格式、严格文档、SHA、保护检查及初次失败保留在 validation_record.json。

验证按 AGENTS §8 最小充分范围，不运行全量 pytest、compileall 或历史大文件 Hash。工程验证通过只说明其覆盖范围，不消除时间映射、许可或 2017 全文阻断。最终 Git commit 与 push/远端核对由 Git 记录及最终回复提供，避免自引用 SHA。完成后立即停止，不自动获取视频、抽样或人工审查。

## 11. Source References

- 当前目录：https://catalog.data.gov/dataset/next-generation-simulation-ngsim-program-us-101-videos
- 官方轨迹元数据：https://data.transportation.gov/api/views/8ect-6jqj/files/ddb2c29d-2ef4-4b67-94ea-b55169229bd9?download=true&filename=1-+US+101+Metadata+Documentation.pdf
- 官方视频附件：复用 Task7 source_bindings.json 中 URL/SHA。
- EPSG 主定义：https://apps.epsg.org/api/v1/CoordRefSystem/2229/export/?format=wkt
- Coifman 2024 全文：https://par.nsf.gov/servlets/purl/10560106
- Zhang 2024 全文：https://pmc.ncbi.nlm.nih.gov/articles/PMC12412117/
- 公开代码：https://github.com/TeRyZh/Spatial-Temporal-Deep-Embedding-for-Vehicle-Trajectory-Reconstruction-from-High-Angle-Video

以上文档/源码、本次控制点与输入绑定于 source_bindings.json；PDF/HTML/ZIP/图像及身份级数据不提交 Git。
