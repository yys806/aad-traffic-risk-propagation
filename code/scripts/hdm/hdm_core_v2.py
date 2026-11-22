"""AAD HDM 内核（0.3.5 规格；0.4.0 起抽出共享步进，供 Python 与 SUMO 桥接共用）

依据：Treiber, Kesting & Helbing 2006, Physica A 360:71-88

实现要点（逐条对原文）：
- 式(1)(2)：反应延迟作用于「全部输入」，非整数步用线性插值
- 式(3)(4)：间距乘性误差 s_est = s·exp(Vs·w_s)；接近率误差 Δv_est = Δv + s·r_c·w_v
- 式(5)(7)：两个独立 OU 过程，相关时间 tau_err
- 式(9)(10)(11)：时间前瞻 s' = s_est - T'·v_est；v' = v_est + T'·a；Δv' = Δv_est
- 式(13)(15)：空间前瞻，对前 n_a 辆车累加交互，s_alpha 为累计净距
- 式(16)(17)：IDM 底座
- 式(18)-(20)：多车前瞻的平衡距重标定（s0→s0/√β，T→T/√β）

积分：ballistic（与 SUMO step-method.ballistic 同构）：x += (v+v_new)/2*dt

【0.4.0 重构说明】为满足「两边不得各写一份」的要求，把每步计算拆成三个共享件：
  head_profile()  头车速度剖面
  car_accels()    各车加速度（含延迟、感知误差、前瞻、裁剪）
  Metrics()       观测期统计（DRAC、净距、事件、到达、接触）
hdm_core.run 与 SUMO 桥接都只调用这三件，不得复制循环体。
重构前后由 baseline_before_refactor.json 与逐元素 npz 比对证明不变。
"""
import numpy as np

# ---------------- 参数 ----------------
class P:
    v0   = 32.0      # 期望车速 m/s
    T    = 1.5       # 期望时距 s
    a    = 1.0       # 最大加速度 m/s²
    b    = 1.5       # 舒适减速度 m/s²
    s0   = 2.0       # 最小净距 m
    L    = 5.0       # 车长 m
    dt   = 0.05
    Vs   = 0.05      # 距离估计变异系数
    rc   = 0.01      # 1/TTC 估计误差 1/s
    taur = 20.0      # 误差相关时间 s
    na   = 1
    Tprime = 0.65    # 反应时间 s
    bmax = 9.0       # 制动上限（工程代表值 9.0，见 0.3.7）

DRAC_THRESHOLD = 3.4
DRAC_MIN_DURATION = 0.2


def beta(na):
    """式(19) 的重标定系数：na 车前瞻时平衡距放大系数。用有限和，na=1 时为 1。"""
    return sum(1.0 / (k * k) for k in range(1, na + 1))


def s_star(v, dv, s0r, Tr):
    """式(17) 期望净距"""
    return s0r + v * Tr + v * dv / (2.0 * np.sqrt(P.a * P.b))


def idm_acc(v, s, dv, s0r, Tr):
    """式(16) 单对交互：自由流项 + 交互项"""
    afree = P.a * (1.0 - (v / P.v0) ** 4)
    ss = np.maximum(s_star(v, dv, s0r, Tr), 0.0)
    aint = -P.a * (ss / np.maximum(s, 1e-6)) ** 2
    return afree + aint


def equilibrium_speed(hw):
    """平衡态：给定车头距 hw，解 a=0（n_a=1，无噪声）"""
    s = hw - P.L
    lo, hi = 0.05, P.v0 * 0.999
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if idm_acc(mid, s, 0.0, P.s0, P.T) > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------- 共享件 1：头车速度剖面 ----------------
def head_profile(t, v_eq, v_target, warm, ramp):
    """头车在时刻 t 的目标速度。t 为**步初**时刻。"""
    if v_target is None:
        return v_eq
    if t < warm:
        return v_eq
    tt = min(t - warm, ramp)
    return v_eq + (v_target - v_eq) * (tt / ramp)


