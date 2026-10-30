# Task7.1 文献与方法复用评估

本任务目标是独立物理参考可行性，不改变正式事件。

| 文献 | 原文读取状态 | 作者方法/发现 | AAD 可借鉴 | 不能直接迁移的内容 |
|---|---|---|---|---|
| Coifman & Li2017，DOI10.1016/j.trb.2017.09.018 | FULL_TEXT_ACCESS_BLOCKED；Crossref 元数据已核验，PDF命名响应为HTML | 本次不将二手转述写成原文发现 | I80单相机人工参考作为待核查方法线索 | Camera6、10fps、Frame_ID验证不能套到US101；全文要求仍未闭合 |
| Coifman & Li2024，DOI10.1016/j.trc.2023.104416 | NSF PAR10560106完整26页PDF已读 | I80七相机partial trajectories、gap/overlap/scale检查、独立正射图重投影 | 分离空间尺度与时间误差，逐相机/视野边界验证 | §3.1/p14先验证无时间偏移；不能用空间方法替代US101的PTS同步；低速拟合限制不是AAD事件过滤 |
| Zhang等2024，DOI10.1111/mice.13160 | PMC12412117完整HTML正文已读 | STMap、embedding及后处理；约100坐标对应点和视野重叠标定；§6.2使用I80单相机人工参考 | 两窗PreciseNGSIM可减少后续定位/辅助比较工作 | 沿用原始坐标锚，不是全部US101源区事件的独立真值；公开实现不完整 |

公开仓库固定commit6c8e38ea20458761290327799db1acf676586094。已读README、Inference/post_processing.ipynb、Evaluation README与CompareWithGroundTruth.m、Consistency.m、JerkAnalysis.m、getTrajectoryPairs.m、platoon_consistency.m。后处理仅包括mask/connected-components等；评估代码比较轨迹/运动学，不提供本US101逐相机PTS锚或事件物理真值。未执行、训练或声称完整复现。

只检查两个授权重处理ZIP。每窗前500行保留ID、Frame_ID、Global_Time、Local_X、Global_X/Y、尺寸/类别和headway等字段，Local_Y/速度/加速度改变。此为有限结构/来源检查，不是全量身份等价证明。两个文件末行语义错列且可用epoch支持较短，不修复原文件、不重算P2。

三篇登记至现有Zotero AAD主题集合：7JHH37JY、SZL54NKN、SQYZHHPM。2024分别有完整PDF和HTML本机导入附件；2017仅元数据。已有easyScholar工具补可用指标，双语翻译未启动。临时文件留忽略的literature-work，不建本地论文库。

来源、访问失败和SHA见source_bindings.json。独立视频、逐文件许可和可信PTS锚仍是后续物理核验条件。
