# AAD-S0.5-POST-R2-TASK12：MiTra T1 候选前后车交互筛选与物理准入预审

日期：2026-10-31。基线：`a813c8e1943c93e92e8b447e5e2f8c345ec929bb`。状态：`COMPLETED_WITH_PHYSICAL_ADMISSION_BLOCKERS`。

本任务只做 MiTra T1 的轨迹筛选、异常来源核对、道路方向相对筛查、候选物理间距预审和最小 tracking-log 获取。没有启动 SUMO/TraCI、Task9 正式实验、视频下载、tau 映射、正式插值规则或新的准入阈值。

## 1. 数据和异常审计修正

### Fact

MiTra 官方记录公开了 `Data_T1.zip`、`Tracking_Logs_Videos_T1.zip` 和 `Teleporting_jumps.csv`；README 同时说明 stitched 数据应有 `Teleporting_jumps_Dall.csv`。[OPARA 数据记录](https://opara.zih.tu-dresden.de/items/68482417-ddc5-40ac-885a-83124bd459e8) [MiTra Readme](https://opara.zih.tu-dresden.de/bitstreams/48e0a468-c779-4f37-80aa-68bbeb1a8fd2/download)

对官方 T1 tracking/video ZIP 做了只读 Range 中央目录核查。完整目录大小为 33,108,729,741 bytes，成员只有 6 个 MP4、6 个单无人机 `.tlgx` 和 `T1_DAll.ftlgx`，没有单独的 `Teleporting_jumps_Dall.csv`。因此：

- 已有 `Teleporting_jumps.csv` 只能作为单无人机异常审计；
- 不能把其 940 条记录直接归入 `T1_DAll.csv`；
- README 宣传的 stitched 27 个纵向、253 个横向异常仍是官方摘要，当前没有对应 DAll 记录可逐条匹配；
- 未下载任何 MP4。仅按中心目录定位并 Range 获取了 `T1_DAll.ftlgx` 成员，大小 54,345,650 bytes，SHA256 已封存。

### Observation

对 `T1_DAll.csv` 做了独立的道路方向相对连续性筛查。使用记录中的 `Angle [rad]` 作为局部切向方向，将相邻 UTM 位移投影为局部纵向和横向位移；没有把 UTM x/y 轴直接当作道路纵横轴。1,576,937 个有效相邻步中：

- 局部纵向位移超过 2 m：0；
- 局部横向位移超过 0.5 m：0；
- 最大绝对局部纵向步长：1.731 m；
- 最大绝对局部横向步长：0.335 m。

这解释了 Task11 中全局 y 轴粗筛得到的异常不能直接当作道路横向 teleport。该筛查不是官方 stitched 审计，也不能替代视频复核。

## 2. 前后车交互筛选

### Method

从 `T1_DAll.csv` 中选取 `Leader_ID >= 0` 的 1,308,347 行，并按 `(leader_id, time)` 回查 leader 记录。每一行同时满足：

- follower 的 `Leader_ID` 等于 leader 的 `Vehicle_ID`；
- leader 的 `Follower_ID` 等于 follower 的 `Vehicle_ID`；
- 两侧时间键一致；
- `Lane` 一致。

结果中的 1,308,347 行均满足 reciprocal leader/follower 字段一致性，且同车道字段一致。按车辆对、时间连续性和车道变化切分后得到：

- 3,791 组车辆对；
- 4,335 个连续同车道候选段；
- 2,414 段持续至少 5 s；
- 760 段持续至少 20 s。

### Observation

候选段按持续时间和采样数量排序。前几条如下，间距为“局部投影 + 车辆长度”的 provisional 值，不是已准入的物理净距：

| Rank | Follower | Leader | Lane | 时间范围 (s) | 持续 (s) | 样本数 | provisional gap 中位数 (m) | 状态 |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 857 | 851 | 1 | 248.082–296.630 | 48.549 | 1456 | 24.56 | Candidate / Unknown |
| 2 | 841 | 831 | 1 | 244.144–292.059 | 47.915 | 1437 | 16.60 | Candidate / Unknown |
| 3 | 926 | 924 | 2 | 268.502–315.082 | 46.580 | 1397 | 14.07 | Candidate / Unknown |
| 4 | 404 | 403 | 1 | 94.828–140.908 | 46.079 | 1382 | 17.44 | Candidate / Unknown |
| 5 | 962 | 958 | 1 | 282.516–328.428 | 45.913 | 1377 | 12.69 | Candidate / Unknown |

这些结果支持“存在连续前后车字段关系”的观察，但不等于已验证的真实物理跟驰关系。便携 CSV 保留按持续时间排序的前 500 个车辆对/候选段；全部数量和筛选口径保存在 JSON 证据中。

## 3. 道路方向和物理净间距

### Fact

主线车道 0–3 与 4–7 的局部位移方向呈相反且稳定的两组模式；匝道车道 10、11、20、21 的航向变化更宽。排名靠前的候选位于主线车道 1、2、6，未把匝道候选作为优先物理片段。

### Provisional calculation

在“坐标点是车辆几何中心、`Angle` 给出道路切向、切向投影方向增加”这一未验证假设下，计算：

\[
g_{\mathrm{prov}} = (s_l-s_f)-\frac{L_l+L_f}{2}.
\]

全部 reciprocal 同车道关系行都能得到有限的 provisional 值；中位数为 33.29 m，5/95 分位为 8.85/160.94 m，1,104 行出现负值。

### Unknown

MiTra README 没有闭合 `x/y` 是车辆中心、前端、后端还是其他跟踪参考点，也没有提供本任务所需的道路标定和车辆几何端点链。因此上述值不能称为 `physical_net_gap`，不能作为 Task9 初始状态匹配输入。需要视频、tracking-log 解码和参考点语义核实后才能重新评估。

## 4. Tracking log 和视频对应

### Fact

已获得并 hash 绑定 `T1_DAll.ftlgx`。该文件本身是一个包含 6 个内部 `.tlgx` 成员的压缩容器；公开 README 规定 stitched 视频查看顺序为 D4、D5、D6、D1、D2、D3。

### Limitation

`.ftlgx` 的 DataFromSky 二进制格式在当前环境没有可用解码器；没有下载 MP4，也没有完成车辆 ID 到单架无人机视频的映射。由于 DAll 车辆 ID 不能从 CSV 单独映射到某个 `T1_Dk.mp4`，本次没有伪造视频绑定，也没有保存关键帧或视频判定。

## 5. Task9 输入兼容性

### Observation

候选段具备以下输入字段：连续前车位置、前车速度、后车速度、时间戳、车辆长度、车道和 reciprocal leader/follower 关系。对最高排名候选做了一个 30 Hz → 0.05 s 的线性速度重采样可行性诊断：

- 原始时间差中位数：0.033367 s；
- 目标步长：0.05 s；
- leader speed 回插误差中位数：0.000274 m/s；
- 95 分位：0.002431 m/s；
- 最大值：0.011640 m/s。

这只是数值诊断，没有冻结正式插值方法。

### Compatibility decision

MiTra T1 当前为 **条件候选，不能准入 Task9**：

- 连续 leader/follower 字段：可用；
- 初始 follower/leader 速度：可提取；
- 物理净间距：`Unknown`；
- 视频复核：未完成；
- DAll ID 到具体视频：未闭合；
- MiTra `Vehicle_type` 到 B00 五档异质 tau：`Unknown`，未自行映射；
- Task9 正式准入片段：0；
- Task9 正式运行：0。

## 6. 最终判断

**Fact：** T1_DAll 中存在大量字段层面的连续前后车关系；官方 DAll 异常文件没有出现在公开 T1 成员目录；DAll tracking log 已以最小 Range 成本获取。

**Observation：** 3,791 组车辆对和 2,414 个至少 5 秒的候选段可以作为后续视频核验清单。局部航向投影的连续性筛查没有复现 Task11 全局坐标粗筛的阈值异常。

**Interpretation：** MiTra T1 已从“轨迹数据源候选”推进到“可排序的前后车候选库”，但尚未形成可提交 Task9 的物理输入。DAll tracking log 的存在降低了进一步绑定的获取成本，但不等于已经完成 ID、视频和物理净距核验。

**Unknown：** DAll 异常记录逐条对应、车辆参考点、道路标定 `s`、视频遮挡/ID switch、实际物理净距以及 MiTra 车辆类别与 B00 tau 的对应均未闭合。

最终状态保持：Stage 0.5 `blocked`；scientific equivalence `false`；Task9 formal runs `0`；Round3、Stage 0.6、Protocol Lock、Stage I 未启动。是否进一步获取一个与候选 ID 已绑定的最小 MP4 片段，以及如何处理车辆类型和参考点问题，提交研究者决定。

机器证据：`evidence/results/RES-STAGE-0.5-POST-R2-TASK12-MITRA-T1-CANDIDATE-PHYSICAL-ADMISSION-20261031/`。新增脚本：`code/scripts/audit_stage_0_5_task12_mitra_t1.py`。
