# AAD 架构与证据流

> 最后核对：2026-09-08  
> 本文描述当前可验证结构，不提出新的科研设计。

## 总体关系

```text
只读 DRIFT / AAD 内 SUMO / 真实数据
                │
                ▼
       数据适配与风险测量
                │
     ┌──────────┼──────────┐
     ▼          ▼          ▼
   E15-A      E16-A      E17-A
 风险尺子   通信边界   现实覆盖参考
     └──────────┼──────────┘
                ▼
       E01 解析真值与预锁验证
                │
       所有 Gate 和容差齐全
                ▼
       protocol_lock_v1.1
                │
                ▼
       才允许设计和运行 E02
```

E00 位于这条链的工程底座：它验证真实 SUMO 四格、五表封存、运行隔离和独立复算，但不提供科学主效应证据。

## 分层

### 研究定义层

- 位置：`paper/主论文/main.tex`、`docs/论文实验推进/`、导师批注和冻结协议。
- 职责：记录问题、变量、设计、统计和论文表达。
- 边界：计划或论文文字不能替代实际实现和结果。

### 正式实现层

- 位置：`code/src/riskprop/`。
- 职责：风险测量、地图匹配、实验契约、运行器、审计和协议锁防护。
- 入口：`code/scripts/`。
- 校验：`code/tests/`。

历史 DRIFT 风险事件、传播、communication/nonlocal Pilot 已整体迁入 `code/src/riskprop/legacy/`，对应命令与测试分别位于 `code/scripts/legacy/` 和 `code/tests/legacy/`。顶层包保留早期公开函数的兼容导出，但当前正式模块不依赖 legacy 子包。

### 数据与实验层

- 本地真实数据：NGSIM、pNEUMA、SPMD；具体来源和哈希由 calibration manifest/audit 记录。
- 仿真：AAD 内 SUMO/TraCI；DRIFT 只作只读上游参考。
- 正式实验产物：`code/outputs/formal/`。
- 临时构建与渲染：`code/tmp/`，不作为科学证据入口。

### 证据与审计层

- 文件格式：Parquet、JSON、JSONL、CSV、manifest、SHA-256、日志。
- E00 每个 cell 包含 state、emission、protocol、action、risk 五表以及配置、来源、拓扑、时钟、生命周期和校验文件。
- 独立分析器只读取封存产物和拓扑，不依赖 runner 隐藏状态。

### 知识与论文层

- 导航：`docs/PROJECT_INDEX.md`、`docs/PROJECT_REGISTRY.json`。
- 当前状态：`docs/RESEARCH_STATUS.md`。
- 追踪：`docs/EXPERIMENT_INDEX.md`、`docs/RESULTS_INDEX.md`。
- 正文：`paper/主论文/main.tex`。
- 历史：`记录/`、`docs/归档/` 和各输出版本目录。

## 关键状态转换

### 消息链

消息生成、发送、交付、校验、采用、动作分化和风险变化是不同状态。任何前一状态都不能替代后一状态的证据。

### pNEUMA 风险测量

```text
原始轨迹 → 地图匹配候选 → 候选前车 → 人工盲审
        → Gate 通过后才可计算 TTC → 纳入 E15-A / E17-A
```

当前停止在人工盲审，候选前车不是已验证真值。

### 协议锁

`protocol_lock_readiness_v1.json` 汇总 E15-A、E16-A、E17-A 和 E01 阻断。只有机器准入允许后才能生成不可覆盖的 `protocol_lock_v1.1.yaml`；协议锁之前 E02 禁止启动。

## 当前目录职责

`code/src`、`code/scripts`、`code/tests`、`code/outputs` 和 `code/tmp` 的逻辑分层已成立。本轮不通过大规模移动来重新制造一套代码架构。物理整理必须在当前脏工作树形成可恢复检查点后分批进行，并同步更新项目登记表和路径索引。
