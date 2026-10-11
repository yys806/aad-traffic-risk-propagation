# Stage 0.2 正式风险测量实现与独立验证（2026-10-11）

## 结论先行

本轮完成了与已确认科研设计相匹配的隔离式正式接口，并以四个已批准 NGSIM 校准源独立重算 P2 源事件。P2 可靠事件共 **4,545** 个，与 Task 2.5.1 封存参考一致；分源为 Lankershim 2,227、US-101 07:50–08:05 543、08:05–08:20 732、08:20–08:35 1,043。该一致性只证明事件提取实现与封存成员结果一致，不证明事故危险识别准确率。

GitHub `project-integrity` 自动工作流已从生效目录移至 `.github/workflows_archive/project-integrity.yml.disabled`，`.github/workflows` 当前为空。由于本环境没有 `gh` CLI，分支保护、历史运行和组织邮件设置无法独立查询；仓库文件层面后续 push 不会再触发该工作流。完整性脚本保留为本地提交前检查。

## 实现与语义

- `code/src/riskprop/formal_risk_measurement.py`：版本化 P2/P1/P3 配置、实际观测帧 `t_confirm`、连续性检查、`rho=exp(-TTC/tau)`、状态贡献上下界、固定窗口真实时间积分、车辆等权平均和 DID 区间算术。
- `code/configs/stage_0_2_formal_risk_measurement_p2_v1.json`：P2 参数和未批准参数的显式 `null` 占位。
- 旧 `extract_rear_end_events` 的 0.1 s 默认值与 `prelock_metrics.integrated_ttc_exposure` 的历史线性指标未修改，避免历史结果漂移。
- `valid` 且可靠、正闭合 TTC 才生成 rho；`not_applicable` 不被写成零 rho；`invalid`/`missing`/`not_measurable` 或空间归属未知贡献为 `[0,1]`；区外可靠记录贡献为 `[0,0]`。
- 固定窗口积分不插值，窗口缺口保留未知上界；目标区域、固定目标车辆资格、评价窗口和消息去重仍未批准，故本轮不伪造正式区域 burden 或四格数值。

## 独立复核结果

| 源 | P2 事件 | 车辆对 | 最小 TTC (s) | 事件中位首末跨度 (s) | 最大跨度 (s) |
|---|---:|---:|---:|---:|---:|
| Lankershim complete | 2,227 | 1,103 | 0.000289 | 0.5 | 4.6 |
| US-101 07:50–08:05 | 543 | 353 | 0.001630 | 0.5 | 2.8 |
| US-101 08:05–08:20 | 732 | 445 | 0.002586 | 0.7 | 3.2 |
| US-101 08:20–08:35 | 1,043 | 611 | 0.006017 | 0.6 | 3.6 |
| **合计** | **4,545** | — | — | — | — |

独立脚本输出 `p2_event_revalidation.csv`，保留事件身份、实际确认时刻和成员行号集合哈希；`historical_comparison.csv` 明确记录与 4,545 参考值的比较。

## 数学与时间验收

构造测试覆盖 rho 有效/不适用/无效/缺失、未知区域、固定窗口前后缺口、内部不连续区间、目标车辆等权、DID 保守区间、100 ms 与 200 ms 连续性及实际观测确认时刻。四项测试全部通过。100 ms 规则要求相邻时间和帧号均匹配；200 ms 不能被当作正式 100 ms 连续性证据，独立语义审计已标记其为不兼容而非零事件结论。

## 状态与限制

- **Verified**：P2 4,545 事件独立重算与封存参考一致；rho 数学映射和区间算术构造值通过。
- **Agreed Research Design**：P2、tau、状态语义、贡献上下界、固定窗口和车辆等权原则来自研究者确认设计。
- **Pending Implementation / Decision Required**：正式目标区域、目标车辆集合资格、评价窗口、多个源事件选择、消息去重和质量门槛。
- **Unverified**：物理真实性、事故/近失真值、跨 100/200 ms 的科学可迁移性、正式四格区域 burden。

本轮没有修改论文、历史产物、正式旧指标默认值，也没有创建 Protocol Lock、宣布 Gate 或启动 Stage I。

## 复现路径

```text
python code/scripts/run_stage_0_2_formal_risk_measurement_validation.py
python -m pytest code/tests/test_formal_risk_measurement.py -q
```

主要产物：`code/outputs/formal/calibration/stage_0_2_formal_risk_measurement_20261011_r1/`。