# ---------------- 共享件 2：各车加速度 ----------------
def car_accels(k, hist_x, hist_v, hist_a, N, n_a, Tp, dt, noise, ws, wv, rng, e, sq, bmax_arr):
    """第 k 步各车加速度（**未限幅**）。

    hist_* 是 (steps+2, N) 缓冲，hist_*[k] 为第 k 步**步初**状态。
    ws/wv 为 OU 状态数组，原地更新（顺序：逐车先 ws 后 wv）。
    """
    new_acc = np.zeros(N)
    dly = Tp / dt
    n_int = np.floor(dly).astype(int)
    w_frac = dly - n_int
    for i in range(1, N):
        k_d = max(k - n_int[i], 0)
        k_d2 = max(k - n_int[i] - 1, 0)
        xi = (1 - w_frac[i]) * hist_x[k_d, i] + w_frac[i] * hist_x[k_d2, i]
        vi = (1 - w_frac[i]) * hist_v[k_d, i] + w_frac[i] * hist_v[k_d2, i]
        ai = (1 - w_frac[i]) * hist_a[k_d, i] + w_frac[i] * hist_a[k_d2, i]
        s_list, dv_list = [], []
        for al in range(1, n_a + 1):
            j = i - al                       # 车 0 是队首，第 al 辆前车索引 i-al
            if j < 0:
                continue
            xj = (1 - w_frac[i]) * hist_x[k_d, j] + w_frac[i] * hist_x[k_d2, j]
            vj = (1 - w_frac[i]) * hist_v[k_d, j] + w_frac[i] * hist_v[k_d2, j]
            s_cum = xj - xi - P.L * al       # 式(15)
            s_list.append(max(s_cum, 0.2))
            dv_list.append(vi - vj)          # IDM 约定：Δv = 本车 - 前车（接近为正）
        if not s_list:
            new_acc[i] = P.a * (1.0 - (min(max(vi, 0.0), P.v0) / P.v0) ** 4)
            continue
        if noise:
            ws[i] = e * ws[i] + sq * rng.standard_normal()
            wv[i] = e * wv[i] + sq * rng.standard_normal()
            s_est = s_list[0] * np.exp(P.Vs * ws[i])
            dv_est = dv_list[0] + s_list[0] * P.rc * wv[i]
        else:
            s_est, dv_est = s_list[0], dv_list[0]
        s_pr = max(s_est - Tp[i] * dv_est, 0.1)   # 式(9) + 物理下界 0.1 m
        v_pr = vi + Tp[i] * ai                     # 式(10)
        nb = min(n_a, len(s_list))
        bt_i = beta(nb)
        sb_i = np.sqrt(bt_i)
        s0r_i, Tr_i = P.s0 / sb_i, P.T / sb_i      # 式(20)
        afree_i = P.a * (1.0 - (max(v_pr, 0.0) / P.v0) ** 4)
        aint_i = idm_acc(v_pr, max(s_pr, 1e-3), dv_est, s0r_i, Tr_i) - afree_i
        for al in range(1, len(s_list)):
            aint_i += idm_acc(v_pr, s_list[al], dv_list[al], s0r_i, Tr_i) - afree_i
        aint_i = max(aint_i, -(bmax_arr[i] + afree_i))
        new_acc[i] = afree_i + aint_i
    return new_acc


