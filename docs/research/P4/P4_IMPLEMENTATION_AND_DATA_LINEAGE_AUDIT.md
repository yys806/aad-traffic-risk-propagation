# P4 现有实现与数据血缘审计

Task: AAD-P4-TASK1-20261103。日期：2026-11-03。状态：Verified source audit / documented limitations。

基线HEAD：f772c860968fd5901894bcfed5475b32fd027b0e，main，开始工作区干净。源码/config/历史证据优先于文档推测。源行号以下均为该基线；[机器审计](p4_implementation_audit.json)、[追溯表](p4_measurement_traceability.csv)及便携source_manifest保存版本/hash。

## 1. 实际调用链与能力矩阵

| 模块/精确位置 | 实际输入/输出与调用 | 能力状态 | 边界 |
|---|---|---|---|
| formal_risk_measurement.py:22–54 | P2 config、正TTC→exp(−TTC/τ) | 已实现/Verified | 事件阈值与rho分开；defaults未冻结 |
| 同文件:171–186 contribution_bounds | 空间/测量质量→点界/rho | 已实现/Verified | 不负责证明region或reliability输入真实 |
| 同文件:194–230 integrate_fixed_window | 带身份/连续性字段的单车序列→固定窗积分/均值界 | 已实现/有适用限制 | 无几何clip/完整名单；no-leader连续性保守 |
| 同文件:233–251 average / did_interval | 输入积分列表→等均值；四格界→差界 | 数值原语已实现 | 无名单、run、同窗核验，无统计估计器 |
| 同文件:269–298 continuity_is_valid | scope/leader/clock/frame/quality→bool | 已实现 | 要可靠matched leader；不直接验lane/region变更 |
| stage_0_5_sumo.py:1042–1162 | 原生状态→ttc_s/drac/status/reason | 已实现 | validate_state_contract仅列存在；唯一键须上游 |
| 同文件:1226起 following_link_is_valid | 同lane/leader/步长条件→链路可用性 | 已实现，stage特定 | 不是全区域风险观测器 |
| 同文件:1620–1694 build_sumo_formal_source_frame | 状态/measurement→Formal source字段 | 已实现，stage特定 | leader按incarnation/ms关联；leader侧drop_duplicates保留首行，需独立重复检查 |
| 同文件:2255起 VehicleIdentityTracker | 实际出现/离开→incarnation | 通用stage能力已实现 | 不代表P7已采用其全部重入能力 |
| stage_i_mechanism.py:84–149 | 两速度轨迹+调用者起点→工程差异候选 | 部分实现 | 非完整Action测量/效应估计 |
| 同文件:152–205 build_joint_timeline | 旧事件表→8列联合时间轴 | 工程排序已实现 | 不校验P3全图，不生成因果结论 |
| prelock_metrics.py:13–89 | valid-time暴露/PET/解析测试真值 | 辅助实现 | 不是Formal rho/Y；NaN一致性风险 |
| 同文件:125–154 first_sustained_divergence | 差序列/阈值/持续时间→起点 | 工程实现有缺陷 | 跨缺口、末点步长外延，见A01 |
| p7_sumo_integration.py:51–91 | TraCI read_state及existing_measurement_attachment | 真实状态与质量引用已实现 | 只调用compute_sumo_measurements，不调rho/积分/等车聚合 |
| p7_message_runtime.py:149–227 | 命令→getter→poststep执行/动作→risk附件 | 证据接线已实现 | 运动差异未在Action记录中直接判定；risk为run级Unknown |
| controller_evidence.py:54–118,364–374,614–625 | 版本化14类记录/时间/显式关联校验 | 正式v1接口已实现 | 不验证全部外部原始字节/区域计算语义/因果效应 |
| ngsim_risk_calibration.py:38–200 | 原始标准化+diagnostic trajectory身份→校准测量输入 | 高速跟驰参考 | 不是真实物理身份认证，不自动城市迁移 |
| pneuma_urban_kinematics.py:1–14,87–113 | 原顺序运动学/组成→分析frame/QC | 城市运动学 | 无可靠leader/TTC/DRAC/Formal风险；缺QC标志时有兼容默认clean风险 |

路径均为code/src/riskprop/，详见机器追溯表。限定范围的调用搜索显示：Formal contribution/integrate被若干既有validation/error-budget脚本使用；**在code/src与code/scripts未找到生产调用equal_vehicle_average**。这只是该代码范围的静态结论，不宣称不存在任何仓库外消费端。

