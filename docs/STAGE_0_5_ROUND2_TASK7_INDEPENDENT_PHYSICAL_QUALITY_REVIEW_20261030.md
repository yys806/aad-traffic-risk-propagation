# Stage 0.5 / Round2 Task7：独立物理质量核验与有限事件人工复核

日期：2026-10-30；任务版本 v1.0；基线 `e586f301977898b05fe851da57328f97c691c85d`，main；科研决策权归研究者。执行前直接查询 GitHub main，确认与基线一致、工作区 clean。

## 状态与核心结论

**资料可用性调查已完成；独立物理审查未完成。** 物理审查状态为：

`BLOCKED_NO_VERIFIED_INDEPENDENT_PHYSICAL_REFERENCE`

授权数据目录中未找到可验证的 US-101 原始或处理后视频。官方目录确实提供原始/处理后视频资源，但目录说明不能替代本机可用的原始帧，也没有给出可验证的 movie PTS/frame—Global_Time 对照。未取得原始视频，不执行 Task7-B 抽样、Task7-C 盲审或 Task7-D 视觉判断。未生成空壳案例清单、盲审索引、片段或人工审查表。

原 Formal P2 清单和源区计数 **167/159**、Task6 分布差异与研究边界完整保留。独立物理可信度仍为 **Unknown**；本次阻断既不是“事件为假”，也不是“事件已获视觉证实”。

## Evidence Reuse Inventory

逐项清单见证据包 `evidence_reuse_matrix.csv`，输入与源码/文档绑定见 `source_bindings.json`。

| 问题 | 已有资料 | 能回答什么 | 仍缺少什么 |
|---|---|---|---|
| 正式事件身份/onset | Task4/5 正式摘要、唯一匹配审计 | 两个源区167/159；全来源543/732；onset唯一且守恒 | 独立物理验证，不重建匹配流程 |
| 数学与局部连续性 | Task2.1 的447案例、Task2.2/2.2.1的48代表案例、Task2.3分母与稳健性 | 已实施公式/身份/连续性核验；旧临时事件与正式规则的差别保留 | 连续性和数学自洽不等于物理真实性 |
| 人工判断 | r9既有人工模板、Task2.3报告 | 两个授权窗口24条模板的判断、依据、无法判断原因及备注均空白 | 未从这些材料获得完成的人工真实性裁决 |
| 联合交互及事件上下文 | Task6封存聚合、两个窗口本地identity_contexts | gap/closing结构、换道/leader转换及质量残差 | 原始运动过程的独立视觉支持 |
| 仿真/测量边界 | Task1–Task6报告及Task4/5/6机器包 | Formal P2、SUMO formal-aligned、D1继续分开 | 不建立科学等价或物理传播结论 |
| 原始视频 | 官方目录、附件PDF、本地US-101文档/GIS | 文件目录、相机编号、资源规模、epoch定义 | 原始视频可用性、精确同步、源区覆盖及具体许可 |

只复用摘要、既有审查材料和两个授权窗口的Task6上下文表。没有打开canonical Parquet、原始车辆轨迹ZIP成员、第三真实窗口或holdout；没有重新提取任何P2事件、重算全量轨迹、重跑324次实验或调用SUMO/TraCI。官方说明及旧摘要中提到第三窗口只是文档背景，不构成本任务数据纳入。

Task4/5/6历史机器包逐项校验39个既有载荷（含其manifest）通过；未改写历史包、Task6对照匹配实现或其报告。

### Task6对照复用限制

直接检查既有source、±2s上下文表：0750对照165行，仅131个不同后车；0805对照149行，仅115个不同后车。无放回是行级，不能解释为后车独立。这与任务书指出的边界一致。这里只记录方法限制，不重做Task6，不用这些重复车辆行推断风险比。Task7如果将来获准进入视觉对照，必须按后车trajectory身份去重，最多每窗6辆，且仅作视觉参照。

### 对照方法边界记录

