# 任务 2.2.1 连续风险判定修复与人工复核包验收

**Observation（Verified）**：r6 的连续段解析没有使用 `contiguous` 边界，且极端连续判断的两个 `any()` 不保证相邻风险帧。本轮修复 `runs()`，并要求相邻帧同时满足 `Global_Time +100 ms`、`Frame_ID +1`、同一后车—前车关系和同一局部序列。

**Observation（Verified）**：447 案例修复后为多帧连续 297、单帧尖峰 3、间歇 1、边界/缺帧 25、窗口内无极端状态 121。与 r6 相比 1 个案例由多帧连续变为间歇；自动 C/D 仍为 C=349、D=98。

**Observation（Verified）**：新包明确保存风险帧数、连续段数、最长帧数、时间跨度、观测覆盖时长及中心帧所属风险段；TTC<0.5、TTC<2、DRAC>10 分别统计，未将其他前车记录并入当前车辆对。

**Observation（Verified）**：代表性案例仍为四源各 12 个，共 48 个，并保留 Lankershim 原始行 31,245。显式配额保证每源至少覆盖普通、阈值、TTC、DRAC、非正间距和近零正间距；`coverage_matrix.csv` 给出单帧、间歇和边界类别的实际缺口，缺少类别不人为制造。

**Interpretation（Unverified）**：修复后仅一个案例分类变化，说明本次问题影响集中于风险段边界解析；这不是对交通物理真实性的确认。

## 产物

`code/outputs/formal/calibration/stage_0_2_task_2_2_1_20261010_r5/`

包括 `case_diagnostics.csv`、`r6_vs_221_case_comparison.csv`、`continuity_summary.csv`、`coverage_matrix.csv`、`representative_cases.csv`、修正图册 `representative_casebook.pdf`、空白模板、配置、provenance、manifest 和 SHA-256。

图册风险曲线只使用目标后车与指定前车；检测到非 100 ms/Frame+1 边界时插入缺口。前车速度单独绘制，未使用前车对第三车的风险字段。

## 验证边界

专项构造测试覆盖交替风险、相邻危险、缺帧、不同前车、不同诊断时钟、多段最长段、单帧、全部正常、TTC/DRAC 分别触发及车辆对污染。几何真值和真实交通危险仍 `Unverified`；未修改任务 1、1.5、2、2.1、2.2 历史产物。
