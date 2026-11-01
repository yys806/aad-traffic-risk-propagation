# AAD-S0.5-TASK18 完成报告

Task18 已完成执行器纠错、完整工程复验、正式重跑、补充重复、确定性复验、初始化专项、时序检查和证据收口。实际执行 174/174 组。

- Task16 回归：60/60 PASS。
- Task9 Primary：60/60 PASS。
- Task9 Supplementary：40/40 PASS。
- 同 seed 复验：6/6 轨迹一致。
- 初始化专项：5 PASS、1 个预期 direct INCOMPLETE。
- Leader 时序：2/2 PASS。
- A/B 实际配对：Primary 30/30，Supplementary 20/20。
- 碰撞、teleport、arrived：0。

Follower 已在正式动态阶段交还 SUMO 原生 Krauss 控制；所有正式运行均使用 80 m 坐标平移、独立 run_id、输入/配置哈希和完整本地 0.05 s/0.1 s 轨迹。Task17 结果与证据保持不变。

证据：`evidence/results/RES-STAGE-0.5-TASK18-EXECUTION-INTEGRITY-20261101/`；输出：`code/outputs/formal/task18_20261101/`。
