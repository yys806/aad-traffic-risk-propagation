"""Task8 reports, scoped context updates and portable metadata evidence."""
from pathlib import Path
import argparse
import csv
import json
import shutil
import numpy as np
import p2_task8_support_experiment as s
import analyze_p2_task8_support as analysis
from finalize_p2_task7 import registry_with_preserved_layout

ROOT=s.ROOT
REPORTS=[f'docs/research/P2/P2_TASK8_{name}.md' for name in ['FINAL_REPORT','SUPPORT_RECOVERY_RESULTS','PARAMETER_RECOMMENDATIONS','INDEPENDENT_V_DECISION','RESEARCHER_DECISIONS']]
SCRIPTS=[f'code/scripts/{name}.py' for name in ['p2_task8_support_experiment','run_p2_task8_serial_continuation','analyze_p2_task8_support','verify_p2_task8_results','finalize_p2_task8']]
EVIDENCE=ROOT/'evidence/research/P2_TASK8_20261102'
STAGE='Formal A=0，独立Qualified=0，F0/总体TR-TP Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS；Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock BLOCKED；StageI READY_ENGINEERING_ONLY；Stage1.1 NOT_AUTHORIZED。'

def write(rel,text):
    p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.rstrip()+chr(10),encoding='utf-8',newline=chr(10))
def table(head,rr):return chr(10).join(['| '+' | '.join(head)+' |','| '+' | '.join('---' for _ in head)+' |']+['| '+' | '.join(str(v) for v in row)+' |' for row in rr])
def facts(out):
    result=s.load(out/'audit/review_completion.json');decision=s.load(out/'detector/independent_V_decision.json')
    return result,decision

