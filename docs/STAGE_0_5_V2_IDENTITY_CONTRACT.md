# V2 身份观测契约 v1（仅软件验证）

实现 `code/scripts/stage_0_5_identity_observation.py`；机器契约在 `RES-STAGE-0.5-V2-ADMISSION-ENGINEERING-V1/identity_contract.json`。声明集合只来自已核对routes，ID唯一、depart非负；未知/重复身份拒绝。每内部步0.05 s记录一个frame，初始frame只能t=0且phase为initial_snapshot；其后严格单调相邻after_simulationStep。校验失败不部分改变状态。

## 来源和时间语义

安装的 `_simulation.py/_vehicle.py/domain.py` AST及SHA与既有绑定核对，未调用可执行文件。历史运行头记录1.26.0；官方对应源：[simulation](https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_26_0/tools/traci/_simulation.py)、[vehicle](https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_26_0/tools/traci/_vehicle.py)、[libsumo vehicle](https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_26_0/src/libsumo/Vehicle.cpp)。本轮运行时版本握手Unknown。

| 字段 | 来源 | 可以断言 | 不可以断言 |
|---|---|---|---|
| loaded/departed/arrived |simulation同名IDList|刚完成内部步的身份事件、观测时钟及区间|观测时钟就是精确事件发生时刻|
| pending |simulation.getPendingVehicles|该快照明确等待插入的身份|缺FCD的声明车辆都是pending|
| active |vehicle.getIDList|原生可见身份，含在路/停车/remote-controlled|与全部loaded或仅on-road集合等价|
| on_road |vehicle.getLaneID非空|该时刻另行在路证据|缺ID/到达事件能决定去向|
| actual_departure_s/depart_delay_s |vehicle.getDeparture/getDepartDelay|可用且一致时的原生出发时间/延迟|用departed观测时钟或FCD首现代填|
| post_step_departure_speed |vehicle.getSpeed|完成步后的速度观测|精确插入瞬间速度；后者仍null|
| teleport start/end |simulation相应IDList|异常转移证据|传送就是正常到达|
| discarded |明确原生日志身份+证据SHA|有身份来源的显式丢弃|总数或缺失推断丢弃身份|
| FCD first/last |流式100ms采样|首末可见记录|精确插入/离网时间|

`None`表示getter/证据不可用，`[]`表示可用且为空，不能互换。初始时尚无完成步，事件列表设None并单独统计初始coverage。异常getter/sentinel不伪造零，记录unavailable原因。未核验通用discard身份API，原生日志解析尚未做普适可靠性认证。

## 状态与核算

| 状态 | 进入证据 | 后续允许/约束 |
|---|---|---|
| Unknown |只有声明或本步去向缺失|不能补成pending、active或discard；保留证据缺口|
| pending_native |本步pending身份快照|未来depart/active须有相容时间；与active/terminal互斥|
| active_native |本步原生可见身份|另存on_road；有departure缺口则核算不完整|
| teleporting_native |明确start且无end|重复start拒绝；end须有start或来源不可用证据|
| arrived_native |原生arrived事件|无departure来源又无可用性降级理由时拒绝；终态不再出现|
| discarded_explicit_evidence |显式ID、允许来源、SHA|终态；与arrived/active/pending互斥|

loaded是正交历史标记，不自动表示进入路网。重复loaded/departed、终态后事件、pending与active/arrived/discard重叠、先到达后出发、反序时钟、原生出发晚于已见FCD均拒绝。缺部分事件API时可降级记录，但不宣称完整核算。没有arrived而从active消失时，去向Unknown并记录warning；不能沿用最后状态假称仍在网。

finish为声明车辆分别记录原生插入状态、最后观测、来源coverage、未决状态与右删失。正常结束或中断时非终态仍右删失；尚未到声明时刻的未来车辆不作为应已插入的遗漏。只有完整来源和相容证据时identity_accounting_complete才可能true；数量相同不能替代逐ID核对。

## 测试与限制

`code/tests/test_stage_0_5_v2_admission.py` 使用虚拟事件覆盖正常/延迟/pending/未知、teleport/discard、晚FCD、丢FCD、重复/未知ID、时钟/事件顺序、来源缺失、中断删失等；没有SUMO import/start。`collect_snapshot`只接受已有connection，不创建连接。原生接口接通、日志完整性、实际安全插入及FCD对齐仍待未来获准验证；状态机通过不能追溯补全旧历史的缺失事件。
