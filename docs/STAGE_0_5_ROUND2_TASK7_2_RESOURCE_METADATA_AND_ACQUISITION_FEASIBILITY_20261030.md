# Task7.2：NGSIM US-101 最小视频资源获取条件与时空映射澄清

- 日期：2026-10-30；Stage 0.5 / Round2；状态：COMPLETED_WITH_BLOCKERS。
- 开始时本地 main 与直接查询的 origin/main 均为 0bf62d49252aae23caf16fee74d5d41ce976e8b8，工作区 clean。
- 本报告是有界公开元数据调查和既有控制点分析，不是视频物理审查，也不是 AAD 显式信息传播的因果证据。
- 证据入口：evidence/results/RES-STAGE-0.5-ROUND2-TASK7.2-RESOURCE-METADATA-AND-ACQUISITION-FEASIBILITY-20261030/。

## 1. 结论与研究者决策

**Verified Fact：四个候选 raw AVI 都存在于当前官方 ZIP 的中央目录，均唯一匹配。** 四成员压缩字节合计 1,248,582,779，解压文件合计 1,248,560,044 bytes（约 1.249 GB；不含传输与本地头开销）。不需要以获取完整 12,539,460,866-byte ZIP 作为唯一技术路线。

**Observation：本次 ZIP Range 请求共 4 次、累计只读取 6,452 bytes，全部为目录或尾部结构，没有读取 local file header、成员视频载荷或视频片段。** 当前官方 ZIP 是扁平目录，与历史文档的逻辑子目录不同。

**Unknown：四个文件的适用许可版本、实际采集时间、PTS 对应与相机实测同步仍未闭合。** 独立物理审查仍为 BLOCKED_NO_VERIFIED_INDEPENDENT_PHYSICAL_REFERENCE。已有控制点支持两窗坐标对应差异主要呈近似固定平移，但不能确定其历史或物理原因，不能据此自动校正正式轨迹。

**Proposal：目前最有信息增益的决策是是否批准向官方联系人发送已准备的英文询问信。** 未发送邮件、未提交申请、未作对外承诺。实际视频获取继续另行待决；本报告不自动启动获取、事件抽样或后续任务。

## 2. Evidence Reuse Inventory 与任务边界

| 问题 | 已有资料 | 本轮复用与信息增量 |
|---|---|---|
| 正式事件与身份 | Task4/5，Task7/7.1 正式报告 | 保留源区 167/159、两窗独立统计；没有重新提取 P2、重建 onset 或读取真实轨迹 |
| 视频候选范围 | Task7.1 candidate_acquisition_manifest、camera_localy_coverage | 保留 Camera 7/8 为地理候选；新增当前 ZIP 的唯一成员、字节数、目录 CRC32 |
| 许可 | Task7/7.1 官方记录、license_resource_matrix | 对照当前两个官方 API 和当前元数据附件，明确资源层级及冲突，不裁决许可效力 |
| 时间 | Task5、Task7/7.1 video_time_alignment_status | 复用轨迹支持；核查公开资料是否提供视频锚，仍缺失 |
| 空间 | Task7.1 spatial_mapping_audit、130 个无身份控制点、EPSG:2229/正射影像说明 | 仅分解既有两窗仿射差异、分车道残差与子集敏感性；无新控制点 |
| 方法与文献 | Task7.1 literature_reuse_assessment | 直接复用 Coifman & Li (2024)、Zhang et al. (2024)、PreciseNGSIM 方法边界；没有重新搜索已阻断的 Coifman & Li (2017) 全文 |

本轮没有修改 Formal P2、D1、source/target、cohort、评价窗口、正式坐标或科研 Gate；没有 SUMO/TraCI、历史实验重跑、新轨迹、第三窗口、holdout、视频下载、ffprobe 或人工案例抽样。Task1–Task7.1 证据不覆盖。AGENTS.md 和 AI_CONTEXT/06_DECISIONS.md 不修改。

