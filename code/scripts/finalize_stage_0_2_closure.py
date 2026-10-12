"""Seal a new review package from a completed full-source closure run.
Never overwrite historical outputs or approve the scientific Gate.
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys
from datetime import UTC, datetime
from pathlib import Path
import numpy as np
import pandas as pd
from run_stage_0_2_final_closure import ROOT, BASE, T15, T23, T221, T252, sha, seal, audit_event_match
from riskprop.formal_risk_measurement import extract_formal_source_events

def markdown(frame):
    return frame.to_markdown(index=False, floatfmt=".6f")

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input-dir',type=Path,default=BASE/'stage_0_2_final_closure_20261012_r4');ap.add_argument('--output-dir',type=Path,default=BASE/'stage_0_2_final_closure_20261012_final_r1');a=ap.parse_args()
    src=a.input_dir.resolve();out=a.output_dir.resolve()
    for line in (src/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest,name=line.split(maxsplit=1);assert sha(src/name.strip())==digest,name
    shutil.copytree(src,out)  # fails if destination exists
    audit=json.loads((out/'audit.json').read_text(encoding='utf-8'));audit['gate_candidate']='Not Submitted: physical evidence / quality criteria pending';audit['scientific_gate_passed']=False
    final_formal=[]
    saved=pd.read_parquet(out/'p2_formal_events.parquet')
    for path in sorted((T15/'states').glob('*.parquet')):
        source=path.stem.removeprefix('ngsim_');print('final interface verification',source,flush=True)
        current=extract_formal_source_events(pd.read_parquet(path));current['source']=source
        details,counts=audit_event_match(saved[saved.source.eq(source)],current,source,'P2_middle','final_code_vs_r4')
        assert counts['missing']==counts['added']==0
        assert not pd.DataFrame(details).filter(regex='_delta$').fillna(0).abs().gt(1e-8).any().any()
        assert current.exit_reason.tolist()==saved[saved.source.eq(source)].exit_reason.tolist()
        final_formal.append(counts)
    (out/'final_interface_reverification.json').write_text(json.dumps({'sources':final_formal,'implementation_sha256':sha(ROOT/'code/src/riskprop/formal_risk_measurement.py'),'note':'finite clock hardening was added during r4 process; final current implementation independently re-extracted all sources here'},indent=2),encoding='utf-8')
    s=pd.read_csv(out/'sampling_sensitivity.csv');edges=pd.read_parquet(out/'sampling_overlap_edges.parquet');summary=[]
    for (rule,step,phase),g in s.groupby(['rule','step_ms','phase_ms']):
        row={'rule':rule,'step_ms':int(step),'phase_ms':int(phase)}
        for k in ['sampled_rows','identity_continuous_span_s','reference_events','comparison_events','reference_retained','reference_disappeared','comparison_no_overlap','reference_split','comparison_merged']:row[k]=float(g[k].sum())
        row['reference_retention_fraction']=row['reference_retained']/row['reference_events'];summary.append(row)
    ss=pd.DataFrame(summary);ss.to_csv(out/'sampling_aggregate.csv',index=False)
    one=[]
    for keys,g in edges.groupby(['source','rule','phase_ms']):
        da=g.groupby('a').b.transform('nunique');db=g.groupby('b').a.transform('nunique');h=g[(da==1)&(db==1)]
        one.append({'source':keys[0],'rule':keys[1],'phase_ms':int(keys[2]),'one_to_one_pairs':len(h),'min_confirm_delta_s':float(h.confirm_delta_s.min()),'median_confirm_delta_s':float(h.confirm_delta_s.median()),'max_confirm_delta_s':float(h.confirm_delta_s.max()),'interpretation':'matched onset may change; not pure processing latency'})
    pd.DataFrame(one).to_csv(out/'sampling_one_to_one_confirmation.csv',index=False)
    kin=pd.read_csv(T23/'case_diagnostics.csv');kin.to_csv(out/'case_447_kinematic_geometry_evidence.csv',index=False)
    ex=pd.read_csv(out/'extreme_sensitivity.csv');risk=pd.read_csv(out/'rho_scale_sensitivity.csv');tau=pd.read_csv(out/'tau_recalculation.csv');p2=pd.read_csv(out/'p2_summary.csv');cases=pd.read_csv(out/'case_447_final_audit.csv')
    # Check every selected difference case independently of whether it belongs to 447.
    cases11=pd.read_csv(out/'cases11.csv');ev=pd.read_parquet(out/'p2_formal_events.parquet');checks=[]
    for source,g in cases11.groupby('source'):
        cols=['original_row_number','trajectory_id','leader_trajectory_id','time_s','ttc_s','drac_mps2','net_gap_m','closing_speed_mps','ttc_valid','frame_id','global_time_ms','leader_matched','identity_uncertain','leader_identity_uncertain','diagnostic_clock_anchor_ms']
        d=pd.read_parquet(T15/'states'/('ngsim_'+source+'.parquet'),columns=cols)
        for _,c in g.iterrows():
            found=d[d.original_row_number.eq(c.center_original_row_number)&d.trajectory_id.eq(c.trajectory_id)&d.leader_trajectory_id.eq(c.leader_trajectory_id)&np.isclose(d.time_s,c.center_time_s)]
            assert len(found)==1
            r=found.iloc[0];members=ev[ev.source.eq(source)&ev.trajectory_id.eq(c.trajectory_id)&ev.leader_trajectory_id.eq(c.leader_trajectory_id)]
            count=sum(int(c.center_original_row_number) in set(map(int,x)) for x in members.original_row_numbers)
            checks.append({'source':source,'center_original_row_number':int(c.center_original_row_number),'unique_center':True,'ttc_formula_pass':bool(np.isclose(r.ttc_s,r.net_gap_m/r.closing_speed_mps)),'drac_formula_pass':bool(np.isclose(r.drac_mps2,r.closing_speed_mps**2/(2*r.net_gap_m))),'p2_center_events':count,'reference_p2_center_events':int(c.P2_middle_center_event_count),'physical_truth_status':'Unverified','manual_judgement':''})
    pd.DataFrame(checks).to_csv(out/'case_11_final_audit.csv',index=False)
    assert all(x['p2_center_events']==x['reference_p2_center_events'] for x in checks)
    # An evidence matrix is a review submission, not a newly selected acceptance threshold.
    items=[
      ('研究范围与职责','06_DECISIONS:纵向代理/描述性校准','最新版PDF与决策核对','可用于四个批准来源的纵向跟驰描述性参考','paper_readonly_excerpts.txt','Agreed Research Design','不代表事故概率、总体安全或P2全局最优'),
      ('来源与封存完整性','批准的四个NGSIM来源；保留unknown','历史SHA与输入provenance核验',str(audit['historical_hash_mismatches'])+' 个封存哈希不一致','historical_sha256_audit.csv','Verified','Lankershim官方两个原始分源和物理身份仍未知'),
      ('正式风险连续性与积分','来源/时钟/双车身份/帧/时间/断点fail-closed','解析边界专项测试','完整固定分母；不跨缺口或首末外推；上下界合法','validation.json','Verified','仅为原语验证，不是实区域四格结果'),
      ('P2逐事件一致性','TTC<2s且首末跨度>=0.2s','独立全量重提取与历史逐成员/时刻/极值比较','4545；missing/added/时间/极值差异均0','event_equivalence_summary.csv','Verified','事件率不是独立个体概率'),
      ('P2在线确认与退出','实际观测确认；中断非解除','消息时间与确认一致；退出原因分类；构造测试','实际确认；原始/可靠/拒绝数量见诊断','p2_online_diagnostics.json','Verified','未建立消息去重；非本阶段阻断'),
      ('P1/P2/P3差异','批准的敏感性对照','完整作用域成员交叠图','1900/4545/8523；分裂/连接与确认差异已量化','rule_member_correspondence_summary.csv','Verified','不宣称某规则全局最优'),
      ('测量状态与转换','valid/not_applicable/invalid/not_measurable分开','5,706,252行全量计数与相邻边转换','缺失原因与来源比例、状态转换均保留','measurement_status_transitions.csv','Verified','状态转换权重是观测边时长，非缺测填补'),
      ('跟驰与闭合暴露','可靠相邻观测边；不重复末帧','独立时间权重重算','512043.2s / 208026.3s','exposure_denominators.csv','Verified','两种事件率仅diagnostic，尚无批准的正式发生率分母'),
      ('tau与rho现实参考','四源时间中位数的中间两源均值','独立端点时间加权中位数与三尺度分布','15.364279197080283s；tau/2、tau、2tau已量化','rho_scale_sensitivity.csv','Verified','条件闭合rho不是固定目标区域burden；来源异质'),
      ('采样语义公平检查','100/200ms及两个相位，不插值','200ms帧步2；完整100ms身份断点约束；保留观测阈值','P2:4545 -> 4155/4162；存在消失和连接','sampling_aggregate.csv','Verified','使用完整源序列约束身份，非纯200ms可观测性证明'),
      ('100到200ms迁移等价性','无已批准等价容差','成员、覆盖与确认量化','事件不等价；不能证明无偏迁移','sampling_one_to_one_confirmation.csv','Unverified','Stage0.5需原生200ms验证；不能强行通过'),
      ('447/48/11物理合理性','公式核对与运动学诊断不替代独立真值','既有447运动学/几何表+全量定位公式+11独立复查','447唯一定位；125运动学探索标记；48人工字段为空','case_447_kinematic_geometry_evidence.csv','Verified','标记无批准科学阈值；同源几何非独立证据'),
      ('独立物理真实性','需独立几何/视频/研究者复核','证据清点；人工模板保持空','Physical Truth Unverified；极端屏蔽改变P2为4370','manual_review_index.md','Blocked','研究者/数据持有人提供独立材料并完成复核，不伪造结论'),
      ('科学质量验收标准','06_DECISIONS:正式质量门槛未冻结','批准记录与实际证据比对','缺失/异常/采样差异可量化，容许范围未批准','gate_matrix.csv','Decision Required','研究者定义有限描述性适用范围与质量标准；Codex不得降低标准'),
      ('SUMO现实覆盖','Stage0.5职责','阶段边界核对','此阶段不执行','config.json','Not Applicable','后续Stage0.5单独验收'),
      ('目标区域/固定车辆/四格窗口','后续因果评价与协议冻结','配置空值与职责核对','原语验证完成，正式四格未配置/未运行','config.json','Not Applicable','不因此判定Stage0.2描述性校准失败'),
      ('论文版本一致性','最新版20261010 PDF；正文不修改','PDF与旧main.tex比较','PDF未锁定映射；旧tex仍线性/观测分母/求和','paper_version_conflict.md','Decision Required','研究者指定正式论文来源；停止论文相关逻辑改写'),
      ('最终科学Gate','不得自动写pass','审阅以上矩阵','未通过；可提交验收准备包，非Gate Pass Candidate','audit.json','Blocked','独立物理证据/质量裁决未完成；协议锁与StageI继续禁止')]
    matrix=pd.DataFrame(items,columns=['验收事项','预定标准/依据','验证方法','实际结果','证据路径','状态','剩余限制']);matrix.to_csv(out/'gate_matrix.csv',index=False)
    matrix.to_json(out/'gate_matrix.json',orient='records',force_ascii=False,indent=2)
    conflict="""# Paper version conflict — read-only