# ---------------- 共享件 3：观测期统计 ----------------
class Metrics:
    """观测期指标。update() 用**步末**状态（x, v 已更新），与内核原写法一致。"""

    def __init__(self, N, v_eq, dt):
        self.N = N
        self.v_eq = v_eq
        self.dt = dt
        self.max_drac = np.zeros(N)
        self.min_gap = np.full(N, np.inf)
        self.drac_run = np.zeros(N)
        self.drac_max_run = np.zeros(N)
        self.first_arrival = np.full(N, np.nan)
        self.contact_frames = 0     # 几何净距 <= 0 的 (步, 车) 计数

    def update(self, k, x, v, steps_warm):
        if k < steps_warm:
            return
        for i in range(1, self.N):
            gap = x[i - 1] - x[i] - P.L
            self.min_gap[i] = min(self.min_gap[i], gap)
            if gap <= 0.0:
                self.contact_frames += 1
            dv = v[i] - v[i - 1]
            dr = (dv * dv / (2.0 * gap)) if (gap > 0 and dv > 0) else 0.0
            self.max_drac[i] = max(self.max_drac[i], dr)
            if dr >= DRAC_THRESHOLD:
                self.drac_run[i] += self.dt
                self.drac_max_run[i] = max(self.drac_max_run[i], self.drac_run[i])
            else:
                self.drac_run[i] = 0.0
            if np.isnan(self.first_arrival[i]) and v[i] < self.v_eq - 0.5:
                self.first_arrival[i] = (k + 1) * self.dt - steps_warm * self.dt

    @property
    def event(self):
        return self.drac_max_run >= DRAC_MIN_DURATION

    def as_dict(self):
        return dict(max_drac=self.max_drac, min_gap=self.min_gap,
                    event=self.event, arrival=self.first_arrival,
                    contact_frames=self.contact_frames)


