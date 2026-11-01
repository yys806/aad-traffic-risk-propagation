# AAD-S0.5-TASK18 执行审计

Task18 已使用独立输出目录执行完整计划，共 174 组 SUMO 运行：Task16 回归 60、Primary 60、Supplementary 40、同 seed 复验 6、初始化专项 6、Leader 时序 2。坐标平移固定为 80 m。

Follower 控制审计：114 个正式/专项动态记录全部执行 `setSpeed(follower, -1)` 释放，动态阶段 Follower `setSpeed` 次数为 0；SUMO `getSpeedWithoutTraCI()` 可用记录 114/114，实际速度与原生速度诊断最大差异 0。Task16 回归也记录为全量释放。

所有 Primary/Supplementary/Task16 记录完成预期轨迹长度；所有正式组初始 gap、初始速度和 Leader 输入通过实际轨迹核验。
