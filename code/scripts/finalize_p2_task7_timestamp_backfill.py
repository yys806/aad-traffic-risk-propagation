"""Versioned report, factual indexes and portable evidence for timestamp backfill."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import backfill_p2_task7_source_timestamps as b
from finalize_p2_task7 import registry_with_preserved_layout

ROOT=b.ROOT;OUT=b.OUTPUT;E=b.EVIDENCE
SCRIPTS=['code/scripts/backfill_p2_task7_source_timestamps.py','code/scripts/verify_p2_task7_timestamp_backfill.py','code/scripts/finalize_p2_task7_timestamp_backfill.py']
TEST='code/tests/test_p2_task7_timestamp_backfill.py'
STAGE='Formal A=0，独立Qualified=0，F0/总体TR-TP Unknown；Stage0.5 CLOSED_WITH_LIMITATIONS；Stage0.6 PRE_LOCK_PACKAGE_COMPLETE_WITH_BLOCKERS；Protocol Lock BLOCKED；StageI READY_ENGINEERING_ONLY；Stage1.1 NOT_AUTHORIZED。'

def write(rel,text):
    p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.rstrip()+chr(10),encoding='utf-8',newline=chr(10))

def table(header,rr):return chr(10).join(['| '+' | '.join(header)+' |','| '+' | '.join('---' for _ in header)+' |']+['| '+' | '.join(str(x) for x in r)+' |' for r in rr])

def report():
    r=b.s.load(OUT/'results/summary.json');v=b.s.load(OUT/'audit/independent_verification.json')
    groups=table(['密度','条件','计划单位','Potential','旧Observed','修正Observed','Qualified'],[[x[k] for k in ['density','condition','planned','Potential','old_Observed','corrected_Observed','Qualified_count']] for x in b.rows(OUT/'results/group_counts.csv')])
    text=f'''# P2 Task7 — 源事件时间记录历史回溯修正报告

Task ID：`{b.TASK}`。Researcher Approved：全部575条完成轨迹。状态：**COMPLETED / HISTORICAL_DERIVED_EVIDENCE_ONLY**。

这是独立更正附录，不覆盖[Task7最终报告](P2_TASK7_FINAL_REPORT.md)、[原协议](P2_TASK7_EXPERIMENT_PROTOCOL.md)、原始359/47/0、原audit/truth/detector，也不是新实验或独立验证。统一定义仍为[Task6 v0.4、27项](../definitions/README.md)。

## 1. 原实现与版本核查

原executor在实际干预后同时要求`v < pre_source−1e−6`及`abs(v−getSpeedWithoutTraCI)>1e−6`才记录source onset。SUMO原生减速度约束期间，真实速度/加速度已改变，两速度读数仍可相同，因此记录延后；不是源命令未执行。

源码：run_p2_task7_parameter_experiment.py原记录条件；原W1–W9与Observed汇总位于finalize_p2_task7.py，而不是detector评价函数。原运行provenance Git基线cb520f8，Task7交付8f7739f，Task8交付及本次回溯基线c65c3d4；实际字节版本以manifest/source SHA及执行快照为准。原manifest保留当时truth v1，实际冻结truth v2仍以audit/truth_freeze.json为准，本任务不改两者。

Task8已给同一批raw的119诊断；本任务先冻结规则，再处理所有576计划单位，通过逐单位和独立标量实现复核，而非把119设为筛选目标。源码、原始输入、报告及全部Task7输出共{r['input_integrity_after']['protected_files']}个保护文件在运行前后哈希一致。

## 2. 冻结修正规则与适用边界

复用Task8 `physical_source_interval()`原样：实际命令执行时间`t_exec`必须由audit和同车slowDown命令记录核对。设`a_pre_min=min a_source(t), 10≤t≤t_exec+1e−9`，`v_ref`为命令执行时最近的源车读回速度；取首个`t>t_exec+1e−9`且`a_source(t)<a_pre_min−1e−6`、`v_source(t)<v_ref−1e−6`的采样时间`t_sig`，记录`I_source*=[t_exec,t_sig]`。1e−6沿用Task8数值比较规则，不用于放宽W6。

只读取实际受干预车辆自身的t/v/a，不读取目标响应或标签来选时间；native读回值另存用于审计，不再要求其与实际速度不同。无签名、缺源状态或无实际执行证据均Unknown。N0没有干预，明确Not Applicable；N1实际/指定源均为lane1 decoy，但没有指定源至lane0目标链；A0实际干预s0、指定源decoy，二者分别记录，不因s0减速而认定指定decoy传播。

该区间是当前完整SUMO模型内的操作性源时间证据。即使本批宽度均.05s，也不是最早任意物理变化、外部时钟、车辆模型或现实交通绝对误差证书。未建立签名的条件不发明替代判据。

## 3. 全量回溯结果

576计划单位逐条对应：575完成，1原启动失败`{r['failed_units'][0]}`保持零帧/Unknown；没有补跑或换seed。503条有实际源干预的完成轨迹均建立签名区间；72条N0为Not Applicable；Unknown仅原启动失败1条。

503个可比较源区间中：288个原区间两端均比修正区间晚1.75s，215个不变。实际命令记录均30.00s，新签名上界均30.05s；延迟288个来自P21、P22、N1、A0，各72个，旧区间[31.75,31.80]改为[30.00,30.05]。P11/P12/Plocal共215完成源区间原本即[30.00,30.05]。原truth中source onset字段仍保留旧值；消费者必须按unit_id及raw/audit/truth SHA显式联结本次版本化overlay，不能静默改写历史truth或audit。

全量表`source_time_comparison.csv`保存实际执行时间、实际/指定源ID、新旧区间、端点差、状态/原因、源前加速度范围、签名帧速度/加速度/native及三个原文件SHA256。N1/A0不进入指定源连通传播分母。

## 4. W6与路径重新计算

主判据严格保持`U_parent < L_response`，没有舍入或放宽。额外每端时间误差e=.05/.2s用`U_parent+e < L_response−e`；e=0是主结果。缺区间保留Unknown_missing_interval，区间接触/重叠为Unknown_overlap，明确反向区间单列Not_ordered_reverse；未通过W6不意味着已证明不存在物理传播。

Observed口径：原source_ok、原固定Micro状态阳性、原终端实体路径全部W6通过。直接保留原micro_witness_levels中的逐跳响应区间与实体连接，只替换第一跳的source parent interval；中间车辆必须沿用同一个原响应段。Task8 witness()用于同口径交叉核对W1/W2/W3/W7，完整575条身份/leader/native/gap质量保持原约束，没有最近邻补链。

| W6比较口径 | 原通过→仍通过 | 原未通过→通过 | 原通过→未通过 | 修正后仍Unknown | 已知反向→仍反向 | 分母 |
|---|---|---|---|---|---|---|
| 原终端路径全部跳，主e=0 | 428 | 72 | 0 | 0 | 0 | 500跳 /119条既有终端路径 |
| 全359个指定源适用run全部followers，50s响应支持 | 2553 | 96 | 0 | 12288 | 0 | 14937跳 |

以上是配对派生证据计数，跳数不是独立样本量；全部来自同一575条历史轨迹。两种口径在e=0/.05/.2均得到相同计数。完整原终端路径由47条通过变为119条，新增72条分别为Medium P22、High P21、High P22各24。

全hop额外96个改善比终端路径72多24，来自Medium P21首跳：第一跳时序可通过，但原固定Region内Micro truth没有达到原阳性/终端条件，仍不能计Observed；没有修改Region、时间窗或a*/b*。12288个Unknown均因原a1b1响应区间缺失，不能当作Negative，更不代表无微小物理影响。

原reaction_clock_evidence只在rep0/23使用46s响应上限，共{r['historical_reaction_rows_reproduced']}行；本任务逐行复现旧值并保存修正比较，原表不覆盖。它与Observed原终端路径50s随访口径分开，不能混合统计。新的全量all_hop表及path表分别保存三个e的逐跳结果和转变。

## 5. Witness统计与Task8复现

| 指标 | 原历史口径 | 本次时间更正overlay |
|---|---|---|
| Potential | 359 | {r['Potential']} |
| Observed | 47 | {r['corrected_Observed']} |
| Qualified已建立数量 | 0 | 0 |
| 指定源qualification Unknown | 360（含原失败1） | 360 |
| Micro any-source状态阳性 | 167 | 167，不改原标签 |

{groups}

Task8保留的575个逐单位诊断与本次回溯完全一致；Task8 helper重算与直接保留原路径的Observed计算也一致，scope_discrepancies为空。独立核验器不调用Task8向量签名或candidate detector，用标量扫描源状态及原响应跨度重算：Potential={v['independent_Potential']}、Observed={v['independent_Observed']}、Qualified count=0。119只适用于同一有限Task7指定源候选/终端路径证据，既不是新119个独立样本，也不是独立Qualified source→cohort Witness。

W8继续Unknown：时间先后和实际leader不能排除原生随机减速、共同原因等。原W8和Qualified空值逐单位保留，W9路径实体/响应段可连接不等于完整来源资格。未因修正时钟提升任何Qualified。

## 6. 对科研结论的实际影响与剩余问题

纠正了指定源首跳时间日志导致的72条保守拒绝，增强的是有限候选路径的时间顺序证据。原1728条truth v2标签及哈希、三层原状态阳性分布、全部detector/参数评价和曲线均不变；没有调用truth生成器或detector评价器，没有选择新参数，a1/b1不变。

Independent V仍未执行、V seeds0，Task8决策仍NOT_EXECUTED_TRUTH_SUPPORT_INSUFFICIENT；η=1%/5%桥接仍Not established/Unknown。独立来源归属、真实最早物理onset及delay/clock/model误差界、F0和正式总体推断没有获得新增支持；参数不冻结。

后续使用应同时引用原报告与本附录，显式标注原记录359/47/0和本次overlay359/119/0。原executor作为历史输入不改，未来如需新运行须在另行授权范围内处理其实现，不能默认复用其旧source onset作为校正值。本任务到此结束，不自动追加历史回溯或交通实验。

{STAGE}

## 7. 验证与交付

影响范围：三个隔离离线脚本、定向测试、报告、上下文/证据账本和索引；无共享生产逻辑或正式科研接口变更。定向测试涵盖native相等仍减速、N0 NA、失败Unknown、实际decoy列、缺签名、目标响应独立性、严格接触/重叠及持续跨度；连同直接依赖Task7/Task8测试共29项通过。未运行无关全量pytest或compileall。

独立标量复核575完成/1失败、1728标签哈希、44811行全hop时钟比较、6000行原代表时钟表及全部原终端响应段。4170个保护文件SHA在前后及独立验证中一致；原Task7报告、audit、truth、detector、历史统计及Task8诊断字节不改。新增SUMO=0、seed=0、V=0；所有结果仍属于历史派生审计。

本地完整输出：`code/outputs/calibration/p2_task7_timestamp_backfill_20261102_v1/`。[便携证据入口](../../../evidence/research/P2_TASK7_SOURCE_TIMESTAMP_BACKFILL_20261102/README.md)含逐单位/逐跳派生表、冻结manifest、输入hash、源快照、独立验证及SHA256SUMS，不复制原始轨迹/日志/图片/密封键。文档strict-git、evidence exporter/verify、Git字节检查的实际记录见同目录verification_record.json。Git baseline与dirty/source hash区别于最终交付commit。
'''
    write(b.REPORT,text)

def prepend(rel,text):
    p=ROOT/rel;old=p.read_text(encoding='utf-8-sig')
    if '## Current — P2 Task7 source timestamp backfill' in old or '## P2 Task7 source timestamp backfill — 2026-11-02' in old:raise RuntimeError('Already synchronized '+rel)
    old=old.replace('## Current — P2 Task8','## Historical — P2 Task8',1)
    write(rel,text+chr(10)*2+old)

def sync():
    fact='研究者已授权全575完成轨迹源时间回溯，576计划逐条保留（1原失败Unknown、72 N0 Not Applicable、503实际干预签名成立）；288区间提前1.75s。原359/47/0不改，本次版本化派生overlay359/119/0；Task8的119已独立逐单位复现。W8/Qualified未知资格不升级，1728原标签、原audit/detector/参数、V与双η结论不改；新增SUMO/seed/V均0。'
    for rel in ['AI_CONTEXT/00_PROJECT_STATE.md','AI_CONTEXT/05_EXPERIMENTS.md','AI_CONTEXT/06_DECISIONS.md','AI_CONTEXT/07_KNOWN_ISSUES.md','AI_CONTEXT/08_CHANGELOG.md']:
        prepend(rel,'## Current — P2 Task7 source timestamp backfill (2026-11-02)'+chr(10)*2+fact+chr(10)*2+'旧Task8“是否回溯待研究者”是历史状态，已被本次明确授权及完成记录接续；原executor仅作为历史字节输入保留，未改旧运行或触发新实验。'+chr(10)*2+'统一定义仍[27项v0.4](../docs/research/definitions/README.md)。'+STAGE+chr(10)*2+'[独立更正报告](../'+b.REPORT+')')
    prepend('AI_CONTEXT/04_MODULE_MAP.md','## P2 Task7 source timestamp backfill — 2026-11-02'+chr(10)*2+'隔离离线工具：'+', '.join(Path(p).name for p in SCRIPTS)+'。复用Task8 source-only签名与witness，独立标量源/响应/W6核验；无SUMO调用、truth重建或生产接口变化。')
    for rel in ['docs/RESEARCH_STATUS.md','docs/PROJECT_INDEX.md','docs/RESULTS_INDEX.md','docs/CHANGELOG.md','PROJECT_CONTEXT.md']:
        link=b.REPORT.removeprefix('docs/') if rel.startswith('docs/') else b.REPORT
        prepend(rel,'## P2 Task7 source timestamp backfill — 2026-11-02'+chr(10)*2+fact+chr(10)*2+STAGE+chr(10)*2+'[独立更正附录]('+link+')；原Task7/Task8报告保留历史字节，本任务无新实验或独立样本。')
    for rel,text in {
        'docs/research/definitions/README.md':'[Task7源时间独立更正附录](../P2/P2_TASK7_SOURCE_TIMESTAMP_BACKFILL_REPORT.md)：仅修正历史时间overlay及W6派生证据；27定义/v0.4、a1b1、W1–W9、正式参数与阶段不变。',
        'docs/research/definitions/EVIDENCE_AND_ASSUMPTION_LEDGER.md':'''历史Task8/E68“Unknown回溯决定”保持当时记录，现由以下授权及运行事实接续，不改科学定义。

| ID | 类型/状态 | 证据与限制 |
|---|---|---|
| E71 | Agreed | 研究者明确批准Task7全部575完成轨迹源时间历史回溯；保留原raw/truth/audit/报告 |
| E72 | Verified工程/Fact派生证据 | 503实际干预签名成立、72 N0 NA、1失败Unknown；288区间提前1.75s；原359/47/0保留，更正overlay359/119/0；无新独立样本 |
| E73 | Unknown保持 | W8与来源资格未建立，Qualified仍0；物理绝对时钟/模型误差、V及双η桥接不由历史时间修正获得证书 |

来源：[独立更正报告](../P2/P2_TASK7_SOURCE_TIMESTAMP_BACKFILL_REPORT.md)、对应冻结manifest、逐跳W6及4170保护文件SHA/1728标签哈希独立验证。'''
    }.items():
        p=ROOT/rel;write(rel,p.read_text(encoding='utf-8-sig')+chr(10)*2+'## Task7源时间历史回溯（2026-11-02，独立更正附录）'+chr(10)*2+text)
    p=ROOT/'docs/PROJECT_REGISTRY.json';before=p.read_text(encoding='utf-8-sig');registry=json.loads(before)
    registry['current'].update({'active_research_task':'P2-TASK7 source timestamp backfill complete; original history retained; overlay359/119/0',
        'why_now':'Researcher authorized all575 completed traces. Source-only retrospective correction and independent W6 verification complete; no new experiment.',
        'p2_task7_timestamp_backfill_status':'COMPLETED_HISTORICAL_DERIVED_EVIDENCE_ONLY','p2_task7_timestamp_backfill_report':b.REPORT,
        'p2_task7_corrected_overlay_Observed':119,'p2_task7_historical_Observed_unchanged':47})
    registry['research_audits']['p2_task7_timestamp_backfill']={'date':'2026-11-02','task_id':b.TASK,'status':'completed_historical_derived_evidence_only',
        'report':b.REPORT,'output':OUT.relative_to(ROOT).as_posix(),'evidence':E.relative_to(ROOT).as_posix(),'planned_units':576,'completed_traces_reprocessed':575,
        'original_startup_failure_retained':1,'source_intervals_established':503,'N0_not_applicable':72,'changed_intervals':288,'original_counts':[359,47,0],
        'corrected_overlay_counts':[359,119,0],'qualification_unknown':360,'independent_Task8_diagnostic_reproduced':True,
        'original_1728_labels_unchanged':True,'all_original_reports_and_outputs_unchanged':True,'new_SUMO_runs':0,'new_seeds':0,'new_V_runs':0,
        'formal_stage_gate_unchanged':True,'scientific_claim_eligible':False,'new_task_started':False}
    for rel in [b.REPORT,*SCRIPTS,TEST,E.relative_to(ROOT).as_posix()+'/README.md']:
        if rel not in registry['canonical_entries']:registry['canonical_entries'].append(rel)
    p.write_text(registry_with_preserved_layout(before,registry),encoding='utf-8',newline=chr(10))

def seal_package():
    E.mkdir(parents=True,exist_ok=True)
    for rel in ['manifest.json','audit/input_hashes.json','audit/integrity_verification.json','audit/independent_verification.json']:
        shutil.copy2(OUT/rel,E/Path(rel).name)
    for p in (OUT/'results').iterdir():
        if p.is_file():shutil.copy2(p,E/p.name)
    (E/'execution_sources').mkdir(exist_ok=True)
    for p in (OUT/'snapshots').iterdir():shutil.copy2(p,E/'execution_sources'/p.name)
    bound=[*SCRIPTS,TEST,b.REPORT,'.gitattributes','docs/research/definitions/EVIDENCE_AND_ASSUMPTION_LEDGER.md']
    b.s.dump(E/'delivery_sources.json',{'baseline_git_sha':b.s.load(OUT/'manifest.json')['git_sha'],'sha256':{rel:b.s.m.sha(ROOT/rel) for rel in bound},'final_commit':'derive live; no self-referential hash'})
    write(E.relative_to(ROOT).as_posix()+'/README.md','''# Task7 source timestamp backfill — portable evidence

Researcher Approved, all575 completed original trajectories. [Independent correction report](../../../docs/research/P2/P2_TASK7_SOURCE_TIMESTAMP_BACKFILL_REPORT.md). Original359/47/0 retained; corrected overlay359/119/0, W8 Unknown and Qualified0. Same historical data, no new independent sample, SUMO, seed or V.

manifest freezes rules before calculation; source_time_comparison records all576 planned units with72 N0 Not Applicable and1 preserved failure Unknown. witness_comparison and path_W6_comparison retain original response segments and compare corrected first-hop time. all_hop_W6_comparison includes all359 applicable specified-source runs and e=0/.05/.2; historical_reaction_clock_reproduction separately retains the original rep0/23 horizon46s scope. These are derived evidence tables, never traffic-frame data or independent n.

input_hashes covers4170 protected original files, including every Task7 output and original reports/code. Original1728 label hashes checked against truth freeze. independent_verification uses scalar source and response extraction. delivery_sources and execution_sources separate runtime bytes from final delivery Git HEAD. verification_record records actual tests/docs/evidence/Git-byte checks. SHA256SUMS covers package except itself.

Full original raw remains at code/outputs/calibration/p2_task7_20261102_v2/, new overlay at code/outputs/calibration/p2_task7_timestamp_backfill_20261102_v1/. No raw trajectory, log, image or sealed key copied here. Formal definitionsv0.4/27, Stage/Gate, detector/truth/parameters, Independent V and eta1%/5% conclusions unchanged. No automatic follow-up experiment.
''')
    (E/'SHA256SUMS').write_text(''.join(b.s.m.sha(p)+'  '+p.relative_to(E).as_posix()+chr(10) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'),encoding='utf-8',newline=chr(10))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['report','sync','package'],required=True);args=p.parse_args()
    {'report':report,'sync':sync,'package':seal_package}[args.phase]();print(json.dumps({'phase':args.phase,'status':'COMPLETE'}))
