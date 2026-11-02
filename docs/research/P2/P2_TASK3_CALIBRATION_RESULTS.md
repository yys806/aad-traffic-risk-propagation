# P2 Task3 Calibration Results

日期：2026-11-02。状态：`CALIBRATION_ONLY`；不是正式确认性实验或Protocol Lock。

## 1. 版本和证据分层

| 层级 | 输出 | 实际完成 | 可支持 / 不可支持 |
|---|---|---|---|
| V1，已撤回 | `code/outputs/calibration/p2_task3_20261102/` | 旧输出和脚本快照保留，新增`SUPERSEDED_V1.json` | 仅保留失败历史；不支持参数推荐 |
| V2，测量验证 | `code/outputs/calibration/p2_task3_20261102_v2/` | 768合成面板，42候选，32,256评估，1,344汇总组 | 测量逻辑与生成器内敏感性；不是交通arrival真值 |
| B，受控SUMO测量域 | `code/outputs/calibration/p2_task3_sumo_b_20261102/` | 60运行全部工程PASS，2,520候选评估，420汇总组 | 独立B域运动学与检测范围；不升级Formal A，不估计正式F0 |

同一面板/运行上的候选评估不是独立重复。V1原持续时间多算一帧、注入后任意报警误算检出、基线距注入过远、无独立验证的问题均已撤回；原日志为重建记录，不能称captured stdout。旧SHA及原产物保留。V2修正后单独运行，不能以V2覆盖原失败。

## 2. V2：设计与结果

V2分类`synthetic_measurement_verification`。16场景，每场景校准/验证各24独立面板；校准seed族202611020起，验证202711020起。20固定成员，0–60s，30s已知注入；基线为相邻源前[30-W,30)。监测从30s开始，未估计独立源前监测FPR。

候选覆盖：mean / median / exceedance proportion；W=2/5/10s，mean/median阈值0.25/0.5/1m/s，比例单车阈值0.5m/s及比例0.25/0.5/0.75；h=0.5/1/2s，q=1.1/3.1/5.1×dt，coverage=0.8/1。42候选为有界对照，不是上述参数的全笛卡尔积。dt=0.05/0.1/0.2s、白噪声、共同AR1、MCAR、块缺口、选择性缺失和自然趋势场景见配置。

持续跨度使用最后时刻减首次时刻，不加dt；超q断段。允许缺口的段标记gap-bridged，不称真实连续。onset区间、confirmation和observation分开。注入事件的有效检出要求在恢复前确认；源前/恢复后报警不算true detection。前触发分类有单测，不代表独立源前FPR已测。

以下均为validation参考配置：mean/median阈值0.5m/s，h=1s，W=5s，q=1.1dt，coverage=0.8；比例候选使用单车0.5m/s和比例0.5。每格n=24。

| 场景 | mean / median / proportion | 科学解释 |
|---|---|---|
| 稳态null | 0/24 / 0/24 / 0/24 | Wilson 95%上界约0.138；小样本未证明低FPR |
| 自然下降趋势null | 24/24 / 24/24 / 24/24 | 真实速度下降会被检测，但不能归属源传播 |
| 全体下降1m/s，3s | 24/24 / 24/24 / 24/24 | 确认延迟约1s，只限生成器 |
| 全体下降1m/s，0.8s | 0/24 / 0/24 / 0/24 | h=1s排除短段，是定义选择而非算法失灵 |
| 全体下降0.5m/s，3s | 0/24 / 0/24 / 1/24 | 阈值边界和噪声/持续共同影响 |
| 半数下降1m/s | 0/24 / 0/24 / 22/24 | 不同算子回答不同问题，不说明比例普遍更好 |
| MCAR 20% | 0/24检出且全部质量Unknown | q与coverage共同限制有效持续段 |
| 0.4s块缺口 | 三者24/24 | 确认延迟约1.8s；重启后的延迟增加 |
| 共同AR1噪声下强shift | 三者22/24 | 相关误差不能按独立车辆噪声平均消除 |

MCAR场景放宽q到3.1dt时mean约22/24，到5.1dt为24/24；这是以更弱连续性证据换取可检测性，不能据此推荐大q。采样0.05/0.2s及noise=0.5m/s的已测强shift仍可检出，不外推为普遍鲁棒。`calibration_summary.csv`和本地`sensitivity_curves.png`记录完整曲线；图已目视核对，便携证据不含图。

合成null窗口报警率、valid detection、条件确认延迟、Unknown率分别报告。标准化阈值从未测试，V1的k=3推荐已撤回；这里没有交通经验最优参数。

## 3. B域：运行方案、环境和完整性