实际P7链：read_state→LocalState→P7Runtime.observe→execution/action；run结束existing_measurement_attachment→compute_sumo_measurements→existing_measurement_states.csv→risk_attachment。Formal版本号作为附件元数据被引用，**不是调用Formal区域聚合的证明**。

## 2. 需要后续治理的具体发现

### A01 动作持续性会跨缺口，末点外延（Verified limitation）

位置：stage_i_mechanism.py:84–149 / prelock_metrics.py:125–154。精确inner merge只用vehicle_id/time_s；缺速度行被删；持续性函数以median(diff)作为末点支持，未检查max gap。例子[0,.1,10]和NaN中间点均可确认跨缺口差异；[0,.1,.2]可被算作.3s持续，超出实际观测跨度。

影响：first_action_change_time_s不可直接当科学T_U；不规则/缺失采样可假阳性。incarnation不参与merge可误配重入车辆。重复键产生many-to-many后在下游times strictly increasing检查报错，没有明确键错误分类。

建议：独立配对manifest、唯一键和clock验证、连续段累积、onset/confirmation分存，不外延末点；阈值/持续时间/对齐方法由研究者决定。**不在本任务修改核心函数。**

### R01 等车平均不是完整名单汇总（Verified limitation）

位置：formal_risk_measurement.py:233–241。只校验数值范围并除以输入行数，重复车辆、漏车、异窗或跨run可被外部调用者传入。例子两车(.2,[0,1])正确界[.1,.6]；漏掉未知车则函数返回.2且无错。

影响：缺少固定名单组装守卫时分母可因观测状况改变。建议上游强制C_e名单完整、唯一、同scope/window，显式补“未知结果记录”而非补零；最终聚合仍Task6/E61待决。生产event级assembler缺失，不能把原语当已部署区域Y。

### R02 时间连续性严格，但空间裁切未集成（Verified limitation）

位置：Formal194–230/269–298。仅对已证明同leader/clock/cadence的相邻对使用左值，no-leader/leader切换段保持未知。时间裁切不能决定空间出入边界，SUMO适配并未为P7提供合法region/window/cohort。

影响：点贡献可计算不代表全窗可点识别；未知上界可能很宽。跨region边界若不单独处理，左值保持可错误延长域内成员资格。建议界定空间clip和边界误差政策，保留未知；不能为缩窄界伪造continuity。

### R03 辅助TTC暴露的valid/NaN不一致（Verified limitation）

位置：prelock_metrics.py:13–33。valid=True、dt>0、TTC=NaN、collision=False时默认risk向量0，函数输出0，与“missing never zero”docstring意图不一致。

影响：若外部错误标valid，缺测可被隐藏为零暴露。该函数不是Formal贡献核心；建议后续输入一致性校验/明确缺测处理。当前完整缺测usable=False仍返回NaN，不能笼统说函数总把missing变零。此次只保存复现和建议。

### L01 P7风险附件只是质量引用（Verified limitation）

位置：p7_sumo_integration.py:70–91、p7_message_runtime.py:208–214。实际target-only状态→TTC/DRAC质量表，无rho/区域积分。leader incarnation用run:leader:entry1合成，适用于当前最小场景假设，非通用leader生命周期跟踪。P7目标退出正确记录，重入会错误终止，不支持多次incarnation实验。

影响：Risk1/Formal measurement_version不能代表正式风险效应或全区域覆盖。附件创建时刻是打包时间，不能作所有风险样本时间。建议保留原P3引用，增加外部state↔action↔execution↔risk及支持表，leader identity须来自真实tracker/明确有限适用假设。

### L02 P3图合法不保证测量支持一致（Verified scope boundary）

P3Action→Execution检查同vehicle，Risk→Action只检查run/pair/cell/block/assignment等通用scope，允许跨车区域汇总。此设计本身不是缺陷；P4应为Risk明确单车/区域级别、成员列表/角色、时空支持、measurement/config/hash，不能仅依时间相近连接。P3不改schema，明细放外部受哈希引用表。

## 3. P7 Task2.1历史结果的可用范围

