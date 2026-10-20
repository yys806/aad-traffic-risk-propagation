"""Package candidate protocol metadata and independently check portable arithmetic.

Reads only this task's small derived files, never raw trajectories or SUMO.
"""
import argparse
import base64
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

RESULT_ID='RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def proposals():
    rows=[]
    def metric(layer,name,meaning,real,sim,method,uncertainty,failure,recommend):
        rows.append(dict(layer=layer,metric=name,scientific_meaning=meaning,real_reference=real,simulation_counterpart=sim,candidate_criterion=method,
            uncertainty=uncertainty,failure_meaning=failure,recommended_decision=recommend,status='Proposed',scientific_margin=None,approved=False))
    metric(1,'速度分布与低速比例','约束目标局部交通状态而非仅均速','A+两个窗口主线1–5、[150,350)m；720/660s既有内部支持；5m/s仅描述',
        'main_1三车道[50,250)m；按车辆时间、同一空间归属和批准时间支持统计均速/分位/经验分布',
        '均值差与预先指定分位差的联合区间；分布CDF/一维Wasserstein辅助。所有必要指标须在独立批准margin内；不按最接近窗口挑模型',
        '轨迹簇+预定时间块/独立seed分层；两个同日窗口不代表道路总体；置信水平和多重性待批',
        '支持足够且误差超界=模型/场景偏差；区间过宽=证据不足；不同口径=不可比较','批准方法候选；暂缓数字margin')
    metric(1,'密度与流量/局部通量','区分在场状态、实际服务和输入需求','归一化1.0lane-km密度；150/300/450m断面实际通行率，不是上游需求',
        '.6lane-km车辆时间/观察秒数；真正几何断面穿越率与局部成员流分别记录，pending不入密度',
        '时间剖面、周期/时间块均值、流入减流出和占有量守恒联合审查；q、k、v非独立，不能三次独立加权',
        '空间边界/缺帧/换道分配与采样时间支持误差；参考窗口分开，不用切片当独立日',
        '守恒失败=测量失败；供需积累=场景动态，不自动为工程错误；平衡必要不充分','批准分账与共同单位；固定需求只作条件假设')
    metric(1,'加速度与尾部','约束运动变化及数值/数据处理支持','A+已处理纵向加速度分布，物理真值与共同偏差未独立验证',
        '公开加速度及100ms同支持描述；步内数值核验仍按步初加速度/1e-6m',
        '均值/尾部分位及极端敏感性分别报告；先核对测量滤波语义，再评估有单位的差值界',
        '真实处理/裁剪、差分噪声与SUMO前步平均语义；不能靠加速度拟合抵消测量差异',
        '测量语义不一致时暂停相应目标，不调驾驶参数掩盖','补共同测量误差证据；不另设科学数值容差')
    metric(2,'物理净距','约束跟驰空间交互','A+两窗口局部正净距分布；非正/缺失不补零',
        'getLeader距离+后车minGap；同车道位置/车长独立核验，其他路径保留API证据',
        '同一跟驰资格/速度密度分层内比较分位与CDF；负/缺失份额单报，不能仅保留易拟合样本',
        '车长/前车身份、车道路径和NGSIM几何物理真值限制；配对/轨迹/时间相关',
        '物理净距冲突=测量失败；分布偏移=行为/供给等替代解释，非参数唯一识别','批准条件分布方法候选')
    metric(2,'闭合速度/有效TTC','约束纵向逼近而非事故概率','A+局部closing=follower−leader；现有局部TTC摘要不足则待同域重算',
        '同符号m/s；closing>1e-3且gap>0的有效TTC；未闭合有跟驰暴露、无有效TTC',
        '联合报告闭合份额、closing和有效TTC分布/低尾；epsilon与P2阈值不改，禁止缺失TTC补无限或零',
        '分母选择、近零closing、TTC重尾、轨迹相依；分布支持缺失不外推',
        '有效样本少=支持不足；字段/符号错=测量失败；稳定差异才为模型差异','冻结目标条件与尾部角色后再评估margin')
    metric(3,'身份/时钟/质量/可评价覆盖','保证分子与分母共同资格','Stage0.2相邻100ms/同车同前车；真实原词no_reported_leader=missing',
        'LF保留标志；SUMO无观测前车=not_applicable但reliable=False；不可直接比较词频',
        '先映射共同语义：无观测前车/已知非闭合/有效闭合/无效gap/身份时间字段未知；未知不为零，严格错误阻断',
        'SUMO1000m查询与真实报告关系不同；选择性缺失和来源质量差异分层披露，不能编造最大5%标准',
        '身份/时间/SHA错误=停止；不可评价集中于核心状态=Evidence Insufficient','批准共同语义审查；数值分层仅既有适用域')
    metric(4,'局部P2强度与暴露','以每可评价跟驰车时的代理频率为主，N/E/率非三个独立目标','当前543/732、111425.9/133505.6s为全源，不能作局部率目标；须按批准规则重算两校准窗口',
        '候选观测开始86/共同E=14636.2s；原核心阈值2s/.2s/100ms不变',
        '主目标lambda=N/(E/3600)；联合重采样N与E；若稀疏/零事件用事先选择的计数过程假设区间，不能给0宽bootstrap或强制匹配N',
        '轨迹交互、时间块、seed、窗口截断；现单轨迹CI仅条件敏感性，不含模型/日间系统误差',
        '局部政策/真实支持未齐=Not Calculated；足够精度下界外才为偏差；不是事故概率','先批归属与真实同域重算，不做全源对局部比较')
    metric(5,'状态支持/有效样本/精度','确认目标状态实际出现且估计足够精确','两个批准参考窗口分别描述，不能生成平均虚构交通日',
        '每目标状态报告实际车辆时间、可评价暴露、独立轨迹/seed及转态，不能用重复轨迹增样本',
        '批准状态定义后，各必要层CI宽度<=预先批准h；有效支持与精度同时满足才继续，h不得从想通过的结果倒推',
        '自相关/共同供给/有限3个晚期周期；没有统一独立样本数或稳定暖机秒数',
        '状态未出现/区间过宽=支持不足，不能由其他层抵消','先批准状态和精度目标，保留剩余运行预算')
    metric(5,'Energy Distance辅助','仅帮助发现分布差异，不作为总体通过分数','只有两个相关校准窗口，real-real上界Not Identifiable',
        '同场景同空间同变量尺度的辅助图/距离；不跨C/D/城乡池化',
        '仅描述/排序敏感性；0.90/0.95工程默认值不升格，五层必要条件取合取而非加权',
        '尺度、抽样、时间/轨迹相关与真实总体支持不可识别',
        'ED小不能修复身份失败、状态不匹配或P2分母缺口','保留辅助，不批准科学ED阈值')
    return rows