- **Documented Intent**：Task6报告将对照描述为不同后车、无放回。
- **Actual Implementation**：Task6 `contexts()` 在候选行索引上无放回，不保证后车trajectory身份唯一。
- **Evidence**：原source、horizon_s=2表165/149行对应131/115个不同后车；仅复用既有表，未重跑分析。
- **Affected Files**：Task6报告、`code/scripts/analyze_stage_0_5_round2_task6_micro_interaction.py`及其本地identity_contexts。
- **Conflict**：行级去重不能支持车辆级独立性解释；不影响正式事件原始计数。
- **Status: Awaiting Researcher Decision**：本任务按研究者指令仅记录方法边界；不修订Task6或启动重分析。

## 文献与已有人工复核材料

读取当前AI_CONTEXT、Task1–Task6正式报告、Task2.1/2.2/2.2.1/2.3报告及文献索引；通过本地只读API检查Zotero `TJU/AAD/07` 11条和 `09` 1条既有常规条目。复用Task6对FHWA《Trajectory investigation for enhanced calibration of microsimulation models》（10.21949/1521658，MIYY2V2Q）的既有阅读边界；ZJGB2X68（10.3141/2315-02）本次仅确认元数据，不引用未读发现。没有新增论文条目、下载论文或建立本地PDF文献库。

Task2.1的“独立重算”仍来自轨迹转录字段；Task2.2/2.3的图册仍是这些字段的展示。它们对工程正确性有用，但不能充当独立物理参考。24条授权窗口模板为空只说明检查到的材料尚未填写，不推断研究者在其他位置从未复核；未扫描私人笔记或OB目录。

## 官方视频资源及本地可用性 / Task7-A

官方入口：[US-101 Videos（4qzi-thur）](https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Program-US-101-Vi/4qzi-thur)。

元数据API：`https://data.transportation.gov/api/views/4qzi-thur.json`；访问时间2026-10-30 09:32:23 UTC。HTTP 200，原响应9823字节，SHA256 `fc9b9ddd4ff08a1b5a7094ed4abdd8bdc2c1b1d09560022423a7331f268400ea`。便携包保留必要字段及来源哈希，不复制网页、完整PDF或媒体。

官方附件 `US_101_metadata_with_disclaimer.pdf`（14页）访问HTTP 200，382253字节，SHA256 `bbbefb720fc9468042170f86d7ea56df2d534721f99c0acda5fd46dfd1fe8112`。本地既有US-101元数据（13页）SHA256 `3a3009e2fac9701784de9fd2768b726ab4d46f8f0faaed4310b58669419c12c8`。只读提取并渲染核查附件第3–4页文件目录；工作产物位于忽略的任务目录。

| 项目 | 已核实内容 | 未核实内容 |
|---|---|---|
| 官方整包 | `NGSIM US-101 Videos.zip`，12,539,460,866 bytes（12.539 GB；约11.678 GiB），官方blob ID已绑定 | 整包SHA、当前内部成员及逐文件大小；未GET/Range视频整包 |
| 原始视频 | 官方附件pp.3–4列出`/raw-video/sb-cameraN-0750am-0805am.avi`及0805–0820对应文件，N=1…8 | 当前每个文件可单独下载与否、实际帧率、起止帧、遮挡及完整性 |
| 处理后视频 | 同页`/processed-video/`及`-processed.avi`；叠加车辆ID、尺寸、轨迹 | 叠加层不能作为独立身份真值，也不能用于盲审揭示标签 |
| 本地松散媒体 | 仅在`dataset/NGSIM`按文件名/尺寸列举媒体扩展名，找到0个；不完整下载目录为空 | 不宣称所有磁盘或未检查的大包中绝对不存在视频 |
| 本地US-101包 | 顶层七个支持数据ZIP，没有raw/processed-video包；小型GIS/CAD/data-analysis成员目录已核查 | 大型航片及其他非视频包未穷举解压；未打开vehicle-trajectory成员 |

官方原文件名的32条授权窗口目录记录在 `documented_video_resources.csv`（16原始+16处理后）。这是文档目录，不是已取得的视频清单。未下载视频，未对远端整包做部分Range读取。附件提及的`windshield.avi`只用于走廊观感，既未在本地data-analysis成员目录找到，也不能自动作为同时段目标车辆证据。没有安装旧XviD软件或下载编解码器。