def reports(out):
    result,decision=facts(out);support=analysis.rows(out/'truth/support_realization.csv');metrics=analysis.rows(out/'detector/candidate_evaluations.csv');w=s.load(out/'audit/witness_summary.json');conflict=s.load(out/'audit/task7_timestamp_conflict.json')
    countrows=[];perf=[]
    for phase in ['1','2']:
        for layer in s.a.LAYERS:
            for density in s.runner.DENSITIES:
                rr=[r for r in support if r['round']==phase and r['layer']==layer and r['density']==density]
                countrows.append([phase,layer,density,len(rr),sum(r['state']=='positive' for r in rr),sum(r['state']=='negative' for r in rr),sum(r['state']=='unknown' for r in rr),sum(r['a2_b1']=='True' for r in rr)])
                ee=[r for r in metrics if r['round']==phase and r['layer']==layer and r['density']==density and r['candidate']=='center']
                positive=[r for r in ee if r['truth_positive']=='True'];negative=[r for r in ee if r['truth_negative']=='True']
                delay=[float(r['delay_upper_s']) for r in positive if r['valid_detection']=='True']
                perf.append([phase,layer,density,f"{sum(r['timely']=='True' for r in positive)}/{len(positive)}",f"{sum(r['false_positive']=='True' for r in negative)}/{len(negative)}",f"{sum(r['unknown']=='True' for r in ee)}/{len(ee)}",f'{np.median(delay):.2f}' if delay else 'Unknown'])
    counts=table(['轮','层','密度','计划分母','Positive','Negative','Unknown','2a*/b*'],countrows)
    performance=table(['轮','层','密度','及时/真阳性','FP/真阴性','Unknown/分母','已检出delay中位上端s'],perf)
    designrows=[]
    for key in sorted({(r['round'],r['density'],r['condition']) for r in support}):
        rr=[r for r in support if (r['round'],r['density'],r['condition'])==key]
        bylayer={layer:[r for r in rr if r['layer']==layer] for layer in s.a.LAYERS}
        designrows.append([*key,len(bylayer['micro']),*[sum(r['state']=='positive' for r in bylayer[layer]) for layer in s.a.LAYERS],
            sum(r['a2_b1']=='True' for r in bylayer['macro']),sum(r['state']=='unknown' for r in bylayer['micro'])])
    designs=table(['轮','密度','源设计','计划run','Cohort+','Macro+','Micro+','Macro 2a+','失败/未知run'],designrows)
    finite=decision['fixed_state_plus_attribution_cost'];state=decision['fixed_state_only_cost'];resource=s.budget(out)
    bridges=table(['η情景','及时检出目标','证书Positive n/格','Negative n/格','理想运行下界','4-worker理想h/串行h','raw GiB','CDF Hoeffding n/格'],[[r['eta_scenario'],r['timely_detection_target'],r['measurement_plan']['n'],r['negative_per_homogeneous_cell'],r['independent_runs_favorable_lower_bound'],f"{r['ideal_four_worker_wall_s']/3600:.1f}/{r['serial_mitigation_wall_s']/3600:.1f}",f"{r['raw_bytes_lower_bound']/2**30:.1f}",r['CDF_Hoeffding_zero_early_n']] for r in decision['strict_scenarios']])
    boundary=f'''统一定义仍为[Task6 v0.4、27项](../definitions/README.md)。Task7原575完成/1失败、truth v2与359/47/0历史记录不改。所有Task8结果为校准/补充支持，Independent V种子消耗0；不是现实交通验证或AAD核心假设证据。

{STAGE}'''
    reasons='''## Task7不足的原始证据与三层差异

audit/task7_support_audit.csv逐单位复核全部575完成轨迹并核对原1728标签；一启动失败仍Unknown。planned C-P机会每密度120（四等级96+局部24），不是保证阳性；固定Cohort局部点原本要求阴性，A0状态阳性另列，不能把总192当计划真阳性。

- Low P22源速度确实降到2 m/s，最低加速度−4.5 m/s²，不能归为“源未执行”。代表run s1/s2/s3到a=1的时刻32.95/36.25/39.55s、位置3093.17/3091.15/3089.07m，均在Region上界3080m之外；固定域内最大下降约.0325，完整Cohort约.027–.031。表明当前剂量下响应与固定支持错位，不是观测缺失。此为已测试域限制，不证明所有可能源曲线都不行。
- Medium P22固定域内原生响应可达s8，峰值约5.94–6.08m/s；尚未到s14–s17，Cohort下降约.026–.031。Macro峰值仅.275–.279，车时权重下局部响应不足以使全域降1。Micro有阳性不要求其他层有阳性。
- High P22 Cohort下降7.78–7.86，Macro仅1.508–1.521，未达2a目标。task7_macro_dilution_decomposition.csv给出逐车D/V及车时权重，贡献和严格等于同域速度下降；.1s truth窗口与2s detector窗口分别保存，空间稀释与时间平滑不是三个独立证据。
- 原Plocal源2m/s×1s在High目标Micro峰值仅.358–.468，低于a*=1；没有可用b*=1状态，而非探测器漏检。Local pulse4m/s×1s与8m/s×1s是预列新设计，不改变Region/cohort。N0/N1完整原生面板中未出现a1b1状态，不能推出任意微小影响不存在。

实际leader和身份在完整运行中连续、目标setter=0。源端剂量、衰减、传播时间/域位置、全群体覆盖和Macro聚合共同影响支持；不把所有缺失都解释为“再加大强度”。因果归属仍需W8，以上是轨迹事实及有限工程解释。

| 缺失条件 | 补充前轨迹依据 | 本次核查问题 | 预列允许调整 |
|---|---|---|---|
| Low Cohort | 原固定群体下降约.03，前车a1响应越过Region | 固定群体能否在原Window响应 | LONG/MAX源条件 |
| Medium Cohort | 原a1响应到s8，未到s14–17 | 更长/强源是否传到完整群体 | LONG/MAX源条件 |
| Low Micro | 原首批a1响应位置大于3080m | 同域原生响应能否形成 | LONG/MAX源条件 |
| Low/Medium Macro | 局部响应的车时权重不足 | 同域平均能否达到a1b1 | LONG/MAX源条件 |
| High Macro 2a | 原峰值约1.51，小于2 | 更强源能否增大原域累计减速 | LONG/MAX源条件 |
| Local non-Cohort | 原局部2×1脉冲峰值低于a1 | 原域局部变化能否不改变完整Cohort | LOCAL4/LOCAL8源脉冲 |

以上均不改变Region、Cohort、Window、原生模型或a1b1；实际实现与失败见分设计结果表，未实现条件作为本次测试域限制停止。
'''
    experiment='''## 一次有界补充及停止

R1预列100单位：三密度×LONG(8m/s×12s)/MAX(10m/s×12s)各8；N0/N1/A0各4/密度；High LOCAL4/LOCAL8(4/8m/s×1s)各8。速度下界0，不加第三档。仍用原Task7网络/vType、Krauss、禁换道、区域[1600,3080]、cohort s14–17、30–46监测和50s随访。请求1s slowDown不是实际1s完成；SUMO原生速度模式限制实际decel4.5、accel2.6，逐run核实，恢复按原曲线释放，不做target setter。

一次R1 TraCI启动失败S1_medium_MAX_01，0帧、0执行；失败seed119947188不重跑。45完成后停机，54个从未启动单位先留Unknown；原partial freeze/零帧占位完整存档。核查唯一归属本任务的orphan SUMO无监听socket后终止。根因Unverified，单进程为有限工程缓解；只首次执行原54个未用seed，无换seed/科学条件变化。后续不再修复迭代。该工程续跑不增加第三轮；原停止记录不抹除。

R1全部truth先封存，再按预注册的truth-only规则冻结R2：三密度MAX各24，High LOCAL4再24，三密度N0/N1/A0各8，共168。LOCAL8已使Cohort改变，不能当局部非Cohort阳性；选LOCAL4依据独立状态而非detector。R2全新namespace，以单进程执行，全部结果保留。R1/R2/可能V分别命名空间[20261102,8,101/202/303]；相同run跨层/参数仍同依赖block。

最大扰动后Low Cohort/Macro及Medium Cohort仍无阳性，已停止这些格；不移动Region/cohort、不延长监测域、不降a*/b*，不继续加seed或更强源。源恢复与目标恢复分别记录，50s前未恢复者right-censored，不外推恢复时刻。扰动较极端，不代表现实交通代表性。
'''
    timing=f'''## 源时间日志问题与W1–W9

Task7实际实现把v<源前速度与v!=getSpeedWithoutTraCI同时作为source onset。SUMO受4.5约束减速时两读数可完全相同：C_low_P22_00实际30.05s已减速，旧字段到31.75–31.8s才触发。Task8以命令时间下界及独立的源前加速度包络外原生状态签名上界记录区间，未用planned time代实际onset；签名缺失记Unknown，不称真实模型误差证书。

Documented Intent：actual physical source onset；Actual Implementation：上述AND条件延迟日志；Evidence：raw速度/加速度/native逐帧对照；Affected Files：旧executor及source-time/W6元数据；Conflict：可能错误拒绝首跳严格时序；Status: Awaiting Researcher Decision，仅指是否回溯修正Task7。本任务不改旧truth、旧代码和359/47/0历史统计。相同旧raw的独立诊断把Observed从{conflict['legacy_Observed']}变为{conflict['diagnostic_Observed_using_signature']}，不是新样本、不是Qualified，更不能新增独立证据。

Task8 Potential={w['Potential']}、Observed={w['Observed']}、Qualified={w['Qualified']}；native state positive={w['state_positive']}是另一对象。witness_levels.csv逐跳保留W1实际leader、W2 ID、W3关系段、W4源区间、W5真实响应、W6严格区间先后、W7质量、W8竞争解释与W9同段连接。固定网络可排除信号/换道/合流/target控制/通信；剩余随机原生制动/共同原因和独立指定源归属金标准尚未认证，W8仍Unknown，未放宽。任何source claim全程弃权，0错误归属只是vacuuous，不证明归属灵敏度。
'''
    parameters='''## 参数候选和容差

三层保留Task7中心：W9s、constant、θ1m/s、h1s、q.05s，Cohort coverage1/full-N、Macro w2s；仅重算中心、θ.5邻居、h2邻居，未重搜83配置。中心只可作为有限状态候选；每密度/源设计的有效检出、早报警、miss、Unknown和延迟见cell_metrics.csv。θ下降可能早于固定a1 truth，h增加可能损失短b1事件；不能只比较报警数。

R2固定MAX中，Micro三密度各24/24及时、High Cohort24/24、Medium/High Macro各24/24；Low Cohort/Macro与Medium Cohort没有真阳性分母。High LOCAL4的Micro24/24，而完整Cohort与Macro均24/24真阴性。中心在全部已实现阳性中没有及时漏检，各层逐轮负样本无FP；这是校准描述，不是参数认证。单个同质格24/24的点态单侧95%灵敏度下界也仅约88.3%，达不到95%规划要求，不能凭零失败通过。

θ=.5邻居在R2已实现MAX阳性与LOCAL4 Micro均出现早于固定a1状态onset的报警，及时有效数0/24；这里“早”相对于有限a1坐标，不等于真实微小物理影响不存在。h=2邻居在Medium MAX Macro和High LOCAL4 Micro均0/24及时（不足持续确认），其他已实现MAX格虽24/24但延迟约增加1s。故保留中心作为待验证候选，不推荐上述邻居全域替代；不能把固定中心的良好描述推成稳定区域。

ε_stab=.01/.025/.05/.1/.2和γ_int=.01/.05/.1/.2/.5仅是概率差容差情景，未冻结。配对差分按run，置信半径保留同质格n；Task7交互336格只复用原结果，不新增n。stability_tolerance_sensitivity/interaction_tolerance_sensitivity给出点估计与同时包络是否落入容差，ε/γ越宽越可能掩盖早检/短时漏检，不能凭不显著证明稳定。

附同一零差/零交互good假设下的Hoeffding充分样本成本（非零失败binomial样本量）：稳定差范围[-1,1]用8 log(2K/.05)/ε²，交互[-2,2]用32 log(2K/.05)/γ²；分配type-II边界也覆盖90%规划功效。无科学损失或独立物理误差依据，无法推荐唯一ε/γ，稳定区域Not established。
'''
    vtext=f'''## 固定候选Independent V决策

**{decision['status']}**。V实际Positive=0、Negative=0、seeds=0，不执行部分验证，不把R2或旧Task7重新命名V。

固定配置验证的科学缩域：每层一组中心参数、每密度一档固定MAX源条件，保留全部三层/三密度和N0/N1/A0；不认证完整剂量范围、局部脉冲或稳定邻域。局部脉冲另作补充诊断，不能用该狭域认证替代局部性能。J=78完整登记：state63（N0/N1 FPR18、主阳性及时miss9、四来源场景Unknown36）；归属15（FAR9、source Unknown3、Qualified timely miss3，其中金标准缺失）。延迟上界4s和及时灵敏/漏检共用同一个二项成功谓词，不重复计信息。

βV=.05，good FPR/FAR=.002对.01、good miss/Unknown=.01对.05，分配单项power=1−.1/J，exact逐n搜索。完整78声明的90%功效仍未建立，因3个Qualified真值端点不可检验。即使假设所有阳性可实现，negative需{finite['negative_per_homogeneous_cell']}/同质格、positive需{finite['positive_per_homogeneous_cell']}/格，合计至少{finite['independent_runs_favorable_lower_bound']}新run；理想4-worker {finite['ideal_four_worker_wall_s']/3600:.2f}h、已采用串行{finite['serial_mitigation_wall_s']/3600:.2f}h、仅raw约{finite['raw_bytes_lower_bound']/2**30:.2f}GiB。只做state63仍需{state['independent_runs_favorable_lower_bound']}run、理想{state['ideal_four_worker_wall_s']/3600:.2f}h/{state['raw_bytes_lower_bound']/2**30:.2f}GiB。不是沿用Task7 J765的成本，也不是零失败最有利n冒充power。

缺失状态支持：{json.dumps(decision['missing_state_support'],ensure_ascii=False)}。源归属truth不足、现有候选边界/局部性能、资源和必要独立样本共同阻断；不能由增加seed假定阳性产率1。当前剩余资源详见decision JSON，已完成工作仍计在2h/10GiB总预算内。

{bridges}

η仅情景，miss/Unknown各η/4，正式αmeasure未冻结，另以.005/J规划，绝不等同βV=.05。CDF K45来自本次更窄的单源条件×3层×3密度×5时点，不是Task7五设计层的K225；仅描述有限状态proxy，非F0。finite_state_cdf_budget.csv按R2同质格分别列detected-early、Unknown和采样余量，n0的格保持Unknown。

完整式detected-early + Unknown + εsampling + mdelay + εtruth/clock/measurement <η。独立V的及时检出/FPR/FAR、真实任意最早物理onset/独立延迟界、Formal A/Qpre/F0、正式H*仍缺失，完整预算不可求值；两个η情景均Not established/Unknown。上述样本成本也建立在极有利假设上，不能代表已达到桥接。

成本复核留痕：首次η=1%估算仅给对照格分配FPR所需n，未同时覆盖更严格Unknown端点；最终表已取二者最大值15571/格，原估算与修订原因保留于initial_statistical_plan/和analysis_revision.json。无truth、detector输出或候选评价改动，不把首次估算伪称正确。
'''
    verification=f'''## 复现、验证及Context Consistency Check

{result['planned_units']}计划单位、{result['completed']}完成、{result['failed_or_not_executed']}失败/未执行，{result['truth_labels']}分层标签，{result['candidate_evaluations']}离线参数评价。完整运行碰撞{result['collisions']}、teleport{result['teleports']}、target setters {result['target_setters']}。目前新增输出{resource['output_bytes']/2**30:.3f}GiB；预算计时{resource['elapsed_wall_s']/60:.1f}分钟，硬上限2小时/10GiB。每单位raw/truth/audit、旧源输入、代码/配置、seed/split均有hash和Git baseline/dirty记录。

定向测试覆盖源onset陷阱、b1时间跨度、identity不拼接、seed分离和Unknown失败；复用Task7算子/精确二项定向测试，不跑无关全量pytest/compileall。独立复算核查全部新run/label hash、Task7原hash、中心指标和16份exact计划；文档strict-git、evidence exporter/verify及纯Git字节保真实际结果见[verification_record](../../../evidence/research/P2_TASK8_20261102/verification_record.json)。启动原失败与一次工程续跑完整保留，不伪称首次通过。

统一定义v0.4/27项不变；AI_CONTEXT/状态/索引/注册/参数证据账本按真实结果同步。旧账本E61–64在Task6/Task7重复，历史表不改，本任务用Task命名空间注明歧义且新增E66以后。无生产模块/正式配置、AGENTS、论文、locked holdout或上游DRIFT变动。{STAGE}

本地输出code/outputs/calibration/p2_task8_20261102_v1/；[便携证据](../../../evidence/research/P2_TASK8_20261102/README.md)仅元数据/小表/运行摘要/原hash与必要源快照，无raw大表、日志、图片或密封键。最终Commit/Push以Git核对为准，不写循环自指SHA。
'''
    write(REPORTS[0],f'# P2 Task8 — 有限阳性支持与Independent V决策最终报告\n\nTask ID：{s.TASK}。状态：SUPPORT_RECOVERY_COMPLETE_WITH_LIMITATIONS；{decision["status"]}。\n\n'+boundary+'\n\n'+reasons+'\n'+experiment+'\n## 分层真值与检测结果\n\n'+counts+'\n\n'+performance+'\n\n表为各轮校准描述，含A0 any-source阳性；没有异质池化iid CI。0/0为Unknown，不是0%灵敏度；已检出delay只描述有效检出者，不替及时成功率。\n\n'+timing+'\n'+parameters+'\n'+vtext+'\n'+verification)
    write(REPORTS[1],'# P2 Task8 — 阳性支持补充结果\n\n'+boundary+'\n\n'+reasons+'\n'+experiment+'\n'+counts+'\n\n## 各源设计实际实现\n\n'+designs+'\n\n'+performance+'\n\n完整分母/阴性/Unknown/恢复区间、源状态、a1/a2实际连续跨度、leader证据见support_realization与witness_levels。固定代表S2各密度MAX_00时间序列图位于本地outputs的figures/fixed_representative_state_traces.png，不作为额外独立样本。全局聚合只作描述，不把R1适应选择后R2合成独立V。\n\n'+timing)
    write(REPORTS[2],'# P2 Task8 — 参数候选建议\n\n'+boundary+'\n\n'+parameters+'\n'+performance+'\n\nCohort：中心仅适用于High已实现状态，Low/Medium不足，不推荐全密度冻结。Macro：Medium/High强长源已有状态支持，Low不足；局部脉冲域不认证。Micro：三密度native状态与High局部状态可审阅，但不是Qualified传播参数。三层都没有独立V，不推荐正式冻结；具体边界失效/延迟与邻域差异见cell_metrics/stability表。\n\n'+timing)
    write(REPORTS[3],'# P2 Task8 — Independent V决策\n\n'+boundary+'\n\n'+vtext+'\n'+verification)
    write(REPORTS[4],f'''# P2 Task8 — 研究者决策与执行边界

{boundary}

| 决策 | 研究者已确认 | 本次执行 |
|---|---|---|
| D1 | 固定双lane/Region/Cohort/Krauss/禁换道 | 全部沿用，无正式网络/config变化 |
| D2 | 一次有限源端补充，最多两轮 | R1 100计划，truth-only冻结R2 168；仅源8/10m/s×12s与4/8×1s；无第三轮 |
| D3 | W1–W9不放宽 | W8仍Unknown、Qualified0；状态阳性不替归属 |
| D4 | a1/b1仅有限校准坐标 | 标签主算子不变；另报2a，ε/γ仅敏感性，不冻结 |
| D5 | 总2h/10GiB，不降标准 | 成本核算后V {decision['status']}，V seed0；不追加资源 |

需要研究者接受而本任务不自动决定：三层候选的有限适用范围；Task7源时间日志问题是否另行回溯修正（旧raw/truth不改）；ε_stab/γ_int的科学损失依据。Low Cohort/Macro与Medium Cohort在已测试最大源下仍缺支持，禁止自动移动域/延长窗口或连续加大源。

W8/独立V/真实物理最早onset与延迟证书未建立，两个η情景均Unknown。可据本任务结束当前有界补充并作下一阶段科研决定；不自动启动任何后续实验、不提出无边界探索。
''')

