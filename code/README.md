# AAD 交通风险研究代码

当前正式实验实现位于 `src/riskprop/`，命令位于 `scripts/`，测试位于 `tests/`。历史 Pilot 已迁入三处对应的 `legacy/` 子目录；`outputs/pilot_*` 和旧可行性结果只作历史参考。

## 当前正式阶段：E00 → E15-A/E16-A/E17-A → E01

E00 已通过基础设施 Gate，但不构成科学结果。当前正完成现实 calibration 和 E01 协议锁定，E02 尚未启动。

```powershell
cd D:\shen\TJU\AAD\code

# 冻结原始数据、分割和 OSM 快照（run id 不覆盖）
python scripts\freeze_calibration_inputs.py --repo-root .. --output outputs\formal\calibration\calibration_inputs_v2

# NGSIM 真实轨迹测量；具体完整 sources 见脚本参数和封存 config
python scripts\run_e15a_ngsim.py --help

# pNEUMA 候选地图匹配与人工 QA；QA 完成前禁止计算 pNEUMA TTC
python scripts\run_e15a_pneuma_mapmatch.py --help
python scripts\prepare_pneuma_manual_qa.py `
  --mapmatch-dir outputs\formal\calibration\e15a_pneuma_mapmatch_v2 `
  --osm "..\docs\归档\真实数据与NC文献调研\datasets\pNEUMA\osm\athens_d1_bbox_20260907.osm" `
  --output outputs\formal\calibration\e15a_pneuma_manual_qa_v5 `
  --total 300 --seed 20260907 --pilot-per-stratum 12

# 打开 v5/review_map.html，先完成页面默认显示的 48 条平衡试标，再导出标签 CSV

# SPMD 只保留 calibration trips 的 RV_RX 接收连续性
python scripts\profile_e16a_rv_rx.py `
  "..\docs\归档\真实数据与NC文献调研\datasets\SPMD\selected\RV_RX.csv.zip" `
  --output outputs\formal\calibration\e16a_rv_rx_calibration_profile_v1.json

# E17 现实参考和 E01 预锁真值；都不会运行 E02
python scripts\prepare_e17a_real_reference.py --help
python scripts\run_e01_prelock_validation.py `
  --output outputs\formal\calibration\e01_prelock_validation_<唯一版本>

# 汇总准入状态；未通过时只写 readiness，不创建协议锁
python scripts\check_protocol_lock_readiness.py --help
```

关键边界：

- `scientific_claim_eligible=false` 的 calibration/E00 产物不能作为“类超距作用成立”的证据；
- pNEUMA 前车关系未经人工审计时不得计算 TTC；
- `RV_RX` 行数不是消息数，状态断点不是丢包，接收不是采用；
- locked holdout 不用于调规则；
- `protocol_lock.py` 在 E15-A、E17-A、E01 未通过或冻结字段不全时拒绝写出 `protocol_lock_v1.1.yaml`；
- 协议锁签署前不得运行 E02。

## 历史 Pilot 范围

This folder began as the first-pass code skeleton for the summer pilot topic:

> Mixed-autonomy risk event extraction, propagation graph construction, and counterfactual intervention analysis based on DRIFT/Flow rollout emissions.

### Historical Pilot Scope

The current version reads an emission CSV and writes event, episode, graph, and role outputs:

- `risk_events.csv`: frame-level risk detections such as hard braking, low TTC, low THW, and near-miss.
- `risk_episodes.csv`: consecutive detections merged into event-level risk episodes.
- `risk_candidate_edges.csv`: all plausible time-space candidate relations between episodes.
- `risk_edges.csv`: selected direct propagation edges, capped per source and relation type.
- `risk_node_roles.csv`: transparent source/amplifier/absorber proxy scores.
- `risk_chains.csv`: a lightweight chain proxy table.
- `risk_summary.csv`: run-level propagation statistics.

### Expected Input Columns

The pipeline works best with these columns:

- `run_id`
- `time`
- `id` or `vehicle_id`
- `speed`
- `realized_accel` or `acceleration`
- `headway`
- `leader_id`
- `leader_rel_speed`
- `x`
- `lane`, or Flow's `edge_id` plus `lane_number`

Missing optional fields are filled with conservative defaults where possible.

Braking detections are non-overlapping. `hard_braking` uses `event_severity=hard|severe`; realized deceleration below `-15 m/s^2` is labeled `safe_speed_override_candidate` and excluded from ordinary braking. TTC and THW require a valid leader and physically valid headway.

### Run Example

```powershell
cd D:\shen\TJU\AAD\code
python -m pytest tests -q
python scripts\legacy\run_pipeline.py --input examples\sample_emissions.csv --output outputs\sample_run
```

若已执行 `python -m pip install -e .`，也可使用安装后的 `riskprop-legacy` 命令；原 `riskprop` 名称作为历史兼容入口保留。未安装时优先使用上述脚本入口。

## 当前正式 E00 Artifact Smoke 与真实四格

从仓库根目录验证正式产物 schema、provenance、Parquet、manifest、SHA-256 和失败账本：

```powershell
python code\scripts\run_e00_artifact_smoke.py `
  --output-root code\outputs\formal\E00 `
  --run-id e00_artifact_smoke_<唯一编号> `
  --repo-root .
```

