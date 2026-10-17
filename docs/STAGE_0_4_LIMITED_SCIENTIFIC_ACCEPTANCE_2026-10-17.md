# Stage 0.4 有限科学验收（Limited Scientific Acceptance）与正式收口

> 任务 AAD-0.4.8（2026-10-17，研究者批准）。**零新下载、零作者邮件、零新数据调查**。结果 ID：`RES-STAGE-0.4-LIMITED-SCIENTIFIC-ACCEPTANCE-V1`；包：`code/outputs/formal/calibration/stage_0_4_limited_acceptance_v1/`（不可覆盖，SHA256SUMS）。
> Stage 0.4 **Gate = `pass_limited`；Stage Status = `Completed / Closed (Limited Scope)`**。关闭通信证据研究阶段**不等于真实通信参数已完成校准**。

## 0. 研究者批准的范围决定（归档 `AI_CONTEXT/06_DECISIONS.md`，2026-10-17）

研究者决定：Stage 0.4 不再以获得完整、精确的真实 V2V 时延、PDR 与距离衰减模型为本阶段必须目标；接受现有 SPMD/SEE-V2X 支持的有限证据范围与已确认的限制；停止进一步大规模通信数据搜索/下载/复核；未校准部分作为标记为不确定的实验/敏感性参数；不授权将未经验证参数标为真实校准、不修改因果识别规则、不启动 Stage I。

## 1. 最终证据矩阵

### A1. 已验证（Verified）
| 证据 | 依据（结果 ID / 包） |
|---|---|
| SPMD RV_RX 可用于接收状态连续性 | `RES-STAGE-0.4-COMM-OBS-V3`（`stage_0_4_observability_v3/`，audit 哈希见包 provenance） |
| RSE_BSM 含车辆侧接收 BSM 内容（身份/序号）但无完整车辆接收时间证据 | `RES-STAGE-0.4-RSE-BSM-V1`（`stage_0_4_rse_bsm_v1/`） |
| SEE-V2X 消息身份关联（48 对有向设备对，配对率 1.0） | `RES-STAGE-0.4-SEE-V2X-BSM-V1`（`stage_0_4_see_v2x_bsm_v1/`） |
| SEE-V2X 描述性日志接收比例（室内 0.998–1.0 / 室外 0.22–1.0） | `RES-STAGE-0.4-SEE-V2X-BSM-REAUDIT-V1`（`stage_0_4_see_v2x_bsm_reaudit_v1/`） |
| SEE-V2X 时延数值复算 `(rx−tx)/1000 == latency`（30,571 行一致） | `RES-STAGE-0.4-SEE-V2X-MINIMAL-V1`（`stage_0_4_see_v2x_minimal_v1/`） |

### A2. 明确未验证（Unverified——不因收口升级）
- 无线接收机持续在线与每条消息的实际接收机会。
- 严格物理意义的真实链路 PDR/PER。
- 跨设备时钟同步精度与真实绝对端到端时延。
- 可靠的距离—PDR / 距离—时延关系。
- 信息/控制器采用及采用后的行为响应。
- 受控 PC5 结果对自然交通 V2V 的普遍适用性。

### A3. 候选参考（受控 PC5，仅描述性/候选参数，非校准）
- 消息身份关联方法（`(tx_equipment_id, tx_seq_num)`）。
- 描述性接收比例范围（≠真实 PDR）。
- 记录时延统计（≠已校准真实时延）。
- 已核实的通信应用配置（128 B/10 Hz/SPS）与消息发送特征。

### A4. 否定性结论（有效研究成果，保留）
- SPMD 现有接收数据不足以恢复真实 V2V 端到端时延。
- SEE-V2X GNSS 不足以支持设备间距离函数（t1/t2/t3 轨迹逐点相同为复制品；RSU 静态；室内无 GNSS）。
- GNSS 覆盖不证明无线模块有效在线。
- 缺独立时钟证据时不能冻结绝对通信时延。

## 2. 参数使用边界（为 Stage 0.6 留规则，不定数值）

| 类别 | 内容 | 使用规则 |
|---|---|---|
| **Real-Evidence-Supported** | 消息关联方法、接收比例范围、应用配置（128B/10Hz） | 仅在原数据支持范围内使用（受控 PC5） |
| **Experimental / Sensitivity** | 投递概率、通信时延、覆盖/可达条件、重传/过期/去重 | 未来研究设计候选；不代表当前已采用 |
| **Unverified / Not Observable** | 真实 PDR、绝对时延、距离衰减、采用 | 保留标记，不得与正式校准混合 |

**后续实验原则**：正式实验前明确取值依据与适用范围；区分基准/敏感性条件；不据核心效应结果事后挑参数；不用 locked holdout 调通信参数；改已冻结协议需研究者批准+可追溯版本；仿真效应与现实经验有效性严格区分。

## 3. 与 Stage 0.5/0.6 衔接

- **Stage 0.5**：不受影响；SUMO 校准样本、车型映射、时间加权抽样、覆盖指标仍独立待决。**本任务未启动/修改 Stage 0.5**。
- **Stage 0.6**：科学容差、效应阈值、样本量、通信参数设计与不确定性声明、正式 Protocol Lock **全部保留未完成**。
- **Readiness**：`protocol_lock_readiness` 中 stage_0_4 允许 `pass_limited`；但 `protocol_lock_allowed=false` 与 `stage_1_1_allowed=false` **保持**（stage_0_5/0_6 未通过即阻断，由 `code/tests/test_stage_0_4_limited_acceptance.py` 锁定：5 测试全过，含"pass_limited 在其他 gate 未过时仍拒绝锁"）。**未创建 Protocol Lock、未启动 Stage I/II、未访问 locked holdout**。

## 4. 历史表述修正记录（避免历史错误继续作为当前依据）

- **RV_RX V3**（`RES-STAGE-0.4-COMM-OBS-V3`）：`pending_official_packet_access` 为**历史事实，未改写**；原始 Packet HTTP-403 记录保留。本次 Limited Acceptance 是 Stage 0.4 整体有限目标的验收，**不代表 Packet 已下载或 packet-level 验证完成**。
- **0.4.6**：`independent_pdr` 曾用接收窗口口径（高估 PDR）——被 **0.4.6.2** 修正为完整运行口径（Run 2=0.9737 非 100%）。
- **0.4.6.2**：曾把跨运行时延差异解释为时钟偏移——被 **0.4.7.2** 修正为真实 PHY/MAC 序列化（包大小×优先级）。
- **0.4.7**：曾以 GNSS 覆盖推定接收机在线——被 **0.4.7.2** 修正（GNSS≠无线在线；室外距离因轨迹复制不可识别）。

## 5. 验收判定与证据

- **验收对象**：可观测性边界 + 已验证描述性证据 + 参数不确定性处理原则 → **满足有限范围**。
- **Gate**：`pass_limited`（非全量 `pass`）；**Stage Status**：`Completed / Closed (Limited Scope)`。
- **真实性测试**：5 项 readiness 测试全过；封存包 manifest/SHA-256 核验通过；便携证据 `--verify` OK。
- **结果**：`code/outputs/formal/calibration/stage_0_4_limited_acceptance_v1/`（gate_report/config/provenance/manifest/SHA256SUMS）；便携 `evidence/results/RES-STAGE-0.4-LIMITED-SCIENTIFIC-ACCEPTANCE-V1/`。

## 6. 收束声明

本任务完成后，除非未来出现新的独立通信证据或研究者重新批准范围，**不再继续开展 Stage 0.4 内部通信数据复核**。项目主要工作转向 Stage 0.5（SUMO 校准样本、车型映射、覆盖指标）。
