# P4 D01–D08 正式决定（2026-11-04）

Task：AAD-P4-TASK2-20261104。来源：研究者本任务书§2–3。**八项均Agreed**，接续Task1同事项的Proposal/Awaiting；[Task1记录](P4_RESEARCHER_DECISIONS.md)保留历史。方向/算子批准不等于所有数值冻结、Protocol Lock或Stage1.1授权。

| 决策 | 原始选择 | 正式解释及约束 |
|---|---|---|
| D01 | A | 有符号Δv主测量、Δa辅助，无综合分数；阈值/持续/误差Unknown，不输出正式T_U |
| D02 | A | 可信pair角色/身份/clock下真实共同观测，不默认插值、不按相近时间关联 |
| D03 | B | 分配前定义完整区域资格车辆/需求角色总体，来源/冻结/完整性/跨run映射可追溯；不是处理后可见名单 |
| D04 | A | 每车同一区域、同一全窗均值，固定N等权分别聚合上下界，不是风险总和 |
| D05 | A | 空间边界/断链/首尾缺失保留界，不估计穿越交点，不延长末点 |
| D06 | A | 源专属QC，不插补；not_applicable需要观测证明，未见leader不自动零 |
| D07 | A | 分配前固定风险窗口W；数值未定，不依观察结果择窗 |
| D08 | A | P3 v1不改；P4独立aad.p4.measurement.v1，显式ID多对多关联，保留NATIVE_NO_COMMAND |

Y_e(a)=(1/N_e)Σ_{i∈C_e^elig}(1/L_e)∫_{W_e}b_ie(t;a)dt，N_e=|C_e^elig|，L_e=|W_e|。

这是**完整区域资格总体的平均Formal贡献**。缺整车仍保留[0,1]、N不变；可靠确认在区域外才为零，轨迹消失不证明区域外。资格总体本身不明则UNKNOWN_SCOPE、不发布完整区域Y；总体确定但数据缺失可发布区间。

D03-B是既有固定集合定义的完整资格总体操作化；D04-A批准最终Y等权标准化算子。统一定义仍AAD-SCI-DEF-20261102-P2T6-v0.4 /27项，不新增Definition ID。**Task6/E61**关于最终聚合待决由本决定接续；**Task7/E61**仍是历史有限校准授权，不混用。

仍Unknown：实际完整总体覆盖、正式region/窗口数值、Action阈值/持续/误差、真实交通可观测性与风险因果效应。Formal rho公式/config/τ/P2参数、P1模型/estimand、P3schema均不改。无新SUMO/seed/Pilot/V/holdout。所有新合成输入只SYNTHETIC_VALIDATION_ONLY。