def decisions():
    return [
        dict(id='D1',status='Awaiting Researcher Decision',question='局部事件究竟算在哪里、哪个时间窗，分母如何归属？',
            recommendation='主口径用观测风险开始位置/开始时间；确认位置及开始至确认均在域为辅助，三者主比较共用开始时间窗；确认时间窗另作边界敏感性。共同分母用已可评价100ms边的两端在域时间。',
            evidence='266事件逐成员核对；86/87/83历史重现；新确认前全在域86；4个差异事件均解释；两端分母14636.2s，左/右端14653.7/14660.4s。',
            alternatives='确认归属会把区段外开始的v00104算入；全事件83还排除确认后离开的3件并需更长未来信息；起始口径较符合本地发生强度。',
            scientific_impact='改变目标估计量，不能按率高低选择；开始仅观测定义，不宣称真实物理最早。事件消息仍不得早于确认。',
            engineering_cost='既有局部代码可候选复算；真实两窗口同域事件需完整前车上下文受控重算。',
            can_continue='合成测试、候选审计和共同语义整理',must_wait='正式局部事件数/率、真实局部P2目标与正式实现登记'),
        dict(id='D2',status='Awaiting Researcher Decision',question='研究稳定局部状态，还是随时间变化的受约束过程？',
            recommendation='保留相位配准的局部速度/密度候选稳定规则，同时单报全网和pending；若目标是稳定态，当前没有合格后暖机窗口；若目标是动态过程，另冻结匹配的时间剖面，不能删除积压求稳。',
            evidence='三个晚期周期v≈2m/s、k≈103–106；网络在场171→214→225，pending末期35；5/10/20%敏感性均到300s才完成两次连续周期检查，后评价支持0。',
            alternatives='固定120s没有正式依据且只剩1个局部开始事件；全网稳态可能因供给低于到达而不存在；空初态瞬态亦不能当真实内部时间窗同分布。',
            scientific_impact='确定估计目标和评价支持，不能以P2多数在前120s选暖机；60s周期来自人工信号，不外推到无信号需求。',
            engineering_cost='需要独立确认候选稳定规则/延长支持；600s旧预测642/1929s可能超600s worker上限，需先重新资源证明。',
            can_continue='现有离线相位/通量/窗口敏感性',must_wait='正式暖机秒数、正式评价窗口及其样本'),
        dict(id='D3',status='Awaiting Researcher Decision',question='仿真要代表哪类现实交通，哪些输入只是条件假设？',
            recommendation='以两个批准窗口分别作为局部目标条件；通用高速路允许，完整几何非前提。原C保留测量压力用途，正式校准场景/供给须在拟合驾驶参数前单独冻结。',
            evidence='真实内部局部v=10.506/7.915、k=43.544/50.505；现人工C末周期v=1.995、k=106.025。1648来自内部断面，不是已识别上游需求。A+已识别观测车型/长度，但不是上游流入车型分布。',
            alternatives='固定候选需求/供给只支持条件校准；独立敏感性可揭示混杂但非唯一需求识别；OD/匝道/真实上游供给需额外观测，当前不自动获取。',
            scientific_impact='不得靠Krauss调参补偿供给过强或宣称真实瓶颈；两个同日窗口/重复seed不代表独立道路日。',
            engineering_cost='固定候选可以复用输入；真实需求识别为独立研究成本；不要求立即复现US101全部几何。',
            can_continue='参考支持/单位和可识别性审计',must_wait='正式需求/供给条件与允许调整参数集合'),
        dict(id='D4',status='Awaiting Researcher Decision',question='允许多大模型偏差、需要多精确的证据？',
            recommendation='批准五层合取、差值区间加共同测量误差与单独margin的设计方法；数值margin及精度h保持待定，依据后续AAD结论允许偏差/独立误差证据共同冻结。',
            evidence='真实簇CI只表达采样不确定性；本轮条件簇率CI16.82–25.76不含seed/交互/系统偏差。real-real ED上界仍不可识别。',
            alternatives='CI重叠/不显著不等于等效；真实波动包络可描述，直接当可接受模型误差会掩盖弱识别；综合分数会抵消必要层失败。',
            scientific_impact='决定可接受性及后续效应可解释范围；无margin和h时只能Pending，不能自动Gate pass。',
            engineering_cost='候选计算接口/拒绝测试已齐；缺少AAD误差影响标准，不能以更多同配置样本替代科学决定。',
            can_continue='方法实现、质量敏感性与证据维护',must_wait='科学容差、现实覆盖验收和正式参数优化'),
        dict(id='D5',status='Proposed',question='下一步如何使用5次余额并维持校准/验证隔离？',
            recommendation='先批D1–D4并受控重算两窗口局部参考；再决定是否执行两个预声明300s重复诊断seed20261020/20261021，其余3次保留。本任务不执行这些运行。',
            evidence='现有仅1个独立交通轨迹；所有266事件/6000交通帧离线可重算。本轮新增SUMO0次，剩5。重复300s能检验规则可迁移，不能保证暖机后精度。',
            alternatives='若已确定短运行无后暖机支持，则跳过300s重复，先批准更长采集设计并证明成本；禁止为匹配率挑seed或失败后换阈值。',
            scientific_impact='候选计划、诊断预算不是正式校准/验证授权；第三窗口仅在独立验证协议获准后另行访问，不能当校准目标。',
            engineering_cost='每300s参考worker约321s/采样RSS228MB，按600s/3GiB冻结上限重新预检；后处理约103s，需计入总预算。',
            can_continue='剩余授权内普通诊断可自主冻结执行、无需重新逐项请示；本轮无新辨识价值故不执行',must_wait='依赖D1–D4的科研选择、更大资源或范围以及正式校准/Stage0.5.5须另行授权')]