## 3. 工作包 A：当前官方文件与获取技术条件

官方入口与本次核验来源：

- 视频目录：https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Program-US-101-Vi/4qzi-thur
- 联邦目录：https://catalog.data.gov/dataset/next-generation-simulation-ngsim-program-us-101-videos
- 视频 API：https://data.transportation.gov/api/views/4qzi-thur.json
- ZIP：https://data.transportation.gov/download/4qzi-thur/application/x-zip-compressed

以下实际成员统一以 NGSIM US-101 Videos/ 为前缀，格式 AVI。旧任务书中的 raw-video/ 是历史文档路径，不是当前 ZIP 成员路径。

| 实际 basename | 压缩 bytes | 解压 bytes | 目录期望 CRC32 |
|---|---:|---:|---|
| sb-camera7-0750am-0805am.avi | 65,254,032 | 65,242,028 | fd607329 |
| sb-camera8-0750am-0805am.avi | 382,246,354 | 382,251,008 | 0c78983c |
| sb-camera7-0805am-0820am.avi | 401,046,211 | 401,035,264 | 1c03f94a |
| sb-camera8-0805am-0820am.avi | 400,036,182 | 400,031,744 | 844d6d58 |
| 合计 | 1,248,582,779 | 1,248,560,044 | 不适用 |

Verified Fact：ZIP 共有 49 个中央目录条目；四成员 compression method=8、未加密。CRC32 是目录中的期望值，本轮没有视频载荷可核验；它不是 SHA256。官方逐文件 SHA256 为 Unknown，HTTP ETag 也不作为 SHA256。

### 3.1 有界 Range 证据

| 结构 | inclusive start–end | body bytes |
|---|---|---:|
| EOCD | 12539460844–12539460865 | 22 |
| ZIP64 locator | 12539460824–12539460843 | 20 |
| ZIP64 EOCD | 12539460768–12539460823 | 56 |
| Central Directory | 12539454414–12539460767 | 6,354 |
| 合计 | 4 个精确 HTTP 206 / Content-Range | 6,452 |

单轮 ZIP Range 上限为 8,388,608 bytes。目录 SHA256 为 66b92eb9fd60bf7206807c7269a0310ff43c7ae64f367ef74c6c79b6ec76c631；它仅绑定目录字节，不代表整包或四个 AVI 的 SHA256。原始响应、目录二进制和中间 HTML/PDF 留在忽略目录 local_research/literature-work/task7_2_20261030/；便携包仅保留元数据、摘要和来源校验。

Observation：首次 ZIP HEAD 超时；另外三个有依据的 HEAD 入口分别超时/400/超时。随后使用当前官方 API 给出的整包大小，精确请求最后 22 bytes 成功，再读取 ZIP64 与中央目录。所有 GET 在读取 body 前要求准确 206、Content-Range 和长度，若 Range 被忽略则关闭并停止。不能把 HEAD 失败等同资源不存在。

最初解析按历史 raw-video/ 路径得到零匹配；检查当前目录后改为精确 basename 匹配并保留全部候选，最终四者均唯一。原始失败记录保留，没有将早先零匹配解释为文件缺失。

Unknown：所检查官方记录没有提供独立 AVI URL；只确认公开整包入口和 Range 能力，不能断言提供方不存在其他单文件获取方式。Camera 7 第一窗文件明显较小，大小本身不能证明时长缩短、缺失或损坏，询问信已列此问题。当前 processed 成员实际带 -processed.avi 后缀，Task7.1 候选命名遗漏该后缀；此处记录差异，未改历史包或扩大 processed 调查。

### 3.2 官方资源更新边界

当前视频 API 字节 SHA256 与 Task7 留存相同（fc9b9ddd4ff08a1b5a7094ed4abdd8bdc2c1b1d09560022423a7331f268400ea），blobId/整包大小相同。没有历史整包 SHA 或可比目录快照，因此 ZIP 字节是否更新为 Unknown。目录 DOS modified literal 是 2026-10-01、时区未知，不是 2005 年采集时间、视频 PTS 或重打包历史的独立证明。

