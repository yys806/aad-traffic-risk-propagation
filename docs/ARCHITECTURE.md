# AAD 架构

```text
dataset/
  NGSIM ──> 阶段 0.2 跟驰风险测量 ─┐
  pNEUMA ─> 阶段 0.3 城市运动学 ───┼─> 阶段 0.5 仿真—现实覆盖
  SPMD ───> 阶段 0.4 通信边界 ─────┘
                                      ↓
                         阶段 0.6 数值验证与协议锁
                                      ↓
                         阶段 1.1 核心效应确认
```

阶段 0.1提供四格运行和五表证据链。五表分别记录车辆状态、源事件、消息生命周期、控制动作和风险。阶段 0.2—0.6只负责测量、校准与准入，不产生核心效应结论。

正式代码、入口和测试分别位于 `code/src/riskprop/`、`code/scripts/`、`code/tests/`；本机完整输出位于 `code/outputs/`；小型便携证据位于 `evidence/`。

2026-10-18：独立stage_0_5_calibration_gaps.py只连接两个SHA/角色受控原始校准成员与封存状态，输出车型/时钟/局部归一化/统一分层摘要；独立订阅式工程基准消费小型摘要，不调用正式校准/Gate evaluator，旧Stage0.2/0.3/0.4及P2语义不变。


## 2026-10-19 B1.2 分层准入与机制再验证

B1.2独立观测/执行层stage_0_5_b12_{observation,network,runtime,worker}.py：内部步全边分层数值、身份守恒与局部穿越分账、显式junction路径与分车道队列。主矩阵由observability_integration_audit准入，首个fixture终速不一致使准入false；未执行的主入口不代表动态验证完成。


## 2026-10-19 B1.2-N（独立工程观测）

`RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1`：独立B1.2-N工程任务。固定SUMO1.26源码完整谓词和调用顺序已审计；无停车任务的fresh/immutable生命周期可用doubleMax不变量，同edge常规停车仅非决策步可作充分条件。一般myStopDist不能由公开getter等价恢复。新候选`b12n-near-zero-observability-v1`不以位移/终速选择上下文，1e-6m不变。3个30s微型运行：2879边，2876精确全过（其中1负近零后处理），3 bounded，0近零未决/不可评价/工程错误；最大残差1.3988810110276972e-14m。冻结前203项受控合成通过。

正近零非决策步清零运行边未出现（Not Observed），未满足运行前冻结的共同准入条件；integration_allowed=false，C/D计划冻结被拒绝，均Not Attempted，未追加试验/搜索。新主矩阵禁止且0次。旧B1.2阻断/0-8/D未运行和所有历史证据不变。下一步由研究者决定正近零覆盖设计与未来政策，再另批接入/主矩阵；不自动继续。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2N_NEAR_ZERO_AND_INTEGRATION.md`；证据同ID目录。科研Gate/ready/现实覆盖/锁/StageI状态不变，科学阈值未批准。