该入口只验证基础设施，生成的表为空，并明确写入 `smoke_only=true` 与 `scientific_claim_eligible=false`。它不运行交通仿真、不能支持效应判断，也不能替代 E02 之后的正式四格实验。run ID 必须唯一；重复 ID 会以非零状态退出、保留首次产物，并向输出根目录的 `failure_ledger.jsonl` 追加失败记录。

真实非空 SUMO 四格 E00 运行与独立复算命令：

```powershell
python scripts\run_e00_sumo.py --output-root outputs\formal\E00 --run-id e00_real_sumo_<唯一编号> --seed 2026080701 --repo-root ..
python scripts\analyze_e00_sumo.py outputs\formal\E00\e00_real_sumo_<唯一编号>
python scripts\compare_e00_sumo_runs.py <主环境包> <干净环境包> --output outputs\formal\E00\e00_real_sumo_environment_comparison.json
```

真实运行的五表、拓扑、时钟和车辆生命周期文件均进入 manifest/checksum；E00 输出固定为 `scientific_claim_eligible=false`。证据见 `outputs/formal/E00/` 与 `environment/`。

DRIFT 上游适配边界和当前 Flow/SUMO 依赖核验见 `docs/论文实验推进/阶段0_基础设施与测量/E00/上游DRIFT资产核验.md` 与 `上游适配审计.json`。

## Historical Pilot Commands

以下入口为早期 DRIFT/Pilot 复现命令，已统一归档到 `scripts\legacy\`。当前正式 E00/E01/E15-A/E16-A/E17-A 命令仍位于 `scripts\` 根层。

### Analyse Existing Flow Results

The first real Flow merge smoke was saved before episode analysis was added. Rebuild the direct graph and figures from its frame-level risk events with:

```powershell
python scripts\legacy\analyse_existing_run.py `
  --events outputs\feasibility_week\riskprop_real_merge_server\risk_events.csv `
  --output outputs\pilot_20260714\real_merge_20pct
```

This creates a compact result package containing direct-edge data, role scores, intervention-candidate screening, and analysis figures.

### Audit DRIFT Before Propagation Analysis

The qualification audit checks formal experiment coverage, like-for-like baseline comparisons, 95% confidence intervals, OOD results, raw emission fields, and risk-event semantics. On this machine the original emissions are available through WSL:

```powershell
python scripts\legacy\audit_drift_qualification.py `
  --raw-output-root "\\wsl.localhost\Ubuntu\home\shen\shen\mixed_autonomy_lab\outputs"
```

The report and supporting CSV/JSON files are written to `outputs\drift_qualification_20260716`. This audit is CPU-only. Model retraining is not part of the command.

### Extract The Historical Event Dataset

The formal extractor uses the adopted DRIFT emissions plus matching FS/PI formal runs. It reports event rates per 1000 vehicle-seconds, TTC/braking threshold sensitivity, adjacent-frame context, and a stratified review sample:

```powershell
python scripts\legacy\extract_full_risk_events.py `
  --raw-output-root "\\wsl.localhost\Ubuntu\home\shen\shen\mixed_autonomy_lab\outputs"
```

Outputs are written to `outputs\risk_event_dataset_20260716`. The local one-hop/multi-hop baseline may use non-boundary episodes after excluding `safe_speed_override_candidate`; interaction transitions and episodes adjacent to override candidates must remain separately flagged. IDM, Flow-AIL, and Flow-RL are not included at event level because their raw emissions are not present locally.

### Build The Local Propagation Baseline

After the formal event dataset is available, build the local one-hop/multi-hop baseline, vehicle-wise circular time-shift null, sensitivity tables, and ten figures with:

```powershell
python scripts\legacy\build_local_propagation_baseline.py `
  --input outputs\risk_event_dataset_20260716 `
  --output outputs\local_propagation_baseline_20260718 `
  --permutations 100 `
  --seed 20260718 `
  --workers 8
```

This command is CPU-only. It excludes `safe_speed_override_candidate` and vehicle entry/exit boundary episodes from the baseline graph, but keeps interaction-transition and adjacent-override context as explicit strata.

## 当前正式 E00 Non-empty Contract Fixture

在连接真实 SUMO runner 之前，可用非空四格解析 fixture 验证 state→protocol→action→risk、处理前一致、状态隔离、时间对齐和车辆 ID 生命周期：

```powershell
python code\scripts\run_e00_contract_fixture.py `
  --output-root code\outputs\formal\E00 `
  --fixture-id e00_contract_fixture_<唯一编号> `
  --repo-root .
```

该 fixture 是确定性软件契约测试，四格均有非空 Parquet，但仍写入 `fixture_only=true` 与 `scientific_claim_eligible=false`；其占位风险值不得进入论文、效应计算或图表。

artifact/contract-fixture 的早期证据继续保存在 `environment/`；真实非空交通运行的最终主环境、clean venv 和结构比较证据保存在 `outputs/formal/E00/e00_real_sumo_20260907_*_v3`。

## 历史 Pilot 候选扩展点

1. Add a topology-aware longitudinal coordinate across merge edges.
2. Add unsafe merge/cut-in detection using lane and leader changes.
3. Add full chain traversal metrics: propagation depth, delay, distance, amplification ratio, and decay rate.
4. Test residual nonlocal candidates after conditioning on the local baseline and context strata.
5. Add counterfactual experiment wrappers that call the existing DRIFT rollout code.
