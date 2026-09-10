# AAD 代码

正式实现位于 `src/riskprop/`，命令位于 `scripts/`，测试位于 `tests/`。历史实现统一在对应 `legacy/` 目录，不得默认接回正式路径。

## 当前阶段入口

```powershell
# 阶段 0.1：基础设施
python scripts/run_stage_0_1_sumo.py --output-root outputs/formal/stage_0_1 --run-id <unique_id>

# 阶段 0.2：NGSIM风险审计，默认读取仓库根目录 dataset/NGSIM
python scripts/run_stage_0_2_ngsim.py --output outputs/formal/calibration/<unique_id>

# 阶段 0.4—0.6
python scripts/run_stage_0_4_observability.py --help
python scripts/prepare_stage_0_5_real_reference.py --help
python scripts/run_stage_0_5_coverage.py --help
python scripts/run_stage_0_6_prelock_validation.py --help
python scripts/check_protocol_lock_readiness.py --help
```

## 数据与输出

- 原始数据：`../dataset/`。
- 当前完整输出：`outputs/`。
- 旧编号输出：`outputs/history/legacy_experiment_ids/`。
- 便携证据：`../evidence/`。

阶段 0.1只验证工程链；阶段 0.2—0.6只负责测量、校准和协议准入。协议锁通过前不得实现或运行阶段 1.1。

## 验证

```powershell
python -m pytest -q
python -m compileall -q src scripts tests
python scripts/validate_project_docs.py --strict-git
python scripts/export_project_evidence.py --repo-root .. --verify
```