def prepend(rel,text):
    p=ROOT/rel;old=p.read_text(encoding='utf-8-sig')
    if '## P2 Task8 — 2026-11-02' in old or '## Current — P2 Task8' in old:raise RuntimeError('already synchronized '+rel)
    old=old.replace('## Current — P2 Task7','## Historical — P2 Task7',1)
    write(rel,text+chr(10)*2+old)

def sync(out):
    result,decision=facts(out)
    fact=f"Task8 bounded recovery：{result['planned_units']}计划/{result['completed']}完成/{result['failed_or_not_executed']}失败或未执行；仅源端调整、原域/a1b1不变。Low Micro、Medium Macro、High Macro2a与High局部非Cohort支持恢复；Low Cohort/Macro、Medium Cohort仍缺支持。三中心配置仅候选，J78（state63）固定配置V {decision['status']}，seeds0；W8/Qualified/真实最早物理桥接不足，两η情景Not established。"
    nav='[Task8最终报告](../docs/research/P2/P2_TASK8_FINAL_REPORT.md) · [V决策](../docs/research/P2/P2_TASK8_INDEPENDENT_V_DECISION.md)'
    for rel in ['AI_CONTEXT/00_PROJECT_STATE.md','AI_CONTEXT/05_EXPERIMENTS.md','AI_CONTEXT/06_DECISIONS.md','AI_CONTEXT/07_KNOWN_ISSUES.md','AI_CONTEXT/08_CHANGELOG.md']:
        extra='源日志AND条件延迟问题仅Task8诊断，新source签名区间先于detector冻结；旧Task7 359/47/0和truth不改，是否回溯待研究者。一次启动失败不重跑，单进程只首次执行未启动的预列seed；停止快照保留。'
        prepend(rel,'## Current — P2 Task8 bounded support / V decision (2026-11-02)'+chr(10)*2+fact+chr(10)*2+extra+chr(10)*2+'统一定义仍[27项v0.4](../docs/research/definitions/README.md)。'+STAGE+chr(10)*2+nav)
    prepend('AI_CONTEXT/04_MODULE_MAP.md','## P2 Task8 — 2026-11-02'+chr(10)*2+'Task8隔离脚本：'+', '.join(Path(p).name for p in SCRIPTS)+'；复用Task7原生executor/Edie/三层detector/exact planning，不改生产riskprop。')
    for rel in ['docs/RESEARCH_STATUS.md','docs/PROJECT_INDEX.md','docs/RESULTS_INDEX.md','docs/STAGE_INDEX.md','docs/CHANGELOG.md','PROJECT_CONTEXT.md']:
        link='research/P2/P2_TASK8_FINAL_REPORT.md' if rel.startswith('docs/') else 'docs/research/P2/P2_TASK8_FINAL_REPORT.md'
        prepend(rel,'## P2 Task8 — 2026-11-02'+chr(10)*2+fact+chr(10)*2+STAGE+chr(10)*2+'[报告]('+link+')；CALIBRATION/SUPPLEMENTARY_ONLY，不新增正式结果资格。')
    for rel,text in {
        'docs/research/definitions/README.md':'Task8当前有限支持证据见[最终报告](../P2/P2_TASK8_FINAL_REPORT.md)。v0.4/27项不变，状态与源归属分开，V未执行，无参数/稳定区域/严格桥接认证。',
        'docs/research/definitions/PARAMETER_AND_CALIBRATION_REGISTER.md':'Task8 D1–D5已Agreed：仅源端有界补充，a1/b1有限坐标，2h/10GiB，ε_stab/γ_int不冻结。W9/constant/θ1/h1/q.05和Macro w2仍C候选；Low Cohort/Macro及Medium Cohort缺支持，J78/state63 V0。容差网格与成本见[参数建议](../P2/P2_TASK8_PARAMETER_RECOMMENDATIONS.md)，不修改T01–07/T10正式η/δ/H*/α。',
        'docs/research/definitions/EVIDENCE_AND_ASSUMPTION_LEDGER.md':'''历史ID说明：Task6与Task7表的E61–64重复，引用须使用Task6/E61或Task7/E61等任务命名空间；不重写历史内容。本任务条目：

| ID | 类型/状态 | 证据与限制 |
|---|---|---|
| E66 | Agreed | Task8研究者D1–D5：固定域、只改源、W1–W9不放宽、a1b1有限坐标、资源硬限 |
| E67 | Verified工程/Fact有限支持 | manifest、原始hash和truth：新增Low Micro/Medium Macro/High Macro2a及局部非Cohort；不是指定源Qualified |
| E68 | Fact日志冲突/Unknown回溯决定 | Task7源onset AND条件晚于实际减速；Task8独立签名区间与旧字段并存，原Task7 truth及359/47/0不改 |
| E69 | Mathematical planning/Proposal标准 | 固定候选state63/完整78声明、exact功效、βV与αmeasure分开，V0；Qualified真值缺失 |
| E70 | Unknown/Not established | Low Cohort/Macro、Medium Cohort、W8、稳定margin及真实最早物理桥接仍不足 |

来源：[Task8最终报告](../P2/P2_TASK8_FINAL_REPORT.md)、对应便携manifest/统计/验证记录。Proposal不升级Agreed，27定义ID与正式阶段不改。'''
    }.items():
        p=ROOT/rel;write(rel,p.read_text(encoding='utf-8-sig')+chr(10)*2+'## Task8 有限支持与验证决策（2026-11-02）'+chr(10)*2+text)
    p=ROOT/'docs/PROJECT_REGISTRY.json';before=p.read_text(encoding='utf-8-sig');registry=json.loads(before)
    registry['current'].update({'active_research_task':'P2-TASK8 bounded recovery complete; Independent V '+decision['status'],
        'why_now':'Bounded source-only supplement completed; missing support/source truth and fixed-family resource gap documented; no further experiments auto-started.',
        'p2_task8_status':'SUPPORT_RECOVERY_COMPLETE_WITH_LIMITATIONS','p2_task8_report':REPORTS[0],
        'p2_task8_new_sumo_planned':result['planned_units'],'p2_task8_completed':result['completed'],'p2_task8_V_status':decision['status'],'p2_task8_scientific_claim_eligible':False})
    registry['research_audits']['p2_task8']={'date':'2026-11-02','status':'support_recovery_complete_with_limitations','reports':REPORTS,
        'output':out.relative_to(ROOT).as_posix(),'evidence':EVIDENCE.relative_to(ROOT).as_posix(),
        'new_planned':result['planned_units'],'new_complete':result['completed'],'new_failure_or_not_executed':result['failed_or_not_executed'],
        'truth_version':s.TRUTH,'truth_labels':result['truth_labels'],'candidate_configurations':3,'fixed_V_family':78,'state_only_V_family':63,
        'independent_V_status':decision['status'],'independent_V_runs':0,'recommended_for_freeze':False,'Qualified':0,'Formal_A':0,
        'F0_and_strict_bridge':'Unknown / Not established','Task7_raw_truth_unchanged':True,'formal_stage_gate_unchanged':True,
        'production_changed':False,'formal_config_changed':False,'locked_holdout_reads':0,'new_task_started':False}
    for rel in REPORTS+SCRIPTS+['code/tests/test_p2_task8_support_experiment.py','evidence/research/P2_TASK8_20261102/README.md']:
        if rel not in registry['canonical_entries']:registry['canonical_entries'].append(rel)
    p.write_text(registry_with_preserved_layout(before,registry),encoding='utf-8',newline=chr(10))

