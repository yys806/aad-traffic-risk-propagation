"""Build review documents from verified bytes; never changes admission objects."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1]
AUD = OUT.relative_to(ROOT).as_posix()
V6 = 'evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6'
SMOKE = 'docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/authorized-execution'
PREP = 'docs/audits/stage_0_5_linux_native_v4/prepared-20261026-r5'
E='RESOLVABLE_FROM_EXISTING_EVIDENCE'
R='RESEARCHER_DECISION_REQUIRED'
D='REQUIRES_FUTURE_DYNAMIC_EXPERIMENT'
A='ENGINEERING_AMBIGUITY_REQUIRES_REVIEW'


def load(name): return json.loads((ROOT/name).read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,value):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,sort_keys=True); stream.write('\n')


def main():
    facts=load(AUD+'/static_facts.json')
    p=load(V6+'/proposal.json')
    files=load(AUD+'/verified_inventory.json')['files']
    issues=[]
    def issue(ident, question, fact, evidence, code, classes, uncertainty, options, validation, next_step, decision, status, priority='normal'):
        for name in evidence:
            assert (ROOT/name).is_file(), name
            files[name]=sha(ROOT/name)
        locations=[]
        for name,fn in code:
            location=next(x for x in facts['source_locations'][name] if x['function']==fn)
            locations.append(dict(path=name,function=fn,line=location['line'],end_line=location['end_line']))
            files[name]=sha(ROOT/name)
        opts=[dict(option_id=f'{ident}-O{i}',option=o[0],solves=o[1],introduced_assumption=o[2],
                   scientific_implications=o[3],affected_measurements=o[4]) for i,o in enumerate(options,1)]
        issues.append(dict(issue_id=ident,question=question,current_fact=fact,evidence_paths=evidence,
            evidence_sha256={n:files[n] for n in evidence},code_locations=locations,observation=fact,
            interpretation='Interpretation: '+next_step,remaining_uncertainty=uncertainty,classification=classes,
            available_options=opts,scientific_implications=[o['scientific_implications'] for o in opts],
            required_validation=validation,recommended_next_step=dict(kind='Research Proposal' if decision else 'Engineering review recommendation',
                owner='Researcher' if decision else 'Research engineer',action=next_step),
            researcher_decision_required=decision,current_status=status,priority=priority))
    issue('AUTH-01','工程accepted=true是否等于科研授权？',
        '不同对象、不同语义。证书schema aad.native-integration-acceptance.v1及proposal.isolation为工程前提；profile四false、proposal三false及admission三false保持。独立精确approval仍必需。',
        [V6+'/proposal.json',V6+'/admission_profile.json',V6+'/integration_acceptance.json',AUD+'/state_field_readers.json'],
        [('code/scripts/stage_0_5_native_capsule_v4.py','authorization_reasons'),('code/scripts/stage_0_5_research_ledger.py','reserve')],
        [E], '没有观察到工程true单独放行科研的路径；JSON决策来源的真实性另见AUTH-02。',
        [('保留分层语义','避免误把工程资格当科研批准','未来执行仍需独立精确授权','不产生科研结论','所有下游状态展示')],
        ['无数据反例：缺任一精确字段/三审批/三政策即拒绝；5项纯测试已执行。'],
        '审批文书和界面同时展示engineering_ready与research_authorization_pending，禁止仅展示accepted。',False,'RESOLVED_SCOPE_EXPLAINED')
    issue('ENG-01','工程ready与accepted_build=false是否一致？',
        'technical_preflight_v4不检查policy.binding.accepted_build；固定B00 policy仍false。V4 execute绕过legacy/profile显示锁，reserve和running在Linux controller verify_live_context之前；该函数从policy false重建isolation并拒绝capsule_build_not_accepted。',
        [V6+'/technical_preflight.json',PREP+'/research_policy.json',AUD+'/static_facts.json'],
        [('code/scripts/stage_0_5_linux_execution_v4.py','technical_preflight_v4'),('code/scripts/stage_0_5_linux_execution_v4.py','_execute_authorized'),('code/scripts/stage_0_5_native_capsule_v4.py','verify_live_context'),('code/scripts/stage_0_5_execution_v2.py','execute')],
        [A], '属fail-closed而非已证实未授权绕过；但未来即使有合法approval也可能先消耗预约/attempt后拒绝，ready不能解释为可直接执行。未启动验证。',
        [('暂停可执行审批，先另行工程修复','消除预检与执行策略不一致','新代码/策略需重新绑定与验收','科学定义保持；旧精确SHA不能覆盖变更后的代码/策略','运行预约、attempt与native lock'),
         ('仅审议科学政策，暂不授权执行','保留研究者讨论进度','承认可执行链尚有已知拒绝','不产生科研数据','审批范围')],
        ['另任务在无数据环境测试policy false在任何reserve/attempt前拒绝；policy变更后需新精确包，旧包不可翻锁。',
         '同时测试profile true/false、legacy lock与v4上下文，不得用修改ready结果掩盖。'],
        '高优先级：暂缓执行授权，单独修复并重绑一致的预检/执行锁；本轮不改。',False,'OPEN_ENGINEERING_REVIEW', 'high')
    issue('ENG-02','碰撞接口不可用时是否安全拒绝？',
        'collect_snapshot异常保留collision_count=None，但run_observation_loop用(frame.get(collision_count) or 0)>0；finish完整性仅检查六类身份API，不要求collision计数可用。',
        ['code/scripts/stage_0_5_identity_observation.py','code/scripts/stage_0_5_execution_v2.py','code/scripts/stage_0_5_acceptance_v3.py'],
        [('code/scripts/stage_0_5_identity_observation.py','collect_snapshot'),('code/scripts/stage_0_5_execution_v2.py','run_observation_loop'),('code/scripts/stage_0_5_identity_observation.py','finish')],
        [A], '静态缺失证据路径存在；未声称历史SMOKE碰撞getter失败，也未声称发生了碰撞。',
        [('先明确缺失即拒绝并另任务修复','避免把不可观测当零碰撞','要求getter每步可用','保留零事故判断的证据边界','运行早停与最终验收')],
        ['无数据mock：getter不存在、抛错、中途缺失、恢复后仍拒绝；None不得补零；原始异常/hash保留。'],
        '高优先级：在科研执行前完成缺失即拒绝的观测守卫审查及新软件绑定。',False,'OPEN_ENGINEERING_REVIEW','high')
    issue('ENG-03','summary、身份核算完整与全车实际插入是否混同？',
        'verify_receipt对summary仅验根标签与封存hash；assess_capsule重建TripInfo/FCD/原生事件，但不将summary inserted/ended/discarded逐时对账。合法pending可保持identity_accounting_complete=true；B00非R臂也没有全车实际出发阈值。',
        ['code/scripts/stage_0_5_acceptance_v3.py','code/scripts/stage_0_5_native_capsule_v4.py',AUD+'/validation/pure-guard-counterexamples/record.json'],
        [('code/scripts/stage_0_5_native_capsule_v4.py','verify_receipt'),('code/scripts/stage_0_5_acceptance_v3.py','assess_capsule'),('code/scripts/stage_0_5_acceptance_v3.py','input_acceptance')],
        [A,R,D], '不能由accounted推导1150全部插入、117初态全在t0或summary已做身份对账；这些动态事实目前unknown。',
        [('接受有限时域下明确pending/删失，但预先定义初态资格','区分合法未出发与未知丢失','研究者接受此目标总体','供给和风险支持随实际进入变化，必须逐车披露','初态117与非初态1033、分母'),
         ('要求特定初态/分组实际插入时限，缺失即失败','使实际初态更接近研究目标','需要明确科学阈值，不得工程师自造','可能阻断候选；改变接受总体需新精确绑定','插入时刻、状态支持')],
        ['研究者明确117初态与晚计划车辆的时限/删失政策；工程另任务补summary与事件/TripInfo计数交叉核算及冲突反例。'],
        '先确认实际插入与删失的科学接受条件，再另任务实现缺失/冲突拒绝；不得删异常车或事后改窗。',True,'AWAITING_RESEARCHER_AND_ENGINEERING_REVIEW','high')
    issue('GIT-01','dirty快照、347绑定及未提交helper是否破坏唯一绑定？',
        'proposal记录生成时735bab0与dirty=true；正式基线753b666。347历史文件复算通过；38源均匹配正式Git按.gitattributes检出字节，其中12生产源闭包匹配。formal_risk_measurement.py的Git原对象LF与绑定CRLF不同，由既定eol=crlf解释。helper未在12源闭包中，不参与native控制；软件验证记录另行绑定helper。',
        [V6+'/scientific_diff.json',V6+'/proposal.json','.gitattributes',AUD+'/static_facts.json','code/scripts/prepare_stage_0_5_b00_admission_v6.py'],
        [('code/scripts/stage_0_5_linux_execution_v4.py','technical_preflight_v4'),('code/scripts/stage_0_5_native_capsule_v4.py','verify_live_context')],
        [E,A], '精确SHA定义提案内容和传递哈希依赖，不认证人类来源，也不保证未来运行时无漂移；审查新报告不在原生闭包。原始Git blob不能不经属性还原就冒充执行字节。',
        [('保留历史生成快照及正式提交复核','保持证据不变','按.gitattributes复现执行源字节','不改变科学定义','源闭包/可复现性')],
        ['347文件、38源、原始blob/属性检出双哈希复算；旧audit manifest在753b666匹配，新增context后按历史Git版本解释。'],
        '把生成时点与提交后证据明确分列，继续每次实际执行前哈希检查。',False,'RESOLVED_WITH_SCOPE_LIMIT')
    issue('INIT-01','DS38应保留、恢复原始初态还是另版修改？',
        '1150=117初态+1033非初态；117全声明t0。仅38个原始departSpeed数值10改为max；79初态及全部非初态属性/顺序不变，后者声明0.3至419.6s。i0007保持15.23。完整38辆before/after及79不变ID见static_facts。',
        [AUD+'/static_facts.json','evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v2/initialization_static_audit.json',V6+'/proposal.json'],
        [('code/scripts/prepare_stage_0_5_admission_v3.py','prepare')], [E,R,D],
        'max允许原生插入规则选值，不证明实际10m/s或t0成功；改变的是被研究的初态政策，动态有效性未证明。',
        [('保留DS38，仅B00诊断','先核验已声明政策可运行与支持','接受38辆原速度约束变化','四臂需同DS38；不能与原初态直接归因供给效应','早期交通状态、插入和后续风险'),
         ('恢复原始数值速度另提案','回到原始声明初态','接受原始速度不相容可能再次失败','当前proposal失效；历史失败不能当控制组成功','初始化、全链支持'),
         ('另版统一安全初态政策','系统处理包含i0007的相容性','需研究者定义修改范围','改变研究对象，全部后续对照需共同重建','所有初态与恢复过程')],
        ['静态差异已解决；获授权后逐车原生depart/TripInfo速度/位置/车道/时延与FCD/事件一致；原生错误立即失败。'],
        'Research Proposal：先审议DS38作为有限初始化诊断的可接受性，禁止把max等同实际固定速度。',True,'AWAITING_RESEARCHER_DECISION')
    issue('INPUT-01','文件级保真是否足以批准交通场景？',
        'network与原policy-A输入完全相同；routes只38速度变化；sumocfg只新增TripInfo路径及unfinished/undeparted三选项。B00未加匝道脉冲，五条main_2恒10；合成SMOKE输入从未被当成B00输入。',
        [AUD+'/static_facts.json',V6+'/proposal.json','evidence/results/RES-STAGE-0.5-DEPART-SPEED-CANDIDATE-V1/review_proposal.json'],
        [('code/scripts/stage_0_5_admission_v3.py','validate_config'),('code/scripts/stage_0_5_acceptance_v3.py','input_acceptance')],
        [E,R], '输入来源是已登记的历史准备场景，不等于逐字节原NGSIM；未证明场景代表性/科学有效性。未显式SUMO默认仍依赖绑定1.26实现。',
        [('批准精确文件及DS38变换的文件保真范围','明确执行输入口径','场景合理性单列待判','可检查执行符合声明，但不能推出现实有效性','输入保真验收'),
         ('要求另版场景审议','在运行前解决研究对象不匹配','需要明确新的科研需求','重绑后再审；不能修改当前输入哈希','场景级解释')],
        ['静态XML差异与三SHA已复算；实际运行后还须只读输入/hash/实际插入验收。'],
        '分别签署文件级保真与场景选择，勿把技术证书当科学同意。',True,'AWAITING_RESEARCHER_DECISION')
    issue('MEASURE-01','D1/C6及18格测量契约能回答什么？',
        '当前v4协调器实际调用measure_completed_capsule->assess_capsule->C6物理状态->local_d1_measurement；TTC<2、连续跨度>=0.2，onset归属，E为可靠同前后身份/前车/原生车道100ms整边。窗口[120,390)、lane1-5、y[150,350)；9x2格30s/100m，参考min states5710、min D1_E562.8，均通过静态支持。',
        ['code/src/riskprop/stage_0_5_d1_measurement.py','code/src/riskprop/stage_0_5_state_support.py',next(iter(p['measurement_reference_sha256'])),AUD+'/static_facts.json'],
        [('code/scripts/stage_0_5_linux_execution_v4.py','_execute_authorized'),('code/scripts/stage_0_5_acceptance_v3.py','assess_capsule'),('code/src/riskprop/stage_0_5_d1_measurement.py','local_d1_measurement')],
        [E,R,D], '实现与引用支持可核验，但B00实际每格>=10状态/正D1/右端点、完整事件/身份均未知。相同公式不保证真实/模拟可观测前车和break处理等价。',
        [('按现有局部可观测D1合同审议','固定分母与onset口径','接受同车道部分支持，非全网真实前车','可报告限定域风险率，不能宣布正式仿真等价','N/E、18单元、缺失份额'),
         ('要求更强前车/支持定义另版','解决目标测量范围不足','需要新科学合同及验证','当前候选不可复用批准','事件、暴露及跨域比较')],
        ['未来FCD4200帧0..419.9、原生8401快照0..420、8400控制、18格含右端点、TripInfo及hash链重建全部通过才具工程测量资格。'],
        'Research Proposal：批准前明确有限可观测合同；零暴露为不可评价，零事件不能证明无风险。',True,'AWAITING_RESEARCHER_DECISION')
    issue('WINDOW-01','保留[120,390)还是另选初始化清空窗口？',
        'candidate固定A窗18格；历史C7的0750最后局部初态记录130.5s，A含106条/10.6veh-s。候选B共同起点180s、14格，改变支持且P2已接触；不具盲验证资格。',
        ['docs/STAGE_0_5_C6_C7_OFFLINE_DECISION_2026-10-25.md',V6+'/proposal.json'],
        [('code/scripts/stage_0_5_admission_v3.py','validate_config')], [R,D],
        '历史初态清空不保证DS38新运行清空；即便零初态记录，间接影响/稳态仍未证明。',
        [('保留A窗并披露初态残留','保留270s/18格共同支持','接受有限初始化影响','不能声称稳态；不能删除初态车后称同一总体','早期风险与支持'),
         ('另版B窗/时序','要求预声明清空规则','接受210s/14格及恢复期缩短','必须新输入/参考/提案，不得运行后切窗','测量目标与操纵时序')],
        ['研究者在任何运行前选窗；新运行逐车初态局部last_FCD与全轨迹支持核对，不由风险值选窗。'],
        '明确选择A的有限时域目标或另版B；当前包不允许事后改窗。',True,'AWAITING_RESEARCHER_DECISION')
    issue('DYNAMIC-01','i0007、i0063与discard归属能否静态解决？',
        '封存日志t0明确i0007慢下游速度不相容；t180明确i0063出发速度过高，随后TraCI关闭。DS38含i0063，i0007不变。aggregate discarded=1不能判定具体ID。',
        ['code/outputs/formal/calibration/stage_0_5_interaction_diagnostics_v1/ID1_SUPPLY_0750/worker_console.log',AUD+'/static_facts.json','docs/plans/2026-10-26-stage-0-5-ready-to-admit-v3.md'],
        [('code/scripts/stage_0_5_execution_v2.py','step'),('code/scripts/stage_0_5_identity_observation.py','observe_tripinfo')],
        [E,R,D], '新B00无180s供给降速，不能把历史i0063失败直接推为B00必败；i0007实际插入/动态相容及discard身份仍unknown。',
        [('保留i0007并接受失败可发生的诊断目标','测试当前声明是否相容','不允许删除该车或容忍原生Error','失败只得失败证据，不复用为B00对照','身份、实际插入、输入资格'),
         ('先另版处理i0007','减少已知声明相容风险','由研究者定义变换','改变初态；四臂及精确授权全部重绑','初始化与可比性')],
        ['逐车计划/loaded/pending/departed/active/on-road/arrival/TripInfo/FCD/explicit discard证据；Error、Unknown、时钟冲突、teleport/collision即失败，不从FCD缺失推断discard。'],
        'Research Proposal：先决定是否接受该有限诊断风险；不能凭SMOKE或DS38静态差异保证成功。',True,'AWAITING_RESEARCHER_DECISION_AND_DYNAMIC_EVIDENCE')
    issue('DYNAMIC-02','实际插入和交互相容性未来如何验收？',
        '本轮零原生执行。现有代码可记录0.05s事件与0.1sFCD、TripInfo插入字段，实际动态值不存在；summary聚合不替代逐车证据。',
        [V6+'/proposal.json','code/scripts/stage_0_5_identity_observation.py','code/scripts/stage_0_5_linux_controller_v4.py'],
        [('code/scripts/stage_0_5_identity_observation.py','collect_snapshot'),('code/scripts/stage_0_5_identity_observation.py','observe_tripinfo'),('code/scripts/stage_0_5_linux_controller_v4.py','main')],
        [D,R], '无法静态确认实际depart、速度、排队、碰撞、残留、逐格暴露与时延；工程SMOKE只有1车3s。',
        [('获得独立精确授权后只运行B00一次','取得初始化和支持资格证据','先解决ENG-01/02/03并冻结科学接受政策','成功仅有限诊断；失败保留，不自动换ID/重试','所有实际测量支持'),
         ('暂缓实验','等待政策或守卫修复','接受继续未知','无新科学结论','研究进度')],
        ['事前清单：完整原始stdout/stderr/Error、控制/时钟、8401身份事件、逐车TripInfo/FCD、summary对账、18格支持、资源/隔离、清理和SHA；失败/中断也封存，不删异常车、不改窗。'],
        '把逐车动态验收与失败归档清单随未来新授权冻结，当前不执行。',True,'AWAITING_FUTURE_AUTHORIZATION')
    issue('IDENTIFY-01','B00及后续四臂可以识别什么？',
        'B00无供给/匝道干预，是0750/seed20261201/DS38初始化及支持诊断；单臂单seed没有处理差异。计划S10、R01、SR11未授权。',
        [V6+'/proposal.json','docs/plans/2026-10-26-stage-0-5-ready-to-admit-v3.md','docs/STAGE_0_5_C6_C7_OFFLINE_DECISION_2026-10-25.md'],
        [('code/scripts/stage_0_5_admission_v3.py','factor_routes')], [R,D],
        '初始化/供给人数与实际插入/有效支持/测量修复/随机过程均可能混杂；四臂有限差分也不是AAD机制因果证明。',
        [('先B00资格，再同政策同seed四臂逐次审议','先验证可比的参照','不把B00通过当全部设计批准','可形成S10-B00、R01-B00、SR11-R01-S10+B00条件性对比','事件N、暴露E、共同支持、状态响应'),
         ('先完善机制与重复设计','为更强科学主张配对照','研究者明确估计量/多seed/消融和敏感性','需要成本与授权；不得挑seed或事后筛支持','外推/随机不确定性/机制区分')],
        ['后续Research Proposal：共同初态政策/匹配身份供给与支持；多预声明seed重复、窗口/初始化敏感性；若主张传播机制，另设传播/通信机制对照、相同局部状态与时延证据。'],
        '先确定B00只回答可运行/可观测问题，更强推断单独提出研究设计和Gate准则。',True,'AWAITING_RESEARCHER_DECISION')
    issue('HISTORY-01','C1-C5/C6-C7及Not Accepted哪些仍影响B00？',
        '当前B00调用新C6/D1/offset100而非旧runner点分母或错位分块。C3旧时距标签不在B00主验收；C4支持时点更正可解释；C5旧包络判据不进入本次八检查。历史结果不自动升级，C7与物理部分可观测/科学等价仍未决。历史POLICY-A-VALIDATION-SCOPE-01仍Not Accepted。',
        ['docs/STAGE_0_5_WP1_EVIDENCE_AUDIT.md','docs/STAGE_0_5_C6_C7_OFFLINE_DECISION_2026-10-25.md','AI_CONTEXT/06_DECISIONS.md',V6+'/integration_acceptance.json'],
        [('code/scripts/stage_0_5_acceptance_v3.py','assess_capsule')], [E,R],
        '本轮没有重算旧原始表/所有历史实验，引用其封存结论并验证相关当前调用；不重新裁定历史事故。',
        [('保留历史资格标签并限定当前参考','避免历史诊断数当正式真值','研究者单独审议跨域等价','新SMOKE/软件测试不能消除历史科学不一致','历史比较与Gate')],
        ['保留全部历史字节；当前直接证据与历史观察分列；不修改Gate/δ/h/B/Stage1.1。'],
        '仅将相关旧问题作为当前科学接受的边界，不机械复验无关旧实验。',False,'RESOLVED_RELEVANCE_WITH_PENDING_SCIENCE')
    issue('AUTH-02','精确proposal SHA能否认证研究者本人批准？',
        'authorization_reasons核对JSON精确task/run/hash、非空decision_record、三审批及三政策。没有签名/独立身份认证；本地受信调用者负责将真实人类决定写入授权记录。工程证书不能完成该人类来源认证。',
        ['code/scripts/stage_0_5_native_capsule_v4.py','code/scripts/run_stage_0_5_admission_v3.py'],
        [('code/scripts/stage_0_5_native_capsule_v4.py','authorization_reasons'),('code/scripts/run_stage_0_5_admission_v3.py','main')], [A,R],
        '不是已证实外部攻击或当前未授权运行；准确边界是字段检查依赖受信操作者，不等于密码学人类批准。',
        [('保留受信研究者决定+审计记录流程','明确当前信任边界','执行者不得制造批准','只对精确SHA/范围有效','未来授权来源'),
         ('另任务增加独立验证来源','减少误写JSON的权限歧义','研究者决定所需认证强度','新守卫需新测试/闭包，不改科学定义','授权可审计性')],
        ['未来授权必须引用真实研究者消息及精确新SHA；测试工程证书/旧SMOKE授权/空决定/错run均不能替代。'],
        '由研究者确认审批来源与执行责任边界；本轮不创建任何授权envelope。',True,'AWAITING_TRUST_BOUNDARY_REVIEW')
    issue('ENV-01','历史实时检查能否证明未来启动环境仍有效？',
        '本轮复核8031文件运行时清单的封存绑定及原生回执；不重启WSL、不重新执行live技术预检。现有ready=true是先前时点实时证据，不能保证未来资源/内核/路径持续不变。',
        [V6+'/technical_preflight.json',PREP+'/runtime_manifest.json','docs/audits/stage_0_5_ready_to_admit_v3/candidate-v6/validation_record.json'],
        [('code/scripts/stage_0_5_linux_execution_v4.py','inspect_linux'),('code/scripts/stage_0_5_linux_execution_v4.py','linux_preflight')], [E,D],
        '当前Linux实时内核/资源/8031依赖文件未在本轮重新读取，明确unverified；本任务只读证据审查不要求宣称新的实时通过。',
        [('未来授权后在启动前实时复核','防止陈旧资源/运行时证据','仍保持原阈值与隔离要求','不赋予科研资格','启动前实际环境')],
        ['未来授权任务重验C5GiB/D14GiB/内存4GiB、WSL余量、namespace/Landlock/seccomp/cgroup/systemd与精确依赖；失败即停。'],
        '无需重跑SMOKE；待科学决定及工程风险解决后，只做当次必要实时检查。',False,'HISTORICAL_PASS_CURRENT_LIVE_UNVERIFIED')
    write('review_matrix.json',dict(schema='aad.scientific-admission-review-matrix.v1',task_id='AAD-0.5-B00-SCIENTIFIC-ADMISSION-REVIEW-01',
        baseline_commit=facts['baseline']['HEAD'],candidate_proposal_sha256=sha(ROOT/V6/'proposal.json'),
        status='RESEARCH_APPROVAL_PENDING',issues=issues,total_issues=len(issues)))
    write('decision_packet.json',dict(schema='aad.scientific-admission-decision-packet.v1',status='RESEARCH_APPROVAL_PENDING',
        recommendation='Research Proposal: 暂缓执行授权；先解决ENG-01/02/03的工程/观测条件，同时逐项审议科学政策。',
        candidate_sha256=sha(ROOT/V6/'proposal.json'),total_issues=len(issues),
        decision_required_count=sum(i['researcher_decision_required'] for i in issues),
        issues=[{k:i[k] for k in ['issue_id','question','current_fact','classification','available_options','scientific_implications',
            'remaining_uncertainty','required_validation','recommended_next_step','researcher_decision_required','current_status','priority','evidence_paths','evidence_sha256']} for i in issues],
        decisions_recorded=[],execution_authorized=False))
    readers=load(AUD+'/state_field_readers.json')['readers']
    write('authorization_boundary_audit.json',dict(schema='aad.scientific-authorization-boundary-audit.v1',
        status='REVIEW_COMPLETE_WITH_OPEN_RISKS',objects=[
            dict(path=V6+'/integration_acceptance.json',schema='aad.native-integration-acceptance.v1',field='accepted_for_new_task',value=True,meaning='engineering input/resource/runtime chain eligibility'),
            dict(path=V6+'/admission_profile.json',field='accepted_for_new_task',value=False,meaning='research admission display; not directly read by v4 execute'),
            dict(path=V6+'/admission_profile.json',field='native_launch_locked',value=True,meaning='profile display; actual v4 kernel lock is policy.accepted_build'),
            dict(path=PREP+'/research_policy.json',field='binding.accepted_build',value=False,meaning='enforced inside native controller before SUMO version process')],
        readers=[dict(**r,role=('active V4 guard/coordinator' if Path(r['path']).name in ['stage_0_5_linux_execution_v4.py','stage_0_5_native_capsule_v4.py','stage_0_5_linux_isolation.py','stage_0_5_research_ledger.py','stage_0_5_execution_v2.py','run_stage_0_5_admission_v3.py'] else 'preparation/verifier or legacy path; not automatic v4 research authority')) for r in readers],
        active_call_path=['run_stage_0_5_admission_v3.main (v4 skips legacy lock)',
            'ExecutionAdapter.execute -> execute_research -> authorization_reasons -> technical_preflight_v4',
            '_execute_authorized -> ResearchLedger.reserve -> envelope transfer -> running -> launch_linux',
            'verify_envelope -> linux_preflight -> exclusive launch_attempt -> Linux broker payload',
            'broker context accepted_build from immutable policy -> controller.main -> verify_live_context',
            'authorization_reasons(proposal_stub accepted_build=false) -> capsule_build_not_accepted before SUMO version'],
        research_flag_states=facts['protected_flags'],engineering_true_alone_authorizes=False,
        human_origin_cryptographically_authenticated=False,risks=[i for i in issues if i['issue_id'] in ['ENG-01','ENG-02','ENG-03','AUTH-02']],
        guard_changes_performed=False,simulation_calls=0,real_TraCI_connections=0,new_research_trajectories=0))
    extra=['AI_CONTEXT/00_PROJECT_STATE.md','AI_CONTEXT/05_EXPERIMENTS.md','AI_CONTEXT/07_KNOWN_ISSUES.md','AI_CONTEXT/08_CHANGELOG.md',
        'docs/PROJECT_REGISTRY.json','docs/RESEARCH_STATUS.md','docs/PROJECT_INDEX.md','PROJECT_CONTEXT.md','AGENTS.md',
        'docs/audits/stage_0_5_ready_to_admit_v3/execution_events.jsonl',
        'docs/audits/stage_0_5_ready_to_admit_v3/candidate-v6/audit_manifest.json','code/scripts/prepare_stage_0_5_b00_admission_v6.py',
        'docs/STAGE_0_5_B00_ADMISSION_V6_2026-10-27.md','docs/STAGE_0_5_V4_SMOKE_3_CONTINUATION_2026-10-26.md',
        'docs/STAGE_0_5_V2_IDENTITY_CONTRACT.md']
    for name in extra: files[name]=sha(ROOT/name)
    # These context hashes are the reviewed baseline, not the later dated additions.
    write('evidence_manifest.json',dict(schema='aad.scientific-review-evidence-manifest.v1',
        baseline_commit=facts['baseline']['HEAD'],hash_semantics='Actual reviewed workspace bytes; Git attributes apply. Baseline AI_CONTEXT hashes refer to pre-review-increment version; later additions are covered by audit_manifest.',
        files=[dict(path=n,sha256=h,verification_status='verified_bytes',
            purpose=('Historical 347-file closure and archived manifests/receipts' if n in load(AUD+'/verified_inventory.json')['files'] else 'Specific review claim, code reader, historical context or audit evidence'),
            portable=(ROOT/n).is_file() and not n.startswith('code/outputs/'),
            scope='File/hash evidence, not independent scientific acceptance') for n,h in sorted(files.items())],
        not_reverified=['Current live Linux runtime files/resources/kernel: unverified in this task',
            'Historical raw trajectories/locked holdout: not opened or remeasured',
            'Actual B00 insertion/measurement/dynamics: no run'],
        missing_evidence=['B00 production receipt, per-vehicle runtime identities, actual 18-cell support: absent because not executed']))
    print(json.dumps(dict(status='REVIEW_COMPLETE_WITH_OPEN_RISKS',issues=len(issues),
        researcher_decisions=sum(i['researcher_decision_required'] for i in issues)),ensure_ascii=True))


if __name__=='__main__': main()
