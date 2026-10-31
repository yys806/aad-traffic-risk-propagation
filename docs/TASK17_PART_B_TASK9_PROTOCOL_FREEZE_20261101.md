# AAD-S0.5-TASK17 Part B Task9 正式协议冻结

正式输入冻结为 962-958-1 与 926-924-1。MiTra 轨迹按 Minimum Sufficient Authenticity 接纳：来源、处理、哈希、字段一致性、连续性、时间戳、车道和正 gap 检查通过；初始间距仍是参考点假设下的估计，不被称为独立物理真值。

正式矩阵为 2 候选 × 5 tau × 2 臂 × 3 seed = 60 组。tau 原值全部保留；不从 MiTra Vehicle_type 映射 tau。Arm A/B 仅 minGap 2.5/1.0 m 不同，Follower 几何采用 B00 passenger length=4.4196 m，Krauss 配置 sigma=0.5、accel=2.6、decel=4.5、apparentDecel=4.5、emergencyDecel=9.0、actionStepLength=0.1、sigmaStep=1.0、maxSpeed=27.78、LC2013、内部步长 0.05 s。

Leader 输入固定、两臂共享、Follower 动态阶段不使用 moveTo；测量网格为 0.1 s，内部网格为 0.05 s，线性重采样且不做尾差外推或端点保持。