## 4. 工作包 B：许可适用范围

| 资源及官方证据 | 已观察到的声明 | 可确认范围 | 待澄清 |
|---|---|---|---|
| 当前视频 record 4qzi-thur | CC BY-SA 4.0 | 当前目录记录的声明 Verified | 是否具体覆盖四 raw、与附件关系 |
| 视频附件 US_101_metadata_with_disclaimer.pdf，pp2/8 | Creative Commons Attribution License 2.0 | 附件对 included data 的历史声明 Verified | 与当前 BY-SA 4.0 的版本/范围冲突 |
| 当前轨迹/support record 8ect-6jqj | CC BY-SA 3.0 | 另一数据记录的声明 Verified | 不自动适用于 raw 视频 |
| US_101_Metadata_Documentation.pdf，p3 | 历史 RDE 注册、署名、不得向第三方复制传播数据/工具 | 文档内历史约束内容 Verified | 与当前公开目录许可的适用关系 |
| 四 raw 与 processed 的逐文件许可；PDF 自身许可 | 未找到单独、明确的版本映射 | Unknown | 不能把文档内数据声明当成 PDF 本身的独立许可裁决 |

机器矩阵 license_scope_matrix.csv 分别记录资源、官方来源、原文/目录许可名称、适用范围、限制、冲突、是否需要提供方澄清和状态。以上不是法律意见；没有裁定任何一个版本自动取代其他版本。

当前轨迹 API：https://data.transportation.gov/api/views/8ect-6jqj.json 。当前轨迹附件：https://data.transportation.gov/api/views/8ect-6jqj/files/50459f5f-c40b-4eec-b9a0-72dfef577f15?download=true&filename=US_101_Metadata_Documentation.pdf 。视频附件沿用 Task7 已留存版本；没有重新下载视频。

本次页面/轨迹附件部分 HTTP 实际采用 gzip；留存原始响应后本地解码，未重复下载。解码后轨迹 PDF 为 557,844 bytes，SHA256 3a3009e2fac9701784de9fd2768b726ab4d46f8f0faaed4310b58669419c12c8，与既有文档相同。

当前官方 API/catalog 列出 data.itsjpo@dot.gov。此为公开联系人，投递可达性未验证；附件中的 James.Colyar@dot.gov 仅作为历史联系人，不宣称现任。provider_inquiry_draft.md 已备妥，明确询问四 raw 的许可、研究分析、论文展示、衍生图片/裁剪/标注、结果发布及再分发范围；没有发送。

## 5. 工作包 C：四种时间与 PTS 缺口

| 时间量 | 可确认内容 | 不能推断的内容 |
|---|---|---|
| Global_Time | 轨迹 epoch 毫秒，已有当地时区解释 | 不是未经验证的视频绝对时间 |
| Frame_ID | 轨迹内部帧编号 | 不天然等于 raw 视频帧编号 |
| Video PTS | 容器/编码流展示时间戳 | 未获取视频或官方技术表，Unknown |
| File Start Time | 视频实际采集起点及其时区 | 文件名仅名义时间段，Unknown |

复用的轨迹时间支持（2005-06-15，UTC−07）：0750 为 07:49:39.700–08:05:32.500，0805 为 08:04:03–08:20:42。89.5 s 时间重叠仍按 Task5/7.1 边界解释，两个窗口继续独立。这些范围不是四 AVI 的实测文件起止时间。

Verified Fact：官方文档描述八台同步摄像机、轨迹每 0.1 s 记录。前者是提供方的文档陈述，不是逐相机 offset/drift 的实测证据；后者不能证明 raw 视频 10 FPS。Global_Time − 100 × Frame_ID 仍只是轨迹身份/时钟诊断锚，不是 PTS 同步。