Documented Intent: AI_CONTEXT/06_DECISIONS.md approves exponential rho, full-window denominator, vehicle equal weighting and bounded missingness. Latest dated PDF paper/历史记录/20261010_YYS.pdf specifies the longitudinal proxy hierarchy and postpones the mapping/aggregation to Protocol Lock.

Actual Implementation: formal_risk_measurement.v2 implements the approved design; the historical linear metric remains isolated. paper/主论文/main.tex:378-405 still describes linear threshold risk, observed-time denominator and summation over vehicles.

Evidence: latest PDF SHA in audit/provenance, readonly extracts; git-tracked main.tex:378-405.

Affected Files: paper/主论文/main.tex; paper/历史记录/20261010_YYS.pdf; AI_CONTEXT/06_DECISIONS.md.

Conflict: current TeX and latest PDF/design are not synchronized. The latest PDF leaves mapping to the lock, rather than contradicting the agreed exponential design. The paper term 'not equivalent to zero risk' refers to indicators/states; whether a reliably out-of-region or reliably not-applicable state contributes zero is governed by the approved contribution rule.

Status: Awaiting Researcher Decision. Researcher identifies the canonical manuscript/version and resolves text later; no manuscript modified, no measurement definition changed. This is not a computational failure of Stage 0.2.
"""
    (out/'paper_version_conflict.md').write_text(conflict,encoding='utf-8')
    p2s=ss[ss.rule.eq('P2_middle')]
    totals=ex.groupby('rule')[['reference_events','comparison_events','reference_disappeared','reference_split']].sum()
    report=f"""# Stage 0.2 综合收口与科学验收准备（2026-10-12）