def package(batch,repo):
    out=batch/'summary';a=read(out/'attribution_summary.json');rows=list(csv.DictReader((out/'event_attribution_audit.csv').open(encoding='utf-8',newline='')))
    temporal=[]
    for w in read(out/'window_sensitivity.json'):
        lo,hi=w['start_s'],w['end_s']
        sel=lambda r:lo<=float(r['start_s'])<hi
        temporal.append(dict(start_s=lo,end_s=hi,onset_spatial_and_onset_time_count=sum(sel(r) and r['onset_inside']=='True' for r in rows),
            confirmation_spatial_same_onset_time_count=sum(sel(r) and r['confirmation_inside']=='True' for r in rows),
            confirmation_spatial_confirmation_time_count=w['counts']['confirmation'],
            crosses_window_start_ids=[r['event_id'] for r in rows if float(r['start_s'])<lo<=float(r['confirm_s'])],
            crosses_window_end_ids=[r['event_id'] for r in rows if float(r['start_s'])<hi<=float(r['confirm_s'])]))
    write(out/'temporal_boundary_audit.json',dict(windows=temporal,reporting_recommendation='Hold onset time W fixed when comparing three spatial policies; confirmation-time W reported as separate temporal sensitivity',
        point_support_difference='Historical acquisition includes t=300 (146825 local points); [0,300) point sensitivity has146758, excluding67 endpoint rows. Full eligible .1s links ending300 are included in integrated [0,300) exposure; point endpoints have zero measure.',
        required_future_context_s=.2,event_end_future_not_required_for_onset_or_confirmation_policies=True,
        left_context='Process full observed sequence before filtering W; do not relabel an ongoing risk as a new local onset at W start. Unknown preceding context stays censored.',
        near_end_unconfirmed_candidates='Do not treat absence of confirmation beyond available context as zero events; classify unconfirmed/right-censored separately. No extrapolation.'))
    write(out/'scientific_admission_table.json',dict(necessary_layers=5,all_layers_required=True,no_compensation_by_weighted_score=True,metrics=proposals(),
        error_rule='For signed scalar Δ, require entire chosen confidence region plus separately bounded systematic measurement error to lie within researcher-approved [-δ,δ]. Multivariate/quantile criteria use simultaneous regions or prespecified multiplicity. No margin ⇒ Awaiting Researcher Decision.',
        uncertainty_not_tolerance=True,confidence_level='Proposed consistent95% reporting; formal level/multiplicity awaits approval',
        pass_scope='Only the approved operational conditions/support. This candidate evaluator never grants a project Gate.'))
    write(out/'researcher_decision_matrix.json',dict(Agreed=['方案A：局部探索不以完整入口回溢为前提','优先通用高速公路与局部匹配，完整真实几何非当前前提'],
        Verified=['266工程事件逐成员/独立风险序列复核','86/87/83历史重现；确认前全在域86','共同分母与边界敏感性','周期交通与积压并存'],decisions=decisions(),
        no_proposal_is_approval=True))
    write(out/'local_measurement_candidate.json',dict(version='lf-protocol-candidate-v1',status='Proposed / Awaiting Researcher Decision',
        primary='Observed risk-onset position AND onset time attribution',auxiliary=['Confirmation position, same onset-time support','All observed onset-to-confirmation members inside, same onset-time support'],
        extra_sensitivities=['Historical all observed event to end','Confirmation-time window','Left/right endpoint local exposure'],
        numerator='Confirmed original Stage0.2 core event, no local re-extraction; N_onset=sum 1{s_e in W} 1{x_e(s_e) in R}',
        denominator='E_R,W=sum h*1{original reliable same-follower/same-leader continuous link AND both endpoint status valid/not_applicable}*1{both follower endpoints in R AND full link in W}',
        rate='N / (E_R,W /3600), events per P2-evaluable following vehicle-hour',
        different_event_subtypes_share_standardized_exposure='Auxiliary rates are different attributed/subtype event intensities per the SAME evaluable local time, not estimates of an identical hazard; do not redefine denominator by event duration or eventual residence',
        core_unchanged=dict(TTC_threshold_s=2.,minimum_span_s=.2,closing_epsilon_mps=.001,recorded_step_s=.1),
        extra_lane_change_break=False,full_network_leader_context_required=True,unknown_not_zero=True,numerical_exact_tolerance_m=1e-6,
        scientific_claim_eligible=False,formal_local_P2='Unresolved',formal_local_rate='Not Calculated'))
    ident=[
        ('内部断面实际通行率/局部密度速度','Directly supported in approved observed support','1648及1449.818veh/h/lane是内部300m断面；不是未服务需求或路网入口需求','固定为工程约束可用；不要改称上游真实需求'),
        ('上游到达需求','Not uniquely identifiable','观测已通过车辆，缺少观察域外等待/未插入及上游服务状态','固定候选并标条件；独立敏感性须新计划；唯一识别需额外上游观测'),
        ('匝道流入/驶出','Indirectly constrained, not uniquely identified','不同断面通量和lane6/7存在间接约束，但不提供完整路网/未服务到达','无活动匝道候选仅适用于有限局部；不声称真实匝道机制'),
        ('OD/路线选择','Not identifiable','短区段边界观察不是完整旅程或OD','固定不可变路线只支持条件实验；不能优化OD来补偿行为参数'),
        ('观测车型组成/长度','Directly supported for observed trajectories only','A+两个窗口原始join已核验，不沿用更早A无车型字段的历史结论','保留A+类型/长度注记候选；上游车型流入分布仍不识别'),
        ('Krauss行为参数','Not uniquely identifiable from these summaries','净距/闭合/速度同时受需求、供给、几何、车长和采样影响；现参数是固定工程候选','先固定边界/目标并做独立可识别性设计，再另批参数集合/范围；本轮不拟合'),
        ('人工信号/真实瓶颈供给','Engineering input, not a real fact','C23.8/6.2/30是压力机制；通用三车道不等于真实US101设施/容量','保留测量压力用途；正式校准供给需研究者单独选择'),
    ]
    write(out/'demand_identifiability_matrix.json',dict(items=[dict(quantity=q,status=s,evidence=e,proposal=p) for q,s,e,p in ident],
        geometry_scope='Density/lane/time units comparable after explicit support matching, not a claim of identical geometry, capacity, lane interactions or wave propagation'))
    issues=[
        dict(id='LFPC-P1-01',severity='P1',fact='旧fully_inside83定义为开始至结束，本任务辅助为开始至确认；新值86。',files=['stage_0_5_local_following.py::analyse','stage_0_5_lf_protocol.py::event_audit'],impact='误把83重命名会错误排除3个确认后驶出事件，并增加未来依赖。',validation='266事件CSV和4差异；独立边界用例。',resolution='本轮独立候选明确两定义，历史83不改。',researcher_decision='D1，仅正式口径待批'),
        dict(id='LFPC-P1-02',severity='P1',fact='参考543/732事件和111425.9/133505.6s暴露为全来源；局部720/660s支持不同。',files=['approved_reference_support.json','candidate_protocol.json historical A'],impact='21.15局部候选与17.54/19.74全源率接近不能判现实覆盖；局部真实P2仍缺同域分子。',validation='读取两窗口封存summary、A+空间切片支持交叉核对。',resolution='五层表阻断该比较，未读全源事件表。',researcher_decision='D1/D3：同域重算及目标'),
        dict(id='LFPC-P1-03',severity='P1',fact='本地三个晚期周期近平台但网络及pending仍增长，300s确认暖机候选后剩余评价0。',files=['traffic_cycle_audit.json','warmup_candidate_analysis.json'],impact='不能用局部平台或风险早期集中宣称全网稳态/任意暖机。',validation='6000帧守恒/周期剖面/三档冻结漂移敏感性；P2不参与暖机判断。',resolution='候选规则与作用域分开，正式窗口留空。',researcher_decision='D2'),
        dict(id='LFPC-P1-04',severity='P1',fact='真实no_reported_leader词汇missing；SUMO无观测前车not_applicable且reliable=False。',files=['stage_0_5_sumo.py::compute_sumo_measurements','approved_reference_support.json'],impact='直接比较missing词频会伪造SUMO观测质量优势；无前车均不进入可靠跟驰暴露。',validation='原始标签/质量依据、合成分母反例和共同语义交叉表。',resolution='协议要求按原因映射，未改历史标签/核心规则。',researcher_decision='采用共同语义审查方法，不批准任意缺失率上限'),
        dict(id='LFPC-P2-01',severity='P2',fact='窗口[0,300)点数比旧含300s采集少67；旧A候选曾称车型不可识别，A+已补足观测车型。',files=['temporal_boundary_audit.json','demand_identifiability_matrix.json'],impact='混用窗口/历史版本会误报结果或可识别性。',validation='端点/时间窗测试；已批准A+摘要和生成代码范围审计。',resolution='明确点/边积分差别与当前观测车型事实；旧证据不改。',researcher_decision=False),
    ]
    write(out/'issue_discovery_report.json',dict(P0_found=0,issues=issues,absence_of_findings_not_proof_of_universal_correctness=True))
    write(out/'execution_ledger.json',dict(new_SUMO_runs=[],new_targeted_attempts=0,previous_targeted_attempts=3,total_authorized_targeted_runs=8,targeted_remaining=5,
        micro_budget_remaining=0,ABCD_runs=0,formal_calibration_runs=0,
        optional_new_seed_diagnostics=dict(status='Not Attempted',seeds=[20261020,20261021],max_simulated_s=300,decision='No new run distinguishes scientific attribution/margins; repeatability work is proposed after protocol review, not executed or authorized as calibration')))
    write(out/'method_sources.json',dict(access_date='2026-10-20',primary_sources=[
        dict(title='FHWA Traffic Analysis Toolbox III,2004 Appendix C (historical initialization guidance)',url='https://ops.fhwa.dot.gov/trafficanalysistools/tat_vol3/sectapp_c.htm',use='Supports examining empty initialization/network accumulation, not adopting an example warmup time'),
        dict(title='FHWA-HOP-18-036,2019 Chapter5',url='https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter5.htm',use='Time-dynamic operating conditions and separate representative-condition targets; its numerical acceptability examples are not adopted'),
        dict(title='NIST/SEMATECH7.2.6.3',url='https://itl.nist.gov/div898/handbook/prc/section2/prc263.htm',use='Statistical confidence and population tolerance intervals differ; neither automatically supplies an acceptable simulator model bias')],
        project_rules_take_precedence=True,external_numeric_thresholds_imported=False))
    write(out/'provenance.json',dict(result_id=RESULT_ID,base_commit=read(batch/'preparation.json')['base_commit'],plan_sha256=sha(batch/'experiment_plan.json'),
        analysis_script=dict(path='code/scripts/design_stage_0_5_lf_protocol.py',sha256=sha(batch/'protocol_entry.py')),
        analysis_module=dict(path='code/src/riskprop/stage_0_5_lf_protocol.py',sha256=sha(batch/'runtime/code/src/riskprop/stage_0_5_lf_protocol.py')),
        candidate_metadata_script=dict(path='code/scripts/package_stage_0_5_lf_protocol.py',sha256=sha(Path(__file__))),
        full_raw_state_exported=False,only_existing_approved_real_summaries_used=True))
    for name in ['experiment_plan.json','PLAN_SHA256','source_manifest.json','preparation.json','analyse_execution.json','analyse_access_audit.json','tests_execution.json','tests_access_audit.json']:
        shutil.copyfile(batch/name,out/name)
    return out

