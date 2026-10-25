# AAD 架构

## 2026-10-25 V2预算与执行边界

独立追加式ResearchLedger管理准入与状态；无累计cap、逐次核验、失败不改成功。旧监督器保留历史绑定，V2不调用旧三次运行入口；新SUMO执行适配器尚未完成。

依据：`docs/STAGE_0_5_RESEARCH_V2_AUDIT_2026-10-25.md`；`docs/STAGE_0_5_RESEARCH_V2_BUDGET.md`；`docs/plans/2026-10-25-stage-0-5-interaction-research-v2.md`；`evidence/results/RES-STAGE-0.5-INTERACTION-RESEARCH-V2/`。以下内容保留其历史时点。


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


## 2026-10-19 B1.2-P（受限正近零独立验证）

`RES-STAGE-0.5-POSITIVE-NEAR-ZERO-V1`：B1.2-P仅数值观测独立任务。固定SUMO1.26/commit fa7df22d，13具名源码完整谓词/赋值路径核对；fresh/no-stop/无恢复/无控制/无特殊设备/非循环路线doubleMax不变量独立成立。5个冻结原生红灯制动探针各2s、无车辆setter/无重试。实际P1/P2在.10→.15s非决策步重建u_pre约1.999999909e-6/4.800000001e-6，公开终速0，最终分支由源码与生命周期先行确定，位移残差-4.6161e-15/-6.4115e-15m。2条目标Exact Pass；195边中192一般精确全过、3 bounded、0未决/不可评价/阻断。P3/P4/P5实际阈值以上保持正终速；P3名义等号但实际略高，运行精确等号Not Observed。1e-6m未放宽，残差不用于反推上下文。

仅target_branch_verified=true，C_D_allowed=false/main_matrix_allowed=false/future_numerical_policy_approved=false。不需要为该受限分支使用调试构建；一般停车/状态恢复/特殊控制域未验证。B1.2-N正近零Not Observed与integration_allowed=false、旧B1.2阻断/0-8及所有历史原样保留。本轮C/D和主矩阵0次；下一步研究者需决定未来数值准入政策，另批剩余接入；不自动执行。科学Gate及所有ready/现实覆盖/锁/StageI资格不变。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2P_POSITIVE_NEAR_ZERO.md`；证据同ID目录。


## 2026-10-19 C/D接入

C/D有限接入新增独立cd_observation/cd_runtime/cd_worker，沿用N数值域和P源码证明，修复队列路径关联及持续性。不接回历史全源数据，详情见STAGE_0_5_TASK_CD_INTEGRATION_AND_ISSUE_DISCOVERY.md。


## 2026-10-19 LF局部探索

局部跟驰入口与只读批处理新增独立LF模块；全域前车和事件上下文保留，局部仅归域候选，正式P2政策不选。详细调用链、协议源和验证见STAGE_0_5_LOCAL_FOLLOWING_EXPLORATION.md。

## 2026-10-20 LF候选协议整合

独立LF候选协议离线模块和胶囊新增；正式测量链未修改，归属/窗口/margin均待科研审批。报告 `docs/STAGE_0_5_LOCAL_FOLLOWING_PROTOCOL_DESIGN.md`；计划 `docs/plans/2026-10-20-lf-protocol-consolidation.md`；证据 `evidence/results/RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1/`。