## 当前结论
四个已批准来源的测量工程、独立逐事件复算、暴露/状态/采样/极端敏感性证据已经集中收口。可以提交研究者审阅本验收准备包，但**不是 Gate Pass Candidate**，未写入正式 Gate pass。现有事实支持受限的“基于 NGSIM 的纵向跟驰风险代理指标与描述性现实校准”，不证明物理真值、事故预测或跨采样率迁移。正式质量门槛尚未批准，独立物理真实性仍 Unverified；必要科学裁决由研究者作出。

完整产物：{out.relative_to(ROOT).as_posix()}；不可覆盖复制输入 r4，原始 r1/r2/r3/r4 均保留。manifest/SHA256SUMS覆盖本包；输入哈希与历史封存核查在provenance/historical_sha256_audit。只读取四源任务1.5状态与已封存校准案例；未访问locked holdout，未创建Protocol Lock，未启动Stage I。GitHub自动CI未启用。

## 正式测量加固
formal_risk_measurement.v2：连续性必须有完整来源、诊断时钟、双车身份、可靠布尔证据、时间与帧步一致性及无当前进入边断点；缺证据fail-closed。来源范围内原始行号唯一，多来源相同行号不混淆；确认函数审计所有成员（包括确认后成员），取第一个实际达到跨度的观测。消息最早触发时间等于确认时间，raw/rejected不授权消息。退出仅对下一帧可靠同车辆对TTC越阈值报告observed_threshold_exit；身份切换/缺测/断点保留unknown，末观测右删失。成员末时刻不等于安全解除时刻。

