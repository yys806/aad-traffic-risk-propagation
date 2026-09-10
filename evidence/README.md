# AAD 可移植证据层

本目录保存能够随 Git 克隆恢复的小型、只读科研证据快照。它解决的是“索引指向本机 `code/outputs/`，换机器后无法核验”的问题，不替代完整运行包。

## 保存内容

- audit 与独立分析 JSON；
- 冻结配置、manifest、provenance、SHA256SUMS；
- 当前 Gate 哨兵；
- `EVIDENCE_MANIFEST.json` 中记录的源路径、快照路径、字节数和 SHA-256。

快照保持源文件原始字节，不把结果重新解释成新的科学结论。每个结果目录名与 `docs/RESULTS_INDEX.md`、`docs/PROJECT_REGISTRY.json` 中的结果 ID 一致。

当前结果位于 `results/`，使用阶段化结果 ID；退出当前研究范围的旧编号证据位于 `history/legacy_experiment_ids/`，只用于追溯。

## 明确排除

大型 Parquet、原始 CSV、HTML、图片、运行日志、密封抽样键和完整本地输出不进入 Git。它们继续位于 `code/outputs/` 或原始数据存储中，并由快照中的 manifest、provenance、checksum 和登记表定位。

## 生成与验证

```powershell
cd D:\shen\TJU\AAD\code
python scripts\export_project_evidence.py
python scripts\export_project_evidence.py --verify
```

重新导出前必须确认源运行包身份没有变化；源文件发生漂移时，验证会失败，应登记新结果版本，不能静默覆盖旧结论。
