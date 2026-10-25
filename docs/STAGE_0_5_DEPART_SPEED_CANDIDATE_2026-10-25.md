# 初态departSpeed最小候选影响审查（离线）

状态：**离线准备已形成；输入政策与新精确提案仍Proposed / Awaiting Researcher Decision**。没有启动SUMO，没有新增轨迹；累计1/3，剩2。原失败、原计划、历史输入及原账本完整保留。POLICY-A-VALIDATION-SCOPE-01仍Not Accepted，Gate和科研授权边界不变，WP2–WP5未整体完成。

决策入口：`docs/plans/2026-10-25-stage-0-5-depart-speed-candidate-v1.md`。便携结果：`evidence/results/RES-STAGE-0.5-DEPART-SPEED-CANDIDATE-V1/`。

## Observation：官方定义与全体输入核对

SUMO当前官方[车辆定义](https://sumo.dlr.de/docs/Definition_of_Vehicles,_Vehicle_Types,_and_Routes.html)与[插入说明](https://sumo.dlr.de/docs/Simulation/VehicleInsertion.html)，以及v1_26_0版本文件的含义一致：max使用min(车道限速×speedFactor, desiredMaxSpeed×speedFactor, 车型maxSpeed)作为可行时的出发速度，可为前车/路口降低；安全检查仍适用，插入仍可能延迟。数值速度在不安全时延迟。逐edge插入调度使排队影响可能传播到后车。

本任务5个passenger类型均显式maxSpeed27.78、speedFactor1、speedDev0，车型其余属性不变。desiredMaxSpeed为未显式字段，官方passenger默认2778m/s；没有动态查询默认值。当前与版本文档完整文件只留本机，URL、获取文件mtime（不冒充发布日）、SHA、短引用见official_semantics.json；首次捕获之前的完整性基准Unknown。已知运行版本1.26.0来自失败FCD头。

|条件|初态总数|数值10候选数|其他数值初态|非初态数|本轮准备新输入|
|---|---:|---:|---:|---:|---|
|0750 ID1|117|38|79|1033|是，仅38辆10→max|
|0750 ID3|117|38|79|1033|是，同38辆10→max|
|0805 ID2|131|44|87|900|否，暂缓|

全部初态depart=0，身份唯一，逐车车型、路线、原生出发车道/限速、位置合法性与整条路线车道限制已静态核查；未使用物理空间映射坐标代替原生物理语义。0750数值范围0.10–16.74，0805为4.73–16.76。0750修改目标均在main_2，按车道0–4分别6/6/11/8/7辆。main_2静态限速10，ID1脉冲5；主线其他段27.78，匝道13.89，连接段还有6.92/7.18/18.89等限速，静态合法不等于实际插入可行。

所有逐车表留本机initial_vehicle_audit.json（含全部117/131/117行审计）；便携仅聚合和哈希。两个候选routes除目标departSpeed属性外保留原字节，network/config字节不变。ID1/ID3声明初态完全相同，非初态两者仍只有原定60辆匝道depart差异。

## Observation：既有FCD插入时序证据

|源|FCD最后时刻|初态被观察/总数|首次观测范围|首次观测>0数量|t120全网在场初态|
|---|---:|---:|---|---:|---:|
|0750历史基线|419.9|108/117|0–119.3s|70|2|
|0805历史基线|419.9|118/131|0–98.4s|96|4|
|首次失败ID1|179.9|108/117|0–119.3s|70|2|

FCD首现只是100ms观测代理，不能当精确插入时刻或departDelay。0750目标38辆中36辆在0–4.9s首现，首现速度均10；i0063/i0064一直未被观察。未修改79辆中72辆首现0–119.3s、首现速度0.21–16.74，7辆未被观察。缺失者不推断补齐为pending、discard或零速。完整首末观测仅本机存档，聚合可从获准FCD重算。

原局部初始化事实保留：0750 t120局部1辆，最后130.5s、106条/10.6veh-s；0805 t120局部0。局部无初态不代表全网无初态，更不代表无待插入者。没有删除记录，也没有为本候选重算/选择P2。

## 影响分析与未决范围

工程影响分析：max作用于所有38辆的插入策略，包括原本更早进入的36辆，不只针对180s报错者；安全适应可改变速度/插入时机/顺序，继而改变在场初态、排队和非初态实际流入。新的插入速度、延迟、残留与完整18单元支持均Unknown。

本最小候选保留其余79辆，尤其i0007的15.23与t0“slow lane ahead”警告没有被修复或隐藏；不能保证所有初始化冲突消除，也不能称零影响工程修复。把全部117辆改max会额外改变79辆的初始速度策略，在main_0/main_1其自由插入上界可到27.78，影响范围明显不同，未自动实施。

**科研范围冲突记录**：Documented Intent是“初态固定10→max”；Actual Implementation并非所有初态为10；Evidence为已绑定routes及上述全体审计；Affected Files为候选两份routes/修订计划；Conflict是修改38或117辆的范围不同；Status: Awaiting Researcher Decision。现阶段提供可审阅38辆最小版，不将候选替研究者写成Agreed。

解释限制：旧基线与候选初始化政策不同，只能作为历史描述参考。候选ID1/ID3相同声明初态不保证相同实现初态（ID3首个匝道脉冲在20s）；两臂同时存在供给/匝道差异，剩余两跑没有同政策无扰动基线，不能独立归因初始化修订、供给或匝道的单因素效应。这里是可识别性限制，不是机制已成立/不成立的科研结论。Hypothesis仍待研究者决定和后续获准数据检验；本报告不作新机制结论。

## 精确提案与验证入口

计划SHA256：`6a81e1a7bf34ccb81a13418f84e8d5a6138cc51b7ec9d09c554977380b47bc6e`。

提案SHA256：`69646b039177e43d874701b2ada548717cdf4bdfeda5cc4f231aecf9193bcaff`。

review_proposal.json绑定精确计划、输入、旧证据、准备/执行/测量/监督源码、测试与SUMO二进制。其execution_allowed=false、researcher_confirmed=false；旧确认不迁移。旧失败账本未重置，旧监督器保持失败后拒绝继续；后续执行适配器若改变，必须更新提案/哈希再确认，不能据本版确认启动变更的代码。

本机范围内哈希复核与准备审计0拒绝/0子进程；这只是Python审计，不证明全系统零访问，不关闭历史隔离偏差。工具除二进制以外本轮未重新核验，未来启动前须按旧精确白名单复核，不以旧哈希宣称当前工具未变。

命令（仓库根）：

```powershell
python code/scripts/prepare_stage_0_5_depart_speed_candidate.py verify --local
python code/scripts/export_depart_speed_candidate_evidence.py --repo-root . --verify
python code/scripts/export_project_evidence.py --repo-root . --verify --result-id RES-STAGE-0.5-DEPART-SPEED-CANDIDATE-V1
```

独立限定导出用export_depart_speed_candidate_evidence.py，不修改旧哈希绑定导出器，保留manifest其他条目。无范围历史导出不是本任务运行入口。纯Git无数据只能验证便携/源码/计划及软件测试，不能验证本机XML/FCD或实际运行隔离。软件检查详情见validation_record.json；既有987纯Git全量记录保留其原覆盖范围，998主工作区记录仍无隔离验效。

**下一步待研究者确认候选范围和精确计划/提案哈希。确认前不启动SUMO、不给剩余额度登记尝试。** 本交付只完成本轮获准的离线候选准备，不代表WP2–WP5完成、Stage0.5通过、科学等效、Protocol Lock或Stage1.1获准。