固定窗口使用左端观测值乘可靠区间实际裁剪时长；不在首帧前/末帧后外推、不跨缺口、拒绝重复时间/非法贡献上下界，不缩小分母。空间归属可靠性与测量可靠性独立。车辆等权及DID以解析数值和16个区间角点复核。完整可观测窗口的二值暴露乘条件rho均值等价性由解析测试确认；含未知时只能给界。历史0.1s工程提取器和旧线性指标未改。NGSIM校准rho采用既定可靠闭合边端点各0.05s权重（梯形）；这与固定窗口原语左值积分用途不同，不宣称任意离散积分完全相同。

## P2事件、暴露与三层现实参考
{markdown(p2.drop(columns=['exit_reason_counts']))}

P2=4,545，来源作用域唯一后车=2,512、唯一车辆对=3,072，不能把这些量当作相互等价。P1/P2/P3=1,900/4,545/8,523。独立100ms实现与Task2.5.1逐事件来源/双车身份/成员/首末/确认/帧数/TTC最小/DRAC最大比较，missing=added=metric differences=0。全部确认时间来自真实观测；P2确认延迟中位0.2s。跨规则分裂/连接与时间差详见rule_member_correspondence_summary.csv；完整逐成员审计event_member_time_comparison.csv。

可靠跟驰观测边512,043.2s，可靠闭合边208,026.3s；两种边互不混为分母，端点权重之和等于区间时长，不加末帧覆盖。每源率同时以这两种分母诊断计算，均标记非已批准正式发生率。基础层见measurement_status/missing_reason_counts/measurement_status_transitions与exposure_denominators；连续层见rho_scale_sensitivity；事件层见p2_formal_events与在线诊断。状态转换仅计同来源/轨迹/时钟且相邻真实帧，断点不跨接。

