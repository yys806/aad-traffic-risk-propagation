# 任务书：用既有 B 源运行数据离线估算区域风险 Y（2026-11-16）

## 一、为什么做这件事
P4 的区域风险算子已实现并通过 172 项测试，但一直没在真实跑出来的数据上跑过，因为缺「按处理前名单/区域/窗口规则生成的 run」。
Task8 已有 268 个 B 源 SUMO 运行，每个都保存了全车面板轨迹。用它们可以零成本验证区域风险这条路能不能走通。

## 二、输入
`code/outputs/calibration/p2_task8_20261102_v1/raw/<run_id>/trajectory.npz`
每 run 字段：`t`(1000)、`v/a/x/gap/lane/leader`(1000×65)。`leader` 为前车列索引，-1 表示无前车；`lane` 全为 0（单车道）。
时间 0.05–50.0 s，步长 0.05 s。

## 三、口径（探索性，明确标注临时）
- 区域：全部 65 辆车（单车道，区域即全段）
- 窗口：5–45 s，避开启动瞬态与末端边界
- 名单：窗口内在场车辆，仿真内全知故完整
- 风险：rho = exp(-TTC / tau)，tau = 15.364279197080283
- TTC = gap / (v_self − v_leader)，仅当自车更快且 gap > 0 时成立
- 无前车或不接近 → 记为 not applicable，不计入均值但保留计数
- 区域 Y：窗口内车辆等权平均

## 四、两步走
**第一步（今天做，自己干）**：用简化算子算出量级、区间宽度与跨 run 方差。明确标注 exploratory / pilot-only。
**第二步（之后，派强 agent）**：接入 P4 的 `RegionalRiskAssembler` 全套契约（roster 完整性证明、provenance、区间上下界），产出可入正式分析的 Y。这一步要满足 12 表 247 字段契约，工作量大且容易做错。

## 五、完成判据
- 第一步：至少 268 个 run 全部能算出 Y；给出 Y 的分布、区间宽度、C0 臂（A0 剂量）与有源臂的对比；写清这次**没证明什么**。
- 第二步：至少 1 个 run 通过 P4 的 `COMPLETE_ELIGIBLE_POPULATION` 校验并输出 lower/upper outcome。

## 六、产物
- 脚本：`code/scripts/offline_regional_y_exploratory.py`
- 输出：`code/outputs/analysis/offline_regional_y_20261116/`
- 报告：`docs/OFFLINE_REGIONAL_Y_20261116.md`

## 七、红线
- 不得把探索性结果写成正式区域风险。
- 不得为了让数好看而调窗口、调区域或排除 run。
- 失败与算不出的 run 必须单列，不许静默丢弃。
