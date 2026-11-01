# AAD-S0.5-TASK18 失败与边界分析

正式 Primary 状态：{'PASS': 60}；Supplementary 状态：{'PASS': 40}；Task16 回归状态：{'PASS': 60}。正式矩阵没有 FAIL、INCOMPLETE 或 INVALID。

初始化专项为 {'PASS': 5, 'INCOMPLETE': 1}：safe_then_move 四组通过，962 direct 低 tau 通过，926 direct 最高 tau 以 INCOMPLETE 失败闭合，原因是 SUMO 插入安全约束导致 Follower 未出现；该结果符合专项预期，没有被改写为 PASS。

碰撞审计记录 0 组碰撞、0 teleport、0 arrived。Task17 最高 tau 碰撞在释放 Follower 控制并将坐标平移到 80 m 后未复现。该事实只说明本次执行链中的碰撞不再出现，不把它解释为科研效应。