### 相机覆盖

官方编号为南端1到北端8。本地GIS确实有八个camera-coverage对象；DBF实际只包含`Id`，不存在可直接引用的纵向覆盖米数。记录类型为polyline，保留原坐标bbox和顶点以便复核，不把折线边界长度冒充沿道路覆盖长度。

没有`.prj`旁文件；元数据正文与字段说明分别出现State Plane Zone 5/III表述。这里只记录影响：尚未建立GIS坐标与canonical `Local_Y → y_m`的可信对应，不能凭北端编号认定7/8号就覆盖完整y[0,150)m，也不能确认每个事件所需相机。细节见 `camera_coverage_audit.json`。不为解决此项而重建全路网/全部轨迹。

### 来源与许可

目录API标记`official`，当前许可字段为CC BY-SA 4.0；该目录自己的官方附件p.2写CC Attribution 2.0，本地2016元数据p.3另列RDE使用约束。**不同版本的声明都保留，具体视频适用条款为Unknown**，不自行作许可裁决，不向GitHub分发媒体。附件p.1还说明数据按AS IS/AS AVAILABLE提供，公开目录不保证准确性、完整性或持续可用性；这种免责声明也不能证明某事件错误。

## 视频—轨迹时间映射

官方附件pp.2–3给出Global_Time为Unix epoch毫秒，须转换到美国太平洋当地时间；本地元数据称八台相机同步。两者都没有给出视频首帧时间、PTS/Frame_ID关系、同步漂移、丢帧或跨相机校核。

复用Task5封存的最小/最大Global_Time，仅进行时区表示转换：

| 来源 | Global_Time观测支持换算为America/Los_Angeles | 边界 |
|---|---|---|
| 0750–0805 | 2005-06-15 07:49:39.700–08:05:32.500（UTC−07） | 不是已验证视频支持 |
| 0805–0820 | 2005-06-15 08:04:03.000–08:20:42.000（UTC−07） | 不是已验证视频支持 |

名义文件窗口与实际轨迹时钟范围并不完全相同，两个来源仍有已知89.5s时钟重叠；不把文件名07:50或08:05当PTS=0，不人为平移，不用最近帧补配，不据时间重叠合并事件。验证成功的视频锚点、event-video映射均为0，offset/frame rate保持Unknown。见 `video_time_alignment_audit.json`。

## 有限样本及盲审：未启动 / Task7-B、C

预条件不满足，**没有抽取案例、没有冻结实际名单、没有观看事件视频**。`conditional_review_plan.json`只是标为Proposal的条件方案，不是已实施抽样或预注册完成。

将来仅在独立原始视频、可信时空映射与许可条件均满足后，才可从已封存Formal P2表按每窗4极端/4中间/4其余代表案例选择，最多24风险+12唯一后车视觉对照。严重程度必须来自已有事件最小TTC，不能拿onset TTC代替，不能为取样重提取全部事件。正式冻结前明确确定性规则、上下文覆盖和不足处理，并记录全部未选原因；任何规则细化必须发生在看视频前。

盲审顺序使用与事件/对照身份分离的确定性哈希种子20261030；Review ID与真实身份映射只在本地。原则上前后各5s，实际覆盖不足如实记录。原始视频不显示Formal P2、TTC、严重程度或原分类；处理后视频只作独立定位辅助，不把叠加真值喂给盲审。审查字段按任务书保留可见性、身份、车道、leader、前后关系、转录疑点、画质、置信度、结论、时点和依据，允许无法判断。

## 视觉结果与物理真实性边界 / Task7-D

本次没有视觉观察结果，不能列出“与视频一致/可疑/无法判断”的案例比例，不能估计总体物理错误率。

必须分开四级证据：视觉确认车辆/相对运动、视觉发现转录疑点、经验证几何标定的物理距离、主观估距。没有几何标定/可靠重建，不产生精确gap/TTC/DRAC真值。原始视频可以独立于轨迹转录进行复核，但它不是新增独立传感器；不能因找到同一数据源的视频就宣布物理量已独立测准。

