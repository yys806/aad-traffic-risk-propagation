# P2 Task3 校准方案（修订 v2，运行前登记）

日期：2026-11-02；状态：`CALIBRATION_ONLY / synthetic_measurement_verification`。
脚本：`code/scripts/run_p2_task3_calibration_only.py`。新输出：`code/outputs/calibration/p2_task3_20261102_v2/`。

## 1. 目的、分域和停止条件

比较三个速度状态聚合器的测量特性，验证持续时间、缺口和覆盖逻辑。合成面板不是交通动力学；不含消息链、真实路径或区域边界，不能验证AAD物理到达、Formal P2、F0或可迁移交通阈值。既有Task17–19不能提供这些标签。本节V2为合成测量；后续§6另行在运行前登记并执行独立B域SUMO校准，没有新正式确认性实验。

初版`p2_task3_20261102/`全部保留，补存原脚本和`SUPERSEDED_V1.json`。其持续条件多计一个采样间隔，且TP分类、基线与验证设计不充分；撤回其数值推荐。原手工重建日志不是捕获的stdout。v2不覆盖初版文件或原哈希表。

停止于预定网格完成、单元测试通过和测量敏感性可报告；不为获得时间优先性继续调参。无真实交通标签时，不输出“最优交通阈值”。

## 2. 输入与时间契约

固定20车；时间0–60s，已知注入onset=30s。每车基线为`[30-W,30)`均值，W=2/5/10s；监测从30s开始，基线样本不进入误报评价。基准速度约15m/s。主噪声独立高斯0.2m/s，另有0.5m/s和共同相关噪声压力条件。源前/后线性趋势单列；静态基线相对趋势偏离不能称为“扰动真值”。

三个聚合器：观测完整时的等车均值、median、超过单车0.5m/s下降的比例。比例阈值与m/s阈值分开。缺失时先报固定分母coverage，再报observed-subset statistic；该统计不自动代表全cohort，信息性缺失不作可识别承诺。

有效观测中stat>=theta，首个至末个合格样本的实际时间跨度至少h，相邻有效样本间隔不超过q。小缺口只有在q允许时连接，仍标记gap-bridged，不是已观测连续。显式低于阈值立即终止；低覆盖片段不补零。输出最后可靠阴性/首个阳性的onset区间、confirmation和缺口标记。没有可靠阴性时下界只能来自监测起点，属于边界/左删失，不虚构前一阴性。

注入检出须无先前误报、onset上界在注入段内、confirmation严格早于恢复；过早和恢复后报警分开。纯null窗口误报、有效检出、首次确认延迟、quality-unknown分别报告。单位测试另检查源前报警和恢复后报警分类。

## 3. 预定网格、种子和划分

场景：平稳null、趋势null、全体下降0.5/1m/s×持续0.8/3s、单车8m/s异常、半数车1m/s下降；另以1m/s×3s施加dt0.05/0.2s、噪声0.5、20%独立缺失、0.4s整体缺口、20%选择性永久失访、共同AR(1)噪声、0.02m/s²趋势。基准dt0.1s，共16场景。

主网格：mean/median阈值0.25/0.5/1m/s；比例阈值0.25/0.5/0.75；h0.5/1/2s；W5s；q=1.1dt；coverage门槛0.8。敏感性：中间阈值、h1s，分别改变W2/10s、q3.1dt/5.1dt、coverage1.0。所有数字仅压力测试网格，不是AAD推荐范围。

校准种子族202611020起；验证种子族202711020起。每场景每分区24次，共16×48面板；同面板复用给所有候选作配对比较。验证只运行一次，不根据验证重选配置。分区提供代理生成器内验证，不提供外部交通验证。

## 4. 评价与不确定性

逐配置逐场景报分母、误报率、检出率、条件平均/中位确认延迟、Unknown率、gap-bridged率及二项率Wilson95%区间。24次不能证明低误报目标；区间逐格而非同时带。候选共享输入，候选数量不算独立重复。至少比较三类聚合器；推荐基于测量目标与完整性，不按最早报警选指标。

