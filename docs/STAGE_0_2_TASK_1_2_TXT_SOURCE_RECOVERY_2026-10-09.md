# Stage 0.2 任务 1.2：US-101 TXT 接入与 Lankershim 源文件恢复

核查日期：2026-10-09（Asia/Shanghai）。本轮只处理 NGSIM US-101 与 Lankershim 校准输入；未访问 I-80、Peachtree 或其他 locked holdout 科学内容，未修改 TTC/DRAC、事件规则、阈值或 Lankershim 正式分段逻辑。

## 结论摘要

- **Verified：US-101 已将 Stage 0.2 配置切换到当前 ZIP 内三个原始 TXT 成员。** TXT 无表头，首行作为数据保留；读取器严格校验 18 个字段、数值转换和配置的预期行数。
- **Verified：实际 TXT 行数为 1,180,598、1,403,095、1,515,240。** 这三个数字修正了任务 1.1 中少计一条的历史记录；原因是此前计数脚本跳过了无表头首条数据。
- **Verified：TXT 与旧 CSV 不是同一完整性水平。** 旧 CSV 每窗均为 1,048,575 行；TXT 在 CSV 末尾之后仍有同车后续帧。TXT 接入修复了已确认的读取输入截断问题，但 TXT 仍不等于官方观测“绝对完整”。
- **Unverified：Lankershim 两个官方观测时段的独立源 TXT/CSV 未恢复。** 当前本地 ZIP 只有合并 CSV；官方目录附件记录也只指向该 ZIP 与元数据 PDF。
- **任务 1.2：US-101 输入接入部分完成；Lankershim 源恢复仍阻断。尚不具备直接进入任务 1.3 正式分段实施与重测量的条件。**

## 1. US-101 TXT 接入

`code/scripts/run_stage_0_2_ngsim.py` 的三个 US-101 source 现在使用：

- `vehicle-trajectory-data/0750am-0805am/trajectories-0750am-0805am.txt`
- `vehicle-trajectory-data/0805am-0820am/trajectories-0805am-0820am.txt`
- `vehicle-trajectory-data/0820am-0835am/trajectories-0820am-0835am.txt`

格式标识为 `ngsim_us101_txt_v1`，预期行数为 1,180,598、1,403,095、1,515,240。旧 CSV 成员、旧输出和历史报告均保留，未覆盖原始压缩包。

`code/src/riskprop/ngsim_risk_calibration.py` 新增无表头 TXT 读取路径：固定 18 列映射（包括 `Preceeding`、`v_Length`、`Space_Hdwy`），逐行检查字段数并执行数值转换；支持嵌套 ZIP；读取结果附带 `source_member` 与 `source_format`，审计记录附带 `expected_rows`。CSV 读取路径保持兼容。

| 窗口 | TXT 数据行 | 车辆数 | Global_Time 覆盖（ms） | CSV 行数 | 结论 |
|---|---:|---:|---:|---:|---|
| 07:50–08:05 | 1,180,598 | 2,169 | 1,118,846,979,700–1,118,847,932,500 | 1,048,575 | **Verified** |
| 08:05–08:20 | 1,403,095 | 2,017 | 1,118,847,843,000–1,118,848,842,000 | 1,048,575 | **Verified** |
| 08:20–08:35 | 1,515,240 | 1,915 | 1,118,848,757,500–1,118,849,752,200 | 1,048,575 | **Verified** |

三窗口 TXT 均来自当前 `dataset/NGSIM/US-101-LosAngeles-CA.zip` 的嵌套 `us-101-vehicle-trajectory-data.zip`。TXT 首条数据未被当作表头；因此较任务 1.1 记录各增加 1 行。当前验证证明“本机 TXT 被完整读取并符合配置行数”，不证明官方观测没有缺失。

新增测试覆盖首行保留、字段映射、嵌套 ZIP、来源标识、预期行数不符、字段数量错误和非数值字段；`code/tests/test_ngsim_risk_calibration.py` 当前 9 项通过。未运行正式 Stage 0.2 风险统计，未生成新的科学分布或通过状态。

## 2. Lankershim 官方源文件恢复

- 本地 `dataset/NGSIM/3- Lankershim Blvd Metadata Documentation.pdf`：观测设计为 08:30–08:45 与 08:45–09:00 两个 15 分钟时期，并说明 TXT 为原始文件、CSV 为转换文件。
- 本地官方目录快照 `docs/归档/真实数据与NC文献调研/dataset_sources/8ect-6jqj.json`：记录 USDOT/ITS DataHub 数据集 `8ect-6jqj` 及附件 `Lankershim-Boulevard-LosAngeles-CA.zip`、元数据 PDF。
- 官方发布入口：[NGSIM Vehicle Trajectories and Supporting Data](https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Vehicle-Trajector/8ect-6jqj)；FHWA 报告入口：[FHWA-HRT-07-029](https://www.fhwa.dot.gov/publications/research/operations/07029/index.cfm)。

当前 `dataset/NGSIM/Lankershim-Boulevard-LosAngeles-CA.zip` 内轨迹部分只有 `NGSIM__Lankershim_Vehicle_Trajectories.csv`，没有两个独立时段 TXT/CSV。按本轮限制未下载无关大型替代数据，也未把合并 CSV 静默拆分为正式源文件。

- **Verified：** 官方设计存在两个时段；本地当前包没有两个独立源成员。
- **Verified：** 合并 CSV 有 1,607,319 行、1,506 个 `Vehicle_ID`；此前审计发现 228 个车辆内时间非递增步、936 个编号出现多组 `Total_Frames`。
- **Inference：** 编号复用/人工轨迹重连可能解释一部分多段现象，但没有独立源文件无法确认每个边界。
- **Unverified：** 合并 CSV 中两个时段的确切边界、时段内中断边界及同一编号是否代表不同物理轨迹。

当前按 `vehicle_id` 排序、计算 `leader_changed`/`trajectory_boundary` 和合并风险事件的结果不能作为最终 Lankershim 科学统计。US-101 TXT 接入不会自动修复 Lankershim 问题。

## 3. 后续决策与验收

若取得源文件，候选身份键为“源时段 + 源成员 + Vehicle_ID”；若官方源确实不可取得，需研究者批准可审计的保守诊断分段方案，并决定时间间隔阈值、边界容差及是否纳入正式统计。本轮不自行设定这些规则。

| 项目 | 状态 |
|---|---|
| US-101 TXT 读取、映射、来源标识、精确计数 | **Verified** |
| US-101 三窗口本机读取完整 | **Verified** |
| US-101 官方观测绝对完整 | **Unverified** |
| Lankershim 两个官方源文件已恢复 | **Failed / Unverified** |
| Lankershim 正式分段规则 | **Unverified / Awaiting Researcher Decision** |
| 任务 1.2 可直接关闭并进入任务 1.3 | **Failed：需先解决 Lankershim 源或批准保守分段方案** |

此报告不创建 Protocol Lock、不启动 Stage I；建议任务 1.3 先处理上述研究者决定，再实施分段、测试并重算受影响测量。