Unknown：四文件的实际起止/时区、绝对帧时间戳、PTS/time base、实际 FPS/固定或可变帧率、Frame_ID 对应、丢帧/重复帧、相机固定偏移及漂移均没有可验证公开技术记录。未构造时间偏移、未用最近帧补配，未运行 ffprobe。询问信逐项要求这些资料；获取后至少需分布于文件开始/中段/末端的可信锚，不能仅凭单一名义起点闭合。

## 6. 工作包 D：两窗空间差异的有限分解

仅读取 Task7.1 的 130 个无身份、未以风险筛选的控制点（每窗 65 个、每车道 13 个）。沿用各窗独立仿射；Global 使用 EPSG:2229 的 US survey foot 转米，Local 位置标签沿用原定义。没有新控制点、没有扫描轨迹。

按行向量 convention，G = b + [x,y]A；本轮计算 ΔG = Δb + [x,y]ΔA。结果见 spatial_shift_diagnostic.json：

- Local 原点常量 Δb = (−8.86199, +8.51769) m。
- 在现有控制点支持中心，ΔG = (−9.14789, +8.20779) m；各点差向量长度均值 12.29247 m，范围 12.25843–12.32788 m。
- 去掉支持中心平移后，线性差异向量长度均值 0.20044 m、最大 0.41441 m。
- 两窗相对线性映射奇异值约 1.0056175 / 0.9999673，polar 旋转约 0.11107°；这只是矩阵分解，不是相机真实 yaw 或物理尺度误差测量。

| 位置（Local_X=31 ft） | ΔGlobal_X m | ΔGlobal_Y m |
|---|---:|---:|
| Local_Y=0 m | −8.91625 | +8.49526 |
| 75 m | −8.97411 | +8.42376 |
| 150 m | −9.03197 | +8.35225 |
| 350 m | −9.18625 | +8.16157 |
| 650 m | −9.41768 | +7.87555 |

按 lane1–5 的内部拟合 RMSE：0750 为 2.1051/2.1127/2.0713/2.1075/2.0441 m；0805 为 2.2625/2.1845/2.1182/2.1016/1.9797 m。各车道误差接近，不能据此证明外部地理精度。

控制点选择敏感性：在源区代表点 (31 ft,75 m)，even 33 点/窗、odd 32 点/窗、source-only 15 点/窗、downstream-only 50 点/窗拟合的差向量长度分别为 12.30131/12.31642/12.29340/12.34766 m。downstream-only 在 75 m 的结果是外推；source-only 在全控制点中心评价同样是外推，JSON 已明确。此为既有早期空间控制点的描述性敏感性，不是独立时间留出验证。

**Interpretation：在已有控制支持内，主要差异是近似固定坐标对应平移，线性差异较小但非零。** Task7.1 的约 12.47 m 是交叉预测 RMSE，不能当作已确认的固定物理位移量。单窗内部 RMSE 约 2.1 m 也不等于相机外部定位精度。

**Unknown：Local 原点/定义、历史标定或坐标处理是否造成差异，没有独立文档可裁决。** 子集结果削弱了“完全由某个控制点子集造成”的解释，但不能排除共同系统偏差。Camera 7/8 仍为合理地理候选，不是已证明的完整可见区域或最小相机集，minimum_camera_set=null。精确事件定位仍需对应窗口和相机的独立几何/同步核验。

## 7. 工作包 E：最小获取方案与状态矩阵

| 状态 | 本轮结果 | 适用范围 |
|---|---|---|
| READY_FOR_RESEARCHER_DECISION | true | 调查/询问信决策包就绪，不是获取授权 |
| BLOCKED_LICENSE | true | 四 raw 的许可适用关系仍待提供方答复 |
| BLOCKED_TIME_METADATA | true | 缺视频实际时间及 PTS/轨迹锚 |
| BLOCKED_RESOURCE_AVAILABILITY | false | 四目录成员和准确 Range 已验证；视频内容可用性未测、独立 URL 未找到 |
| BLOCKED_SPATIAL_MAPPING | true | 对精确事件/帧物理审查仍阻断；不阻止将 Camera7/8 提为获取候选 |