只读复用[报告](../P7/P7_TASK2_1_FINAL_REPORT.md)和[便携验证](../../../evidence/research/P7_TASK2_1_20261103/validation.json)，不是新增运行或独立重复。唯一Enabled v2已通过工程验收，No Message/Disabled原基准未重跑。52次纳入、39命令、326执行、352 Action（351在场+1退出），首命令2.8s、首次实际差异2.9s、8.0s恢复上限。P7已有比较的全部351共同点、v/a差异只是ENGINEERING_DIAGNOSTIC_ONLY。

P3图2076记录VALID_WITH_UNKNOWNS；没有独立Safety符合D6。退出后的运动量null，不当漏测补零。Risk引用per-state TTC/质量、Formal范围未定，风险效应Unknown。v1的9m/s²异常/误报PASS及失败证据保持原字节，v2接受不覆盖该历史事实。

## 4. 数据、时钟与质量能力

| 来源 | 可复用能力 | 不具备/不可外推 | 本次使用 |
|---|---|---|---|
| NGSIM | 高速跟驰trajectory/leader、单位转换、TTC/风险校准参考 | 轨迹身份不是物理实体认证；噪声/缺口/leader切换；城市风险外推 | 源码和已有审计，不扫描原始数据 |
| pNEUMA | 城市速度/加速度/组成，原顺序dt质量诊断 | 当前无可靠leader、Formal TTC/DRAC风险；未清洗标志的默认不等QC已通过 | 源码/历史结果，只读 |
| SPMD | RV_RX接收状态连续性/通信可观测边界 | 不是逐包发送/接收分母、controller adoption或区域风险真值 | P3通信登记与P2已有审计，不读raw/holdout |
| SUMO | 模型内v/a/position/leader/gap、时间/step/phase读回 | 环境真实风险外部有效性；单target不覆盖区域 | 现有P7 capture和测试，不新启动 |

时间必须保留原生timestamp/unit/clock anchor、mapped lower/upper、step/phase/sequence、observed_at与available_at。不同源时钟不默认同步；重复同phase报错，不同phase合法；采样率不一致不能静默插值。leader/lane切换、身份断裂、退出、缺测、右删失均独立登记。空间映射应保留坐标系、边界约定及geometry hash。

## 5. 方法来源及阅读程度

优先复用[P2 Task5方法审计](../P2/P2_TASK5_LITERATURE_AND_METHOD_AUDIT.md)、P2 Task4相关审计及doc/literature-notes既有索引；无新论文导入、无无关指标扩展。

| 来源 | 当前核验程度 | 支持的有限用途 |
|---|---|---|
| FHWA SSAM manual 2008 / final report 2008，Zotero SLTMG63B / 9LCCTDGZ | 既有方法审计复用；本次只读本地API核元数据，未重新精读全文 | TTC/PET冲突定义依赖具体场景，不能构成AAD正式区域rho |
| Hall, Traffic Stream Characteristics，26RQQ7EE | P2已读章节结论复用；当前元数据核验，年份Unknown | 同域Edie-type D/V/A，支持/单位/采样边界 |
| Edie原始1963 | 原文仍未获得/未精读 | 不声称直接原始文献验证，现用Hall及源码范围 |
| 自然驾驶SSM评价，Q9NQASFD，DOI 10.1016/j.aap.2021.106403 | 本次只核元数据，未新读全文 | 仅保留后续适用域参考，不作新实证依据 |
| 既有NGSIM质量/不完整轨迹文献，7JHH37JY / B8J8W6P2 | 已有P2审计引用，本次不重新全文阅读 | 质量/QC与抽样覆盖边界，不据此选择新阈值 |

本次外部搜索未取得可审计的新全文，不以此声称新方法已验证。方法结论以实际源码、统一定义和既有有范围的审计为依据。未将TTC/DRAC/PET相关性当作独立证据，也未引入综合风险分数。

## 6. 验证覆盖与未实施事项

本次六个相关测试文件84 passed/0 failed/0 errors；另27项确定性语义复现全部通过。pytest运行期间审计钩子禁止任何subprocess启动，blocked_attempts=[]，新SUMO=0。P7历史143项不计入本次数量。未运行旧native启动测试、全仓pytest或compileall。

“复现通过”包括确认A01/R01/R03等限制，**不等于相关缺陷已修复**。生产控制器/风险算法/config/schema/历史实验不改。后续真正缺少：合格Action比较器、通用空间/连续性支持适配、固定名单区域组装器、规范化Action–Risk明细及正式Y/测量参数批准；本任务已给出可直接决策的契约，不再追加无关前置研究阶段。