# ---------------- 车队仿真（只调用上面三件） ----------------
def run(N=100, hw=45.0, n_a=1, Tprime=0.65, seed=0,
        v_target=None, ramp=6.0, warm=40.0, observe=300.0, noise=True,
        bmax=None, record=True, dt=None, v_init=None, s_init=None,
        msg_state=None, drac_log=False, x0=0.0):
    """msg_state: hdm_msg.MsgState 实例或 None。None 时必须是**零副作用**（见 verify_msg_noop.py）。

    drac_log=True 时额外返回逐帧 DRAC 数组（供事件切段用）。
    """
    rng = np.random.default_rng(seed)
    dt = float(P.dt if dt is None else dt)
    hw = float(hw)
    s_eq = hw - P.L
    v_eq = equilibrium_speed(hw)

    x = x0 - np.arange(N) * hw      # x0: 与 SUMO 侧同坐标系（0.5.0 用 5000）
    v = np.full(N, v_eq)
    if v_init is not None:
        v = np.asarray(v_init, dtype=float).copy()
    if s_init is not None:
        x = np.zeros(N)
        for i in range(1, N):
            x[i] = x[i - 1] - (s_init[i] + P.L)
    acc = np.zeros(N)
    if isinstance(bmax, str) and bmax == 'markkula':
        samp = rng.normal(6.68, 1.69, N)
        bmax_arr = np.clip(np.abs(samp), 3.5, 9.5)
    elif bmax is None:
        bmax_arr = np.full(N, float(P.bmax))
    elif np.isscalar(bmax):
        bmax_arr = np.full(N, float(bmax))
    else:
        bmax_arr = np.asarray(bmax, dtype=float)

    ws = rng.standard_normal(N)
    wv = rng.standard_normal(N)
    Tp = np.full(N, Tprime)
    if Tprime is None:
        Tp = rng.uniform(0.60, 0.80, N)

    steps_warm = int(round(warm / dt))
    steps_obs = int(round(observe / dt))
    total = steps_warm + steps_obs

    hist_x = np.zeros((total + 1, N))
    hist_v = np.zeros((total + 1, N))
    hist_a = np.zeros((total + 1, N))
    hist_x[0], hist_v[0] = x, v

    preclip_min = 0.0
    preclip_steps = 0
    preclip_max_cars = 0
    M = Metrics(N, v_eq, dt)
    drac_buf = np.zeros((total + 1, N)) if drac_log else None
    # 全程安全检查（GPT/Gemini 审计：原稿只查观测期接触，漏预热期与瞬移/越界/非有限值）
    safety = dict(contact_warm=0, contact_obs=0, nonfinite=0, oob=0, teleport=0,
                  max_abs_x=0.0, min_x=float("inf"), min_speed=float("inf"), max_speed=0.0)
    x_prev = x.copy(); v_prev = v.copy()

    e = np.exp(-dt / P.taur)
    sq = np.sqrt(2.0 * dt / P.taur)

    for k in range(total):
        t = k * dt
        v[0] = head_profile(t, v_eq, v_target, warm, ramp)
        acc[0] = 0.0

        new_acc = car_accels(k, hist_x, hist_v, hist_a, N, n_a, Tp, dt,
                             noise, ws, wv, rng, e, sq, bmax_arr)

        raw_min = float(np.min(new_acc[1:])) if N > 1 else 0.0
        if raw_min < preclip_min:
            preclip_min = raw_min
        _ex = np.sum(new_acc[1:] < -bmax_arr[1:])
        if _ex > 0:
            preclip_steps += 1
            preclip_max_cars = max(preclip_max_cars, int(_ex))

        new_acc = np.minimum(np.maximum(new_acc, -bmax_arr), P.a)
        v_new = np.maximum(v + new_acc * dt, 0.0)
        acc = new_acc
        if msg_state is not None:
            # 消息速度上限（柔和斜坡）。只改接收车，非接收车逐位不变。
            # 时钟：传入**步末**时刻 (k+1)·dt，对齐目标书 v3 §2.2
            v_new, modified = msg_state.apply(v_new, v, (k + 1) * dt, dt, x=x)
            if modified.any():
                # 只有被限速的车才用实际执行加速度回写，
                # 否则前瞻项 v_pr = vi + T'*a 被污染（Gemini 0.5.0 评审第 4 条）；
                # 未被限速的车保持 new_acc 原值，保证零副作用。
                acc = new_acc.copy()
                acc[modified] = (v_new[modified] - v[modified]) / dt
        x_new = x + 0.5 * (v + v_new) * dt
        v, x = v_new, x_new
        hist_x[k + 1], hist_v[k + 1], hist_a[k + 1] = x, v, acc

        if drac_log and k >= steps_warm:
            # 与 hist_*[k+1] 对齐：k 步末的状态写进索引 k+1
            for i in range(1, N):
                g = x[i - 1] - x[i] - P.L
                dvv = v[i] - v[i - 1]
                drac_buf[k + 1, i] = (dvv * dvv / (2.0 * g)) if (g > 0 and dvv > 0) else 0.0

        # 全程安全检查（Gemini 审计：原 oob 是死字段、无瞬移检查）
        if not (np.all(np.isfinite(x)) and np.all(np.isfinite(v))):
            safety["nonfinite"] += 1
        else:
            ax = float(np.max(np.abs(x)))
            if ax > safety["max_abs_x"]:
                safety["max_abs_x"] = ax
            if float(np.min(x)) < -1.0:      # 负位置=引擎级不合理；网界由调用方按臂判
                safety["oob"] += 1
            # 瞬移：单车单步位移不得超过 v_max·dt（留 5% 余量）
            dx_step = np.abs(x - x_prev)
            if float(np.max(dx_step)) > 1.05 * float(np.max(np.abs(v_prev))) * dt + 1e-9:
                safety["teleport"] += 1
            safety["min_speed"] = min(safety["min_speed"], float(np.min(v)))
            safety["max_speed"] = max(safety["max_speed"], float(np.max(v)))
            safety["min_x"] = min(safety.get("min_x", float("inf")), float(np.min(x)))
            x_prev = x.copy(); v_prev = v.copy()
        gaps = x[:-1] - x[1:] - P.L          # 向量化，避免 800k 次 Python 循环
        n_contact = int(np.sum(gaps <= 0.0))
        if n_contact:
            if k < steps_warm:
                safety["contact_warm"] += n_contact
            else:
                safety["contact_obs"] += n_contact

        M.update(k, x, v, steps_warm)

    out = dict(v_eq=v_eq, s_eq=s_eq, preclip_min=preclip_min,
               preclip_steps=preclip_steps, preclip_max_cars=preclip_max_cars,
               hist_x=hist_x if record else None,
               hist_v=hist_v if record else None,
               hist_a=hist_a if record else None)
    out.update(M.as_dict())
    out["safety"] = safety
    if drac_log:
        out["drac"] = drac_buf
    return out