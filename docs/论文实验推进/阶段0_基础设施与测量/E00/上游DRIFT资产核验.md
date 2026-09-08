# E00 上游 DRIFT 资产核验（只读）

核验日期：2026-08-18。DRIFT 工作树：`D:\shen\TJU\DRIFT`。本次只读，没有向 DRIFT 写入、复制回写或运行会改变其工作树的命令。

## 核验结论

此前 E00 审计中“当前可见 Git 历史缺少决定性双走廊代码”的结论需要修正：在用户提供的当前 DRIFT 工作树中，决定性双走廊相关源码和测试确实存在，并且被 Git 跟踪。此前结论只针对当时 AAD/可见历史和旧外部路径，不能继续作为“DRIFT 当前资产缺失”的表述。

DRIFT 当前 `main` HEAD：`58397fb2834e238d5d4d5e72d0307f1d09674b48`。

已核验的 Git 跟踪资产：

| 文件 | 用途 | 只读核验信息 |
|---|---|---|
| `mixed_autonomy_lab/mixlab/dual_corridor_network.py` | 两条无共享 node/edge/route 的物理断开走廊；提供 edge specs 与路径计数 | 130 行；blob `bdafecd5744fb60875b3d920ee614eae4641ee8e` |
| `mixed_autonomy_lab/mixlab/decisive_trial.py` | 来源资格、三步真实减速度验证、消息生成、目标 hazard 与透明动作状态机 | 479 行；blob `bc6ab9957b00d26ce59968baa70a288626459ce3` |
| `mixed_autonomy_lab/scripts/run_decisive_dual_corridor.py` | Flow 实验运行入口；四格 cell、seed、通信延迟/丢包/模式参数与 state/emission/mechanism 输出 | 200 行；blob `eb71b20912b01e33a5b110d7f2e37c30b7c0f4cf` |
| `mixed_autonomy_lab/scripts/analyze_decisive_dual_corridor.py` | receiver TTC burden、四格差中差、paired bootstrap/permutation、处理前 identity 与 mechanism summary | 315 行；blob `cd3f66cb6ac244cc7bdfec82c7a85bc86c569eeb` |
| `mixed_autonomy_lab/tests/test_decisive_dual_corridor.py` | 拓扑、四格 timing、消息链、来源资格与动作采用测试 | 431 行；blob `242afc66075391c6426e3d37144a311150d748cb` |
| `mixed_autonomy_lab/tests/test_decisive_analysis.py` | 风险 burden、DiD、bootstrap、pre-adoption identity 和 mechanism summary 测试 | 94 行；blob `89c5c82f00d36dad526e0c226f7dc970eeb3302f` |

## 与 AAD 冻结 contract 的逐项差距

DRIFT 资产是重要上游参考，但不能直接视为 AAD E00 已通过：

1. Flow runner 目前硬编码 `FLOW_REPO = Path.home() / "shen" / "paper_repos" / "flow"`；当前 Windows AAD 环境没有该目录，且 `import flow` 不可用。
2. DRIFT runner 的原始输出是 JSONL/CSV/机制文件，不是 AAD 冻结的每 run `state.parquet`、`emission.parquet`、`protocol.parquet`、`action.parquet`、`risk.parquet` 五表加 manifest/provenance/audit/log。
3. DRIFT 的四格编号是 `r00/r01/r10/r11`，AAD 冻结接口使用 `s0c0/s0c1/s1c0/s1c1`；迁移时必须建立显式映射，不能靠字符串替换后默认为等价。
4. DRIFT 的 state 行包含 step/time/edge/x/lane_position/speed/headway/leader/follower/realized_accel，但 AAD schema 还要求 scenario、configured/simulation seed、二维位置、net gap、relative speed 等字段；需明确转换来源，缺字段必须阻断而不是填零。
5. DRIFT 的 mechanism log 具备消息/采用原型，但 AAD protocol contract 还要求 generated/sent/delivered/validated/adopted 各时刻、source/target/freshness validity、rejection reason 和 message age；必须逐字段映射并重新验证单调性。
6. DRIFT 分析器的 TTC burden/DiD 不能直接作为 AAD 独立只读 analyzer；它需要从 AAD 原始五表读取，且先通过 pre-treatment、tauP、路径和失败分母审计。

## 可复用与不可复用边界

- 可复用候选：双走廊拓扑定义、`count_edge_paths` 解析逻辑、`DecisiveTrialCoordinator` 的来源资格/消息生命周期设计、四格 timing 与 negative-control 模式、已有专用测试中的机制约束。
- 不可直接复用：Flow 绝对路径、旧输出目录、旧 cell 命名、旧 JSONL/CSV schema、历史摘要数字和未经 AAD manifest/provenance seal 的任何结果。
- AAD 后续若迁移代码，必须在 AAD 中新增适配提交并保留上游 commit/blob provenance；绝不修改 DRIFT 原文件。

## 下一步唯一动作

先在 AAD 新增一个只读上游适配层设计和测试：完成 `r00/r01/r10/r11 → s0c0/s0c1/s1c0/s1c1` 映射、五表字段转换契约和 Flow 缺失时的明确阻断；随后优先尝试直接 SUMO adapter（当前 `sumo 1.26.0`、`traci` 和 `sumolib` 可用），而不是降低理论或偷偷依赖不存在的 Flow 路径。
