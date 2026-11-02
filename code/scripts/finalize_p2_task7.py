"""Task7 reports, portable research evidence, and project-context synchronization."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
import json
import math
from pathlib import Path
import shutil
import subprocess
import numpy as np
import p2_task7_measurement as m
import analyze_p2_task7_parameter_experiment as a

ROOT=Path(__file__).resolve().parents[2]
REPORTS=[f'docs/research/P2/P2_TASK7_{s}.md' for s in ['FINAL_REPORT','EXPERIMENT_PROTOCOL','PARAMETER_RESULTS','RESEARCHER_RECOMMENDATIONS']]
SCRIPTS=[f'code/scripts/{s}.py' for s in ['p2_task7_measurement','run_p2_task7_parameter_experiment',
    'repair_p2_task7_truth','analyze_p2_task7_parameter_experiment','complete_p2_task7_diagnostics',
    'plan_p2_task7_validation','verify_p2_task7_results','finalize_p2_task7']]
EVIDENCE=ROOT/'evidence/research/P2_TASK7_20261102'

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def read_rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(rel,text): (ROOT/rel).write_text(text.rstrip()+chr(10),encoding='utf-8',newline=chr(10))

def registry_with_preserved_layout(before,registry):
    """Retain exact text for unchanged JSON subtrees, including historical entries."""
    def spans(text):
        result={};decoder=json.JSONDecoder()
        def walk(start,path):
            while text[start].isspace():start+=1
            value,end=decoder.raw_decode(text,start);result[path]=(start,end,value)
            if isinstance(value,dict):
                i=start+1
                while text[i].isspace():i+=1
                while text[i]!='}':
                    key,i=decoder.raw_decode(text,i)
                    while text[i].isspace():i+=1
                    assert text[i]==':'
                    i=walk(i+1,path+(key,))
                    while text[i].isspace():i+=1
                    if text[i]==',':
                        i+=1
                        while text[i].isspace():i+=1
                    else:break
            return end
        walk(0,());return result
    after=json.dumps(registry,ensure_ascii=False,indent=1)+chr(10)
    old=spans(before);new=spans(after);patches=[];covered=[]
    for path,(start,end,value) in sorted(new.items(),key=lambda item:len(item[0])):
        if any(path[:len(parent)]==parent for parent in covered):continue
        if path in old and old[path][2]==value:
            left,right,_=old[path];patches.append((start,end,before[left:right]));covered.append(path)
    for start,end,text in sorted(patches,reverse=True):after=after[:start]+text+after[end:]
    assert json.loads(after)==registry
    return after
def table(header,rows):
    return chr(10).join(['| '+' | '.join(header)+' |','| '+' | '.join('---' for _ in header)+' |']+['| '+' | '.join(str(v) for v in row)+' |' for row in rows])
def prepend(rel,block):
    p=ROOT/rel;s=p.read_text(encoding='utf-8-sig')
    if '## Current — P2 Task7' in s or '## P2 Task7 — 2026-11-02' in s:raise RuntimeError('already synchronized '+rel)
    s=s.replace('## Current — P2 Task6','## Historical — P2 Task6',1)
    p.write_text(block.rstrip()+chr(10)*2+s,encoding='utf-8')

def history_and_micro(out):
    paths=[
        'code/outputs/calibration/p2_task3_20261102_v2/calibration_runs.csv',
        'code/outputs/calibration/p2_task3_20261102_v2/calibration_summary.csv',
        'code/outputs/calibration/p2_task3_sumo_b_20261102/run_audits.csv',
        'code/outputs/calibration/p2_task3_sumo_b_20261102/detector_results.csv',
        'code/outputs/calibration/p2_task3_sumo_b_20261102/measurement_audit.json',
        'code/outputs/formal/task18_20261101/primary_results.csv',
        'code/outputs/formal/task18_20261101/supplementary_results.csv',
        'code/outputs/analysis/task19_20261101/analysis_dataset_run_level.csv',
        'evidence/research/P2_TASK6_20261102/design_evidence.json',
        'docs/research/P2/P2_TASK6_PARAMETER_DETERMINATION_EXPERIMENT_PROTOCOL.md',
        'code/src/riskprop/formal_risk_measurement.py','code/src/riskprop/formal_design.py']
    audit=[]
    for rel in paths:
        p=ROOT/rel;entry={'path':rel,'exists':p.is_file(),'sha256':m.sha(p) if p.is_file() else None}
        if p.suffix=='.csv' and p.is_file():entry['rows']=len(read_rows(p))
        audit.append(entry)
    m.dump(out/'audit/history_asset_audit.json',{'status':'historical development only','explicit_whitelist':audit,
        'historical_V2_B60_reexecuted':False,'task9_18_19_same_100_trajectories':True,'historical_samples_added_to_V':0,
        'locked_holdout_reads':0,'Formal_A':0,'independent_Qualified':0,'F0':'Unknown'})
    manifest=load(out/'manifest.json');levels=[];contracts=[]
    for unit in manifest['units']:
        uid=unit['unit_id'];audit=load(out/'audit'/f'{uid}.json');labels=load(out/'truth'/f'{uid}.json');micro=next(r for r in labels if r['measurement_layer']=='micro')
        source_ok=audit['status']=='COMPLETE' and audit['actuated_source']=='s0' and unit['specified_source']=='s0'
        path=[];ordered=None;terminal=micro.get('terminal_entity')
        if source_ok and terminal is not None:
            raw=dict(np.load(out/'raw'/uid/'trajectory.npz'));times={0:audit['actual_source_onset']}
            for i in range(1,terminal+1):
                events=a.fast_events(raw['t'],10-raw['v'][:,i],np.ones(len(raw['t']),bool),1.,1.,.05,stop=50.)
                times[i]=[events[0]['onset_lower_s'],events[0]['onset_upper_s']] if events else None
                path.append({'leader':f's{i-1}','follower':f's{i}','parent_interval':times[i-1],
                    'response_interval':times[i],'W6':bool(times[i-1] and times[i] and times[i-1][1]<times[i][0])})
            ordered=all(e['W6'] for e in path)
        observed=bool(source_ok and micro['state_truth']=='positive' and ordered)
        failed=audit['status']!='COMPLETE'
        levels.append({'unit_id':uid,'density':unit['density'],'condition':unit['condition'],'specified_source':unit['specified_source'],
            'Potential':None if failed else source_ok,'Observed':None if failed else observed,'Qualified':None if source_ok or failed else False,
            'any_source_state_positive':micro['state_truth']=='positive','terminal_entity':terminal,'path':path,
            'W1':None if failed else 'verified actual same-lane leader for source chain' if source_ok else 'no specified-source event/path',
            'W2':None if failed else 'continuous actual IDs','W3':None if failed else '50s relation panel',
            'W4':audit['actual_source_onset'],'W5':'independent finite a=1,b=1 native response','W6':ordered,
            'W7':None if failed else 'positive geometric gaps; native readback; complete .05s grid',
            'W8':'Unknown competing-cause exclusion' if source_ok else 'specified event absent/disconnected' if not failed else 'Unknown startup failure',
            'W9':'same entity and response segments; terminal in fixed region' if observed else 'Not established',
            'qualified_count_contribution':0,'claim_scope':'controlled B candidate evidence, not independent Formal source-to-cohort witness'})
        contracts.append({'unit_id':uid,'dependency_block':uid,'split':'calibration','seed':unit['sumo_seed'],
            'scenario':unit['scenario_family'],'source_type':'controlled_B_or_no_source','source_assignment':unit['condition'],
            'assignment_probability':'N/A: fixed calibration matrix','Qpre':'N/A: no formal communication randomization',
            'communication_assignment':'disabled','message_generation':'not_attempted','delivery':'not_attempted',
            'validation':'not_attempted','adoption':'not_attempted','controller_action':'not_attempted',
            'regional_formal_risk':'not_evaluated','cohort_version':'s14-s17 fixed','region_version':'1600-3080 lane0',
            'truth_version':m.TRUTH_VERSION,'raw_sha256':audit['raw_sha256'],'status':audit['status']})
    a.csv_write(out/'audit/micro_witness_levels.csv',levels);a.csv_write(out/'audit/unit_contract.csv',contracts)
    m.dump(out/'audit/micro_witness_summary.json',{'Potential':sum(r['Potential'] is True for r in levels),
        'Observed':sum(r['Observed'] is True for r in levels),'Qualified':0,'no_observation_unknown':sum(r['Potential'] is None for r in levels),
        'source_specific_qualification_unknown':sum(r['Qualified'] is None for r in levels),
        'any_source_state_positive':sum(r['any_source_state_positive'] for r in levels),
        'formal_independent_qualified':0,'scope':'finite model candidate chains; not causal identification'})

def parameter_rows(out):
    selection=load(out/'detector/calibration_selection.json');params=selection['cohort']['parameters']
    definitions={
    'C01':('baseline W','9 s calibration center; 4.5/9/13.5 s conditional curves','pre-only fitting; no independent optimality proof'),
    'C02':('baseline model','constant center; linear compared','only pre-source data'),
    'C03':('theta_P','1 m/s calibration candidate','finite a=1 state; not earliest physical onset'),
    'C04':('h_P','1 s candidate; 1/2/4 s compared','actual last-first span; available delay <=4 s tested'),
    'C05':('q_P','0.05 s clean-grid candidate','clean q grid degenerates; missing-gap domain not calibrated'),
    'C06':('coverage','1 center; .6/.8/.9/.95/1 compared','full-N bounds; gate cannot repair MNAR'),
    'C07':('recovery','negative reset; exit persistence 0/2 s','event lifetime and re-entry recorded'),
    'C08':('hysteresis','off center; numeric-floor exit delta tested','physical sensor-error scale Unknown'),
    'C09':('missing','fixed-N [0,10] model-speed bounds or Unknown','no survivor mean; exit/identity missing retained'),
    'U01':('actual leader relation','same-lane native leader IDs audited','no nearest-neighbor substitution'),
    'U02':('identity','0 unresolved switches in complete clean runs','identity stress causes Unknown'),
    'U03':('relation continuity','complete 50 s relation panel','no cross-leader segment stitching'),
    'U04':('source interval','actual state/TraCI readback bracket width .05 s','planned 30 s never substitutes actual onset'),
    'U05':('response candidate','theta=1 m/s,h=1 s Observed-state candidate','not Qualified propagation sensitivity'),
    'U06':('reaction window','Unknown','threshold-lag/window x clock audit is not true reaction calibration'),
    'U07':('quality','geometric gap/native equality checks; .05 s grid','external sensor/noise tolerances Unknown'),
    'U08':('attribution','Unknown for affirmative source claims','0 claims is abstention, not successful attribution'),
    'U09':('full witness','Not established; Qualified=0','W8/independent source-to-cohort evidence absent'),
    'M01':('region/lane','[1600,3080] m, lane0 fixed','not optimized; other lane is disconnected control'),
    'M02':('macro window','2 s center; 1/2/4 s compared','window is part of operator, not onset correction'),
    'M03':('spatial grid','L/4,L/2,L; primary full region unchanged','partition integral identity checked'),
    'M04':('temporal grid','.05/.1/.2 s','fixed q causes loss of support after coarsening'),
    'M05':('Edie operator','D/A,V/A,D/V with clipped segments','V=0 => undefined u; q=ku not independent evidence'),
    'M06':('coverage/sampling','complete census center; mask stresses','unknown p does not justify full-traffic ratio'),
    'M07':('macro theta','1 m/s calibration candidate','target 2a* positive design never realized'),
    'M08':('macro persistence','1 s calibration candidate','delay from finite oracle state, not first physical effect'),
    'M09':('lane aggregation','lane0 separately; no lane union','no multilane/merging mechanism coverage'),
    'M10':('macro attribution','N/A for any-source endpoint; source-specific Unknown','never inferred from wave or detector state'),
    'T08':('clock/phase','same simulation clock, .05 s phase bracket','external offset/drift/model numerical-time error Unknown'),
    'T09':('delay/measurement bound','Unknown for formal physical bridge','independent V absent; no alpha_measure certificate')}
    rows=[]
    for key,(name,value,limit) in definitions.items():
        rows.append({'parameter_id':key,'name':name,'calibration_value_or_scope':value,'status':'Not established / structural model fact only',
            'independent_V':'Unknown; not executed','limitation':limit,'researcher_freeze':'not_frozen'})
    a.csv_write(out/'detector/parameter_register_results.csv',rows);return rows

def figures(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    folder=out/'figures';folder.mkdir(exist_ok=True)
    rows=read_rows(out/'detector/conditional_single_parameter_curves.csv')
    fig,axes=plt.subplots(1,3,figsize=(12,3.4),sharey=True)
    for ax,layer in zip(axes,a.LAYERS):
        rr=sorted([r for r in rows if r['layer']==layer and r['density']=='high' and r['condition']=='P22' and r['variable']=='theta'],key=lambda r:float(r['value']))
        ax.plot([float(r['value']) for r in rr],[float(r['timely_rate']) if r['timely_rate'] else np.nan for r in rr],'o-')
        ax.set(title=layer,xlabel='Threshold (m/s)',ylim=(-.03,1.05));ax.grid(alpha=.2)
    axes[0].set_ylabel('Timely valid detection, calibration only')
    fig.suptitle('High-density P22: conditional parameter curve, n=24 (no independent V)');fig.tight_layout();fig.savefig(folder/'threshold_curves.png',dpi=160);plt.close(fig)
    labels=[];counts=[]
    inventory=read_rows(out/'truth/label_counts.csv')
    fig,ax=plt.subplots(figsize=(8,3.8));width=.25;x=np.arange(3)
    for j,layer in enumerate(a.LAYERS):
        yy=[sum(int(r['n']) for r in inventory if r['layer']==layer and r['density']==d and r['state']=='positive') for d in a.DENSITIES]
        ax.bar(x+(j-1)*width,yy,width,label=layer)
    ax.set_xticks(x,a.DENSITIES);ax.set(ylabel='Actual finite-state positive labels',title='576 planned calibration units; same raw across layers');ax.legend();fig.tight_layout();fig.savefig(folder/'truth_support.png',dpi=160);plt.close(fig)
    stress=read_rows(out/'detector/selected_robustness_evaluations.csv');fig,axes=plt.subplots(1,3,figsize=(12,3.8),sharey=True)
    keys=[('none',0.),('MCAR',.05),('MCAR',.2),('MNAR',.2),('quantization',.1),('noise',.1),('identity',1.)]
    for ax,layer in zip(axes,a.LAYERS):
        rr=[]
        for kind,amount in keys:
            group=[r for r in stress if r['layer']==layer and r['stress']==kind and float(r['amount'])==amount]
            rr.append(sum(r['unknown']=='True' for r in group)/len(group))
        ax.bar(np.arange(len(keys)),rr);ax.set_xticks(np.arange(len(keys)),[k+':'+str(v) for k,v in keys],rotation=75,ha='right');ax.set(title=layer,ylim=(0,1.05))
    axes[0].set_ylabel('Unknown fraction, 576 calibration attempts');fig.suptitle('Selected candidate stress response (descriptive, no V)');fig.tight_layout();fig.savefig(folder/'unknown_stress.png',dpi=160);plt.close(fig)

def reports(out):
    s=load(out/'detector/calibration_selection.json');resource=load(out/'audit/resource_actual.json');v=load(out/'detector/independent_validation_manifest.json');bridge=load(out/'detector/bridge_feasibility.json')
    analysis=load(out/'audit/analysis_completion.json');extra=load(out/'audit/additional_diagnostics.json');micro=load(out/'audit/micro_witness_summary.json');param=parameter_rows(out)
    counts=read_rows(out/'truth/label_counts.csv');evals=read_rows(out/'detector/parameter_evaluations.csv')
    label_table=table(['层','Low +/−/?','Medium +/−/?','High +/−/?'],[[layer]+['/'.join(str(sum(int(r['n']) for r in counts if r['layer']==layer and r['density']==d and r['state']==state)) for state in ['positive','negative','unknown']) for d in a.DENSITIES] for layer in a.LAYERS])
    metric_table=table(['层/对象','状态阳性及时检出(C)','真阴性 FP(C)','state Unknown','有效检出delay中位上端'],[[layer+(' (native finite state)' if layer=='micro' else ''),f'{r["descriptive_metrics"]["timely_n"]}/{r["descriptive_metrics"]["positive_n"]}',f'0/{r["descriptive_metrics"]["negative_n"]}','1/576',f'{r["descriptive_metrics"]["delay_median_upper_s"]:.2f} s'] for layer,r in s.items()])
    bridge_table=table(['η情景','miss/Unknown各上限','及时检出目标','证书positive n/同质格','乐观运行下界','预计墙钟/原始数据','CDF Hoeffding n/格'],[[r['eta_scenario'],r['timely_miss_budget'],r['timely_detection_lower_target'],r['measurement_exact_certificate']['n'],r['planned_run_lower_bound'],f'{r["wall_s_at_measured_4workers"]/3600:.1f} h / {r["raw_bytes_at_measured_size"]/2**30:.1f} GiB',r['favorable_zero_early_mass_hoeffding_n']] for r in bridge])
    strata=[]
    for layer in a.LAYERS:
        for density in a.DENSITIES:
            for condition in ['N0','N1','P11','P21','P12','P22','Plocal','A0']:
                rr=[r for r in evals if r['layer']==layer and r['density']==density and r['condition']==condition and r['config_id']==s[layer]['config_id']]
                np_=sum(r['truth_positive']=='True' for r in rr);y=sum(r['truth_positive']=='True' and r['timely']=='True' for r in rr);un=sum(r['truth_unknown']=='True' for r in rr)
                strata.append({'layer':layer,'density':density,'condition':condition,'attempts':len(rr),'positive_n':np_,'truth_unknown_n':un,'timely_n':y,
                    'conservative_positive_denominator':np_+un,'timely_lower_pointwise95':m.cp_lower(y,np_+un),
                    'scope':'C descriptive only; within homogeneous predeclared cell; not family acceptance'})
    a.csv_write(out/'detector/selected_cell_metrics.csv',strata)
    pre=m.cp_upper(0,24);finite=v['finite_domain_required']
    result=f'''# P2 Task7 — 参数确定实验最终报告

Task ID：AAD-P2-TASK7-PARAMETER-DETERMINATION-EXPERIMENT-20261102。日期：2026-11-02。
状态：EXPLORATION_COMPLETE_WITH_LIMITATIONS / INDEPENDENT_V_NOT_EXECUTED。参数认证与严格桥接 **Not established / Unknown**。

## 1. 实际完成与核心判断

连续执行了历史资产核查、独立truth、冻结manifest、三密度576计划单位、参数逐项/关键交互/压力分析、精确验证功效与η双情景计算。575次SUMO完成，1次TraCI连接启动失败保留，未更换seed或补跑。主参数47,808次、参考压力29,952次、所选配置压力24,192次、条件单因素39,168次，均是同576依赖单位上的离线重算，不增加独立n。

三个层的有限状态校准中心恰好相同：W=9 s、constant baseline、θ=1 m/s、h=1 s、q=.05 s；Cohort c=1/固定N界；Macro w=2 s且固定lane0域。它们是 **Calibration candidate**，不是Recommended-for-freeze、Agreed数值或已验证稳定区域。各层输出分别报告，未构造OR/AND检测器。

微观源归属/W8、独立V、最弱信号边界和科学稳定等效margin仍不足。目标A没有获得独立验证的参数推荐；目标B两个η情景均无法建立。任务未产生Formal A、独立Qualified source→cohort、F0或AAD假设证据。

## 2. 历史资产、版本和执行范围

Task6协议AAD-P2-PARAM-20261102-v1.0、统一定义v0.4的27项ID保留。Task3 V2 768面板/42候选/32,256评价、B60/2,520评价只审计；Task9/18/19的Primary60+Supplementary40是同100轨迹，未重跑或计入V。白名单/hash见本次history_asset_audit。未读取locked holdout、OB或上游DRIFT，没有论文/正式config/production模块修改。

独立双lane 6 km直路，lane0为R=[1600,3080] m、固定s14–s17 cohort；lane1为断开跟驰链对照。Krauss、速度上限10 m/s、sigma=.25、tau=.6 s，原始步长.05 s、显式ballistic；仅s0/decoy可被控制，全部目标车辆native，动态target setter=0，碰撞/teleport=0（完整575运行）。Low/Medium/High为不同初始platoon packing，不是持续输入交通总体；实际pre Edie k约16.216/27.027/43.243 veh/km/lane，实际表见actual_density.csv。没有换道、合流或现实迁移资格。

主机16逻辑CPU、约27.7 GiB物理内存；启动可用约10.5 GiB内存、196 GiB磁盘，使用4 workers。原始npz约{resource['raw_bytes']/2**30:.3f} GiB，成功单位平均{resource['mean_run_s']:.3f} s。版本、二进制SHA、解释器和dirty来源见provenance；运行Git SHA是基线+明确dirty脚本hash，不能冒称当时工作树完全已提交。

## 3. 真值、设计点和失败

独立truth由完整高频原始状态、固定10 m/s参考、a*=1 m/s、b*=1 s和Macro oracle .1 s域构造；10 m/s是有限模型状态参考，不是无源反事实。a*/b*是有限测试坐标Proposal，**不是由精度证明的最小可传播物理信号**。不使用detector θ/h、拟合baseline或change point生成标签。实际source onset由命令后物理速度/native读回区间确定，不能用计划30 s替代。

先生成全部标签并封存1728条layer-label及原始hash，再运行detector。末端确认工程修复在detector前完成：初版把确认/恢复截在46 s，v2按既定随访延至50 s；原575份v1标签完整保留，48条cohort恢复区间扩展、主状态/起点未改，另补3条失败Unknown记录。没有参数结果驱动的truth修改。

{label_table}

各格分母是192计划单位；阳性包括A0真实状态变化，不能把A0正确状态报警记作FPR。C-N=144、C-P=360（359完成+1失败）、C-A=72。原始N0/N1均为有限状态阴性；不能从中推出任意微小物理变化不存在。

源命令四格为速度下降4/8 m/s、保持4/8 s，另局部2 m/s×1 s；命令不等于目标a*/b*。planned_signal_realization.csv独立核查实际目标强度/持续：Low全部四点未形成指定目标；Medium仅Micro P22达到其目标；High Cohort/Micro四点达到各自最低信号，Macro四点均未达到相应目标等级（P22有a=1有限Macro阳性，但未达计划2a=2）。局部非cohort设计点未形成预列有限阳性。没有扩大源剂量、移动region、降低truth或替换seed。弱于观测支持的范围、边界性能和未实现格均不能认证。

唯一失败C_high_P12_15：FatalTraCIError: Could not connect in 61 tries；0帧、0命令执行，保留空轨迹和audit并作为三个层的Unknown。没有仿真响应失败伪装成阴性。发现后执行器停止，不启动额外单位；已在并发队列内的其余单位已完成。确认归属本任务的孤立SUMO进程已终止，记录保留。

## 4. 三层参数和描述性性能

{metric_table}

上表是校准集状态检测点估计，**不是独立V性能，也不是跨密度/条件iid合并CI**。每个同质N0/N1密度格仅n=24，0 FP的单侧95%精确上界为{pre:.6f}，远高于1%。Unknown按全部576 attempts计1/576；若Unknown视作额外未检出阳性，所选候选总体及时率最坏分别为Cohort119/120、Macro48/49、Micro167/168，但这仍是异质校准描述，不能套一个总体CP界。每格保守分母/CI见selected_cell_metrics.csv。

Micro的167是any-source native有限速度状态阳性，**不是167个Qualified Witness**。指定源候选链Potential={micro['Potential']}、Observed={micro['Observed']}、Qualified=0，{micro['source_specific_qualification_unknown']}单位的指定源资格Unknown；逐跳W1–W9、原始ID/leader、strict W6和竞争解释见micro_witness_levels.csv。W8未被独立证明，不能让拓扑和响应相似性填补。Micro source-claim为全程弃权；0/216已知非指定源机会错误归属不代表有归属灵敏度，Macro/Cohort any-source FAR为N/A。

延迟是相对独立a=1,b=1状态onset区间的available delay；另存first-positive、confirmation、availability和恢复。它不覆盖更早、低于a*或短于b*的真实物理影响。Macro窗口不能通过减w校正成最早物理onset。

## 5. 单因素、交互、稳定性与鲁棒性

按Task6 pre支持生成W=4.5/9/13.5 s，constant/linear；阈值来自独立cal-null最大残差分位及a*/4,a*/2,a*；h=1/2/4 s；q清洁网格退化为.05 s；c=.6/.8/.9/.95/1；recovery0/2 s、hysteresis off/数值floor、Macro w=1/2/4、Δt=.05/.1/.2、Δx=L/4,L/2,L。1e-6仅数值比较floor，不冒称物理传感误差证书。

原25 Cohort/36 Macro/22 Micro候选共47,808评价；所选中心周围追加条件单因素39,168评价，不改变冻结候选或重新选择。pre_baseline_predictions为完全源前块外预测。阈值更低时会早于有限truth状态报警，这不等于“没有物理影响”；在本次事件匹配中单列early/invalid，不能改物理onset追求更高recall。

11类依赖全部有明确产物/限制：W×model、θ×h、h×q、recovery×hysteresis、w×θ、Δx×Δt在interaction_summary（336分层对比）；coverage×missing在coverage_missing_interaction与压力表；density×threshold单独分层、不伪成paired；reaction-window×clock在reaction_window_clock_summary（固定rep0/23代表单位，边不是独立n）；identity×missing在robustness表；H*×η×α×n在精确规划/CDF预算。q退化、reaction真值和完整identity机制不足时结论Unknown，而不是交互为零。

同run交互差分用[-2,2] Hoeffding同时界，n=24/格，区间宽；科学ε_stab和γ_int未冻结，不能用“不显著”认定稳定。144次独立代码路径的Edie裁切/分区crosscheck通过（同一raw不算144个独立实验），q=ku只为恒等式；V=0速度undefined。

压力层包括0/5%/20% MCAR、块/MNAR，原始采样/2倍/4倍，数值floor及.05/.1 m/s噪声、.1/.2 m/s量化、ID断裂。分别保存reference与所选向量，不用剩余车辆均值冒充full-N；降采样但q不变会失去持续证据，缺失/ID会增加Unknown。缺失gate不能修复MNAR，稳定范围尚未建立。

## 6. 独立验证和统计预算

V未执行、V seed消耗0；没有把C或历史V2/B60改名独立V。实际计划族J_V=765，其中459项性能声明、306项稳定性对比，完整清单保留候选和邻域。β_V=.05用于保守同时置信控制；按1−.1/765分配各可检验二项端点的规划功效，以控制该部分联合type-II错误。稳定性margin及Qualified truth仍Unknown，因此完整765项验证族的90%功效**未建立**。所有同轨迹参数/层/mask共享run block，不按车/帧/边计n。

规划good FPR/FAR=.002对.01、good miss/Unknown=.01对.05，均为假设备选，不是已观测真率。精确逐n搜索得到每同质negative格n={finite['required_negative_per_homogeneous_cell']}、positive格n={finite['required_positive_per_homogeneous_cell']}。即使所有预列目标均能实现，至少{finite['planned_run_lower_bound']}运行、{finite['wall_s_at_measured_4workers']/3600:.2f} h、{finite['raw_bytes_at_measured_size']/2**30:.2f} GiB原始数据；还没包括无法实现格、真实稳定margin和失效率额外成本。超过预定V预算2 h/10 GiB，且若阳性支持本身为0，不能仅靠样本量补足。因此不启动无充分支持的V。

零失败最有利n与90%验收功效n分别保存；16组规划经独立lgamma二项CDF复算。首次CDF规划只数45目标格，现已保留初版并修正为225=3层×3密度×5时点×5固定源设计层；实际C-CDF原本即使用225。未将异质固定格池化为iid。此修正发生在任何V之前，阈值和科学标准未改。

## 7. η双情景严格桥接

{bridge_table}

上述certificate成本按α_measure=.005情景计算，β_V=.05不能替代。每个情景独立V Positive=0、Negative=0；及时检出、miss、Unknown、FPR、FAR的独立证书均Unknown。CDF极有利成本还假设早到质量0、为Unknown和delay各分η/4，K=225、α_P=.02；固定格exact CDF power规划另存，η1%需8238/格、η5%需1639/格。这些不是Formal F0样本量或正式已接受α分配。

calibration_cdf_budget按每格n=24并保留固定权重，列出detected-early、Unknown、ε_sampling、finite-state possible mass和partial floor；它不是F0。完整条件必须是detected-early + Unknown + ε_sampling + m_delay + 适用truth/clock/measurement误差 < η。当前m_delay独立界、任意微小物理onset界、Formal A/Qpre同资格无消息总体及正式H*均缺失，完整式不能求出有效通过结果，不能把缺项补0。

三类判断明确区分：有限域仅有校准状态性能与算子工程支持，未有独立V；严格桥接的统计规划成本可计算；两个η情景的真实物理桥接均Unknown/Not established。η=.01/.05只是损失情景，不冻结正式η，也不证明现实交通或AAD核心假设。

## 8. 科研冲突、限制和待研究者接受范围

Documented Intent：Task6四个target a*/b*最低信号点及局部非cohort点。Actual Implementation：固定原生SUMO源剂量，不直接控制目标；实际region信号部分达不到目标格。Evidence：manifest、planned_signal_realization、原始SHA。Affected Files：本次协议/参数结果/manifest，未改旧Task6和正式配置。Conflict：计划target信号不等实际source命令，部分实验格未实现。Status: Awaiting Researcher Decision（仅未来如何调整未实现格；本任务停止扩展，不擅改主对象/真值/区域）。

当前不推荐正式冻结任何数值。可供研究者审阅的只有模型域、独立标签规则和C候选；如未来需要改变source剂量/区域/机制或科学稳定margin，先由研究者决定。本任务不再自动启动后续实验。

## 9. 工程复现、验证与Context Consistency Check

本次代码只在code/scripts和定向tests；未改code/src、正式configs、AGENTS、Overleaf、历史轨迹/结果。数据链raw→独立truth v2/hash→候选manifest→离线评价→统计规划→报告/证据。原准备v1、truth v1、CDF规划v1及唯一失败完整保留，不伪装首次通过。早期读取UTF-8/命令转义失败均未触发科研运行。

核心复算：python code/scripts/verify_p2_task7_results.py --output-dir code/outputs/calibration/p2_task7_20261102_v2。它独立检查全部raw/truth/audit hash、1728 label hash、失败分母、所选指标、16 exact计划和保护路径。定向pytest、文档strict-git与evidence导出/verify的实际结果记录在evidence verification_record.json；不默认跑全量pytest/compileall。

AI_CONTEXT、定义账本/参数入口、研究状态/索引/注册同步实际新事实；不把Proposal升级Agreed。Stage0.5=CLOSED_WITH_LIMITATIONS；Stage0.6=PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock=BLOCKED；StageI=READY_ENGINEERING_ONLY；Stage1.1=NOT_AUTHORIZED。Formal A=0，独立Qualified=0，F0/总体TR-TP Unknown。

本地输出：code/outputs/calibration/p2_task7_20261102_v2/；便携证据：[P2_TASK7_20261102](../../../evidence/research/P2_TASK7_20261102/README.md)。大型raw、图像和日志不进入便携证据。执行基线SHA/dirty/code hashes在provenance；最终commit/push以交付时Git和远端HEAD为准，不写自指SHA。
'''.replace('../../../evidence/research/P2_TASK7_20261102/README.md','../../../evidence/research/P2_TASK7_20261102/README.md')
    write(REPORTS[0],result)
    param_text='''# P2 Task7 — 参数结果与稳定区域

状态：Calibration candidates only；三层独立验证性能Unknown；无Recommended-for-freeze。统一定义[入口](../definitions/README.md)仍为v0.4/27项，不在本文件另建定义。

'''+metric_table+'''

上表包含A0的真实any-source状态阳性，Micro只为native有限状态检测，不是W1–W9的Observed或Qualified计数。任何总比例均为校准描述，不给异质池化exact CI。指定源Qualified=0；每同质N0/N1格n24、0 FP上界11.73%，没有1%FPR证书。

## 28项测量参数与T08/T09

'''+table(['ID','参数','本次候选/事实','局限'],[[r['parameter_id'],r['name'],r['calibration_value_or_scope'],r['limitation']] for r in param])+'''

## 曲线、交互与可行区域

主要曲线：parameter_curves.csv、conditional_single_parameter_curves.csv；原始逐单位结果仅在本地输出。条件单因素围绕所选候选重算，未用它再次选择V向量。baseline pre预测误差独立列出。实测点估计plateau不是科学稳定/等效区域；ε_stab、γ_int、真实弱信号支持和独立V均不足。

11类依赖的表、分母和限制见最终报告§5。恢复/滞回同时记录事件数、首段结束和重入，不能靠不变的首次报警宣布无影响。Macro空间分区完整普查下D/V可加性应成立；时间降采样仍会改变插值误差与质量。reaction-window记录阈值到阈值lag，不冒称生理反应时间。

missing/identity/噪声/量化压力全部保留Unknown，未降低coverage后把可见均值作为全cohort。宏观已知抽样与未知p的全域恢复没有获得独立证书；本次主结果为完整模型普查。

## 推荐状态

Cohort：Not established；Macro：Not established（目标强度四格未实现）；Micro：native有限状态候选可复算，source-specific Qualified参数Unknown。独立验证每层V n=0。适用仅本次无换道直路platoon和有限a=1,b=1原生响应；不适用真实交通、Formal A、微弱/短暂影响、多源因果归属、换道/横向交互和总体早窗。

本地图：figures/threshold_curves.png、truth_support.png、unknown_stress.png；便携证据仅保存小表和hash，不复制图像或raw。详细成本和结论见[最终报告](P2_TASK7_FINAL_REPORT.md)。
'''
    write(REPORTS[2],param_text)
    recommendations=f'''# P2 Task7 — 研究者审阅与推荐边界

当前没有可正式冻结的参数。W9/constant/θ1/h1/q.05、Cohort完整N、Macro w2只是Calibration candidate；不请求把校准点估计升级成独立V或Agreed数值。

1. 可审阅：575个完成原生模型单位、1个保留启动失败、独立a1/b1 truth v2、三个分层算子和完整参数曲线。a*/b*仅是有限构造坐标，不是已证明的真实物理最小信号。
2. 需要未来决定：如何处理Low/Medium无目标阳性、Macro四个目标等级与局部非cohort点未实现；任何修改源剂量、机制、region/cohort或truth须研究者决定，本任务未做这些改动。Documented Intent / Actual Implementation / Evidence / Affected Files / Conflict / Awaiting Researcher Decision详见最终报告§8。
3. 科学稳定性仍缺ε_stab/γ_int的后果依据。现有宽CI或某些参数不显著不能替代等效证明；不擅定margin。
4. 独立V建议保持NOT_EXECUTED：J765下有限域乐观成本至少{finite['planned_run_lower_bound']}运行/{finite['wall_s_at_measured_4workers']/3600:.1f}h/{finite['raw_bytes_at_measured_size']/2**30:.1f}GiB，且假设所有阳性格可实现。目前预算与truth支持不满足，未消耗V seeds。
5. η1%和η5%两情景的统计成本已算，完整物理桥接Unknown；不应接受任一情景“通过”，也不冻结正式η/δ/H*/联合α。

Formal A0、独立Qualified0、F0/总体TR-TP Unknown；所有Stage/Gate原状态保持。无需新增Task6.1/6.2；本Task7以真实限制、未实现格和未完成V统一交付，不自动启动下一科研任务。
'''
    write(REPORTS[3],recommendations)
    protocol=(ROOT/REPORTS[1]).read_text(encoding='utf-8').split('## 实际执行增量与偏离（2026-11-02）')[0].rstrip()+chr(10)
    protocol=protocol.replace('状态：Active。','状态：EXPLORATION_COMPLETE_WITH_LIMITATIONS / V_NOT_EXECUTED。',1)
    protocol += f'''
## 实际执行增量与偏离（2026-11-02）

575完成/1启动失败，576 planned attempts全部保留；没有重跑历史或补seed。实际source剂量4/8 m/s×4/8 s、local2×1，与目标a*/b*分开。target等级实现详情见planned_signal_realization；特别是Macro 2a*格未实现，不将source命令当真值。本次primary truth仅a=1,b=1；其他目标强度/持续以描述性实现审计报告，不另造事后主标签。

独立truth v2在首次detector前冻结；初版v1完整保留，48个cohort恢复区间按原随访要求延到50s，不改变主状态/onset。失败产生3个Unknown。候选25/36/22，离线逐项/交互/压力完成。J_V={v['family_size']}，source/scene/seed/run block完整登记；独立V因资源和真值支持不足NOT_EXECUTED，seed消耗0。科学ε_stab/γ_int、Formal H*/η/δ/α和真实物理误差仍Unknown。

CDF规划225项包含固定5设计层，初版45项规划留档；β_V=.05与α_measure=.005分别计算。原始执行manifest及当时协议/代码字节快照不可用最终报告版本替换；源执行m-v1、独立truth修复m-v2和detector版本分别有hash。最终脚本/文档版本另见便携证据。

复算与输出契约见[最终报告](P2_TASK7_FINAL_REPORT.md)。Formal A/Qualified/F0、Stage/Gate/Lock和论文未改变。
'''
    write(REPORTS[1],protocol)

def sync(out):
    common='统一定义：[docs/research/definitions/README.md](../docs/research/definitions/README.md)，仍v0.4/27项；Task7不建立第二套定义。'
    facts='Task7探索576计划单位，575完成、1次TraCI启动失败保留Unknown；三层独立truth先冻结，83候选/47808主评价及条件单因素/交互/压力完成。W9/constant/θ1/h1/q.05、Macro w2仅C候选，无独立V或稳定性认证。J765下有限域乐观V需54534运行/14.6h/69.5GiB，未运行V、未消耗V seed。Macro目标强度格、局部点和低/中密度阳性支持不足；Qualified/F0及任意最早物理桥接仍Unknown。'
    stage='Formal A=0、独立Qualified=0、F0/总体TR-TP Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS，Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS，Protocol Lock BLOCKED，StageI READY_ENGINEERING_ONLY，Stage1.1 NOT_AUTHORIZED。'
    nav='[最终报告](../docs/research/P2/P2_TASK7_FINAL_REPORT.md) · [参数结果](../docs/research/P2/P2_TASK7_PARAMETER_RESULTS.md) · [实际协议](../docs/research/P2/P2_TASK7_EXPERIMENT_PROTOCOL.md)'
    for rel,detail in {
        'AI_CONTEXT/00_PROJECT_STATE.md':facts,
        'AI_CONTEXT/05_EXPERIMENTS.md':facts+' 本地raw/truth/detector/audit隔离在code/outputs/calibration/p2_task7_20261102_v2/；历史V2/B60/Task9-18-19不进入V。',
        'AI_CONTEXT/06_DECISIONS.md':'Agreed：研究者Task7授权有限SUMO执行、固定N等车mean、Macro同域速度主状态、Micro纵向机制；数值只是Proposal。'+facts+' 不自动推荐冻结或改变科学边界。',
        'AI_CONTEXT/07_KNOWN_ISSUES.md':'Unknown：W8指定源归属、Qualified、独立V、最小物理信号/任意最早onset、ε_stab/γ_int、正式H*/η/δ/α。目标信号未实现格见planned_signal_realization。唯一启动失败C_high_P12_15保留；truth恢复确认/CDF族修复均有原版存档。',
        'AI_CONTEXT/08_CHANGELOG.md':'完成隔离Task7执行器/独立truth/离线三层算子、参数/交互/压力、精确功效与η双情景、报告/便携证据；更新当前入口/定义证据/注册。正式代码/config、AGENTS、历史产物与论文未改。'+facts
    }.items():prepend(rel,'## Current — P2 Task7 parameter experiment (2026-11-02)'+chr(10)*2+common+chr(10)*2+detail+chr(10)*2+stage+chr(10)*2+nav)
    for rel,detail in {
        'AI_CONTEXT/02_ARCHITECTURE.md':'新增隔离校准辅助模块code/scripts/p2_task7_measurement.py与run/analyze/plan/verify/finalize脚本；不导入或替换生产riskprop模块。只有本任务离线工程，正式架构不改。',
        'AI_CONTEXT/03_DATA_FLOW.md':'Task7：冻结source manifest/seed→SUMO raw+审计→独立truth v2/hash（失败Unknown）→candidate manifest→同raw离线三层曲线/压力→精确V/CDF规划→报告/证据。V没有执行，不能从C接回正式F0或risk结论。',
        'AI_CONTEXT/04_MODULE_MAP.md':'隔离Task7代码入口：run_p2_task7_parameter_experiment.py、p2_task7_measurement.py、repair_p2_task7_truth.py、analyze_p2_task7_parameter_experiment.py、complete_p2_task7_diagnostics.py、plan_p2_task7_validation.py、verify_p2_task7_results.py、finalize_p2_task7.py（均code/scripts/）；定向测试code/tests/test_p2_task7_parameter_experiment.py。'
    }.items():prepend(rel,'## P2 Task7 — 2026-11-02'+chr(10)*2+detail)
    for rel in ['docs/RESEARCH_STATUS.md','docs/PROJECT_INDEX.md','PROJECT_CONTEXT.md','docs/STAGE_INDEX.md','docs/RESULTS_INDEX.md','docs/CHANGELOG.md']:
        link='[Task7报告](research/P2/P2_TASK7_FINAL_REPORT.md)' if rel.startswith('docs/') else '[Task7报告](docs/research/P2/P2_TASK7_FINAL_REPORT.md)'
        prepend(rel,'## P2 Task7 — 2026-11-02'+chr(10)*2+facts+chr(10)*2+stage+chr(10)*2+link+'；本项是CALIBRATION_ONLY研究记录，不新增正式结果资格或阶段通过。')
    p=ROOT/'docs/research/definitions/PARAMETER_AND_CALIBRATION_REGISTER.md';p.write_text(p.read_text(encoding='utf-8-sig')+'''
## Task7 有限域实验结果增量（2026-11-02）

v0.4/27定义保留。研究者Task7接受本次固定N等车signed mean、Macro同域速度主状态和Micro同lane有限机制的执行；不冻结正式参数。30行C01–09/U01–09/M01–10/T08–09结果见[参数结果](../P2/P2_TASK7_PARAMETER_RESULTS.md)，机器表evidence/research/P2_TASK7_20261102/parameter_register_results.csv。

W9/constant/θ1/h1/q.05、Macro w2是C候选，575完成/1失败、J765、V0；没有Recommended-for-freeze。Low/Medium及Macro目标格缺支持，W8/Qualified/最弱信号/ε_stab/γ_int/正式物理delay证书Unknown。T01–07/T10未冻结，正式η/H*/δ/α不改。原Task6十三字段/数学域/探索范围/历史撤回保留。
''',encoding='utf-8',newline=chr(10))
    p=ROOT/'docs/research/definitions/EVIDENCE_AND_ASSUMPTION_LEDGER.md';p.write_text(p.read_text(encoding='utf-8-sig')+'''
## Task7 证据与授权增量（2026-11-02）

| ID | 类型/状态 | 实际依据与限制 |
|---|---|---|
| E61 | Agreed, Task7有限校准授权 | 研究者Task7任务书接受固定cohort等车mean、Macro Edie同域速度和Micro纵向三层分别执行；不冻结正式值 |
| E62 | Verified工程/运行事实 | 576计划、575完成、1启动失败；完整raw、independent truth/hash、source-only controls；生产与历史未改 |
| E63 | Fact有限状态校准 | Cohort119/Macro48/Micro167 any-source状态阳性，含A0；不能计作Qualified或独立V |
| E64 | Verified设计数学, Proposal标准 | J765、βV=.05/αmeasure=.005分开、exact power及η双情景成本；V未执行，good rates是规划假设 |
| E65 | Unknown/Not established | W8/Qualified、正式F0与真实最早物理onset、独立V与稳定margin；不由calibration点估计或有限a1b1填补 |

完整来源：[Task7最终报告](../P2/P2_TASK7_FINAL_REPORT.md)、便携manifest/原始hash索引和source脚本。没有将Proposal升级Agreed，没有新Formal A或科学Gate变化。
''',encoding='utf-8',newline=chr(10))
    for rel,block in {
        'docs/research/definitions/README.md':'Task7当前有限域证据：[最终报告](../P2/P2_TASK7_FINAL_REPORT.md)。v0.4的27项定义保持；575完成/1失败，三层C候选、V0，未建立独立参数认证或严格物理桥接。',
        'docs/research/definitions/CORE_SCIENTIFIC_DEFINITIONS.md':'研究者Task7在本次隔离校准域接受固定N等车signed mean、Macro同域速度主状态及Micro同lane机制。575完成/1失败的有限a1b1状态校准不改变27定义、正式风险或最早真实物理arrival；W8/Qualified/独立V与桥接仍Unknown，详见[Task7报告](../P2/P2_TASK7_FINAL_REPORT.md)。'
    }.items():
        p=ROOT/rel;p.write_text(p.read_text(encoding='utf-8-sig')+chr(10)+'## Task7 有限域执行/证据增量（2026-11-02）'+chr(10)*2+block+chr(10),encoding='utf-8')
    registry_path=ROOT/'docs/PROJECT_REGISTRY.json';registry_before=registry_path.read_text(encoding='utf-8-sig')
    registry=json.loads(registry_before);current=registry['current']
    current.update({'active_research_task':'P2-TASK7 exploration complete with limitations; independent V not executed; no parameter certification/strict bridge',
        'why_now':'Task7 executed the authorized finite calibration matrix and exact feasibility; no further experiment auto-started.',
        'p2_task7_status':'EXPLORATION_COMPLETE_WITH_LIMITATIONS','p2_task7_report':REPORTS[0],
        'p2_task7_protocol':REPORTS[1],'p2_task7_new_sumo_attempts':576,'p2_task7_complete':575,
        'p2_task7_failed':1,'p2_task7_independent_v_runs':0,'p2_task7_scientific_claim_eligible':False})
    registry['research_audits']['p2_task7']={'status':'exploration_complete_with_limitations','date':'2026-11-02','report':REPORTS[0],
        'reports':REPORTS,'output':str(out.relative_to(ROOT)).replace(chr(92),'/'),'evidence':'evidence/research/P2_TASK7_20261102/',
        'planned_attempts':576,'completed_sumo':575,'failed_sumo':1,'truth_version':m.TRUTH_VERSION,'truth_labels':1728,
        'parameter_candidates':{'cohort':25,'macro':36,'micro':22},'parameter_evaluations':47808,'validation_family':765,
        'independent_v_runs':0,'independent_v_status':'NOT_EXECUTED','recommended_for_freeze':False,
        'eta_scenarios':{'0.01':'Unknown / not established','0.05':'Unknown / not established'},
        'formal_a_sources':0,'independent_qualified_witnesses':0,'f0_and_population_temporal_precedence':'Unknown',
        'locked_holdout_reads':0,'production_code_changed':False,'formal_config_changed':False,'overleaf_edited':False,
        'stage_status_unchanged':True,'scientific_claim_eligible':False,'new_task_started':False}
    for rel in REPORTS+SCRIPTS+['code/tests/test_p2_task7_parameter_experiment.py','evidence/research/P2_TASK7_20261102/README.md']:
        if rel not in registry['canonical_entries']:registry['canonical_entries'].append(rel)
    registry_path.write_text(registry_with_preserved_layout(registry_before,registry),encoding='utf-8')

def package(out):
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    names={
        'manifest.json':'manifest.json','provenance.json':'provenance.json',
        'audit/truth_freeze.json':'truth_freeze.json','audit/history_asset_audit.json':'history_asset_audit.json',
        'audit/resource_actual.json':'resource_actual.json','audit/FAILED_STOP.json':'FAILED_STOP.json',
        'audit/C_high_P12_15.json':'failed_unit_audit.json','audit/orphan_cleanup.json':'orphan_cleanup.json',
        'audit/truth_horizon_repair.json':'truth_horizon_repair.json','audit/cdf_family_correction.json':'cdf_family_correction.json',
        'audit/design_denominator_correction.json':'design_denominator_correction.json',
        'audit/analysis_completion.json':'analysis_completion.json','audit/additional_diagnostics.json':'additional_diagnostics.json',
        'audit/independent_recompute.json':'independent_recompute.json','audit/run_ledger.csv':'run_ledger.csv',
        'audit/unit_contract.csv':'unit_contract.csv','audit/micro_witness_levels.csv':'micro_witness_levels.csv',
        'audit/micro_witness_summary.json':'micro_witness_summary.json','audit/edie_crosschecks.csv':'edie_crosschecks.csv',
        'truth/truth_inventory.csv':'truth_inventory.csv','truth/label_counts.csv':'label_counts.csv',
        'truth/planned_signal_realization.csv':'planned_signal_realization.csv',
        'detector/candidate_manifest.json':'candidate_manifest.json','detector/calibration_selection.json':'calibration_selection.json',
        'detector/parameter_register_results.csv':'parameter_register_results.csv','detector/parameter_curves.csv':'parameter_curves.csv',
        'detector/conditional_single_parameter_curves.csv':'conditional_single_parameter_curves.csv',
        'detector/interaction_summary.csv':'interaction_summary.csv','detector/robustness_summary.csv':'robustness_summary.csv',
        'detector/reaction_window_clock_summary.csv':'reaction_window_clock_summary.csv',
        'detector/exact_sample_size_power.csv':'exact_sample_size_power.csv','detector/validation_family.csv':'validation_family.csv',
        'detector/independent_validation_manifest.json':'independent_validation_manifest.json','detector/bridge_feasibility.json':'bridge_feasibility.json',
        'detector/calibration_cdf_budget.csv':'calibration_cdf_budget.csv','detector/selected_cell_metrics.csv':'selected_cell_metrics.csv'}
    for rel,name in names.items():shutil.copy2(out/rel,EVIDENCE/name)
    (EVIDENCE/'execution_sources').mkdir(exist_ok=True)
    for name in ['run_p2_task7_parameter_experiment.py','p2_task7_measurement.py','P2_TASK7_EXPERIMENT_PROTOCOL.md']:
        shutil.copy2(out/'snapshots'/name,EVIDENCE/'execution_sources'/name)
    final_paths=SCRIPTS+REPORTS+['.gitattributes','code/tests/test_p2_task7_parameter_experiment.py',
        'docs/research/definitions/PARAMETER_AND_CALIBRATION_REGISTER.md','docs/research/definitions/EVIDENCE_AND_ASSUMPTION_LEDGER.md']
    m.dump(EVIDENCE/'delivery_sources.json',{'runtime_git_sha':load(out/'provenance.json')['git_sha'],
        'runtime_dirty_status':load(out/'provenance.json')['dirty_status'],
        'execution_source_bytes':'local output snapshots plus manifest hashes; source and truth versions separately preserved',
        'delivery_source_sha256':{rel:m.sha(ROOT/rel) for rel in final_paths},
        'final_commit':'derive git rev-parse HEAD after commit; no self-referential SHA',
        'large_raw_logs_figures':'local only; see truth_freeze raw hashes and run_ledger',
        'parameter_candidates_not_frozen':True})
    (EVIDENCE/'README.md').write_text('''# P2 Task7 portable research evidence

576 planned calibration units: 575 complete, one preserved startup failure. Independent V NOT_EXECUTED. No parameter certification, formal source/witness, F0 or strict physical bridge.

Entry: [final report](../../../docs/research/P2/P2_TASK7_FINAL_REPORT.md). manifest/provenance record execution Git baseline, dirty source hashes, SUMO and seeds; truth_freeze indexes all raw/truth/audit hashes. run_ledger/unit_contract retain every assignment. Core state metrics and sample-size plans can be independently recomputed using code/scripts/verify_p2_task7_results.py with the local Task7 output.

parameter_curves/conditional curves, interaction/robustness summaries, actual planned-signal realization, complete V family and exact planning preserve denominators and Unknown. Micro state positives are not Qualified witnesses. βV=.05 and αmeasure=.005 planning are distinct. Both η scenarios remain Unknown/not established.

No raw trajectories, frame-level detection tables, full logs, figures, PDFs, HTML or sealed holdout keys are copied. All large artifacts and original pre-correction truth/planning versions remain under code/outputs/calibration/p2_task7_20261102_v2/. SHA256SUMS covers this portable package except itself. Actual validation outputs are in verification_record.json.
''',encoding='utf-8')
    hashes=''.join(m.sha(p)+'  '+p.relative_to(EVIDENCE).as_posix()+chr(10) for p in sorted(EVIDENCE.rglob('*')) if p.is_file() and p.name!='SHA256SUMS')
    (EVIDENCE/'SHA256SUMS').write_text(hashes,encoding='utf-8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--phase',choices=['report','sync','package'],required=True);args=p.parse_args();out=args.output_dir.resolve()
    if args.phase=='report':history_and_micro(out);reports(out);figures(out)
    elif args.phase=='sync':sync(out)
    else:package(out)
    print(json.dumps({'phase':args.phase,'status':'COMPLETE'}))

if __name__=='__main__':main()
