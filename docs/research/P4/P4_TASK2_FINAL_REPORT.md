# P4 Task2最终报告

Task ID：AAD-P4-TASK2-20261104。日期：2026-11-04。状态：**IMPLEMENTATION_COMPLETE_WITH_LIMITATIONS**。本任务完成工程实现与离线验收，未启动交通实验。

## 1. 决策与项目状态

研究者D01–D08全部Agreed，选择A/A/B/A/A/A/A/A。Δv主、Δa辅；可靠真实共同点；处理前完整区域资格总体；固定N等权平均；边界/断链留界；源专属QC；处理前固定窗；P3不变/P4独立。完整说明见[正式决定](P4_RESEARCHER_DECISIONS_20261104.md)。

最终Y=(1/N)Σ_i[(1/L)∫_W b_i(t)dt]，表示完整区域资格车辆/角色总体的平均Formal贡献，非总和。D03-B操作化既有固定集合，D04-A确定最终聚合算子；Task6/E61历史待决由有日期增量接续，Task7/E61有限校准授权另记。统一定义v0.4／27项不变；数值参数未因此冻结。

## 2. 已实现与验证

新增5个P4模块、3个离线脚本、1个专项测试文件。完成strict pair/clock/identity及Δv/Δa；固定处理前名单/完整性守卫；源QC与Formal贡献；空间区间证据与完整窗口；每成员恰一条窗口记录；固定N上下界平均；11实体版本化JSON与P3外部桥、多对多显式关联、NATIVE_NO_COMMAND、assignment-level导出。

缺整车仍[0,1]、不减N；缺scope返回UNKNOWN_SCOPE无Y；缺窗口每member null占位；同N错名单/重复/额外/错run/同窗域不符拒绝。动作阈值/持续未批准，THRESHOLD_UNSET，正式T_U不输出。不用旧跨缺口持续比较、不延长末点，不插补、不按近邻时间关联。

Formal rho=exp(−TTC/τ)及既有τ/config/P2参数全部保持原字节；P3schema、StageI旧比较器和辅助旧指标亦不改。valid/NaN由P4入口阻断或标invalid Unknown，绝不零暴露。核心调用与单位见[实现规范](P4_MEASUREMENT_IMPLEMENTATION_SPEC_v1.md)、[工程契约](P4_MEASUREMENT_DATA_CONTRACT_v1.md)、[实现审计](P4_TASK2_IMPLEMENTATION_AUDIT.md)。

## 3. 验证结果与数据边界

最终172项离线测试通过（88新P4+84历史回归），0失败/错误/跳过；15项独立Fraction复算通过。首次两轮各1项开发期失败及纠正留档；不是首次全绿。独立部分缺失三车例Y∈[7/36,3/4]，完整点例5/12；UNKNOWN_SCOPE与同N错成员拒绝均核验。详见[验证报告](P4_TASK2_VALIDATION_REPORT.md)及[便携证据](../../../evidence/research/P4_TASK2_20261104/README.md)。

P7 Task2.1现有352行仅p7_target实际轨迹；具备消息→消费→决策→命令→执行→动作来源，可在P4用明确ID读回桥接；不具完整区域资格名单/全部成员轨迹/正式region-window，**不能作为完整区域Y样本**。未造名单、未重跑Enabled/NoMessage/Disabled。

SUMO支持模型内合格输入；NGSIM限质量合格后向跟驰参考；pNEUMA仅运动学，不能自动leader/TTC；SPMD通信观察不替代行为/区域风险。现实完整区域覆盖仍Unknown。

## 4. 验收与剩余限制

|验收|结果|
|---|---|
|科研决策|通过：八项Agreed、最终算子确定；版本结构/正式参数边界保持|
|Action|通过：身份/clock/真实共同点及分段；数值阈值未设，不发布科学T_U|
|名单与Formal|通过：处理前完整性、固定N、缺车/Unknown、显式采样与完整窗口|
|RegionalY|通过：每member唯一、同域同窗、上下界等权及独立复算|
|P3/P4|通过：原P3不改，独立v1及显式外键；native车辆保留|
|工程交付|定向验证/字节/文档/证据/索引与Context同步；Git最终结果以实际HEAD为准|

仍Unknown：真实完整总体覆盖、正式区域几何/观察窗值、Action阈值/持续/误差、现实测量和区域因果效应。现有无leader连续性保守；不做自动几何插值/全数据集导入；宏观通道不混入Formal风险。旧prelock直接调用的NaN限制未扩大修复，P4复用必须经新guard。

Formal A/独立Qualified仍0；F0/总体T_R–T_P Unknown；Protocol Lock BLOCKED、Stage1.1 NOT_AUTHORIZED，原阶段Gate不变。P4可阶段性收口，后续P5/P6使用每assignment固定总体/窗/域/Y界/质量/provenance接口，不在本任务估ITT/四格/功效，不把车辆数当独立样本。

## 5. Context与Git

同步AI_CONTEXT 00–08、PROJECT_CONTEXT、PROJECT_INDEX、RESEARCH_STATUS、RESULTS_INDEX、PROJECT_REGISTRY；旧任务文字/失败证据不改。代码/config/历史证据554文件保护，定义四文件仅追加。最终验证通过后以一个逻辑完整提交推送origin/main，并核对本地/远端HEAD；实际SHA在Git与最终回复，避免报告自引用。