## 5. 记录与验证

输出config、runs、summary、captured stdout/run log、provenance、脚本快照和SHA256SUMS。记录命令、环境、Git SHA和dirty状态、脚本/协议哈希。输出目录必须新建，存在则拒绝覆盖。定向测试和语法检查覆盖持续时间、缺口、coverage、onset、恢复后报警和分区。真实交通校准需先具备冻结的区域/cohort观测契约、独立路径和校准/验证标签。


## 6. 补充B域交通测量校准（运行前登记）

新增独立脚本run_p2_task3_sumo_b_calibration_only.py；输出code/outputs/calibration/p2_task3_sumo_b_20261102/。分类CALIBRATION_ONLY / controlled_B_sumo，禁止称Formal P2 A、随机no-message F0或现实真值。不读取历史原始大表/holdout，不修改正式配置。此补充是合成代理不足后的必要有界交通测量验证，不重跑Task17–19。

**目的与场景：** 独立5000m单车道直路、16车（source s0，native followers s1–s15）、无信号/换道/通信。Krauss域内参数显式记录：maxSpeed15m/s、accel2.6、decel4.5、length5m、minGap2.5m、tau1s、sigma0.3、step0.1s；这些是本次B域配置，不改变Formal参数，也不代表真实交通标定。车辆初始source位置1800m、每后车相隔30m、初速15m/s。SUMO安全模式保持默认，不关闭碰撞/速度安全机制。

**固定测量对象：** cohort预选s5–s10（N=6），region=[1300,2240]m，baseline=[25,30)s，监测[30,39]s。未按处理后状态挑车辆/窗口；记录出区和覆盖，若cohort出区则该段结构性Unknown，不用区域外速度替代。source在计划扰动时应位于region之外；实际位置不满足则记设计失败，不事后移动region。

**扰动与null：** 计划30s对source调用slowDown至12.5或10m/s，1s渐变；在31s以setSpeed保持source目标速度，在30+3或30+6s恢复至15m/s，1s渐变，恢复完成后setSpeed(-1)释放；这些setter仅作用source。保存计划、实际API执行、首次post-step运动学时刻/区间和执行失败；指令时间不是精确物理crossing。Null不发任何速度指令，native followers全程不受外部速度控制。检测标签是已知B域command condition；它不证明每个目标真的已受物理影响，测量检出率应称command-conditioned alarm fraction，而非物理真阳性率。

**网格/划分：** null及2强度×2持续=5条件；每条件校准6seed（202611020–202611025）、验证6seed（202711020–202711025），共60run；同seed跨条件共享处理前配置，但不据此声称有效逐事件反事实。每运行用V2相同42候选，W2/5/10s源前基线（附加窗口明确），速度mean/median/proportion，h/q/coverage网格不变。该规模只给本域范围和敏感性，不能确定低FPR数值。验证只一次，不根据验证扩场景/挑seed。

**评价：** 每个条件的window-level alarm fraction、null FPR及Wilson区间、first confirmation相对实际执行的delay、source/target运动学区间、身份/leader关系/道路位置连续性、collision/teleport/exit；全部保留。不能用命令有无当每个target-arrival的gold label，也不以earliest alarm选主指标。无消息只描述此域通信始终关闭，不等于F0的随机化参考总体。

**停止/环境：** 单次有界60run，碰撞/teleport/ID缺失/位置支持不满足则保留失败并停止该场景，不为制造arrival调参；任一系统性失败停止全部新run。预计原始输出<100MB；运行前记录D盘free，至少留1GB余量。版本、官方TraCI路径、命令、每run config/seed、日志、轨迹、Git+dirty、协议/源脚本SHA及SHA256SUMS完整记录。不扩展为仿真参数优化或正式实验。