Proposal：若提供方澄清许可、可提供同步资料且研究者另行批准，优先索取这四文件的官方子集或独立 URL；否则可研究仅选择这四成员的 ZIP Range 获取。预计压缩成员 1,248,582,779 bytes，文件 1,248,560,044 bytes。若同时保留压缩成员和解压文件，基础占用约 2,497,142,823 bytes（2.50 GB），另留临时与工具余量；这不是实测获取成本。本轮不读取 local header，不实现或执行成员下载。

Raw 是独立视觉参考候选，Processed 只可辅助定位，叠加 ID 不能作独立身份真值。本轮没有发现必须增加 processed 的证据，因此最小提案仍只含四 raw、无第三窗口；不能进一步断言一台相机足够。

获取后最低必要验证：绑定来源并计算本地 SHA256；若从 ZIP 提取则验证目录期望 CRC32；检查实际容器/codec/时长/FPS/PTS；建立各文件多点绝对时间锚并检查漂移/帧缺失；核实相机区域与各窗坐标对应。只有这些条件满足后，才由另行授权的预先抽样进入人工复核。视频目视关系本身不能升级为精确 gap/TTC/DRAC 真值。

## 8. 工程交付、复现与验收范围

新脚本 code/scripts/audit_stage_0_5_round2_task7_2_resources.py 默认只读取旧控制点并输出本地空间诊断；网络探测开关有已执行记录保护，拒绝重置单轮预算。当前工作资料已保存，不再运行 --probe-official；复核目录可直接对已留存的 6,354-byte central_directory.bin 调用 parse_directory。三项合成测试只覆盖 Range fail-closed、当前扁平 raw 名称/CRC 区别和重复候选保留，不读取媒体或真实轨迹。

影响范围仅为本次独立分析脚本/测试、三个 CSV 的精确导出白名单、新证据及项目状态索引。没有共享科研逻辑变化。按 AGENTS §8 和本任务 15 分钟预算进行定向测试、改动 Python 语法检查、严格文档校验及仅本 RID 的封包校验；不运行全量 pytest、全仓 compileall、历史大文件 SHA 或纯 Git 克隆。

validation_record.json 记录实际命令、结果、失败及适用范围；manifest.json 与 SHA256SUMS 管理新包，EVIDENCE_MANIFEST 只新增本 RID。历史证据保护通过 Git 差异与既有登记结构比对完成，不重建历史包。Context Consistency Check 覆盖 AI_CONTEXT 00/05/07/08、结果/项目索引、RESEARCH_STATUS 和注册表；保留原科研状态和 Gate。

本次有限验收结果：新脚本三项合成测试加一项 exporter scope 回归，共 4 passed（0.34 s）；三个改动 Python 文件语法检查通过；严格文档校验 PROJECT_DOCS_OK；本 RID exporter 校验 PORTABLE_EVIDENCE_OK；独立新包检查通过。既有 75 条全局证据登记逐项结构相等，注册表除新增 result 及 stage result-id 外保持相等。原始 HEAD/匹配/解码失败均保留，未伪装为首次通过。未运行全量回归或历史 SHA 扫描。

## 9. 最终停止与未解决事项

元数据、许可、时间、空间和最小方案调查均结束，Task7.2 为有效的 COMPLETED_WITH_BLOCKERS 交付。实际视频独立物理真实性仍为 Unknown。唯一建议当前研究者决定的事项是是否批准发送现成官方询问信；如不发送，继续保留现有阻断。不得为获得 READY 而降低许可、同步或物理证据标准。

没有建立 Task7.3，没有下载视频、抽样、仿真或推进 Stage 0.6 / Protocol Lock / Stage I / Round3。167/159 与所有历史测量契约不变。既有历史文档的编码显示问题不在本任务修复范围内，不作全仓替换。