运行前方案写入`P2_TASK3_CALIBRATION_PROTOCOL.md` `6。独立5000m单车道，16车s0–s15，source=s0，初速15m/s、初始间距30m。Krauss参数、全部命令和seed保存于配置/来源记录，没有改正式配置。

固定cohort=s5–s10，N=6；固定region=[1300,2240]m，监测[30,39]s。30s时source在区外；仅source收到slowDown/setSpeed，所有follower动态段由SUMO native演化。null不发速度setter。每步记录身份、leader、lane、位置、速度、加速度、net gap及speedWithoutTraCI。leader gap按官方定义加minGap后，与位置差减车长逐步校核。

矩阵为null及幅度2.5/5m/s×持续3/6s，共5条件；每条件校准6seed（202611020–025），验证6seed（202711020–025），共60run。相同seed跨条件不解释为逐事件反事实配对。验证结果没有用于再次调参或扩展矩阵。

环境：Windows、Python3.13.5、NumPy2.3.2、SUMO1.26.0及matching官方TraCI；运行前D盘空闲198.41GiB，预计输出<100MB。运行Git SHA、dirty状态、网络生成命令、二进制与源码快照、配置、seed、逐run日志、provenance和SHA256SUMS均保留。`SUMO_HOME`未设导致自动XML schema验证关闭；后处理只确认XML wellformedness，不称XSD验证通过。

60/60运行无collision、teleport、缺ID或cohort出区失败。工程PASS不代表检测阳性或科学假设成立。

## 4. B域：实际检测结果

**2,520项候选评估全部未报警。** 固定cohort在全部60run的峰值mean下降仅0.01623808–0.02806257m/s，低于已测最小均值阈值0.25m/s。没有足够阳性arrival标签，不能估计真实检出率、检出延迟或选择最优阈值。

每validation条件n=6，0/6报警的Wilson 95%上界约0.3903；这不是低误报保证。对command条件仅称command-conditioned alarm fraction，命令已执行不等于目标arrival真值。未出现报警不能编码成Formal A物理未到达，更不能成为F0估计。

源实际减速可见：validation、幅度5、持续6、seed202711020中，source在30.0s速度14.9932536，30.1s为14.5432536m/s，加速度-4.5m/s²；首个观测下降区间(30.0,30.1]，命令执行30.0s分别记录。`speedWithoutTraCI`在被控制source上也可等于实际速度，不是无控制反事实；follower无setter事实来自代码和control_log。

## 5. 关键适用边界：区域进入不等于cohort阈值状态

上述同一validation运行，source在30s位于2247.388m、区外。以单车下降≥0.25m/s、观测跨度≥0.5s生成的**响应候选**如下（不是预先冻结的Qualified Witness）：

| 车 | onset候选区间s | confirmation s | 确认位置m | 位于固定region |
|---|---|---|---|---|
| s0 | (30.0,30.1] | 30.6 | 2255.439 | 否 |
| s1 | (30.6,30.7] | 31.2 | 2234.483 | 是 |
| s2 | (31.6,31.7] | 32.2 | 2219.806 | 是 |
| s3 | (33.7,33.8] | 34.3 | 2221.339 | 是 |
| s4 | (36.0,36.1] | 36.6 | 2225.781 | 是 |

最多4条顺序候选边，未覆盖完整source→cohort链，全部`qualified_witness=false`。数据提供模型内实际中间车辆响应，未证明现实因果，也未建立正式Qualified路径。

**Inference：固定cohort速度阈值状态未报警，不能排除普通物理影响已进入几何区域。** 非cohort车辆、阈值以下速度、gap或density变化可能先发生。未来即使TR早于本phi，也只支持早于“指定cohort达到指定持续速度下降状态”；不能自动宣称所有普通物理竞争机制尚未到达。risk和arrival的车辆/空间支持域必须一致；更强排除主张需要额外证据，提交研究者决定。

## 6. 参数结论及停止理由

可推荐测量结构、持续计时和证据契约，**不能推荐已验证的θ/h/q/coverage/clock数值**。V2有已知代理标签，B有真实模型运动学但缺目标阳性，A合格源0；三者证据域不混用。W、θ、h、q、coverage和恢复规则须联合校准，不能独立挑最早报警组合。

按预定停止规则，在B无目标阳性、Formal A无事件时停止，不追加种子、不降低阈值、不重设cohort/region追求检测。独立验证seed保留；F0、TR、总体时间优先性仍Unknown。本轮充分完成可执行测量校准，但真实交通适用范围和参数数值受证据限制。

便携摘要：`evidence/research/P2_TASK3_20261102/`。原始轨迹、日志、图、全文工作产物仅在本地，不进入便携包。