- **Observation**：官方文件/相机目录存在；本地检查范围没有可验证独立视频；既有两窗人工字段为空；源区正式事件数原样保留。
- **Interpretation**：当前证据只支持身份/公式/连续性及描述性差异，不能关闭极端风险的物理真实性问题。
- **Hypothesis**：部分观测可能有转录/定位疑点，也可能是真实紧密交互；本任务没有证据分配二者比例。
- **Proposal**：先取得覆盖、时钟、许可与具体资源清单，再由研究者决定最小原始视频取得方案。

## 最小资源需求与下一步

`resource_request.json`列出资源边界。先请提供方给出两窗候选相机的覆盖、原始首帧/PTS时钟、逐文件大小/校验及适用许可；随后仅请求经证明覆盖source的相机和时间段。现在无法诚实指定最小相机集合或逐文件字节数。

官方附件已列出两窗各8个原始文件名，处理后文件仅为定位辅助；全部是条件候选，不是下载授权。若未来36案例各10s且单视角，剪辑总时长上限360s；多相机倍率、码率、下载/磁盘字节数仍Unknown。不能把这个时长上限当全文件取得成本，也不建议下载含第三窗口的12.54GB整包。没有发出对外联系或资源申请。

本次无需新增实验、参数搜索或固定前车输入实验。下一步仅限研究者决定是否获取必要独立参考；没有足够参考时，应保持当前估计对象和正式计数，保留物理真实性Unknown，不以删事件或放宽测量解决。

## AGENTS第8节与验证范围

研究者明确授权只替换第8节。新增风险分级、按文档/独立脚本/共享核心选择验证、全量测试准入、历史失败分类、20%/通常30分钟预算及有限纯Git验证；保留main、Conventional Commit、正常push及禁止破坏性Git操作。第10节锁及其他章节字节保持不变；前后SHA、前缀/后缀SHA及diff均入证据。

本任务改变文档/元数据证据、结果索引和exporter白名单，不改科研逻辑或共享生产接口。按新规则仅运行文档/证据范围的定向检查、修改Python文件语法检查、封包独立校验及小型Git对象便携性检查；不运行全量pytest、全仓库compileall、原生仿真测试或历史输入修复。最终实际结果见 `validation_record.json`。

AI_CONTEXT只更新00/05/07/08；06_DECISIONS不改。Gate、Stage0.6、Protocol Lock、Stage I与Round3均保持原状态，Task1–Task6历史及Formal P2/D1定义不改。

复核入口：`evidence/results/RES-STAGE-0.5-ROUND2-TASK7-INDEPENDENT-PHYSICAL-QUALITY-REVIEW-20261030/`。该包完整交付的是可用性调查与明确阻断记录，不能解释为已完成人工物理审查。

### 实际工程验证结果

定向 `test_project_docs.py` 与 `test_project_evidence_scope.py` 共 **14 passed**；修改exporter的单文件py_compile通过。严格文档检查在修正本任务结果ID标题并显式重封包后为 `PROJECT_DOCS_OK`；初始标题遗漏、修改校验记录后的索引大小/SHA过期、exporter拒绝自动覆盖self-managed哈希均保留在validation_record，不伪装为首次通过。只显式刷新Task7条目，73个历史导出条目完整保留。

18个暂存Git元数据对象及exporter在小型隔离目录完成便携入口和SHA校验，未复制轨迹或完整克隆；最终暂存对象一致性再核对。Task4/5/6共39份既有载荷及其SHA清单保持不变，AGENTS第8节外字节及Git表示核验通过。工程Pass只覆盖可用性调查及证据登记，物理审查始终Blocked。未运行全量pytest、全仓库compileall或任何原生仿真。

提交后clean核查发现原忽略规则仅覆盖Task6，故仅新增Task7工作目录的.gitignore条目，保留资料原位、不作清理；该发现纳入验证记录，并修订尚未推送的同一Task7提交。未扩大忽略范围或改动历史规则。
