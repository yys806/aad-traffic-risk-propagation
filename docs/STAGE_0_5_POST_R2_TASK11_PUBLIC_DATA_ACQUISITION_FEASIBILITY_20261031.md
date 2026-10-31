# AAD-S0.5-POST-R2-TASK11：公开独立物理参考数据源调研与获取可行性审计

日期：2026-10-31。基线：`4b94253be84e489b1bf78fa54a55e88e0c0f045b`。状态：`COMPLETED_WITH_EXTERNAL_AND_PHYSICAL_BLOCKERS`。

本任务只审计 I24V、MiTra 和 NGSIM US-101 的公开资源、许可、最小获取能力、真实字段结构及对三个科研用途的适用性。没有修改 Formal P2、D1、B 或 Task9 协议，没有启动 SUMO/TraCI、固定前车正式实验、第三窗口或 locked holdout，也没有把外部数据并入 NGSIM 正式样本。

## 1. 当前背景

Task10 保留了 40 条同一车辆的 source→target 有序候选，但合格 B 类物理路径仍为 0；Task9 工程接口已准备而合格真实物理片段为 0。NGSIM 原始视频只有 Task7.2 的目录级元数据，尚未完成载荷、PTS/Global_Time、空间覆盖和人工审查闭合。因此本任务分别判断：

1. 外部数据能否直接核验现有 40 条 NGSIM 候选；
2. 外部数据能否提供独立物理参考；
3. 外部数据能否提供 Task9 所需的连续前车/后车输入。

## 2. 资源和许可核查

### I24 MOTION / I24V