def seal(out):
    files=sorted(p for p in out.iterdir() if p.is_file() and p.name not in ['manifest.json','SHA256SUMS'])
    if any(p.stat().st_size>256*1024 for p in files):raise ValueError('portable_file_size')
    write(out/'manifest.json',dict(result_id=RESULT_ID,files=[dict(path=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in files]))
    (out/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in files+[out/'manifest.json']),encoding='utf-8',newline='\n')

def verify(out,repo=None):
    out=Path(out);manifest=read(out/'manifest.json');files={e['path']:e for e in manifest['files']}
    for name,e in files.items():
        if Path(name).name!=name or sha(out/name)!=e['sha256']:raise ValueError('file_SHA')
    actual={p.name for p in out.iterdir() if p.is_file()}
    if actual!=set(files)|{'manifest.json','SHA256SUMS'}:raise ValueError('file_inventory')
    for line in (out/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1)
        if Path(name).name!=name or sha(out/name)!=digest:raise ValueError('sums_SHA')
    plan=read(out/'experiment_plan.json')
    if sha(out/'experiment_plan.json')!=(out/'PLAN_SHA256').read_text().strip() or sha(out/'source_manifest.json')!=plan['frozen_files']['source_manifest.json']:raise ValueError('plan_source_manifest')
    if plan['new_SUMO_runs'] or plan['scientific_tolerance'] is not None or plan['ABCD_allowed'] or plan['calibration_allowed']:raise ValueError('plan_promotion')
    rows=list(csv.DictReader((out/'event_attribution_audit.csv').open(encoding='utf-8',newline='')))
    if len(rows)!=266 or len({(r['incarnation_id'],r['start_s'],r['end_s']) for r in rows})!=266:raise ValueError('event_inventory')
    for r in rows:
        a,c,b=map(float,[r['start_s'],r['confirm_s'],r['end_s']])
        if c-a<.2-1e-9 or b<c or int(r['member_count'])<3 or r['same_pair_and_clock_verified']!='True':raise ValueError('event_confirmation_or_support')
    counts={key:sum(r[col]=='True' for r in rows) for key,col in [('onset','onset_inside'),('confirmation','confirmation_inside'),('through_confirmation','through_confirmation'),('through_end','through_end')]}
    if counts!=dict(onset=86,confirmation=87,through_confirmation=86,through_end=83) or counts!=read(out/'attribution_summary.json')['counts']:raise ValueError('count_definition')
    den=read(out/'denominator_audit.json');rates=read(out/'attribution_summary.json')['candidate_rates']
    for k,n in counts.items():
        if rates[k]['observed_events']!=n or rates[k]['evaluable_vehicle_s']!=den['local_both_s'] or abs(rates[k]['rate_per_evaluable_vehicle_hour']-3600*n/den['local_both_s'])>1e-9 or rates[k]['formal_policy_approved']:raise ValueError('rate_semantics')
    if not (den['local_both_s']<den['local_left_s'] and den['local_both_s']<den['local_right_s']) or den['formal_policy_approved']:raise ValueError('exposure_semantics')
    for w in read(out/'temporal_boundary_audit.json')['windows']:
        lo,hi=w['start_s'],w['end_s']
        onset=sum(lo<=float(r['start_s'])<hi and r['onset_inside']=='True' for r in rows)
        confirm=sum(lo<=float(r['start_s'])<hi and r['confirmation_inside']=='True' for r in rows)
        confirm_time=sum(lo<=float(r['confirm_s'])<hi and r['confirmation_inside']=='True' for r in rows)
        if (w['onset_spatial_and_onset_time_count'],w['confirmation_spatial_same_onset_time_count'],w['confirmation_spatial_confirmation_time_count'])!=(onset,confirm,confirm_time):raise ValueError('temporal_attribution')
    policy=read(out/'local_measurement_candidate.json')
    if policy['status']!='Proposed / Awaiting Researcher Decision' or policy['extra_lane_change_break'] or policy['core_unchanged']!=dict(TTC_threshold_s=2.,minimum_span_s=.2,closing_epsilon_mps=.001,recorded_step_s=.1):raise ValueError('core_or_approval')
    table=read(out/'scientific_admission_table.json')
    if not table['all_layers_required'] or not table['no_compensation_by_weighted_score'] or {r['layer'] for r in table['metrics']}!={1,2,3,4,5}:raise ValueError('necessary_layers')
    for r in table['metrics']:
        if r['scientific_margin'] is not None or r['approved']:raise ValueError('margin_promotion')
    audit=read(out/'audit.json')
    if any(audit[k] for k in ['scientific_claim_eligible','ready_to_start_stage_0_5_4b','reality_coverage_accepted','protocol_lock_allowed','stage_1_1_allowed']) or audit['local_formal_P2']!='Unresolved' or audit['C_entry_spillback']!='Evidence Insufficient':raise ValueError('gate_promotion')
    w=read(out/'warmup_candidate_analysis.json')
    if w['formal_warmup_s'] is not None or w['formal_evaluation_window'] is not None or any(s['risk_used_to_choose_warmup'] or s['network_stationarity_supported'] or s['local_candidate_end_s']!=300 for s in w['sensitivity']):raise ValueError('warmup_promotion')
    ledger=read(out/'execution_ledger.json')
    if ledger['new_SUMO_runs'] or ledger['new_targeted_attempts'] or ledger['targeted_remaining']!=5 or ledger['ABCD_runs']:raise ValueError('budget')
    ref=read(out/'approved_reference_support.json')
    if {r['window'] for r in ref['windows']}!={'us101__0750_0805','us101__0805_0820'} or ref['actual_real_trajectory_reads_this_task'] or ref['actual_validation_window_reads']:raise ValueError('reference_scope')
    for r in ref['windows']:
        if r['formal_local_event_count']!='Not Calculated' or not r['source_P2_scope_not_local']:raise ValueError('reference_P2_promotion')
    if repo:
        prov=read(out/'provenance.json')
        for name in ['analysis_script','analysis_module','candidate_metadata_script']:
            src=prov[name];raw=subprocess.check_output(['git','show','HEAD:'+src['path']],cwd=repo)
            if hashlib.sha256(raw).hexdigest()!=src['sha256']:raise ValueError('source_binding_'+name)
        binding=read(out/'git_source_bindings.json')
        for e in binding['files']:
            raw=subprocess.check_output(['git','show','HEAD:'+e['path']],cwd=repo)
            if hashlib.sha256(raw).hexdigest()!=e['canonical_git_sha256']:raise ValueError('git_binding')
            if e['byte_transform']=='canonical LF to original CRLF':raw=raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
            elif e['byte_transform']!='none':raise ValueError('source_transform')
            if hashlib.sha256(raw).hexdigest()!=e['frozen_sha256']:raise ValueError('frozen_source_transform')
        for e in binding['generated']:
            if hashlib.sha256(base64.b64decode(e['base64'],validate=True)).hexdigest()!=e['sha256'] or e['sha256']!=plan['frozen_files'][e['path']]:raise ValueError('generated_binding')
    result=dict(passed=True,event_rows=266,counts=counts,new_SUMO_runs=0,budget_remaining=5,formal_policy='Awaiting Researcher Decision')
    print(json.dumps(result));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['package','seal','verify']);p.add_argument('path',type=Path);p.add_argument('--repo-root',type=Path);a=p.parse_args()
    if a.mode=='package':package(a.path.resolve(),Path(__file__).resolve().parents[2])
    elif a.mode=='seal':seal(a.path.resolve())
    else:verify(a.path.resolve(),a.repo_root)