def package(out):
    EVIDENCE.mkdir(exist_ok=True,parents=True)
    mapping={'manifest.json':'manifest.json','round2_manifest.json':'round2_manifest.json','provenance.json':'provenance.json'}
    for folder,names in {
        'audit':['task7_audit_summary.json','task7_support_audit.csv','task7_support_counts.csv','task7_source_dynamics.csv','task7_input_hashes.json','round1_truth_freeze.json','round2_truth_freeze.json','round1_serial_manifest.json','round2_serial_manifest.json','round1_serial_completion.json','round2_serial_completion.json','startup_orphan_cleanup.json','FAILED_STOP.json','review_completion.json','witness_summary.json','witness_levels.csv','task7_follower_geometry.csv','task7_macro_dilution_decomposition.csv','task7_witness_timestamp_reaudit.csv','task7_timestamp_conflict.json','analysis_revision.json','independent_recompute.json'],
        'detector':['review_manifest.json','cell_metrics.csv','stability_tolerance_sensitivity.csv','interaction_tolerance_sensitivity.csv','validation_family.csv','exact_power_plans.csv','independent_V_decision.json','bridge_feasibility.json','finite_state_cdf_budget.csv'],
        'truth':['support_realization.csv']}.items():
        mapping.update({folder+'/'+name:name for name in names})
    for source,dest in mapping.items():
        if (out/source).exists():shutil.copy2(out/source,EVIDENCE/dest)
    (EVIDENCE/'first_stop').mkdir(exist_ok=True)
    for name in ['round1_truth_freeze.json','round1_completion.json']:
        p=out/'audit/round1_pre_serial_stop'/name
        if p.exists():shutil.copy2(p,EVIDENCE/'first_stop'/name)
    initial=out/'audit/initial_statistical_plan'
    if initial.exists():
        (EVIDENCE/'initial_statistical_plan').mkdir(exist_ok=True)
        for p in initial.iterdir():
            if p.is_file():shutil.copy2(p,EVIDENCE/'initial_statistical_plan'/p.name)
    (EVIDENCE/'execution_sources').mkdir(exist_ok=True)
    for p in (out/'snapshots').iterdir():
        if p.is_file():shutil.copy2(p,EVIDENCE/'execution_sources'/p.name)
    shutil.copy2(ROOT/'code/scripts/run_p2_task8_serial_continuation.py',EVIDENCE/'execution_sources/run_p2_task8_serial_continuation.py')
    s.dump(EVIDENCE/'output_file_index.json',{'root':out.relative_to(ROOT).as_posix(),
        'scope':'all local output bytes at package time; full raw and logs are indexed by hash only, never copied',
        'files':[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':s.m.sha(p)} for p in sorted(out.rglob('*')) if p.is_file()]})
    all_labels=[];ledger=[]
    for u in analysis.units(out):
        all_labels.extend(s.load(out/'truth'/f'{u["unit_id"]}.json'));audit=s.load(out/'audit'/f'{u["unit_id"]}.json')
        ledger.append({k:audit.get(k) for k in ['unit_id','dependency_block','split','density','condition','rep','sumo_seed','status','rows','elapsed_s','collisions','teleports','native_target_setters','source_execution','actual_source_onset','legacy_executor_source_interval','source_min_speed','source_final_speed']})
    s.a.csv_write(EVIDENCE/'truth_inventory.csv',all_labels);s.a.csv_write(EVIDENCE/'run_ledger.csv',ledger)
    bound=SCRIPTS+REPORTS+['.gitattributes','code/tests/test_p2_task8_support_experiment.py','docs/research/definitions/PARAMETER_AND_CALIBRATION_REGISTER.md','docs/research/definitions/EVIDENCE_AND_ASSUMPTION_LEDGER.md']
    s.dump(EVIDENCE/'delivery_sources.json',{'runtime_git_sha':s.load(out/'provenance.json')['git_sha'],
        'delivery_source_sha256':{rel:s.m.sha(ROOT/rel) for rel in bound},'no_self_referential_commit':'final Git HEAD recorded at delivery',
        'source_execution_versions':'original Task8 source snapshots plus serial engineering amendment; Task7 source/truth unchanged'})
    (EVIDENCE/'README.md').write_text('''# P2 Task8 portable evidence

Entry: [final report](../../../docs/research/P2/P2_TASK8_FINAL_REPORT.md). Bounded source-only support recovery; fixed Region/Cohort/Window and finite a1/b1. Independent V NOT_EXECUTED; no parameter/stability/strict physical bridge certification.

manifest/round2_manifest/provenance, run_ledger and truth_inventory retain all prelisted assignments, failure and Unknown. Per-round freezes bind raw/truth/audit hashes. First stop snapshots and the unused-seed serial continuation are preserved. Source-time conflict is a Task8 diagnostic, not a rewrite of Task7 359/47/0 or truth v2.

validation_family, exact_power_plans and independent_V_decision separate fixed native-state claims, attribution, betaV and alpha_measure scenarios. No historical or supplemental unit is Independent V. Only metadata/small summaries/source bytes are portable; full raw trajectories, frame tables, logs and figures remain local under code/outputs/calibration/p2_task8_20261102_v1/.

Actual tests/doc/evidence/Git-byte checks are recorded in verification_record.json. SHA256SUMS covers package files except itself. Stage/Gate/Formal A/independent Qualified/F0 remain unchanged. Runtime Git SHA plus dirty source hashes are distinct from final delivery Git HEAD.
''',encoding='utf-8',newline=chr(10))
    (EVIDENCE/'SHA256SUMS').write_text(''.join(s.m.sha(p)+'  '+p.relative_to(EVIDENCE).as_posix()+chr(10) for p in sorted(EVIDENCE.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'),encoding='utf-8',newline=chr(10))

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--phase',choices=['report','sync','package'],required=True);args=p.parse_args();out=args.output_dir.resolve()
    if out.parent!=ROOT/'code/outputs/calibration' or not out.name.startswith('p2_task8_'):raise ValueError('isolated Task8 output only')
    if args.phase=='report':reports(out)
    elif args.phase=='sync':sync(out)
    else:package(out)
    print(json.dumps({'phase':args.phase,'status':'COMPLETE'}))

if __name__=='__main__':main()