官方工具仓库和 README 记录了公开数据入口、234 个摄像头、约 234 小时/4.2 英里覆盖、270 条人工校正 GPS 车辆通行轨迹，以及每个摄像头的 MKV 与同步时间戳、GPS 和 homography 资源。仓库中的 Data Use Agreement 写明学术和商业使用、匿名车辆与禁止重新识别、发表需引用、可在保留条款的情况下分享衍生产品，并按“as is”提供。[官方 I24V 数据工具与 README](https://github.com/I24-MOTION/i24-video-dataset-utils)

本次有限检查中，`https://i24motion.org/data` 的直接访问失败，没有下载 I24V 视频或 GPS 文件。因此公开文档和许可范围已记录，实际 endpoint、最小文件下载和文件级校验仍为 `Unknown`。README 的 234 摄像头是具体公开版本的事实；不能与系统文档中的当前摄像头规模混用。

### MiTra

OPARA 页面公开了 Readme、每个飞行批次的轨迹 ZIP、Teleporting jumps 文件，以及单独的 tracking logs/videos。页面给出 CC BY 4.0；论文描述为米兰 A50 约 900 m、9 次飞行、6 架无人机、30 fps 原始视频、124,641 条单无人机轨迹和 24,161 条拼接轨迹。[MiTra OPARA 数据记录](https://opara.zih.tu-dresden.de/items/68482417-ddc5-40ac-885a-83124bd459e8) [MiTra 论文](https://www.nature.com/articles/s41597-025-05472-0)

本次实际下载并解析：`Readme_OPARA_MiTra.pdf`、`Data_T1.zip` 和 `Teleporting_jumps.csv`。没有下载约 30.83 GB 的 T1 视频/跟踪日志，也没有下载其他批次。下载 URL、字节数、SHA256、ZIP 成员 CRC32 和字段解析结果已写入机器证据。

### NGSIM US-101

官方数据目录说明轨迹由同步数字视频以 0.1 s 转录，并列出公共轨迹/支持数据入口和 CC BY 3.0 目录许可。[Data.gov NGSIM 目录](https://catalog.data.gov/dataset/next-generation-simulation-ngsim-vehicle-trajectories-and-supporting-data) 现有视频入口和 ZIP 下载链接沿用 Task7.2；本任务不重复 ZIP 中央目录分析，也未重新下载载荷。[US-101 视频目录](https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Program-US-101-Videos/4qzi-thur)

Task7.2 已记录四个目标 raw AVI、约 1.249 GB 压缩大小和约 1.249 GB 解压大小，但视频文件许可声明仍有版本和适用范围差异，PTS/Global_Time、Camera 7/8 有效覆盖和空间对应仍未闭合。公开可下载不等于具体 raw AVI 的许可已经闭合。

## 3. 实际 MiTra T1 结构与质量观察

`Data_T1.zip/T1_DAll.csv` 实际解析得到：

- 1,578,393 行、1,456 个车辆 ID；车辆类型包含 Bus、Car、Heavy Vehicle、Medium Vehicle、Motorcycle；车道值为 0–7、10、11、20、21。
- 字段包括 `Vehicle_ID`、`Time [s]`、UTM 米制 `x/y`、速度、纵向/横向加速度、车辆长宽、`Lane`、`Leader_ID`、`Follower_ID` 及邻车 ID。
- 时间范围 0–439.873633 s；相邻时间差约 0.033367 s，全部通过 1/30 s 的有限误差检查。
- 1,435 个车辆 ID 出现 leader 记录，1,428 个出现 follower 记录；leader/follower 记录各 1,308,347 行。
- 车辆轨迹持续时间中位数 36.336 s、95 分位 53.921 s；1,340 个车辆达到至少 20 s。
- 752 个车辆跨多个车道值出现。核心时间、位置、速度字段没有发现非有限值。
- `Teleporting_jumps.csv` 有 940 行、547 个车辆 ID、26 个纵向标记和 914 个横向标记。README 中的 stitched jump 审计与本地对全局 x/y 的粗略逐步筛查不是同一统计；本报告不把 25,922 个粗筛横向步长异常直接解释为物理错误。

这些结果说明 T1 可用于筛选连续的前后车轨迹候选，但它们仍是 DataFromSky 处理后的轨迹输出。没有配对 tracking log/原始视频审查，就不能把轨迹文件单独包装成独立物理真值。

## 4. 三种用途的适用性

### 4.1 现有 NGSIM 物理路径核验

- **I24V：NO-GO。** 道路和车辆来源不同，不能直接对应 US-101 的 40 条候选。
- **MiTra：NO-GO。** 米兰 A50 数据不能直接核验 US-101 车辆身份、道路连接或事件先后。
- **NGSIM US-101：CONDITIONAL。** 只有原始 US-101 视频可能直接核验现有候选；仍需文件级许可、视频载荷、PTS/Global_Time 和 Camera 7/8 有效覆盖闭合。Task7.2 的阻断条件仍有效。

### 4.2 独立物理参考

- **I24V：CONDITIONAL。** 独立多摄像头视频、GPS/manual 轨迹和 homography 使其成为有价值候选；本次没有实际 payload，也没有完成 GPS—视频复核。
- **MiTra：CONDITIONAL。** 无人机采集和多机拼接提供独立采集基础；本次仅验证轨迹 ZIP，必须再取得小型配对视频/跟踪日志并审查身份、遮挡、空间和时间关系。
- **NGSIM US-101：NO-GO。** 当前轨迹是正式研究所用 NGSIM 转录结果，不能作为独立采集真值；其原始视频只能作为同源视觉核验。

### 4.3 Task9 固定前车输入

- **I24V：CONDITIONAL。** 公开材料支持进一步寻找连续前后车轨迹，但本次未验证稳定的 leader/follower 配对和物理净距准入链。
- **MiTra T1：CONDITIONAL-GO。** 30 Hz 轨迹、车辆尺寸、前后车 ID、速度和加速度足以构造候选输入。当前正式合格片段数仍为 0，因为尚未用配对视频/跟踪日志核验物理净距、身份连续性和遮挡。
- **NGSIM US-101：CONDITIONAL。** 可作为候选输入来源，但视频许可、时间映射、空间映射和初始物理净距仍未满足 Task9 物理准入。

## 5. 最小获取方案

推荐的最小、可复核路径是：

1. **MiTra：** 保留已下载的 T1 轨迹、Readme 和 teleport 审计；由研究者决定后，只获取一个连续 T1 片段所需的 tracking-log/video 子集，避免下载完整 30.83 GB 归档。先用轨迹筛出候选，再用视频核验身份、遮挡、前后车关系和物理净距。通过后才能向 Task9 提供候选输入，不能直接把当前 T1 ZIP 写入正式实验矩阵。
2. **I24V：** 先解决官方数据 endpoint 的可访问性，再以 270 条 GPS/manual 参考中的最小子集和对应摄像头文件验证 GPS—视频—时间映射；不下载全部 234 小时。
3. **NGSIM：** 只有在文件级许可和时间/空间条件闭合后，才获取 Task7.2 已核定的四个 Camera 7/8 raw AVI；不扩大到其他摄像头、第三窗口或 processed 视频。

## 6. 最终科研判断

**Fact：** MiTra T1 小型轨迹包已实际下载、校验并解析；I24V 官方 README/许可已核查但 endpoint 未闭合；NGSIM 视频仅复用 Task7.2 目录事实。

**Observation：** MiTra T1 提供密集、时间规则、带 leader/follower 字段的连续轨迹，适合作为 Task9 候选输入筛选层；它没有在本次任务中获得独立视频验证。

**Interpretation：** MiTra 是当前最值得进入下一步的 Task9 候选来源；I24V 是独立物理参考的高价值候选；NGSIM raw AVI 仍是核验现有 40 条候选的唯一直接方向。三者角色不能互换。

**Unknown：** 没有任何数据源在本任务中形成已通过独立视频、许可、时间和空间闭合的 B 类物理见证；没有形成 Task9 合格片段；没有证据改变 Stage 0.5 Gate。

最终状态：Stage 0.5 继续 `blocked`，scientific equivalence 继续 `false`，Round3/Stage 0.6/Protocol Lock/Stage I 均未启动。Task9 正式运行保持 0；后续是否获取 MiTra 视频/日志、I24V 子集或 NGSIM raw AVI，由研究者决定。

机器证据：`evidence/results/RES-STAGE-0.5-POST-R2-TASK11-PUBLIC-DATA-FEASIBILITY-20261031/`。新增审计脚本：`code/scripts/audit_stage_0_5_task11_public_data.py`。
