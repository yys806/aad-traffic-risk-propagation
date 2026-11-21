"""AAD HDM 快筛内核（0.3.5 规格，按 Treiber, Kesting & Helbing 2006, Physica A 360:71-88）

实现要点（逐条对原文）：
- 式(1)(2)：反应延迟作用于「全部输入」，非整数步用线性插值
- 式(3)(4)：间距乘性误差 s_est = s·exp(Vs·w_s)；接近率误差 Δv_est = Δv + s·r_c·w_v
- 式(5)(7)：两个独立 OU 过程，相关时间 tau_err
- 式(9)(10)(11)：时间前瞻 s' = s_est - T'·v_est；v' = v_est + T'·a；Δv' = Δv_est
- 式(13)(15)：空间前瞻，对前 n_a 辆车累加交互，s_alpha 为累计净距
- 式(16)(17)：IDM 底座
- 式(18)-(20)：多车前瞻的平衡距重标定（s0→s0/beta，T→T/beta）

积分：ballistic（与 SUMO step-method.ballistic 同构）：x += (v+v_new)/2*dt
"""
import numpy as np

# ---------------- 参数 ----------------
class P:
    v0   = 32.0      # 期望车速 m/s（Treiber §3.1 用 115 km/h≈32 m/s）
    T    = 1.5       # 期望时距 s（§3.1 条件）
    a    = 1.0       # 最大加速度 m/s²（表 1）
    b    = 1.5       # 舒适减速度 m/s²（表 1）
    s0   = 2.0       # 最小净距 m（表 1）
    L    = 5.0       # 车长 m
    dt   = 0.05
    Vs   = 0.05      # 距离估计变异系数
    rc   = 0.01      # 1/TTC 估计误差 1/s
    taur = 20.0      # 误差相关时间 s
    na   = 1
    Tprime = 0.65    # 反应时间 s
    bmax = 9.0       # 制动上限（快筛先用 9 作数值保护，仅用于防发散；实测分布待核后替换）

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