## tau、异常比例与连续风险
{markdown(tau[['source','closing_time_s','ttc_weighted_median_s','time_weighted_median_screened_s']])}

tau独立复算={audit['tau_s']:.15f}s，与批准值一致（差<1e-12）。四源tau下条件rho均值0.438476/0.337249/0.352553/0.382906；tau/2为0.288730/0.183972/0.194961/0.220376，2tau为0.581885/0.503373/0.521956/0.550690。P50/P95/P99与积分完整表已封存；这是闭合条件分布，不是正式固定区域burden。来源异质性实质存在，不能代表总体交通或直接推到SUMO。

5,706,252状态中有效闭合2,211,378。Lankershim missing/invalid分别23.6929%/4.7201%；US101 missing4.1302–5.0297%、invalid0.1283–0.1620%。非闭合not_applicable独立保留，missing不补零；详细原因和转换在机器表。缺失的风险不可识别，不能从可观测闭合样本推断缺失无偏。旧rho报告数字与本轮严格边权结果略异，旧结果为历史口径，当前边权重以本包为准；不重写历史。

## 100/200ms采样敏感性
{markdown(p2s)}

200ms使用Frame_ID步长2、Global_Time步长200ms、两个anchor相位0/100ms，持续条件仍为真实首末时间；不沿用100ms固定帧数，也不插值风险。100ms完整身份/观测断点用于限制抽稀连接，而被丢弃帧的TTC不被补回。这是**有完整源诊断约束的抽稀试验**，不是仅凭200ms序列可重建100ms连续性。

P2两相位消失373/366，连接17/17，无分裂；200ms存在相位100的1个无100ms合格事件重叠的事件，来源为短事件连接后满足时长。保留4,172/4,179个原100ms事件（多个原事件可连接到一个采样事件），不能拿4155/4162直接计算保留率。负确认差主要源于连接或观测onset改变，非提前知道未来；一对一确认变化另表sampling_one_to_one_confirmation，不把多对一时间差称作纯确认延迟。可评价身份连续边覆盖100ms=512043.2s、两相位200ms=509975.4/509968.6s。采样率不等价，适用范围保留为100ms NGSIM描述性校准；原生200ms SUMO在Stage0.5单独验证。

## 极端与物理合理性
447固定案例重新定位447/447；399个有效闭合中心TTC/DRAC按净间距/闭合速度重算一致，48个非适用中心保留NA，不将其算成公式通过。源内独立匹配447/447为历史证据，来源/长度/净间距与几何残差仍来自同一NGSIM测量体系，非独立物理真实性。case_447_kinematic_geometry_evidence保留每案例轨迹断点、位置-速度/速度-加速度最大差、几何残差、风险段、可靠性与适用性。125/447有既定探索运动学标记（四源60/40/8/17），无批准物理容差，不能判定125个错误；采样病例不是总体异常率。段边界最终修复后的多帧连续298、单帧3、间歇0、边界25、无极端121，均为诊断分类。48重点复核四源各12个，人工判断保持为空；11关键差异案例独立复查中心、公式和P2归属，不依赖其是否在447内。Lankershim原始行31245保留。

