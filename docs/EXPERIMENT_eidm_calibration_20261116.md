# EIDM 标定实验结果：撞上源码硬限制

日期：2026-11-16。状态：`ENGINEERING_PILOT`。

## 一、做了什么

按研究者要求，把 EIDM 的人类驾驶员参数真正用起来，看能否复现真实近冲突。

1. 先从 SUMO 源码 `MSCFModel_EIDM.cpp` 取到全部 13 个参数与默认值
2. 用行为对比法确认参数写法（`<param key="cf.eidm.xxx">` **不生效且不报错**，必须写成 vType 的 XML 属性）
3. 12 个参数逐个验证生效（见 `eidm_attr_probe.py`）
4. 用 6 对含可信真实事件的轨迹做参数扫描，六组参数从默认到激进

## 二、参数扫描结果

| 参数组 | 仿真最小 TTC 中位 | 真实最小 TTC | 比值 | 事件数 |
|---|---|---|---|---|
| default（SUMO 默认） | 4.98 s | 0.261 s | 19.1 | 1 |
| salles2020（原论文值） | 4.98 s | 0.261 s | 19.1 | 1 |
| perception_mid | 4.59 s | 0.261 s | 17.6 | 1 |
| perception_high | 4.42 s | 0.261 s | 16.9 | 1 |
| **aggressive**（误差拉满） | **3.67 s** | 0.261 s | **14.0** | 1 |
| realtime_lag | 3.72 s | 0.261 s | 14.3 | 1 |

参数确实起作用了：从 4.98 压到 3.67，有效果。但**离真实的 0.261 还差 14 倍，事件数始终是 1**。

顺带一个发现：**Salles 2020 原论文的参数组与 SUMO 默认值几乎无差别**（4.98 对 4.98），说明默认值就是照论文设的。

## 三、根因：源码里写死的 3 米下限

查六组参数的仿真最小间距：

| 参数组 | 仿真最小间距 |
|---|---|
| default | 3.046 m |
| perception_high | 3.038 m |
| **aggressive** | **3.000 m** |
| realtime_lag | 3.140 m |

**全部卡在 3 米附近，aggressive 组正好等于 3.000。**

对照 SUMO 源码 `MSCFModel_EIDM.cpp` 第 44 行：

```c
#define EST_REAC_THRESHOLD 3. // under this threshold estimation, error and reaction time
                              // variables don't get taken into account
```

**含义：间距低于 3 米时，EIDM 直接忽略感知误差与反应时间，退回确定性行为。**

这是写死在源码里的常量，**不是可调参数**。所以：

- `sigmaerror` / `sigmagap` / `sigmaleader` / `treaction` 无论调多大，**在 3 米以下全部失效**
- 把 `minGap` 设成 0.5、`tau` 设成 0.7 也没用，因为下限来自 `EST_REAC_THRESHOLD` 而不是 `minGap`

## 四、而真实近冲突正发生在 3 米以下

六对真实轨迹的最小间距：0.79、1.07、1.62、1.37、0.30、4.29 m。

**六对里有五对低于 3 米。**

也就是说：**真实近冲突所在的区间，恰好是 EIDM 关闭人类行为的区间。**

## 五、这解释了什么

这件事一次性解释了今晚所有的"改一个另一个就不行"：

- 为什么 Krauss/EIDM/IDM 三者的最小 TTC 大多数情况下完全相同（都停在安全包络外）
- 为什么调 driverstate、调 tau、调 minGap、换模型，都只能到 3–5 秒就下不去
- 为什么文献（Bevrani & Chung 2012）说必须"改模型结构"而不是"调参数"

## 六、与文献的一致性

Bevrani & Chung (2012) 明确写：所有主流跟驰模型都有安全约束，导致安全事件数远低于实测；解法是**放松安全约束并修改模型结构**，五类模型的改进幅度是 CA +92%、Gipps +87%、IDM +44%、GHR +19%、Wiedemann −108%。

我们遇到的 `EST_REAC_THRESHOLD = 3.0` 正是"安全约束"的一种具体实现。

## 七、可行的三条路（需研究者定）

**路 1：改 SUMO 源码，把 `EST_REAC_THRESHOLD` 调小后重编译**
- 优点：直接打开 3 米以下的区间，EIDM 的感知误差参数就能在近冲突区起作用
- 代价：改的是仿真器本体，必须在论文里写明"我们修改了 EIDM 的安全阈值"，审稿人可能质疑
- 工程量：编译 SUMO（Windows 上需要 MSVC + CMake），约半天到一天

**路 2：换 Gipps 模型**
- 依据：Bevrani 实测 Gipps 对短 TTC 的复现最好（71%），改进后 +87%
- 问题：SUMO 1.26 未必有 Gipps 实现，需先确认
- 代价：换模型要重跑全部实验

**路 3：不追求"复现近冲突"，改风险口径**
- 既然 D1 已定"改主张"，风险可以定义为连续量（TTC 的映射），不必依赖离散近冲突事件
- 优点：不用改仿真器，现有框架直接可用
- 代价：需要在论文里说明"仿真的 TTC 分布与真实分布存在系统性差异"，作为明确限制

## 八、复现

```
D:/hermes-yan/envs/aad/Scripts/python.exe code/scripts/eidm_attr_probe.py
D:/hermes-yan/envs/aad/Scripts/python.exe code/scripts/eidm_calibration_sweep.py --top 6
```

产物：`code/outputs/analysis/eidm_attr_probe_20261116/`、`code/outputs/analysis/eidm_calibration_20261116/`

## 十、作废的中间版本（不要引用）

这三轮跑出来的数字都不能用，列在这里防止以后误引：

| 脚本/轮次 | 结果 | 为什么作废 |
|---|---|---|
| `verify_eidm_params.py` 首轮 | 0/13 参数生效 | **测试场景错了**：六辆车都在自由流（18 m/s、20 m 间距跑满全程），从不跟驰，跟驰参数本来就不起作用。不是参数的问题 |
| `find_cf_param_prefix.py` 第一、二轮 | 全部 0 差异 / SUMO 崩溃 | 第一轮的 `<param key>` 写法本身就不对；第二轮在基础属性上重复追加 `minGap`/`decel`，造成 XML 属性重复，SUMO 直接退出，TraCI 只报 "Connection closed by SUMO" 掩盖了真实原因 |
| `eidm_attr_probe.py` 首轮 | SUMO 崩溃 | 同上，属性重复 |

**有效的是**：`eidm_attr_probe.py` 第二轮（12/12 生效）与 `eidm_calibration_sweep.py`（六组参数、卡在 3 米）。

**两条工程教训**：
1. 测跟驰参数必须构造"真的会跟驰"的场景（慢前车逼迫后车制动），自由流测不出任何差异。
2. vType 属性不能重复出现，否则 SUMO 静默退出，TraCI 的报错信息完全指不到根因。改用"基础属性字典 + update"的方式合并。

## 九、还没做

- 没测比 aggressive 更极端的参数（但受 3 米下限约束，再极端也无益）
- 没验证 3 米下限在 SUMO 1.26 的具体行为是否与我读到的 main 分支源码完全一致（**行为证据强烈支持，但未逐行核对该版本的源码**）
- 没测 W99 / Wiedemann / ACC / CACC