# ---------------- 车队仿真 ----------------
def run(N=100, hw=45.0, n_a=1, Tprime=0.65, seed=0,
        v_target=None, ramp=6.0, warm=40.0, observe=300.0, noise=True,
        bmax=None, record=True, dt=None, v_init=None, s_init=None):
    """返回 dict：每车 max DRAC、最小净距、事件标记、到达时刻等"""
    rng = np.random.default_rng(seed)
    dt = float(P.dt if dt is None else dt)
    hw = float(hw)
    s_eq = hw - P.L
    v_eq = equilibrium_speed(hw)
    bt = beta(n_a)
    # 式(20) 重标定：由平衡条件 sqrt(beta)*(s0r + v*Tr) = s0 + v*T 得 s0r=s0/sqrt(beta)、Tr=T/sqrt(beta)
    sb = np.sqrt(bt)
    s0r, Tr = P.s0 / sb, P.T / sb

    # 初始：默认平衡态；可传 v_init / s_init 覆盖（用于非平衡自检）
    x = -np.arange(N) * hw                 # x[0] 最前
    v = np.full(N, v_eq)
    if v_init is not None:
        v = np.asarray(v_init, dtype=float).copy()
    if s_init is not None:                 # s_init[i] = 第 i 辆与其前车的净距
        x = np.zeros(N)
        for i in range(1, N):
            x[i] = x[i - 1] - (s_init[i] + P.L)
    acc = np.zeros(N)
    bmax_arr = None
    if isinstance(bmax, str) and bmax == 'markkula':
        # Markkula 2016 Fig.10：乘用车最大减速度 n=31, μ=-6.68, σ=1.69（负号为方向），截断 [3.5, 9.5]
        samp = rng.normal(6.68, 1.69, N)
        bmax_arr = np.clip(np.abs(samp), 3.5, 9.5)
    elif bmax is None:
        bmax_arr = np.full(N, float(P.bmax))
    elif np.isscalar(bmax):
        bmax_arr = np.full(N, float(bmax))
    else:
        bmax_arr = np.asarray(bmax, dtype=float)

    # OU 状态
    ws = rng.standard_normal(N)
    wv = rng.standard_normal(N)
    # 每车反应时间（核心组 2 用分布）
    Tp = np.full(N, Tprime)
    if Tprime is None:
        Tp = rng.uniform(0.60, 0.80, N)

    steps_warm = int(round(warm / dt))
    steps_obs = int(round(observe / dt))
    total = steps_warm + steps_obs

    # 历史缓冲：记录 x, v, a（用于延迟取值）
    hist_x = np.zeros((total + 1, N))
    hist_v = np.zeros((total + 1, N))
    hist_a = np.zeros((total + 1, N))
    hist_x[0], hist_v[0] = x, v

    preclip_min = 0.0
    preclip_steps = 0
    preclip_max_cars = 0
    max_drac = np.zeros(N)
    min_gap = np.full(N, np.inf)
    drac_run = np.zeros(N)        # 连续超阈计时
    drac_max_run = np.zeros(N)
    first_arrival = np.full(N, np.nan)

    e = np.exp(-dt / P.taur)
    sq = np.sqrt(2.0 * dt / P.taur)

    for k in range(total):
        t = k * dt
        # ---- 头车速度剖面 ----
        if v_target is None:
            v_lead = v_eq
        else:
            if t < warm:
                v_lead = v_eq
            else:
                tt = min(t - warm, ramp)
                v_lead = v_eq + (v_target - v_eq) * (tt / ramp)
        v[0] = v_lead
        acc[0] = 0.0

        # ---- 各车加速度 ----
        new_acc = np.zeros(N)
        # 延迟索引
        dly = Tp / dt
        n_int = np.floor(dly).astype(int)
        w_frac = dly - n_int
        for i in range(1, N):
            k_d = max(k - n_int[i], 0)
            k_d2 = max(k - n_int[i] - 1, 0)
            def dval(h):
                return (1 - w_frac[i]) * h[k_d, i] + w_frac[i] * h[k_d2, i]
            # 延迟时刻的自身与前车状态
            xi = dval(hist_x); vi = dval(hist_v); ai = dval(hist_a)
            # 需要前车（延迟时刻）位置
            nl = min(i + n_a, N - 1)
            s_list, dv_list = [], []
            for al in range(1, n_a + 1):
                j = i - al               # 车 0 是队首，第 al 辆前车索引是 i-al
                if j < 0:                # 前面没车了：该项不参与
                    continue
                xj = (1 - w_frac[i]) * hist_x[k_d, j] + w_frac[i] * hist_x[k_d2, j]
                vj = (1 - w_frac[i]) * hist_v[k_d, j] + w_frac[i] * hist_v[k_d2, j]
                s_cum = xj - xi - P.L * al        # 式(15)：累计净距 = 前车位置 - 本车位置 - al 个车长
                s_list.append(max(s_cum, 0.2)); dv_list.append(vi - vj)   # IDM 约定：Δv = 本车 - 前车（接近为正）
            if not s_list:                       # 前面没车了
                new_acc[i] = P.a * (1.0 - (min(max(vi, 0.0), P.v0) / P.v0) ** 4)
                continue
            # 感知误差（式3、4）
            if noise:
                ws[i] = e * ws[i] + sq * rng.standard_normal()
                wv[i] = e * wv[i] + sq * rng.standard_normal()
                s_est = s_list[0] * np.exp(P.Vs * ws[i])
                dv_est = dv_list[0] + s_list[0] * P.rc * wv[i]
            else:
                s_est, dv_est = s_list[0], dv_list[0]
            # 时间前瞻（式9-11）：未来间距 = 当前间距 - 反应时间 × 接近速度
            s_pr = s_est - Tp[i] * dv_est
            # 物理下界：司机预判的未来间距不可能为负；趋于零即"必然追上"，此时按最大制动处理
            # 下界只取 0.1 m：未来间距不能为负；趋零即「必然追上」，由交互上限接住，不引入自由参数
            s_pr = max(s_pr, 0.1)
            v_pr = vi + Tp[i] * ai
            dv_pr = dv_est
            # 多车前瞻累加（式13）：第一项用带误差的，其余用原始累计距
            # 式(12)(13)：a = afree + Σ_α aint(α)，afree 只加一次
            # 重标定按"本车实际能看到几辆前车"逐车计算（队首附近不足 n_a 辆）
            nb = min(n_a, len(s_list))
            bt_i = beta(nb); sb_i = np.sqrt(bt_i)
            s0r_i, Tr_i = P.s0 / sb_i, P.T / sb_i
            afree_i = P.a * (1.0 - (max(v_pr, 0.0) / P.v0) ** 4)
            aint_i = idm_acc(v_pr, max(s_pr, 1e-3), dv_pr, s0r_i, Tr_i) - afree_i
            for al in range(1, len(s_list)):
                aint_i += idm_acc(v_pr, s_list[al], dv_list[al], s0r_i, Tr_i) - afree_i
            # 总加速度 a = afree + aint 不低于 -b_max  =>  aint 不低于 -(b_max + afree)
            aint_i = max(aint_i, -(bmax_arr[i] + afree_i))
            new_acc[i] = afree_i + aint_i
        # 记录裁剪前的制动请求（GPT 0.3.6 要求：判断某个 b_max 档是否真的会改变轨迹）
        raw_min = float(np.min(new_acc[1:])) if N > 1 else 0.0
        if raw_min < preclip_min:
            preclip_min = raw_min
        _ex = np.sum(new_acc[1:] < -bmax_arr[1:])
        if _ex > 0:
            preclip_steps += 1
            preclip_max_cars = max(preclip_max_cars, int(_ex))
        # 限幅
        new_acc = np.minimum(np.maximum(new_acc, -bmax_arr), P.a)
        # ballistic 更新
        v_new = np.maximum(v + new_acc * dt, 0.0)
        x_new = x + 0.5 * (v + v_new) * dt
        v, x = v_new, x_new
        acc = new_acc
        hist_x[k + 1], hist_v[k + 1], hist_a[k + 1] = x, v, acc

        # ---- 观测期统计 ----
        if k >= steps_warm:
            for i in range(1, N):
                gap = x[i - 1] - x[i] - P.L
                min_gap[i] = min(min_gap[i], gap)
                dv = v[i] - v[i - 1]
                if gap > 0 and dv > 0:
                    dr = dv * dv / (2.0 * gap)
                else:
                    dr = 0.0
                max_drac[i] = max(max_drac[i], dr)
                if dr >= 3.4:
                    drac_run[i] += dt
                    drac_max_run[i] = max(drac_max_run[i], drac_run[i])
                else:
                    drac_run[i] = 0.0
                # 到达判据：相对平衡速度降 0.5 m/s 持续
                if np.isnan(first_arrival[i]) and v[i] < v_eq - 0.5:
                    first_arrival[i] = (k + 1) * dt - warm

    return dict(v_eq=v_eq, s_eq=s_eq, max_drac=max_drac, min_gap=min_gap,
                event=(drac_max_run >= 0.2), arrival=first_arrival,
                hist_x=hist_x if record else None,
                hist_v=hist_v if record else None, hist_a=hist_a if record else None,
                preclip_min=preclip_min, preclip_steps=preclip_steps, preclip_max_cars=preclip_max_cars)