极端联合屏蔽（TTC<0.5s或DRAC>10m/s²或gap<1m）仅为既有诊断条件：P2 4545→4370，原事件181消失、6分裂，净数减少175（3.8504%）；P1 1900→1682，P3 8523→8380。来源分布、确认变化与成员保留见extreme_sensitivity。重分段屏蔽后的tau下条件rho均值0.435828/0.336455/0.351531/0.382003，说明连续均值变化小于事件成员变化，但不说明被屏蔽事件无科学影响。筛选后中位数仅诊断，**不重选tau、不改变正式规则**。

复核优先级在case_447_final_audit：P2成员且有运动学/极端标记优先1，其余48/11优先2，其余3；每例给出是否进入主P2参考。人工入口manual_review_index指向已封存48/24/11图册与空白模板。不能凭同源字段重算或图册宣称物理真实；独立视频/几何数据缺失，Physical Truth Unverified。

## 最少科学阻断项与责任
1. 独立物理证据/真实人工审阅缺失：极端诊断屏蔽影响181个原P2事件，不能排除主风险参考受伪差影响。研究者/数据持有人提供独立视频或几何材料，并完成优先1与重点48/关键11审阅；如确实不可得，由研究者明确裁决受限描述性使用的证据边界。Codex可整理和复算，不能签真人结论或代替独立真值。
2. 正式质量标准与有限适用域未批准：来源缺失率、异常比例及采样不等价已量化，何种证据足以验收属科研裁决。研究者需批准描述性校准的验收依据、是否将正式发生率作为必须终点及相应分母、100ms范围和迁移限制。Codex不得自选阈值/降低标准。迁移等价性不是Stage0.2描述性校准自动硬阻断，SUMO覆盖、区域/车辆/四格窗口属后续阶段。

论文版本冲突另行记录Documented Intent/Actual Implementation/Evidence/Affected Files/Conflict/Status，见paper_version_conflict.md：最新版PDF留待锁定映射，旧main.tex仍为旧线性指标。研究者指定最终论文入口；不自行修改论文或科研逻辑。不是Stage0.5/四格配置缺失造成Stage0.2必然失败。

## 历史一致性与验证
Task2.3的5880对5381差异已由Task2.4解释为不可比持续时间/连续性，非当前未解决事件数冲突；Task2.5–2.5.2的P2 Proposal描述是当时历史状态，已被2026-10-11批准设计取代；0.1s工程5381不替代正式P2 4545。Task2.2早期段首漏计已由r9修复。既有raw/失败/uncertain产物均保留；不覆盖历史报告。Context Consistency Check同步当前快照、模块/数据流/实验/已知问题、注册表/阶段/结果索引。

专项、全量pytest、compileall、严格文档与便携证据检查结果见validation.json。封存后仅read-only verify；新验证记录使用新目录，不覆盖本包。用户既有paper删除/移动和$stage未提交目录未清理、未纳入提交；因此原工作区require-clean预期受阻，在纯Git克隆运行strict-git --require-clean完成项目提交验证。

## 验收矩阵
{markdown(matrix)}
"""
    (out/'report.md').write_text(report,encoding='utf-8')
    for filename in ['audit.json','config.json','provenance.json']:
        obj=json.loads((out/filename).read_text(encoding='utf-8'));obj['review_package_parent']=src.relative_to(ROOT).as_posix()
        if filename=='audit.json':obj.update(audit);obj['key_difference_cases_verified']=len(checks);obj['gate_matrix_status_counts']=matrix['状态'].value_counts().to_dict()
        if filename=='provenance.json':obj['finalizer_sha256']=sha(Path(__file__));obj['finalized_utc']=datetime.now(UTC).isoformat();obj['additional_inputs']={str(p.relative_to(ROOT)):sha(p) for p in [T23/'case_diagnostics.csv',T252/'key_difference_cases.csv',ROOT/'paper/主论文/main.tex',ROOT/'AI_CONTEXT/06_DECISIONS.md']}
        (out/filename).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # validation.json must be written from actual commands before seal, not inferred.
    print(out)

if __name__=='__main__':main()
