## Current — AAD-S0.5-POST-R2-TASK11 (2026-10-31)

Task11 completed a bounded public-data feasibility audit. MiTra T1 small files were downloaded, SHA/CRC checked and parsed: 1,578,393 rows, 1,456 vehicle IDs, nominal 30 Hz, 1,340 vehicles with at least 20 s, and 1,308,347 leader/follower rows per relation. MiTra is a conditional Task9 input candidate pending paired video/tracking-log and physical-gap review. I24V public README and Data Use Agreement were reviewed but the data endpoint was not reached; no I24V payload was obtained. NGSIM video directory facts were reused from Task7.2; no raw AVI payload, PTS/Global_Time mapping or camera coverage was closed. Stage 0.5 remains blocked, scientific equivalence false, Task9 formal runs 0, and Round3/Stage 0.6/Protocol Lock/Stage I remain unchanged.

Evidence: `evidence/results/RES-STAGE-0.5-POST-R2-TASK11-PUBLIC-DATA-FEASIBILITY-20261031/`.

## Current — AAD-S0.5-POST-R2-TASK10 (2026-10-31)

Round2 final offline diagnostic is complete with Case B blockers. Task4/5/6/8/9 evidence was reused; the new event/control quality audit remains descriptive, PreciseNGSIM event-level crosswalk is `BLOCKED_EVENT_LEVEL_CROSSWALK`, and 40 same-trajectory source→target candidates were found with 0 qualified B witnesses and 40 `Unknown` due missing independent physical connection basis. Task9 formal runs remain 0 and readiness is `BLOCKED_BY_PHYSICAL_INPUT`. Stage 0.5 `blocked`, scientific equivalence `false`, Stage 0.6/Protocol Lock/Stage I unchanged, Round3 not started.

Report: `docs/STAGE_0_5_POST_R2_TASK10_FINAL_DIAGNOSTIC_20261031.md`; evidence: `evidence/results/RES-STAGE-0.5-POST-R2-TASK10-FINAL-DIAGNOSTIC/`.

## Current — AAD-S0.5-POST-R2-TASK9 (2026-10-31)

Task9 engineering preparation is complete with external blockers. The unchanged Task7 provider inquiry was not sent because the available Edge state could not be safely observed and a Gmail authentication origin was rejected by automatic review; no sender, receipt or provider response exists. No raw AVI was downloaded, no ffprobe/time-space mapping or physical review occurred. Sealed B00/Round2 static inputs confirm only five heterogeneous passenger `minGap` changes (2.5→1.0) with the five tau values retained. The approved fixed-leader seeds are 20261101/20261102/20261103; a fail-closed module now checks common leader input, matched physical initial state and `C_initial/C_f/C_l/C/C_gap/R` closure. Formal runs: 0; qualified segments: 0; B status: `Blocked by physical input`. Stage 0.5 `blocked`, scientific equivalence `false`, Stage 0.6/Protocol Lock/Stage I unchanged, Round3 not started.

Report: `docs/STAGE_0_5_POST-R2_TASK9_FIXED_LEADER_AND_PHYSICAL_REFERENCE_20261031.md`; evidence: `evidence/results/RES-STAGE-0.5-POST-R2-TASK9-FIXED-LEADER-PREP-20261031/`.

## Current — AAD-S0.5-POST-R2-TASK8 (2026-10-30)

Verified offline Task8 extends every Task6 source/target event and original control to five-second precursor diagnostics: source strict events105/167 and107/159, original paired strict contrasts94/89. Leader-speed-change contributions are substantial; generic initial-positive-closing or follower-acceleration-only explanations are weakened, not causally rejected. Official SUMO1.26.0 tagged source distinguishes dynamic ballistic follow from insertion and LC constraints. Seven existing near-threshold cases remain non-P2; five change leader and only two allow full fixed-pair decomposition. Physical truth and unique mechanism attribution remain Unknown.

Original Round2 candidate remains CLOSED_FAILED_ORIGINAL_SOURCE_CONDITION; Formal P2 and independent D1/B standards unchanged; scientific equivalence false; physical reference/path insufficient; Stage0.5 blocked, Stage0.6/Protocol Lock/StageI unchanged, Round3 not started. No simulation, TraCI, new seed, third-window trajectory, holdout, video or OB access.

Report: docs/STAGE_0_5_POST_R2_TASK8_KINEMATIC_MECHANISM_DIAGNOSIS_20261030.md; evidence: evidence/results/RES-STAGE-0.5-POST-R2-TASK8-KINEMATIC-MECHANISM-DIAG-20261030/. Older dated entries remain historical.

## Current — AAD-ROUND2-CLOSURE-20261030

Original Round2 minGap1.0 source branch is Agreed closed after one failed source-condition run; no independent confirmation. C general Formal P2, separate D1 and B physical-path witness standard are Agreed. Current implementation already supports C pair/time lane-independent qualification; native/formal flagged endpoints and source clocks still differ, so scientific equivalence remains false.

Campaign is COMPLETED_WITH_BLOCKERS: bounded matrix complete (100 passed/3 historical dependency-blocked; 95 historical payload checks); official inquiry BLOCKED_NOT_SENT after app-access approval timeout, no actual send/receipt. Video acquisition is NO_GO: file-specific license, PTS/time anchors and source-lane coverage remain Blocked. Conditional authority exists but evidence gates have not passed. No acquired video, sampled case, human judgment, new SUMO/TraCI or holdout read. Gate/Stage0.6/Protocol Lock/StageI remain blocked/unchanged. Primary reports: docs/AAD_ROUND2_RESEARCH_DECISIONS_20261030.md; docs/VIDEO_ACQUISITION_GO_NO_GO_20261030.md; docs/FIXED_LEADER_PAIRED_EXPERIMENT_PROPOSAL_20261030.md; docs/ROUND3_CANDIDATE_READINESS_REPORT_20261030.md. Earlier entries are dated historical snapshots.

## 2026-10-30 Round2 Task7.2 - resource and mapping conditions

Task7.2 COMPLETED_WITH_BLOCKERS. Four unique current raw AVI members verified from 6,452 bytes of exact ZIP metadata Ranges; compressed total 1,248,582,779 bytes, extracted total 1,248,560,044 bytes. Per-file license and PTS/time anchors remain unresolved. Existing 130 controls show a predominantly near-constant correspondence difference (mean norm 12.29247 m), not verified physical displacement. Camera7/8 remain geographic candidates, minimum_camera_set null. Provider inquiry drafted but not sent; acquisition and physical review remain unapproved/blocked. Formal P2 167/159, historical evidence, AGENTS,06_DECISIONS and scientific Gate/later stages unchanged. No videos, cases, simulations or new trajectory/holdout reads.

Report: docs/STAGE_0_5_ROUND2_TASK7_2_RESOURCE_METADATA_AND_ACQUISITION_FEASIBILITY_20261030.md; evidence: evidence/results/RES-STAGE-0.5-ROUND2-TASK7.2-RESOURCE-METADATA-AND-ACQUISITION-FEASIBILITY-20261030/.

## 2026-10-30 Round2 Task7.1 — metadata and mapping feasibility

Task7.1 bounded investigation COMPLETED_WITH_BLOCKERS. Per-window Local_Y/Global/ortho mapping supports geographic camera candidates7/8 (EPSG:2229), not certified full-source visibility; minimum_camera_set remains null. PTS mapping, per-file license/size and Coifman2017 full-text access remain unresolved. PreciseNGSIM two-window structure is useful auxiliary evidence with inherited fields, shorter time support and malformed last records; not independent truth or formal replacement. Source Formal P2 167/159, Task1–Task7 evidence, AGENTS,06_DECISIONS and scientific Gate/later stages unchanged. No video acquisition, event sampling, SUMO/TraCI, third window or holdout.

Report: docs/STAGE_0_5_ROUND2_TASK7_1_VIDEO_METADATA_AND_MAPPING_FEASIBILITY_20261030.md; evidence: evidence/results/RES-STAGE-0.5-ROUND2-TASK7.1-VIDEO-METADATA-AND-MAPPING-FEASIBILITY-20261030/.

## Current — 2026-10-30 Round2 Task7: physical-reference availability

Verified bounded Task7 evidence-availability investigation is complete; physical review remains BLOCKED_NO_VERIFIED_INDEPENDENT_PHYSICAL_REFERENCE. Official raw/processed camera files are documented, but no local independent raw video, source-camera/Local_Y mapping or video-PTS/Global_Time mapping is verified. No event selection or human review occurred. Source Formal P2 167/159 and Task1–Task6 history remain unchanged; Task6 controls are row-distinct, not vehicle-independent (131/165 and 115/149 source followers/rows). AGENTS section8 alone adopts risk-based validation. No new video/trajectory/SUMO/TraCI/third-window/holdout; Gate and later stages unchanged.

Report: `docs/STAGE_0_5_ROUND2_TASK7_INDEPENDENT_PHYSICAL_QUALITY_REVIEW_20261030.md`; evidence: `evidence/results/RES-STAGE-0.5-ROUND2-TASK7-INDEPENDENT-PHYSICAL-QUALITY-REVIEW-20261030/`.

## Current — AAD-S0.5-ROUND2-TASK6 (2026-10-30)

Verified offline Task6 reproduces NGSIM source Formal P2 167/159 and sealed SUMO source zero. Small gaps alone do not explain the difference: low-speed positive closing tails and gap-closing joint structure differ, including coarse common macro support. Lane/leader transitions occur near a subset of real events, but most complete source contexts show no observed transition. Measurement artifacts, precise causal mechanism and scientific equivalence remain Unknown. No new SUMO/TraCI/trajectory/holdout; scientific definitions and Gate/Stage 0.6/Protocol Lock/Stage I unchanged.

Report: `docs/STAGE_0_5_ROUND2_TASK6_REAL_SIM_MICRO_INTERACTION_ANALYSIS_20261030.md`; evidence: `evidence/results/RES-STAGE-0.5-ROUND2-TASK6-REAL-SIM-MICRO-INTERACTION-20261030/`.

## Current — AAD-S0.5-ROUND2-TASK5-TASK4-EVIDENCE-INTEGRITY-CLOSURE-20261030

Verified offline integrity closure for Task 4. The two authorized NGSIM windows overlap in `Global_Time` for 89.5 s, but exact `(original_vehicle_id, Global_Time, Frame_ID)` record intersection is 0, trajectory ID intersection is 0, and Formal P2 onset-key intersection is 0; 1430 shared raw vehicle IDs do not prove cross-window identity, so statistics remain separate. Onset attribution is unique and conserved: NGSIM 543/732 events have 543/732 unique matches and 0 unmatched/ambiguous; source/target remain 167/159 and 174/252. SUMO formal-aligned B00 has 0 events and Round2 has 1 unique target event. Real NGSIM partial 30 s tails now use effective durations 22.9 s and 9.1 s; SUMO full blocks unchanged. Task 4 historical evidence SHA256 remains unchanged; Stage 0.5 Gate, Stage 0.6, Protocol Lock and Stage I unchanged. Report: `docs/STAGE_0_5_ROUND2_TASK5_TASK4_EVIDENCE_INTEGRITY_20261030.md`; evidence: `evidence/results/RES-STAGE-0.5-ROUND2-TASK5-TASK4-EVIDENCE-INTEGRITY-20261030/`.

## Current — AAD-S0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030

Verified offline real-source support: the two authorized NGSIM US-101 windows reproduce full-source Formal P2 `543/732` and full-source P2-evaluable exposure `111425.9/133505.6 s`. Full-context onset attribution gives fixed source-region Formal P2 `167/159` with local evaluable exposure `30519.4/30560.7 s`; target-region `174/252`. B00 and Round2 sealed SUMO formal-aligned/D1 source remain zero; Round2 retains one target event. Macro/micro state differences are descriptive only: NGSIM and SUMO time origins are not proven identical, `C_INPUT_ROUTE=1112` is not vehicle-matched to NGSIM, and simulator formal equivalence remains false/pending. No new SUMO/TraCI/trajectory/holdout; Stage 0.5 Gate, Stage 0.6, Protocol Lock, Stage I and Round3 unchanged. Report: `docs/STAGE_0_5_ROUND2_TASK4_REAL_SOURCE_SUPPORT_AND_MULTISCALE_CROSSWALK_20261030.md`; evidence: `evidence/results/RES-STAGE-0.5-ROUND2-TASK4-REAL-SOURCE-SUPPORT-AND-MULTISCALE-CROSSWALK-20261030/`.

## Current — AAD-S0.5-ROUND2-TASK3-MEASUREMENT-CONTRACT-ALIGNMENT-20261029

Verified minimal formal-alignment repair preserves explicit identity/continuity flags; formal pair/time qualification remains separate from D1 same-native-lane diagnostics. B00 and Round2 candidate sealed source P2 remain zero; no SUMO/TraCI/new trajectories/holdout. Stage 0.5 Gate, Stage 0.6, Protocol Lock, Stage I and Round3 unchanged.
Report: docs/STAGE_0_5_ROUND2_TASK3_MEASUREMENT_CONTRACT_ALIGNMENT_20261029.md; evidence: evidence/results/RES-STAGE-0.5-ROUND2-TASK3-MEASUREMENT-CONTRACT-ALIGNMENT-20261029/

## Current — AAD-S0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029

Verified offline measurement-contract audit: 16 deterministic synthetic cases reproduce formal P2, SUMO-native, formal-aligned and D1 differences; candidate A/B/C remain pending researcher adjudication. Reused post-R2 sealed evidence; no SUMO/TraCI/new trajectories/holdout. Stage 0.5 Gate, Stage 0.6, Protocol Lock, Stage I and Round3 unchanged.
Report: docs/STAGE_0_5_ROUND2_TASK2_MEASUREMENT_CONTRACT_20261029.md; evidence: evidence/results/RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029/.

## Current — 2026-10-29 Post-R2 offline mechanism diagnostic

Verified offline reconstruction of all 610725/645369 sealed states reproduces source D1 exactly: 86234/91058 source observations; 8457.4/8900.0 evaluable veh-s; no 0<TTC<2 state and no source onset. [2,3) diagnostic support is 30/29 states in 4/3 segments; minimum TTC 2.157878/2.673198 s. No observed short formal-risk segment was blocked by duration. Missing lane-boundary support remains Unknown. Target m00485/r00036 remains one target-only event, not source propagation. D1/native/formal-aligned lane and explicit-flag contracts differ in new synthetic counterexamples; formal_equivalence_accepted remains false. SUMO/TraCI/new trajectories/holdout=0. Stage 0.5 Gate, Stage 0.6, Protocol Lock and Stage I unchanged. Report: docs/STAGE_0_5_POST_R2_OFFLINE_DIAGNOSTIC_20261029.md; evidence: evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029/. Full offline regression: 1415 passed, 28 failed, 4 skipped, 7 native tests excluded; individual dependency evidence retained. Older entries below are historical snapshots.

## Historical — 2026-10-29 Round2 Task1 completed candidate result

Verified: the researcher-approved candidate started exactly once (seed 20261201, 420 s, 8400 native steps, one SUMO/TraCI pair) and completed. Rule A strict joint macro support passed: mean density 44.0526 veh/km/lane, mean speed 10.3333 m/s, 18/18 block speed support and 18/18 closing support against the existing 0.63636 baseline. The fixed formal source-region P2 count is 0. One target-cohort event occurred at 271.8–272.1 s on main_1_1, with target D1 exposure 10572.4 veh-s; auxiliary events were not pooled. Zero-launch remeasurement repaired only the capability-record path binding and passed all eight engineering/measurement checks; the original ledger measurement_rejected event remains preserved. No independent seed or holdout read. Stage 0.5 Gate, Stage 0.6, Protocol Lock and Stage I remain unchanged. Report: `docs/STAGE_0_5_ROUND2_TASK1_EXECUTION.md`; final evidence: `evidence/results/RES-STAGE-0.5-ROUND2-TASK1-20261028/execution_final_v1/`.

# AAD Current State Snapshot

## Historical — 2026-10-28 Round1 Task3 scientific decision and Round2 freeze candidate

Verified: Round1 engineering/evidence closure is ready. The recommended scientific space preserves S_UPSTREAM_MAIN, mainline target lanes 1–5 y[150,350), [120,390) s, C_INPUT_ROUTE and separate auxiliary diagnostics. A single static Round2 candidate is prepared: current B00 A03 heterogeneous Krauss vTypes with only minGap 2.5→1.0. Candidate inputs, decision matrix, acceptance matrix and SHA are bound in RES-STAGE-0.5-ROUND1-TASK3-DECISION-20261028. Status is ROUND1_AWAITING_RESEARCHER_DECISION; SUMO/TraCI=0, Stage 0.5 blocked, Stage 0.6 and Stage I unchanged.

## Historical — 2026-10-28 first-round evidence-consistency repair

Verified: R1 B10/B01/B11 were each executed once and B00 A03 was reused; the first-round package now computes event counts from `event_inventory.csv`, `count_reconciliation.json`, and R1 `arm_comparison.json`. Corrected classification is B11 full 16/19 auxiliary and window 16/17 auxiliary; the remaining full events are two window-outside `target_main` events and one window `other_upstream_mainline` event. Local manifest self-reference is false, SHA256SUMS independently checks all listed payload files plus manifest, and source R0/R1/offline/week SHA bundles pass. Offline regression evidence is saved with 1,353 passed, 28 pyarrow/parquet dependency failures, and 4 skipped; SUMO/TraCI launches remain 0. Stage 0.5 remains blocked; Stage 0.6 and Stage I are unchanged.

Evidence: `evidence/results/RES-STAGE-0.5-FIRST-ROUND-OFFLINE-DECISION-20261028/`; report: `docs/STAGE_0_5_FIRST_ROUND_OFFLINE_DECISION_20261028.md`.

## Historical — 2026-10-28 R0 offline design packet（任务标签；实际准备2026-10-27起）

Verified：R0离线候选包READY_FOR_RESEARCHER_REVIEW，科学冻结AWAITING_RESEARCHER_DECISION；基线HEAD4a7c204、accepted A03精确绑定。完整610725状态与raw FCD逐项核对，正式全上下文P2=0（84227缺失点仍缺失），不推断未观测风险。B10/B01/B11候选与60辆匝道映射完成、未执行；新SUMO/TraCI0。源/目标/cohort/合格物理路径和精确操纵待决；Stage0.5科学Gate仍blocked，Stage0.6/StageI/历史Not Accepted不变。 证据：evidence/results/RES-STAGE-0.5-R0-DESIGN-PACKET-20261028/；审查报告：docs/plans/2026-10-28-stage-0-5-r0-design-freeze.md。

## 2026-10-27 Weekly B00 accepted; Stage I remains BLOCKED

Verified: A03 completed420s/8400native steps, independent receipt and all8 measurement checks Pass; B00_EXECUTED_MEASUREMENT_ACCEPTED. This task had3 real B00 starts: A01/A02 resource-coverage failures retained; A03 sealed trajectory independently remeasured with zero new launches after a coordinator import fix.1150declared=1005inserted+145native pending;857arrived/148active; collision/teleport/discard0 with complete required observation.18/18state/D1 support, E=9778.4veh-s, localP2=0. Final isolated software:1386passed/17skipped/7native excluded; audit denied0/SUMO0; compileall/docs/hash Pass. Scientific interaction Gate blocked; numerical budget/protocol candidate are Proposed, StageI BLOCKED. Historical Not Accepted unchanged. Evidence: docs/AAD_WEEK_TO_STAGE_I_2026-10-27.md; evidence/results/RES-AAD-WEEK-20261027-V1/; evidence/results/RES-STAGE-0.6-WEEK-20261027-V1/. Older blocks below retain their historical time points.

## 2026-10-27 B00已真实启动：BLOCKED_BY_VERIFIED_HARD_FAILURE

Verified：ENG-01/02/03修复、无数据全量1361通过/16跳过/7原生排除、compileall、修复后3s原生集成及独立回执Pass；纯Git定向165通过。新candidate-v8及聊天来源授权、实时硬检查完成后已直接执行一次B00（版本/仿真/真实TraCI各1）。最终状态BLOCKED_BY_VERIFIED_HARD_FAILURE：首个simulationStep发生i0007_i0007 slow lane ahead原生Error；冻结输入为15.23m/s、位置233.91m，下游main_2限速10m/s，按既定停止规则终止，420s未完成。仅t=0初始身份快照有效，末态插入/pending/discarded及全程碰撞/teleport均Unknown；三XML截断，18格测量不验收。capsule退出1，SUMO退出码未成功观测；后代已清理且无残留PID。未重复相同失败。具体初态/下游限速/原生Error停止规则冲突需科研决定，不能伪装成工程修复。旧Not Accepted及Gate不变。依据：docs/STAGE_0_5_B00_CLOSURE_2026-10-27.md；evidence/results/RES-STAGE-0.5-B00-NATIVE-V1/。下方为历史时点。

## 2026-10-27 B00科研准入审查V1（Verified audit / Research approval pending）

只读优先审查基线origin/main=753b666a3c9e4b8d88add2ead1973ff8e2d4439f。candidate-v6精确三SHA、347历史文件、38源按Git属性检出及12生产源闭包复核一致，现有SMOKE独立verify_receipt通过；没有新的live环境认证。工程accepted与科研approval分层，不自动授权。新增15项矩阵/9项研究者决定；高优先级待审：预检ready未检查policy accepted_build=false，可能先预约/attempt后晚拒绝；collision getter缺失在循环被or 0处理；summary缺逐车数值交叉核算且accounted pending不等于全部插入。Research Proposal：暂缓可执行批准，先另任务复核/修复并重绑；本轮不改守卫、候选、输入或锁。DS38确认为仅38初态速度10→max，其余79初态及1033非初态不变，实际插入/i0007/测量支持仍未知。科研审批、历史Not Accepted、Gate/δ/h/B/Stage1.1均保留；本轮SUMO0/真实TraCI0/新科研轨迹0。报告：docs/STAGE_0_5_B00_SCIENTIFIC_ADMISSION_REVIEW_V1_2026-10-27.md；审计：docs/audits/stage_0_5_scientific_admission_review_v1/。下方为历史时点。

## 2026-10-27 B00 candidate-v6 工程准入（Verified / 待研究者审批）

新增不可覆盖 candidate-v6，独立复核347份封存文件、原生产 verify_receipt Pass、12源闭包/8031运行时文件及B00输入/支持/18测量参考/资源策略精确绑定。静态预检仅保留实时检查要求；当前无SUMO的完整Linux技术预检 technical_errors=[]、ready=true、READY_FOR_RESEARCHER_APPROVAL。proposal SHA=b43e2d3af03dd53dd23bee3abd027725f298f58c97a2ae73d868ca9168a229b3。工程证书的accepted仅表示静态输入/资源资格与工程链，不证明B00实际插入、测量支持或科学效应。科研execution_allowed/researcher_confirmed/protocol_frozen及profile accepted_for_new_task仍false，native_launch_locked=true，旧B00 policy accepted_build=false硬锁保留；没有科研授权迁移。candidate-v5/历史失败/SMOKE归档原字节保留，历史Not Accepted、Gate/δ/h/B/Stage1.1不变。本任务SUMO0/真实TraCI0/新B00轨迹0。依据：docs/STAGE_0_5_B00_ADMISSION_V6_2026-10-27.md；docs/audits/stage_0_5_ready_to_admit_v3/candidate-v6/；evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v6/technical_preflight.json。下方为历史时点。

## 2026-10-26 SMOKE_V4_20261026_3：SMOKE PASS（最新）

同一精确授权在辅助流程修复/提交推送及完整实时验收后实际执行一次：launch1/版本进程1/仿真1/真实TraCI1，3s合成60步，10/5/10限速施加/时钟/回读全验收；FCD/summary/tripinfo有效，原协调器和独立verify_receipt均Pass。66资源采样、峰值RSS100130816B、最大采样间隔0.345776584s，1GiB/16MiB预算及隔离/清理通过，无残留进程，无重试。新授权envelope SHA=`a9ce5a370957387690adfcfc953e7d20d5a877d3d73e628418bd73b816b1271d`；结果SHA=`ae4ce45d42b37b4b42598987c9bae22c50f69641b80ee49c5c5d2449f2df0c64`。原r5/proposal/runtime/12源/输入/policy与false envelope不改，旧失败result/SHA保留。仅工程SMOKE PASS，candidate-v5/B00仍BLOCKED_ENGINEERING、四false/历史Not Accepted/科研Gate/δ/h/B/Stage1.1不变，新B00科研轨迹0。依据：`docs/STAGE_0_5_V4_SMOKE_3_CONTINUATION_2026-10-26.md`；证据`docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/authorized-execution/`。下方为历史时点。

## 2026-10-26 smoke 3继续执行（Active）

研究者明确继续同一精确授权：上次辅助预检异常、launch0不消耗唯一实际尝试。修正版在`docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/continuation-r2/`，旧脚本/result/SHA原字节保留。修复可选sysctl、已有审计目录判定、显式独占输出及安全日志；使用真实无害userns/Landlock/seccomp/systemd/cgroup检查与原生产预检。仅辅助脚本改变，r5/proposal/12源/输入/runtime/policy不改；本段登记时仍0 launch/0 SUMO/0 TraCI，完成测试及辅助修复提交后继续实时验收与唯一launch，不重复询问授权。科研Gate、candidate-v5四false、历史Not Accepted不变；本轮最终结果以后续continuation记录为准。

## 2026-10-26 V4 smoke 3启动前停止（最新）

研究者精确授权SMOKE_V4_20261026_3后，本轮新纯Git检出实际135项通过、20条命令及38源码/12 Git生产源核验完成；r5绑定核验后，任务辅助预检脚本错误假定WSL必须提供`/proc/sys/kernel/unprivileged_userns_clone`，因该文件缺失抛FileNotFoundError，未完成实时隔离/资源验收。状态`PRELAUNCH BLOCKED`，按停止规则未重试、未创建新授权envelope、未调用launch；SUMO版本进程0/仿真0/真实TraCI0/步数0/科研轨迹0，无生产receipt/acceptance。不能把可选sysctl缺失解释成内核能力失败。原r5/false envelope/candidate-v5不改，B00仍BLOCKED_ENGINEERING、四false/硬锁/历史Not Accepted/Gate/δ/h/B/Stage1.1不变。依据：`docs/STAGE_0_5_V4_SMOKE_3_2026-10-26.md`；独占审计`docs/audits/stage_0_5_linux_native_v4/smoke-20261026-3/`。下方为历史时点。

## 2026-10-26 V4 r5 严格校验与新准备（最新）

`PREPARED / AWAITING_EXPLICIT_AUTHORIZATION`；研究准入仍 `BLOCKED_ENGINEERING`。版本解析改为独立整行精确 release，拒绝 `.1/-dev/+custom/rc1` 及同行附加文本；最终V4离线122项通过。全新 `/home/shen/AAD/code/tmp/stage05_v4_20261026_r5` 绑定本轮修复、重新生成的完整Linux1.26/TraCI22运行时清单与新六组内核探针，不复用r4生产接线证据。新 `SMOKE_V4_20261026_3` proposal SHA=`a5f419029a7dc3ddc527d9b7e7e824c9f0f3779f4f3e17e769d87d472ca4a550`，envelope SHA=`6b37149d000f28258ee22bb499d7db7ee0e7a1255d4195c4bb7658f5aae8a463`，`engineering_authorized=false`，未启动。新candidate-v5使用 `aad.native-admission.v4` 与Linux绑定，保留全部B00科研定义；实际预检因当前生产回执未验收阻断，正常待研究者批准另列。四false/硬锁/历史Not Accepted/Gate/δ/h/B/Stage1.1不变，本轮0 SUMO/0真实TraCI/0新科研轨迹。依据：`docs/STAGE_0_5_V4_PREPARATION_2026-10-26.md`；新审计 `docs/audits/stage_0_5_linux_native_v4/prepared-20261026-r5/`；验证数字以其中validation_record为准。Context Consistency Check已完成；下方为历史时点。

## 2026-10-26 Linux V4 合成集成（最新：仍未Ready）

明确授权的一次 `SMOKE_V4_20261026_2` 在真实 Linux capsule 中完成了生产 broker/controller 接线，但在控制器版本预检阶段因 SUMO 1.26 CLI 输出格式解析过窄而失败；未建立 TraCI 连接，也未启动合成仿真步。失败证据、六组 r4 原生隔离探针和固定 runtime allowlist 见 `docs/audits/stage_0_5_linux_native_v4/collection-20261026-r3/`，工程记录见 `docs/STAGE_0_5_LINUX_NATIVE_V4_2026-10-26.md`。控制器/回执解析已修正并有 63 项定向回归，但 r4 staging 仍绑定修复前源码，不能把修复后的代码写成已通过原生 smoke；新任务仍 `BLOCKED_ENGINEERING`，需要新 staging 和新的单次授权。候选包 `evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/candidate-v4/` 保留 `execution_allowed=false`、`researcher_confirmed=false`、`protocol_frozen=false`、`accepted_for_new_task=false`。本轮合成 SUMO 版本进程 1、真实 TraCI 0、新科研轨迹 0；历史隔离事故 `Not Accepted`、Gate、δ/h/B、Stage 1.1 不变。

## 2026-10-26 WSL限范围解阻（历史：仍未Ready）

显式授权后，WSL工作目录固定/home/shen/AAD（非Git checkout），只新增code/tmp独立临时探针。Linux namespace/Landlock3/seccomp/systemd-cgroup六组14判据成立，含文件/子进程/网络/资源及失败保留；证据已接入预检和第八项验收。现有Linux SUMO1.18不同于提案Windows1.26，Python缺必要依赖，完整控制器capsule未成立。四false、硬锁、历史Not Accepted和全部科研Gate不变，0 SUMO/netconvert/真实TraCI/新轨迹。只做相关回归，不重跑1130项；candidate-v3仍BLOCKED_ENGINEERING。依据：`docs/STAGE_0_5_WSL_ISOLATION_2026-10-26.md`；下方为历史时点。

## 2026-10-26 V3首次准入工程（当前：未Ready）

任务AAD-0.5-READY-TO-ADMIT-V3：八项验收已改为实际封存产物/身份日志重建/正式C6-D1/逐格时间与右端点/供给回读/资源/隔离证据推导，增加TripInfo未完成/未出发输出。0750四臂有独立具体输入候选，首个建议B00 DS38 seed20261201；仍Proposed，0805暂停。新预算/账本独立、实际0次；旧C6、账本、提案和既有manifest未改。Windows无已配置容器入口，WSL启动能力探针被自动审批按AGENTS拒绝，未执行；OS隔离仍Unknown/Blocked，原生硬锁保留，不能报告READY_FOR_RESEARCHER_APPROVAL。三个执行标志及accepted_for_new_task均false，历史事故Not Accepted，Gate/δ/h/B/Stage1.1不变，0 SUMO/0真实TraCI/0新轨迹。

依据：`docs/STAGE_0_5_READY_TO_ADMIT_V3_2026-10-26.md`；`docs/plans/2026-10-26-stage-0-5-ready-to-admit-v3.md`；`docs/audits/stage_0_5_ready_to_admit_v3/`；`evidence/admission/AAD-0.5-READY-TO-ADMIT-V3/`。最终版本/验证数字见本任务validation_record及final_blockers；下方保留历史时点。

最终软件验证：定向163通过/1跳过，全量1130通过/15跳过/7原生测试排除，编译/strict docs/旧便携证据通过，25源码与无数据克隆字节一致。最终candidate-v2 proposal SHA `978fe0222a3fc00bb7a92b8c9065a204df0233449c6f778070628876864f6edc`；技术预检仍为OS隔离未接受及原生构建硬锁两项阻断，不可执行。candidate-v1为保留的中间快照，已源码漂移失效。最终机器矩阵：`docs/audits/stage_0_5_ready_to_admit_v3/final_blockers.json`。

## 2026-10-26 V2身份完整性最小修正（软件验证通过）

`IdentityObserver.finish()`将非初始步的teleport_start/end不可用计数纳入完整性拒绝；初始快照按设计不可用仍单独记录。API_coverage为稀疏Counter快照，新增测试的零计数读取改为get(key,0)；首次117通过/10失败/1跳过审计保留。继续后定向127通过/1跳过、全量软件1094通过/15跳过/7原生测试排除，编译/文档/便携证据检查通过，仅合成软件验证。不改状态转移、初始化或测量定义。既有证据/账本和f6ca808源码绑定原样保留，不能视为绑定了当前修正；本轮0 SUMO/0新轨迹、无真实TraCI连接。四个准入标志false、Gate不变，原生隔离Unknown、历史偏差Not Accepted。

依据：`code/scripts/stage_0_5_identity_observation.py::IdentityObserver.finish`；`code/tests/test_stage_0_5_v2_admission.py`；`docs/STAGE_0_5_V2_IDENTITY_CONTRACT.md`。

## 2026-10-25 V2准入工程闭环（最新）

Verified：新增身份状态机/逐步getter适配、初始化静态保真校验、精确历史允许清单、锁定执行适配器与隔离守卫，仅合成软件验证；旧核心科学源/提案/输入/账本不改。六份历史FCD完成当前C6重测及独立几何/事件/D1核对，两份已有C6基线直接复用。原[300,420)结构N33/32→14/10，四时序样本N1/2/1/2→0/0/0/0且支持改变，不能解释为风险消失。0750仍仅DS38候选，0805潜在冲突52辆，i0007未解决。原生启动构建硬锁；本轮0启动/0新轨迹，V2真实账本0，无累计cap。四条件/初始化/重复仍Proposed；三个执行标志和accepted_for_new_task均false，原生隔离Unknown、历史偏差Not Accepted，Gate/δ/h/B/Stage1.1不变，WP2–WP5未整体完成。

依据：`docs/STAGE_0_5_V2_ADMISSION_ENGINEERING_2026-10-25.md`；`docs/STAGE_0_5_V2_IDENTITY_CONTRACT.md`；`docs/STAGE_0_5_V2_ADMISSION_VALIDATION.md`；`evidence/results/RES-STAGE-0.5-V2-ADMISSION-ENGINEERING-V1/`。下方“尚缺适配器/仅两份重测”等描述仅保留历史时点，不代表最新工程状态。

## 2026-10-25 V2追加式研究任务（当前）

Agreed：研究者取消新研究累计次数上限；新任务AAD-0.5-INTERACTION-RESEARCH-V2独立hash链追加账本，实际0次。旧任务一次failed_stop/3次上限及历史余2原字节保留，不再限制V2。已审计324响应、58条件状态、20到达时序；C6只重测两份旧FCD，其他旧P2未升级。四臂同政策基线/供给/匝道/联合为Proposed，未冻结、不执行。0750 DS38未获批，i0007未解决；0805 main_2另有8辆非10速度>5，不能照搬44辆策略。身份采集、实际执行适配器和新批次隔离证明尚缺，POLICY-A-VALIDATION-SCOPE-01仍Not Accepted。Gate、δ/h/B/Stage1.1不变，WP2–WP5未整体完成。

依据：`docs/STAGE_0_5_RESEARCH_V2_AUDIT_2026-10-25.md`；`docs/STAGE_0_5_RESEARCH_V2_BUDGET.md`；`docs/plans/2026-10-25-stage-0-5-interaction-research-v2.md`；`evidence/results/RES-STAGE-0.5-INTERACTION-RESEARCH-V2/`。以下内容保留其历史时点。


## 2026-10-25 初态速度候选（当前待确认）

研究者只授权离线准备。核查0750初态117辆仅38辆为10；独立DS10MAX-V1只将这38辆改max，另外79辆和全部非初态不改。ID1、ID3候选已准备，ID2暂缓；新的精确计划/提案及38辆范围待研究者确认。未启动SUMO，本轮0次、累计1/3、剩2；原失败/原账本保留。max会影响插入速度/时序/初始化，i0007原警告仍未解决；新支持Unknown，旧基线仅作不同初始化历史参考。隔离Not Accepted、Gate和δ/h/B/后续阶段均不变，WP2–WP5未整体完成。

依据：`docs/STAGE_0_5_DEPART_SPEED_CANDIDATE_2026-10-25.md`；`docs/plans/2026-10-25-stage-0-5-depart-speed-candidate-v1.md`；`evidence/results/RES-STAGE-0.5-DEPART-SPEED-CANDIDATE-V1/`。以下原内容保留。


## 2026-10-25 政策A首次尝试失败，后续停止

研究者已批准最终诊断设计，精确计划/提案及隔离工程哈希已绑定。ID1_SUPPLY_0750在180s因待插入初态departSpeed=10与main_2限速5冲突退出，累计1/3；ID2/ID3未执行，余2未动用。18单元仅2个完整D1支持，另2个仅状态完整；完整270s比较不可评价。POLICY-A-VALIDATION-SCOPE-01仍Not Accepted，研究者允许有限继续的裁决保留；不重跑主工作区全量。Gate不变，WP2–WP5不标整体完成。

依据：`docs/STAGE_0_5_INTERACTION_DIAGNOSTICS_POLICY_A_EXECUTION_2026-10-25.md`；`evidence/results/RES-STAGE-0.5-INTERACTION-DIAGNOSTICS-V1/`。以下旧状态保留为历史时点。

## 2026-10-25 POLICY-A-VALIDATION-SCOPE-01（当前执行阻断）

补充全量回归误在主工作区运行，13项本地历史/原始数据测试变为可执行。998 passed的该次记录不计为有效隔离验证；任务级零验证资源访问不可认证、数据隔离不Accepted，Status: Awaiting Researcher Decision。源码审计详见 `docs/STAGE_0_5_POLICY_A_VALIDATION.md` 与便携 `validation_scope_incident.json`，不重读相关数据。先前独立纯Git回归985 passed保留其有限效力；最终源码在无数据Git克隆另获987 passed / 14 skipped / 7 deselected，定向9项及compileall通过，仍不能逆转隔离偏差。政策A仍Agreed；最终计划Proposed，新轨迹0/3，Gate不变。工程准备不能代替研究者对偏差及运行资格的裁决；未决前不按有效完成任务提交/推送。


## 2026-10-25 政策A与最终计划预检

Agreed：研究者选择政策A，保留elapsed[120,390)、供给扰动[180,240)，披露0750残留初态，不声称稳态。两条件18/18共同单元、真实N/E38/11794.3和50/12431.4独立复核；输入/资源快照通过。最终运行计划仍Proposed，未冻结，0/3次，未启动SUMO，Gate不变。以下旧状态块保留为历史时点。

依据：`docs/plans/2026-10-25-stage-0-5-interaction-diagnostics-policy-a-final.md`；`evidence/results/RES-STAGE-0.5-POLICY-A-PREFLIGHT-V1/`。


## 2026-10-25 C6/C7 offline phase

C6修复获研究者明确授权并完成两份旧FCD离线重测；物理间距与映射空间分离，跨路段/连接段不可观测关系降级。C7政策A/B待研究者确认，运行计划未冻结，0/3次新轨迹；不是WP2–WP5整体完成。

依据：`docs/STAGE_0_5_C6_C7_OFFLINE_DECISION_2026-10-25.md`；`evidence/results/RES-STAGE-0.5-C6-C7-OFFLINE-V1/`。


## 2026-10-25 Interaction diagnostics preflight

Current task AAD-0.5-INTERACTION-DIAGNOSTICS-V1: **Awaiting Researcher Decision**. D1 engineering edits are uncommitted; 50 related software tests pass and two historical baseline N/E checks match the independent oracle. Preflight confirms C6 (scaled spatial coordinates used as physical gaps) and C7 (one initial vehicle remains locally at120s in0750). Protocol not frozen; new trajectory attempts0/3; WP2–WP5 not complete. Gate unchanged.

Evidence: `docs/STAGE_0_5_INTERACTION_DIAGNOSTICS_2026-10-25.md`; `docs/audits/stage_0_5_interaction_preflight_v1/preflight.json`; `execution_ledger.json` in the same directory.


## 2026-10-24 Issue #1：工作包1证据审计与冻结候选（优先入口）

新增 [证据审计与非覆盖式更正](../docs/STAGE_0_5_WP1_EVIDENCE_AUDIT.md) 和 [冻结候选 WP1-FC-v1](../docs/STAGE_0_5_ACCEPTANCE_FREEZE_CANDIDATE_V1.md)，状态 **Proposed / Awaiting Researcher Decision，未正式冻结**。在基线 `c94e6cc` 上离线核验2个已访问真实校准源与74份既有模拟输出，无新轨迹/额度消耗、第三窗轨迹/locked holdout访问。

**Verified Fact**：真实D1 N/E=147/31051.6、216/33091.1独立复现；44个历史模拟局部N、74个点分母复现，边分母影响有新版本聚合表；30份早期grid缺显式前车incarnation，不认证正式等价。C4的829382与644067及tau/closing差异由全采集/内部窗混用精确解释，追加erratum、历史包不改。C2三种共同分块和C5文字计划/执行判据反事实已量化；C3错误字段实际g/closing已确认。**C4（所审计两源）Resolved by evidence；C1/C2/C3/C5 Partially resolved，科学选择及生产修复仍Awaiting Researcher Decision。** 当前runner与freeze源码SHA不同，完整历史源码冻结合规Unknown；不能只凭哈希存在声称一致。

R1–R5压缩为候选§4的五项选择，delta/h/B、窗口/分块、条件输入、预算/seed和独立验证仍未批准。第三窗已使用的时间迁移角色、B0隔离Unknown、原剩3次保留全部保留。历史“唯一剩余阻断为交互相容”不足以表示正式准入；测量/支持/计划一致性也未齐。Gate=`pending_simulation_sample`、现实覆盖/科学资格false、Protocol Lock/Stage1.1禁止不变。验证见 [执行记录](../docs/STAGE_0_5_WP1_VALIDATION.md)。

## 2026-10-24 Stage 0.5 验收协议草案与审计提醒

新增 `docs/STAGE_0_5_ACCEPTANCE_PROTOCOL_DRAFT.md`（**Proposed / Awaiting Researcher Decision，未冻结**）：汇总已批准 D1–D5、R1–R5、指标矩阵、delta/h/B、三类判定与验证资源边界。当前 Gate 与既有决定不变，无新实验。

**先读草案 §3 冲突记录，再复用下方历史结论**：当前状态支持/时序诊断以可评价状态点数×0.1估计 P2 分母，未落实 D1 连续边/可靠跟驰资格；真实块云裁 [150,350) 后按全球100m格分块而边块仍除100m，仿真却用200m整体块；部分时距字段实际为gap/closing；报告真实参考值与 `real_domain.json` 不一致；冻结计划覆盖判据文字与执行不同。上述五项均 `Status: Awaiting Researcher Decision`，未修改源码、配置、结果或 Gate，不把它们追写成已修复或重新判定。历史“状态支持已成立”及模拟风险率不能未经审查直接用于正式验收。

第三窗口 `us101__0820_0835` 已在状态支持任务中使用，不能再称未接触 holdout；原收口保留3次额度不自动移给新任务。R1–R5仍全部开放。详细证据/函数/受影响文件与工作包2输入条件见草案；当前任务仅核查已发布摘要，未重读验证轨迹或 locked holdout。

## 执行环境导航（2026-10-24）

- **默认环境**：Windows 原生环境；WSL（Ubuntu）是可选 Linux 任务执行与临时实验环境。完整长期规则以 `AGENTS.md` §13 为唯一入口，WSL 不新增项目事实来源。
- **唯一 AAD WSL 工作区**：Windows `\\wsl.localhost\Ubuntu\home\shen\AAD`；Ubuntu `/home/shen/AAD`。
- **待核验**：容量目标约 20 GB，缩减由其他执行者独立负责；当前容量、实际可用空间、工作区可用性均为 `Pending Verification`。本次只登记文档，未执行任何 WSL 操作，未验证可用性或容量目标达成。

## 论文及研究材料位置（2026-10-23）

- **当前最新版论文在 Overleaf**：正文、公式、符号与正式表述以 Overleaf 当前版本为准；本仓库不保留活动 `.tex` 论文源，根目录 `paper/` 已于 2026-10-23 退役。未登记真实项目链接前不写 URL。
- **GitHub 仓库负责当前实现与实验状态**：代码、配置、实验产物、正式决策与 Gate 以本仓库为准；新会话先读本文件，再核查源码、config、experiment、audit、manifest 与正式结果。
- **历史 PDF、图稿、组会 PPT 与辅助笔记在本机** `D:\shen\OB\科研\TJU\AAD`（`AAD\` 00–05、`历史Paper\paper\`、`历史Paper\figure\`、`组会PPT\`、`组会笔记\`）；仅作历史与辅助上下文，不进入 Git。
- **OB 笔记只提供辅助上下文**，不能覆盖本文件与仓库当前状态；当前科研状态仍以本文件及最新源码、实验结果为准。导航：`docs/PAPER_AND_MATERIAL_SOURCES.md`。

## 2026-10-21 边界到达时序与交互动态诊断（当前）

`RES-STAGE-0.5-ARRIVAL-TIMING-V1`（AAD-0.5-ARRIVAL-TIMING）：检验「等间隔到达丢失真实时间结构」是否是上一轮交互相容缺口的解释。**Gate 不变。**

**决定性发现（Observation）**：主线入口是**排队受限**边界，声明的主线到达结构被入队过程完全抹平——声明主线间隔 CV 0.25 vs 0.86（0750）/ 0.20 vs 0.91（0805），实现后为 **0.820 vs 0.831 / 0.788 vs 0.851**，平均入队延迟 25–30 s / 4.5–5.6 s，92%/61–65% 的车辆被延迟超过一个平均间隔。因此**主线到达时序不可施加**。匝道入口不受此限，实现 CV **0.006 vs 1.397 / 0.008 vs 1.412**（延迟 0.05–0.45 s），故本轮有效对照是**仅匝道到达时序**。

**审计事实（Observation）**：主线入口对应真实 `y ≈ 0 m`，而此前需求取自 `y = 150 m` 穿越率并施加在入口，**错配 150 m**；本轮改用真实**首次观测**事件（中位 `y_first` 11/23 m）并声明入口带 `y ≤ 30 m`。事件 0750 = 989 主线 + 57 匝道、0805 = 873 + 66；与初始状态的身份交集为空；被重叠过滤器丢弃的车辆不被重新引入。车型不可逐车获得。

**配对结果（20 次，0 teleport / 0 collision，状态支持 20/20）**，E−U：速度离散 **+0.25（5/5）/ +1.78（5/5）** 朝真实值上升（真实 3.64/3.99；U 1.17/1.78 → E 1.42/3.55）；净拉开份额 −0.004（2/5）/ **−0.112（0/5）** 反向恶化（真实 0.530/0.537）；局部 P2 率 **−0.23（2/5）/ +0.80（5/5）** 两窗口方向相反、绝对值仍低一个数量级；最大异常连通域 −24.4 / −5.6（均 0/5）。

**波诊断修正（H3 Supported）**：旧绝对 10 m/s 份额在平均 9.7 m/s 的配置上无判别力，降级为历史描述。新 `temporal_position` 相对定义（单元格 ≤ 同位置自身时间分布 15% 分位、50 m × 10 s、8 邻接）+ 相邻位置互相关滞后独立裁决 + 置换零模型：**真实两窗口均 `propagating_structure`**（互相关上游份额 1.00、中位 −5.0 m/s、零模型超越 0.000、敏感性全网格不变）；上一轮周期到达运行同一诊断下为 `uncorroborated_structure`（0.31/0.23）。合成验收区分上游/静止/下游/无异常/含缺口。任务书建议的密度条件基线形式**不具判别力**（异常全落上游位置、无波前），作为否定结果登记。

**判读**：H1 **Partially Supported**（因果归因只能落在匝道流）；H2 **Not Supported**；H4 保持未决。Stage 0.5 仍被交互相容层阻断。新增保真判据（实现到达结构是否在两臂间仍可比）在**主线**触发，据此把主线因果归因判为不能成立，并按停止规则未追加第三种供给编码或新参数搜索。`never_inserted` 达 13%（0750），两臂缺口数不同，已披露。

第三窗口读取 0 次、locked holdout 0 次。Gate=`pending_simulation_sample`、`scientific_claim_eligible=false`、`reality_coverage_accepted=false`、`protocol_lock_allowed=false`、`stage_1_1_allowed=false`。

报告 `docs/STAGE_0_5_ARRIVAL_TIMING_DIAGNOSTICS.md`；计划 `docs/plans/2026-10-21-stage-0-5-arrival-timing.md`；证据 `evidence/results/RES-STAGE-0.5-ARRIVAL-TIMING-V1/`。

## 2026-10-21 条件性交通状态验证（历史）

`RES-STAGE-0.5-STATE-SUPPORT-V1`（AAD-0.5-CLOSURE）：把阻断层「状态支持」从 `Evidence Insufficient` 提升为可复现正向证据，并把唯一剩余缺口定位到「交互相容」。**Gate 不变**，结论等级为既有事实修正 + 条件性状态域。

**事实修正（必须先读）**：上一轮「真实间距低于 `v·tau+minGap`，故抬 `tau` 必然有害」只对**分层 12 对样本**成立，被写成总体陈述。按**局部区域全体可靠跟驰观测**（829,382 条，`0<net_gap≤80 m`）的线性平衡比例估计，`tau_eff = 1.5393`（0750）/`1.5687`（0805）s，留出窗口 `1.5570`；对应的解析车道能力 **1,981–2,013 veh/h/lane** 与观测**最大 30 s×100 m 块流量 1,996.4** 一致，而冻结 `tau=1.0` 给出 2,882（高 44%）。仍成立的是更窄的陈述：单一 `tau` 无法拟合总体两侧尾部（每车 `tau_eff` p05 0.58–0.61、p95 2.97–3.04，23–25% 的车 <1.0 s）。`(tau, minGap)` 只能联合辨识。

**真实状态域**：局部块云 `k ∈ [14.52, 76.10]`、`v ∈ [2.75, 15.79] m/s`（真实局部区域从不是自由流）；域用 k 分带 2.5/97.5 速度包络 + 同构造闭合速度包络表达；**跨窗口基线由数据自身给出**（0750 有 0.833 落在 0805 包络内，0805 有 0.636 落在 0750 包络内），因此成员判据不是任意阈值。

**网格（30 次）**：`B_frozen`（tau=1.0）在 5 个声明供给水平**全部出域**；`B_mean`（tau=1.566）/`B_het`（每车 tau 取自真实分布分位）在 `vlim=10 m/s`（声明能力 7,971 / 8,130 veh/h 对穿越需求 8,506）**同时通过两个校准窗口**（`k=48.4/41.8`、`43.4/43.4`；`v=8.26/9.96`、`9.84/9.68`）。5 个独立 seed 复现（`B_het` 0750 `k=43.98±1.10`、`v=9.70±0.27`、`tau_eff=1.565±0.012`），20/20 运行 0 teleport、0 collision。

**失败层（交互相容）**：局部 P2 率 **0.9–1.5 events/veh-h** 对真实 **17.0/23.5**（低 12–25 倍）；速度离散 2.33–2.61 对 3.64–3.99 m/s；净拉开份额 0.395–0.432 对 0.530–0.537。原因是闭合速度几乎为 0 的均匀同步流几乎不产生 `TTC<2 s` 且持续 ≥0.2 s 的段。低速波在本轮**无判别性证据**（`jam_waves` 的继承绝对 10 m/s 阈值几乎等于该配置平均速度 9.7 m/s），已登记为度量局限。

**结构变体（4 次，匹配能力 8,130/7,933）**：4 车道缩减（能力下降约 18%）把离散度 5.09–6.02、净拉开份额 0.563–0.623、局部 P2 率 **18.2–25.5** 带进真实范围，但平均状态越界（`k=51–55`、低速份额 0.445–0.505）。→ **供给的「水平」决定平均状态，「形式」决定相对运动与风险事件**；两种编码各满足一半，预声明判伪规则已触发，未尝试第三种编码。

**留出窗口（freeze 后 4 次）**：真实 `us101__0820_0835` 为 `k=47.57`、`v=7.37`、`tau_eff=1.557`，**落在校准域内**（域覆盖率 0.851 ≥ 基线 0.636）→ **状态域可迁移**；同一 `vlim=10` 供给在其较低需求下欠拥堵 → **具体供给值不可迁移**，因为下游供给在观测段内不可识别。

**四项必要条件**：测量可信 Met；状态有支持 **Partially** Met（平均状态成立、关键动态未成立）；交互相容 **Not** Met；独立证据 Met（仅状态层）。合取不满足 → Stage 0.5 **未通过**。唯一剩余阻断是交互相容层。能力更正的工程上报缺陷（异质臂原按最低时距类计能力）已修并写入 `mechanism_analysis.json`，不影响任何判据。

**风险测量定义一致性**：指数 `rho=exp(-TTC/tau)`（`tau=15.364279197080283`）**已是被正式批准的主定义**；实现/配置/测试本已一致；论文原为阈值线性 + 求和，已同步为指数 + 车辆等权，线性版本明确标记为历史基线，并新增定义测试。

第三窗口读 4 次（冻结后，留出验证），locked holdout 0 次。Gate=`pending_simulation_sample`、`scientific_claim_eligible=false`、`reality_coverage_accepted=false`、`protocol_lock_allowed=false`、`stage_1_1_allowed=false`。δ/h 仍 `Tolerance Not Yet Justified`，但本轮证明它们不影响该判定（失败发生在"是否有支持"与"机制是否相容"层）。58 次轨迹生成运行单独记账，与 2026-10-20 冻结的"剩余 3 次"分属不同授权。

报告 `docs/STAGE_0_5_CONDITIONAL_STATE_SUPPORT.md`、`docs/STAGE_0_5_FORMAL_RISK_DEFINITION_CONSISTENCY.md`；计划 `docs/plans/2026-10-21-stage-0-5-state-support.md`；证据 `evidence/results/RES-STAGE-0.5-STATE-SUPPORT-V1/`。

## 2026-10-20 方法扩展与行为诊断（当前）

`RES-STAGE-0.5-METHOD-EXPANSION-V1`（AAD-0.5-METHOD-EXPANSION）：在**更正一处初始化误判**之后，用 324 次有界诊断运行把「`tau` 能不能修复错配」这件事在微观层面彻底否证，并给出可出资的替代方向。**Gate 不变**，结论等级 **Level 2 + Level 3**。

**更正（必须先读）**：上一任务报告「48 个对×配置组合中 26 个被 Krauss 插入安全包络**拒绝**」是**错误结论**。源码与探针证明 SUMO 对失败的插入会在后续步**重试**（`MSLane::isInsertionSuccess()` 失败后车辆保持等待），旧重放实现只等 0.25 s 就中止并把延迟误记为拒绝。实测延迟 0.05–0.70 s（中位 ≈0.45 s）。已登记显式更正（`docs/STAGE_0_5_INITIALIZATION_FIDELITY.md`、`AI_CONTEXT/07_KNOWN_ISSUES.md`），旧报告正文按惯例不追溯改写。仍然成立的**弱化**结论：观测拥堵跟驰状态常落在冻结模型安全包络之外，表现为插入延迟。

**初始化（P3）**：两条**原生**路线均通过保真度与控制链核验——`native`（等待并记录延迟、按后车自身时间对齐）与 `none`（官方 `--insertion-checks none`，观测时刻精确进入）；**控制实验证明 `none` 不改变后续动力学**（原生即可插入的车辆对在两条路线下轨迹逐字节相同）。后车全程无 `setSpeed` 覆盖。

**覆盖与可辨识性（P2）**：5,815 个可靠连续跟驰段 / 186,529 s；近似稳定 40.4%/52.0%、加速 32.1%/24.6%、减速 27.5%/23.5%、低速 9.2%/25.3%、贴近跟驰 18.0%/31.8%；21–43% 的段含 ≥1 s 低速段 → **H1（缺行为阶段）大部分被反驳**，缺的是长连续段与完整排队循环。样本选择从「最长优先」改为**声明式车头时距分层**。`tau` 与 `minGap` 的效应在同一批车辆对上高度相关（r = **−0.944** / **+0.818**），**不可分别辨识**，与 Wang et al. (2022) 的实用不可辨识性结论方向一致；参数效应约为 seed 噪声的 **13.5 倍**。

**响应诊断（P4，324 次独立 SUMO 运行，0 失败；12 对 × 9 配置 × 同一 seed 集 3 个）**：配对差异（vs `K_tau1.0`）——**`tau` 单调有害** +18.31（1.3）/ +40.70（1.6）/ +72.51 pp（2.0），**三个 seed 符号一致**；`minGap`→1.0 改善 **−7.31**、→5.0 恶化 **+29.75**；`sigma=0` 改善 **−6.34**；**IDM(T=1.0) 最好 −5.52**（18/18 对改善），增益集中在**长期窗 −8.09** 而局部窗仅 −0.09；IDM(T=1.6) 恶化 +26.50。独立 **Newell 原型**（非 SUMO 原生）τ=1.0 → 50.94%、τ=1.6 → 85.42%，与 Krauss(53.08)/IDM(47.56) 同量级且随 τ 增大而恶化。seed 波动中位 1.5–5.2 pp，随 `tau` 增大。

**解读**：真实 US-101 车辆对的间距水平**低于**冻结 Krauss 的平衡式 `v·tau + minGap`，所以抬高平衡间距（增大 `tau` 或 `minGap`）必然变差，减小静止间距或去掉抖动才会改善。宏观反推的「有效 `tau`≈1.53–1.63 s」是**密度层面的等效量**，不是驾驶员的期望时距；把它当微观参数用，方向正好相反。**不同模型结构收敛到相近误差**（47.6/50.9/53.1%），说明剩余差距不是"选错模型"能一步解决的。

**P5 宏观**：门控未开（无配置获得配对证据支持），**未执行**新宏观对照；RC1/RC2/RC3 原样保留。

**文献**：Zotero 新增 3 条（Wang 2022 `4J5V4A3I`、Rhoades 2016 `4ABZDRVU`、Newell 2002 `DIVRKX7J`），集合 07/08/09 = 10/2/1；方法索引扩到 18 条并新增 `method_status_matrix`（Adopt/Adapt/Explore/Reject/Blocked，逐条记实施结果）。**附件上传失败**：本机 API `/items/<key>/file` 返回 `HTTP 400 MD5 hash not provided`（即使提供 `md5` 字段与 `Content-MD5`），已记录为待研究者用 Zotero 客户端挂接，并给出 4 个开放 PDF 链接；两个空附件条目已删除。

第三窗口 0 行、holdout 0 次。Gate=`pending_simulation_sample`、`scientific_claim_eligible=false`、`reality_coverage_accepted=false`、`protocol_lock_allowed=false`、`stage_1_1_allowed=false`。δ/h 仍 `Tolerance Not Yet Justified`。

报告 `docs/STAGE_0_5_METHOD_EXPANSION_SUMMARY.md`（综合）、`docs/STAGE_0_5_METHOD_EXPANSION_RESULTS.md`、`docs/STAGE_0_5_TRAJECTORY_COVERAGE_AND_IDENTIFIABILITY.md`、`docs/STAGE_0_5_INITIALIZATION_FIDELITY.md`；计划 `docs/plans/2026-10-20-method-expansion-baseline.md`；证据 `evidence/results/RES-STAGE-0.5-METHOD-EXPANSION-V1/`。

## 2026-10-20 文献依据的行为诊断（历史）

`RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1`（AAD-0.5-LIT-CAL）：把每个方法绑定到经原文核验的文献，并在**逐对微观层面**检验「有效 `tau` ≈1.6 s 能否修复错配」。**未新增科学结论支持，Gate 不变。**

主线 A（只读，20 个「窗口 × 规则」组合）：低速波的**方向与起始位置稳健**——10 种状态定义中除 2 条饱和规则（绝对 15 m/s；以工程值 27.78 m/s 为参考的 `λ<0.5`）外，**16/16** 均为向上游扩张，最早位置一律 **y=500–650 m**，反向传播速度 2.0–8.3 m/s。逐时间片空间置换零模型（1000 次、种子 20261031）：Duan `W<0.5`（窗口 p95）与 Saberi `λ<0.3–0.6` 下最大连通域显著超出随机排列（超越率 0.000–0.142，两窗口一致）；但 **0750 在绝对 10 m/s 下不可区分于随机（0.999）**，因此 TR-RECON 的「规模」结论收窄为**依赖相对速度定义**。饱和规则失效的原因是把工程配置速度当成实测自由流速度——两条源的参考速度本应来自 30 天 / 24 h 记录，本项目窗口只有 12–16 分钟，属**不可消除的口径差异**（Unidentifiable）。

主线 B（48 次独立微型 SUMO 运行，每窗口 12 对 × 2 配置，内部 0.05 s / 记录 0.1 s / ≤25 s）：前车由 TraCI 逐 0.05 s 施加并预补偿，**前车跟随偏差 0.013–0.112 m**（全部达标），后车完全由模型驱动。**26/48 组合的观测初始状态被 SUMO 自身 Krauss 插入安全包络拒绝（44%）**，集中在拥堵窗口（例：0750 观测净间距 10.65 m、速度 11.36 m/s，`tau=1.0` 下允许的插入速度仅 10.31 m/s）。候选 `tau=1.6` **未改善**跟驰行为：配对 Brockfeld 间距误差 **+19.57 pp**（95% CI [4.25, 35.51]，7 改善 / 13 恶化），间距偏差 **20/20 对变大**（+5.62 m，CI [4.90, 6.33]），`NRMSE(speed)` 基本不变（+0.00）。按观测车头时距分层：<1.0 s 与 1.0–1.5 s 分层显著恶化（+56.7、+63.8 pp）；1.5–10 s 分层接近中性（−2.60 pp，CI [−12.95, 8.56]）且速度指标略改善（−0.01，CI [−0.02, −0.00]）→ **指标冲突 + 状态异质性**。

**结论收窄（Derived）**：TR-RECON 的「有效 `tau` ≈1.53–1.63 s」是**拥堵区宏观平衡等效量**，不能当作单一微观 `tau` 使用。按预声明门控（「候选须在两窗口均改善间距误差且核心指标不恶化」）→ 判定为**不支持**，**主线 C 未执行**，RC1/RC2/RC3 原样保留。三处重放实现缺陷（后车 `setSpeed` 冻结速度、前车位置每样本领先、模拟/观测时钟错一拍）已修复并有回归测试，缺陷版本中间结果未进入任何报告数值。

文献（P0）：Zotero `TJU → AAD` 新建 `07_微观跟驰校准与轨迹重放`、`08_拥堵状态识别与时空传播`、`09_仿真校准规范与验证` 三个专题集合；补入 8 条经 DOI 核验的条目（Brockfeld、Kesting、Punzo、Krauss PRE、Krauß 博士论文、Sharma、Schrader、FHWA-HOP-18-036），Duan 2023 与 Saberi 2020 加入 08 并补方法标签，**未新建重复条目**。方法表区分「全文已读 6 篇（含公式与章节号）」与「仅元数据核验 6 篇（未据其采用任何公式）」。

日期勘误：`afdc3d0` 中三份文档原标 2026-10-21，核对 author/committer date（2026-10-20 20:20:17 +08:00）与本地时区后确认**实际执行日为 2026-10-20**，已在文档与 `budget_ledger_audit.json` 显式登记勘误，文件名与已提交正文按惯例保留。

预算台账：`RES-STAGE-0.5-FINAL-CLOSURE-V1` 的 FR1/FR2 与本任务的 48 次微型重放分属不同授权；RC1r/RC2r 亦未转移（`budget_ledger_audit.json`）。

第三窗口读取 0 行、holdout 0 次。Gate=`pending_simulation_sample`、`scientific_claim_eligible=false`、`reality_coverage_accepted=false`、`protocol_lock_allowed=false`、`stage_1_1_allowed=false`。

报告 `docs/STAGE_0_5_TRAFFIC_STATE_DEFINITION_SENSITIVITY.md`、`docs/STAGE_0_5_LEADER_REPLAY_BEHAVIOUR_DIAGNOSTICS.md`、`doc/literature-notes/STAGE_0_5_METHOD_EVIDENCE_MAP.md`；计划 `docs/plans/2026-10-20-stage-0-5-literature-calibration.md`；证据 `evidence/results/RES-STAGE-0.5-METHOD-DIAGNOSTICS-V1/`。

## 2026-10-21 真实交通重建与条件场景诊断（历史；原标注日期见文末勘误）

`RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1`（AAD-0.5-TR-RECON）：只读重建两个已批准校准窗口的交通过程，并按任务书 §3.2 重新规划诊断预算执行 3 项运行前冻结的 SUMO 诊断。**未新增科学结论，Gate 不变。**

几何（Observation）：轨迹独立识别出 US-101 段为 **5 条主线车道 + 驶入匝道（128.74–187.58 m）+ 辅助车道（187.58–399.22 m）+ 驶出匝道（399.22–450.84 m）**，与官方 NGSIM 元数据「五主线 + Ventura/Cahuenga 匝道间一条辅助车道」一致。已批准 D1 区域 `[150,350) × 车道 1–5` **内部含第六车道**，因此该区域不是闭合控制体（0750 残差 +67 辆）；改用六车道断面闭合区域得守恒残差 −28 辆 / 720 s（1.6%）与 +72 辆 / 660 s（5.1%）。

真实状态（Observation）：0750–0805 = 43.544 veh/km/lane、10.506 m/s、q=1,646.9 veh/h/lane、低速份额 0.0969；0805–0820 = 50.505、7.915、1,439.2、0.2530。边界需求 8,345 / 7,227 veh/h；驶入匝道官方 516 / 490 veh/h（轨迹法 690 / 665，差 34 辆未解释）；驶出匝道 355 / 360 veh/h。官方输入—输出表显示断面 **先积累后释放**（+24、+16、−38、−33）。**规模最大的低速波都最先出现在观测段下游端（y=500–650 m，0750 于 t=750 s、0805 于 t=180 s）并向上游扩张**（0805 最大波 300 s 内从 y≈600 扩到 y≈0–50，反向后传速度约 2 m/s）。同一流量在 27.78 m/s 下对应密度仅 16.5 / 14.4 veh/km/lane → **断面流量不能识别状态**。

条件场景诊断（运行前冻结计划 + `PLAN_SHA256`，各 300 s、内部 0.05 s、评估窗 `[180.0,299.7]`，SUMO 1.26.0）：RC1（5 车道 + 匝道 + 辅助车道观测几何、观测边界需求、空网、下游开放）→ **23.90 m/s / 21.05 veh/km/lane / q=1,811**（自由流，且流量高于观测）；RC2（注入真实拥堵初始状态 117 辆、下游开放）→ 前 30 s 16.71 / 34.14，**180 s 内完全退化为 23.81 / 21.20**；RC3（RC2 + 声明的条件 3 车道下游供给，解析容量 8,646 veh/h）→ **6.76 / 61.35 / q=1,492**（比目标更深）。三者均未落入真实目标 30 s 块包络 → `EvidenceInsufficient_StateSupport`；按预声明停止规则**未搜索参数、未执行独立 seed 重复、未加第 4 次构造**。

拥堵分支诊断（Derived + Hypothesis）：冻结 Krauss 参数下观测密度对应的平衡速度为 16.05 / 12.88 m/s（观测 10.51 / 7.92）；观测**密度**与观测**净间距**两条独立路径一致给出有效时间间隔 **1.527/1.628 s** 与 **1.552/1.627 s**（冻结 1.0 s）。这是「同一流量只在自由流支可达」的定量原因，定位为行为模型参数 Hypothesis，需受控平衡态探针 + 研究者决定，**未做参数搜索**。

第三窗口读取 0 行、holdout 0 次、验证行物化 0。Gate=`pending_simulation_sample`、`scientific_claim_eligible=false`、`reality_coverage_accepted=false`、`protocol_lock_allowed=false`、`stage_1_1_allowed=false`。2026-10-20 决策包 R1–R5 仍全部开放。

报告 `docs/STAGE_0_5_TRAJECTORY_RECONSTRUCTION.md`、`docs/STAGE_0_5_SUMO_SCENE_RECONSTRUCTION.md`；计划 `docs/plans/2026-10-21-stage-0-5-trajectory-reconstruction.md`；证据 `evidence/results/RES-STAGE-0.5-TRAJECTORY-RECONSTRUCTION-V1/`。

## 2026-10-20 Stage 0.5 最终收口（历史）

`RES-STAGE-0.5-FINAL-CLOSURE-V1`：研究者批准 D1–D5 后，按 D1 主口径重算两个真实校准窗口，**正式局部 P2 与暴露首次计算完成**——0750–0805 = 147 件 / 31,051.6 veh-s / 17.0426（车辆簇条件区间 [13.604, 21.131]，1,789 簇）；0805–0820 = 216 件 / 33,091.1 veh-s / 23.4988（[19.621, 27.806]，1,431 簇）。全源确认事件 543/732、全源可评价暴露 111,425.9/133,505.6 s 与 A+ 合格切片求和逐位复现，拒绝 0、右截断 0，未读旧全源事件表、未访问第三窗口与 holdout。此前"正式局部 P2 Unresolved / Not Calculated"的计算缺口关闭，但不等于现实覆盖通过。

条件候选 FC1/FC2 各 300 s 完成（seed 20261019）：数值精确 100%、守恒与局部平衡残差 0、期末待插入 0、1e-6 m 未放宽。但**预声明 30 s 块状态支持未通过**：模拟 20–22 m/s、约 20 veh/km/lane 对真实 8–10.5 m/s、43–50 veh/km/lane；模拟平均闭合速度为正（净接近 +2.73/+3.67 m/s）而真实为负（净拉开 −0.171/−0.109 m/s）。两次运行都复现观测内部断面流量（1647.4 对 1646.9、1451.4 对 1439.2 veh/h/lane）却落在**自由流分支**，属边界供给/需求的结构性条件失配，D3 禁止用行为参数补偿。

按冻结失败分支停止：未用第 3 次构造（单次变更边界无法覆盖两个目标条件）、未执行保留的 2 次独立 seed 重复、未访问第三窗口。五层必要条件合取 = **Evidence Insufficient**（阻断层 1/2/5；层 3 Engineering Consistent；层 4 Measurement Closed）。δ 与 h 的独立依据审计结论为"无依据"，保持 Awaiting Researcher Decision，未编造数值；集中决策包 R1–R5 一次性提交。新增 2 次轨迹运行（累计 5/8，剩 3），4 次空网软件冒烟单独登记。

报告 `docs/STAGE_0_5_FINAL_CLOSURE_2026-10-20.md`；计划 `docs/plans/2026-10-20-stage-0-5-final-closure.md`；证据 `evidence/results/RES-STAGE-0.5-FINAL-CLOSURE-V1/`。Gate 保持 `pending_simulation_sample`；协议锁、Stage 1.1、ABCD 均未启动。

## 2026-10-20 LF候选协议整合（历史；其 D1–D5 待决已被本次批准取代政策）

266个原核心工程事件独立重建、逐成员核对；历史86/87/83重现，开始至确认全在域为86，差异4件。共同候选分母14636.2veh-s，局部正式P2仍Unresolved/Not Calculated。相位周期5/10/20%敏感性均到300s才完成，后评价0s；局部平台而全网/pending增长。五层必要目标、需求可识别性和科学误差/精度候选已整合为D1–D5待决；无新增SUMO，累计3/8剩5。C回溢EI与全部历史、Gate/Lock/I-II状态不变。

报告 `docs/STAGE_0_5_LOCAL_FOLLOWING_PROTOCOL_DESIGN.md`；计划 `docs/plans/2026-10-20-lf-protocol-consolidation.md`；证据 `evidence/results/RES-STAGE-0.5-LF-PROTOCOL-CONSOLIDATION-V1/`。

## 2026-10-19 局部跟驰探索（方案A）

`RES-STAGE-0.5-LOCAL-FOLLOWING-EXPLORATION-V1`：方案A局部探索已独立执行3/8次（120s同步、120s批处理、300s延长），剩5；接入额度不复用。175679行/28非标签字段及延长前缀完全相等，worker283.31→68.63s约4.13倍，无缓存/观测降频。固定原尺度C main1[50,250)m局部可测；LF3均速2.964/density81.558/低速77.03%，1222个TTC<2点中1203在前120s。全网核心266工程事件/42404.3veh-s；局部归属起始86/确认87/全程83，正式局部P2/暴露Unresolved、率Not Calculated。14.35m间隙离线分解，C回溢EI不变；正式Gate/历史不变。

报告 `docs/STAGE_0_5_LOCAL_FOLLOWING_EXPLORATION.md`；证据同结果ID目录。研究者已批准局部探索不以完整入口回溢资格为前提；未批准局部P2归属、正式暖机/窗口、科学容差/需求识别/校准目标。需要的3项决定集中在researcher_decision_matrix.json。当前工程闭环不代表科学Gate，通过只在受限fresh/no-stop/只读域成立。LF1/LF2为同seed读取对照，LF3为同seed延长，不当独立重复池化。正式Gate、C回溢EI与历史不变；没有ABCD/正式校准/Lock/I-II。


## 2026-10-19 C/D有限接入与自主问题发现

`RES-STAGE-0.5-CD-INTEGRATION-V1`：C/D有限接入2次各60s；62707边中62513精确全过、63 bounded、131合法坐标不可评价、0数值阻断。C内部队列/上游扩展/入口邻近与87 pending可观测，但入口与下游锚定组件约14.35m>10m，持续回溢EI。D9辆实际换道和main2出口由原始状态独立验证；v1 main_1-only假阻断保留，v2修复无重试。定向0/8、主矩阵0次；正式Gate和全部历史不变。

报告 `docs/STAGE_0_5_TASK_CD_INTEGRATION_AND_ISSUE_DISCOVERY.md`；证据 `evidence/results/RES-STAGE-0.5-CD-INTEGRATION-V1/`。研究者本轮授权工程分层与新增2次接入（已用完）、定向最多8次（未用）；无ABCD授权。近零仅fresh/no-stop域，1e-6m不变。当前最重要决策是下一局部跟驰探索是否需要完整入口回溢，以及评价时间/需求/科学容差/P2局部归属协议；不为非核心私有量无限追加验证。旧B1/N/P授权与状态作为历史保留。通用路网/局部匹配为当前研究者优先，真实几何完整复现非必要前提，但结构/匝道/波传播结论受限。


## 当前补充：B1.2-P（2026-10-19，优先于下文历史更新）

`RES-STAGE-0.5-POSITIVE-NEAR-ZERO-V1`：B1.2-P仅数值观测独立任务。固定SUMO1.26/commit fa7df22d，13具名源码完整谓词/赋值路径核对；fresh/no-stop/无恢复/无控制/无特殊设备/非循环路线doubleMax不变量独立成立。5个冻结原生红灯制动探针各2s、无车辆setter/无重试。实际P1/P2在.10→.15s非决策步重建u_pre约1.999999909e-6/4.800000001e-6，公开终速0，最终分支由源码与生命周期先行确定，位移残差-4.6161e-15/-6.4115e-15m。2条目标Exact Pass；195边中192一般精确全过、3 bounded、0未决/不可评价/阻断。P3/P4/P5实际阈值以上保持正终速；P3名义等号但实际略高，运行精确等号Not Observed。1e-6m未放宽，残差不用于反推上下文。

仅target_branch_verified=true，C_D_allowed=false/main_matrix_allowed=false/future_numerical_policy_approved=false。不需要为该受限分支使用调试构建；一般停车/状态恢复/特殊控制域未验证。B1.2-N正近零Not Observed与integration_allowed=false、旧B1.2阻断/0-8及所有历史原样保留。本轮C/D和主矩阵0次；下一步研究者需决定未来数值准入政策，另批剩余接入；不自动执行。科学Gate及所有ready/现实覆盖/锁/StageI资格不变。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2P_POSITIVE_NEAR_ZERO.md`；证据同ID目录。

## 当前补充：B1.2-N（2026-10-19，优先于下文历史更新）

`RES-STAGE-0.5-NEAR-ZERO-INTEGRATION-V1`：独立B1.2-N工程任务。固定SUMO1.26源码完整谓词和调用顺序已审计；无停车任务的fresh/immutable生命周期可用doubleMax不变量，同edge常规停车仅非决策步可作充分条件。一般myStopDist不能由公开getter等价恢复。新候选`b12n-near-zero-observability-v1`不以位移/终速选择上下文，1e-6m不变。3个30s微型运行：2879边，2876精确全过（其中1负近零后处理），3 bounded，0近零未决/不可评价/工程错误；最大残差1.3988810110276972e-14m。冻结前203项受控合成通过。

正近零非决策步清零运行边未出现（Not Observed），未满足运行前冻结的共同准入条件；integration_allowed=false，C/D计划冻结被拒绝，均Not Attempted，未追加试验/搜索。新主矩阵禁止且0次。旧B1.2阻断/0-8/D未运行和所有历史证据不变。下一步由研究者决定正近零覆盖设计与未来政策，再另批接入/主矩阵；不自动继续。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2N_NEAR_ZERO_AND_INTEGRATION.md`；证据同ID目录。科研Gate/ready/现实覆盖/锁/StageI状态不变，科学阈值未批准。

## 当前补充：B1.2（2026-10-19，优先于下文历史更新）

`RES-STAGE-0.5-BOUNDARY-BOTTLENECK-R2`：研究者已批准方案B仅用于工程探索、队列候选接入和条件性新A/B/C/D。严格布尔/时钟防御已修复；受控合成回归142 passed。首个压缩C接入fixture在19.70→19.75s遇到非决策步终速不一致，执行器自动停止；D fixture未启动、主矩阵0/8、主计划未冻结、`B1_2_MAIN_MATRIX_ALLOWED=false`。数值已审计10145边：10047精确全过、14 bounded、84不可评价（83合法edge转换+1阻断）；最大精确残差7.1054e-15m。

固定SUMO源码在加速度延续后有近零清零，预测4.658e-6m/s低于5e-6内部阈值、实际终速0，与反例相符；私有条件未经仪器化。旧“非决策步任意情形最终候选精确”等广泛叙述不能无条件外推。冲突`Awaiting Researcher Decision`，未改公式/容差或追溯放行；B1.1-S的947/948封存结果原样保留。压缩fixture仅部分计数/坐标/队列证据，不能替代主C机制或现实样本。下一步只建议独立近零适用域和剩余接入验证的新计划。

历史B0隔离false/验证Unknown、旧B1 C两阻断/D未运行、B1.1 Pending均保留。科学Gate=pending_simulation_sample，所有校准ready/现实覆盖/锁/StageI资格false，Tolerance Not Yet Justified、ED上界Not Identifiable、局部P2 Unresolved。报告：`docs/STAGE_0_5_TASK_0_5_4B1_2_BOUNDARY_BOTTLENECK_REVALIDATION.md`；证据同ID目录。下文B1.2“未授权/待另批”为历史记录，本节授权和实际停止状态为当前事实。


## 当前补充：B1.1-S（2026-10-19，优先于下文历史更新）

`RES-STAGE-0.5-STOPPING-OBSERVABILITY-V1`：固定SUMO1.26.0源码审计确认，非决策步延续公开加速度（`vSafe=v0+a_pub_start*h`），因此内部带符号候选终速可由公开TraCI独立重建`u=v0+a_pub_start*h`，对任意符号精确成立，包括`u<0`的真实步内停车；决策步`v1=0`（含`h=actionStep`的停车步）仍被`max(u,0)`钳制，仅可范围一致。决策步判定：步[`t_prev`→`t_now`]为决策步当且仅当`t_now`读到的`lastActionTime`等于`t_prev`。3个微型运行、948条相邻边：947精确核验且全过，最大残差`1.4210854715202004e-14m`，1条决策步停车仅范围，0不可评价，0异常；未用位移反推、未用调试二进制、未改官方二进制。因此“全部停车边精确等价”仍未成立；B1.1精确停车`Pending`记录与B1 C/D、B0均不变。

Gate=pending_simulation_sample，scientific_claim_eligible=false、ready_to_start_stage_0_5_4b=false、reality_coverage_accepted=false；容差Tolerance Not Yet Justified、ED上界Not Identifiable、锁/StageI禁止。方案A/B数值准入与B1.2前置条件待研究者决定；B1.2需另批，不自动执行。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_1S_STOPPING_OBSERVABILITY.md`及同ID便携证据；协议/源码/输入冻结SHA见experiment_plan、PLAN_SHA256和provenance。

> 核对日期：2026-10-20（Asia/Shanghai）
> 当前任务：AAD-0.5-LF-PROTOCOL-CONSOLIDATION候选协议整合完成，等待研究者审阅D1–D5；局部P2/暖机/容差未获批准，正式校准和ABCD不启动。

## 当前研究阶段

项目处于阶段 0：测量、现实证据边界、仿真适用域与协议锁准备。阶段 1.1 核心效应确认尚未实现、未运行，并被协议锁阻断。依据：`docs/PROJECT_REGISTRY.json`、`docs/RESEARCH_STATUS.md`。

## 当前主要研究目标

验证来源可追溯且被控制器采用的远端风险消息，能否在普通物理影响到达目标区域前改变车辆动作与区域总体风险。当前工程目标是先闭合阶段 0 的测量与准入证据，不生成核心效应结论。

## 当前模型版本

当前没有可核验的可训练模型、训练循环、loss 或 checkpoint。正式代码是确定性测量、SUMO 工程运行、覆盖审计与协议准入工具；阶段 1.1 的模型为 `not_determined`。依据：`code/pyproject.toml`、`code/src/riskprop/`、注册表 `model`/`model_checkpoint` 字段。

## 当前主要实验

- `stage_0_2`：NGSIM 跟驰风险审计，`Completed / Closed`（有限范围），作为已封存参考。
- `stage_0_3`：pNEUMA 城市运动学校准，`Completed / Closed`（2026-10-16 R3 科学验收，`pass` 有限范围：单文件描述性城市运动学）。
- `stage_0_4`：已在可观测性与描述证据有限范围验收，Gate=`pass_limited`；真实通信模型/参数未因此校准。
- `stage_0_5`：R2真实参考与canonical接口已完成；SUMO工程基线和B0探索已运行，尚缺获批适用域/容差及正式校准样本，Gate=`pending_simulation_sample`。B0实验输入与根回归访问范围分开审计，后者发生历史全源产物读取例外，任务数据隔离未认证。

（2026-10-18 AAD-0.5.1 更新）`RES-STAGE-0.5-REAL-REF-R2` 已完成正式真实参考重建：canonical pNEUMA 已原生接入并通过 fail-closed 质量/来源契约；US-101 三窗口、Lankershim、正式 P2=4,545 和 Stage 0.3 封存运动学统计均已绑定。旧句描述 0.5.0 历史冲突；当前仍缺 SUMO 校准样本，Gate=`pending_simulation_sample`。

（2026-10-18 AAD-0.5.2 更新）已完成分场景现实覆盖指标与校准—验证协议候选设计。US-101 建议按五层必要条件评价，Lankershim 独立辅助，pNEUMA 仅城市运动学；现有 pooled real-real Energy Distance 不具备直接科学容差资格。校准/验证窗口、容差、Energy Distance 角色、辅助场景范围和 0.5.3 前置契约均待研究者批准，未运行 SUMO。

（2026-10-18 AAD-0.5.4-A 更新）已完成 SUMO 正式校准前的科学准入与测量等价性审计。P2 测量契约 16 项维度：10 项 `Equivalent / Verified`、6 项 `Engineering Consistent Only`、**0 项阻断**；16 个确定性边界用例两适配器一致；独立复现封存值（可评价暴露 111,425.9 / 133,505.6 s，事件 543 / 732，事件率 17.5435 / 19.7385 veh⁻¹h⁻¹）。修复 6 项适配层缺陷（绝对 `global_time_ms`、前车自身 `leader_frame_id`、`exit_reason` 保留、闭合 epsilon=1e-3、可靠跟驰层与正式边缘审计对齐、DRAC 已批准闭式），未修改任何 Stage 0.2 阈值/持续时间/分母。产出校准窗口运动学/跟驰/可观测性统计、需求可识别性矩阵（上游需求、匝道流、OD、车型组成与车辆长度不可识别）、候选交通状态分层、轨迹簇不确定性（事件率 CI 约 ±15%，逐行 i.i.d. 窄 12.7 倍）、时间步敏感性（内部步长减半使事件边界移动 0.2 s）与 300 s 基准成本。准入清单 `ready_to_start_stage_0_5_4b=false`，5 项待批准、5 项阻断；验证窗口物化 0 行，未冻结任何容差或参数，Gate 仍 `pending_simulation_sample`。结果 `RES-STAGE-0.5-CALIBRATION-READINESS-V1`（工程审计，非 Gate 结果）。

（2026-10-18 AAD-0.5.3 更新）已建立独立 `stage_0_5_sumo.py` 工程骨架、`no_message_baseline` 运行入口和校准/验证 fail-closed 访问守卫。US-101 `generic_highway_candidate`（3 主线段 × 3 车道 + 入口匝道 + 出口匝道）在本地 SUMO 1.26.0 完成两个工程 fixture：baseline（8,453 state、17 vehicles、6,118 leader rows、724 valid TTC、0 个工程 P2）与 measurement probe（2,720 state、7 vehicles、1 个 P2 事件，onset 3.1 s、确认 3.3 s、TTC min 1.794 s）。TraCI `getLeader` 距离已核验为「物理保险杠净间距 − 后车 minGap」，统一换算为 `net_gap_m = traci_distance + follower_min_gap`，同车道残差 0.0 m；`closing_speed_mps = follower − leader`。工程 P2 经 SUMO-native adapter 与 Stage 0.2 formal-alignment adapter 双路确认，但正式等价性仍 `pending_measurement_equivalence_review`；Lankershim/pNEUMA 保持 candidate_entry_only，pNEUMA 六类原始车型全部 `unmapped`。结果 `RES-STAGE-0.5-SUMO-BASELINE-ENGINEERING-V1` 仅 engineering_only，Gate 仍 `pending_simulation_sample`。
- `stage_0_6`：技术真值检查已有证据，科学容差与协议锁未完成。

## 当前最重要的问题

阶段 0.2、0.3 均已在有限范围内关闭（0.3 于 2026-10-16 经研究者五项批准：单文件范围、0<Δt≤0.043 s 正式参数、极端观测保留、描述阈值仅描述、Gate=pass）；阶段 0.5 缺 SUMO 校准样本，其车型映射、时间权重抽样与覆盖阈值独立待决；阶段 0.4 有限证据边界待冻结；科学容差和样本量未冻结。当前便携 readiness 是迁移前旧键快照，只能证明当时 `protocol_lock_allowed=false`。

## 当前下一步

阶段 0.4 已在有限范围验收、0.2/0.3 已关闭。阶段 0.5 的真实参考侧（含已批准 D1 的局部 P2 与暴露）已计算完成，唯一剩余阻断是仿真侧目标状态支持与数值科学容差：等待研究者对集中决策包 R1–R5 的裁决（δ 与 h 的数值及依据、能到达观测拥堵分支的目标条件与边界供给设计、有限时间评价窗与暖机定义、剩余 3 次运行的使用、第三窗口验证协议）。**不得在裁决前追加 SUMO 运行、不得执行保留的独立 seed 重复或访问第三窗口**，也不得以行为参数补偿供给失配。随后才依次完成阶段 0.6 科学参数冻结与协议锁；协议锁通过前不得进入阶段 1.1。

## 2026-10-09 Stage 0 基线核查

只读审计报告：`docs/STAGE_0_BASELINE_AUDIT_2026-10-09.md`。六个登记数据文件均存在，完整文件 SHA-256 与历史下载清单一致，总大小 1,862,308,265 bytes（1.862 GB）。I-80、Peachtree 与 SPMD holdout 只做文件级核验，未解压或查看内容。当前结论仍为 0.2/0.3/0.5/0.6 未闭合，Protocol Lock 未创建，Stage I 禁止启动。

## 2026-10-09 任务 1 NGSIM 基础核验

报告：`docs/STAGE_0_2_TASK_1_NGSIM_INTEGRITY_2026-10-09.md`。US-101 三窗口各 1,048,575 行，程序 parquet 与 ZIP CSV 一致，但每窗口各有一个 `Total_Frames` 不一致车辆，不能确认与官方完整窗口一致。Lankershim 有 228 个非递增车辆内时间步、936 个多 `Total_Frames` 车辆，身份/分段边界未解决。公式与单位真值夹具通过；任务 1 未验收，需任务 1.1。

## 2026-10-09 任务 1.1 来源与分段核查

报告：`docs/STAGE_0_2_TASK_1_1_NGSIM_SOURCE_SEGMENTATION_2026-10-09.md`。US-101 同 ZIP 内 TXT 已证明比 CSV 完整；任务 1.2 更正无表头首行计数为 1,180,598、1,403,095、1,515,240。官方元数据建议使用 TXT，但不保证数据完整性。Lankershim 官方设计为两个 15 分钟源文件，当前包只有合并 CSV；编号复用主要原因仍为 Inference，未由源文件证实。

## 2026-10-09 任务 1.2 TXT 接入与源恢复

报告：`docs/STAGE_0_2_TASK_1_2_TXT_SOURCE_RECOVERY_2026-10-09.md`。US-101 三个 Stage 0.2 输入已切换到 ZIP 内原始无表头 TXT，读取器固定校验 18 列、来源标识和精确行数；9 项相关测试通过。Lankershim 当前包仍无两个独立官方源文件，正式身份/分段规则未修改，任务 1.3 仍需研究者决定源不可得时的保守方案。

## 2026-10-10 任务 1.3 轨迹身份与测量链验证

报告：`docs/STAGE_0_2_TASK_1_3_TRAJECTORY_IDENTITY_VALIDATION_2026-10-10.md`。US-101 三个 TXT 共 4,098,933 行，独立全量测量链产物位于 `code/outputs/formal/calibration/stage_0_2_task_1_3_us101_txt_20261010_r2/`，有效 TTC 1,728,280 行、候选事件 2,604 个。Lankershim 1,607,319 行保留，基于原始 `Frame_ID` 冲突建立 2,654 个确定性诊断片段；228 行身份不确定、1,379 行观测缺口。单帧有效 TTC 483,098 行，其中 482,470 行通过保守连续性筛选。正式科学事件单位和最终阈值仍未冻结，Protocol Lock/Stage I 继续禁止。

## 最近的重要项目变化

- 当前阶段与入口统一为“阶段 X.X”/`stage_X_Y`。
- 研究者于 2026-09-10 明确批准 pNEUMA 前车推断与人工复核退役；相关代码、输出和证据保留在 legacy/history。
- 建立 `AI_CONTEXT/`，并将长期 Research Engineer 协作边界固化到 `AGENTS.md`。

## 当前 Git branch

`main`。实时核验：`git branch --show-current` 与 `git status --branch --short`。

## 对应的最新 commit

任务 1.4 实现版本由文件所属 Git 提交及本轮 provenance 的实现 SHA-256 追溯；历史对照基线为 `da4072909a93c16e96e89fa436fd23127a581b69`。AI_CONTEXT 自身的最新提交用 `git log -1 --format=%H -- AI_CONTEXT` 查询，仓库实时 HEAD 用 `git rev-parse HEAD` 查询。

## 2026-10-10 任务 1.4 当前工程基线

报告：`docs/STAGE_0_2_TASK_1_4_RELIABILITY_CLOSURE_2026-10-10.md`；证据：`RES-STAGE-0.2-TASK-1.4`。Lankershim 两个诊断时钟锚解释 936 个旧异常编号；按字段序列建立 2,442 段，全部 1,607,319 行保留、无同编号同时间冲突，有效 TTC 483,098 行，原始/可靠候选各 2,777、拒绝 0。US-101 4,098,933 行核心测量与任务 1.3 等值，候选事件仍 2,604。任务 1.3 的 482,470 是有效 TTC 排除行级标记后的数量，不是已验证连续事件；旧实现不确定标记只切段，未可靠排除。本轮修复并区分后车/前车、完整序列和记录/段级可靠性。字段 confirmed 不代表官方物理身份；source_period=unknown。建议任务 1 工程验收，等待研究者；Stage 0.2 科学 Gate 仍 Active，不启动任务 2/协议锁/Stage I。

## 2026-10-10 任务 1.5 当前工程基线

报告：`docs/STAGE_0_2_TASK_1_5_LEADER_MATCHING_CLOSURE_2026-10-10.md`；结果：`RES-STAGE-0.2-TASK-1.5`；最终产物为 `code/outputs/formal/calibration/stage_0_2_task_1_5_20261010_r4`。Lankershim 1,226,499 条报告前车在时间、诊断时钟锚、Frame_ID 和编号约束下均唯一；真实跨时钟匹配 0，跨时钟有效 TTC 0。匹配键修复并增加显式时钟缺失/冲突阻断，四源状态核心与任务 1.4 0 行差异，事件数保持 US-101 2,604、Lankershim 2,777；全量测试 201 passed。任务 1 建议关闭，等待研究者审核；Stage 0.2 科学 Gate 仍 Active。

## 2026-10-10 任务 2 当前基线

报告：`docs/STAGE_0_2_TASK_2_RISK_QUALITY_AUDIT_2026-10-10.md`；结果：`RES-STAGE-0.2-TASK-2`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_risk_quality_audit_20261010_r4`。四个 NGSIM 校准 state 共 5,706,252 行、2,211,378 条有效 TTC；质量状态、有限值分布、极端记录追溯和完整状态序列上的 6×4 事件敏感性网格已完成。TTC/DRAC 为重尾，当前结果仅支持描述性校准和后续人工复核；最终阈值、事件规则、暴露分母和科学 Gate 仍 Active。

## 2026-10-10 任务 2.1 当前基线

报告：`docs/STAGE_0_2_TASK_2_1_EXTREME_REVIEW_2026-10-10.md`；结果：`RES-STAGE-0.2-TASK-2.1`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_1_extreme_review_20261011_r4`。固定种子分层案例 447 个，独立前车唯一匹配 447 个，公式重算浮点误差范围内一致；自动分类 C=399、D=48、A/B=0。物理真实性仍需人工/独立几何复核，科学事件规则和 Gate 仍 Active。

## 2026-10-11 任务 2.2.1 最终修复

连续风险边界现按前一帧边定义，风险段统计保留段首帧；固定 447 案例已在独立 r9 产物重算。多帧连续 298、单帧 3、间歇 0、边界 25、无极端 121；自动 C=349、D=98。48 案例包和 PDF 图册已重生成，人工字段为空，物理真实性仍 Unverified。

## 2026-10-11 任务 2.3

任务 2.3 完成工程质量与探索性稳健性收口：5,706,252 条 state、2,211,378 条有效 TTC、5,381 个正式基线候选事件已核对；独立重提取 S0=5,880，差异保留为 Unverified。447 个案例中心定位 unique=447，几何/物理真实性仍 Unverified。Protocol Lock 与 Stage I 继续禁止。

## 2026-10-11 任务 2.4

任务 2.4 完成正式候选事件提取等价性与稳健性最终验证。独立实现补齐正式 0.1 s 首末时间跨度条件后，与 `extract_rear_end_events()` 四源逐事件等价：总计 5,381，成员集合、时间边界和极值一致；任务 2.3 的 5,880 与正式基线差异由不可比的最小持续时间/正式连续性语义造成。S1 在完整 state 副本上真实重跑质量条件，raw/reliable/rejected 为 5,381/5,381/0。S2a/b/c/d 探索性屏蔽后事件数为 5,366/5,353/5,263/5,235。连续跟驰暴露按严格相邻帧分段，同时保留首末跨度与覆盖时长。报告：`docs/STAGE_0_2_TASK_2_4_EVENT_EQUIVALENCE_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_4_20261011_r2/`。科学阈值、事件规则、暴露分母和 Stage 0.2 Gate 仍未冻结。

## 2026-10-11 任务 2.5

任务 2.5 完成源端 TTC 阈值与最小持续时间联合敏感性、事件级参数对应、因果确认时刻、非插值采样限制、24 个定向真实案例选择和文献证据矩阵。四源 6×4 事件数（TTC 1.0/1.5/2.0/2.5/3.0/4.0 s；持续 0.1/0.2/0.3/0.5 s）已封存，2.0 s 基线为 5,381。所有候选参数均为 Proposal；未冻结正式规则、Protocol Lock 或 Scientific Gate。报告：`docs/STAGE_0_2_TASK_2_5_THRESHOLD_VALIDATION_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_5_20261011_r1/`。


## 2026-10-11 任务 2.5.1

P1/P2/P3 定向验证已完成：成员级事件重叠图 20,171 条边，事件数 P1=1,900、P2=4,545、P3=8,523、工程参考=5,381；24 个案例全部重新生成记录与 24 页图册，保留 Lankershim 原始行 31,245。在线确认时刻由实际观测验证，P1/P2/P3 中位 onset→confirm 分别为 0.3/0.2/0.1 s。rejected 通过 event_id 与 raw 候选联接；公平 200 ms 采样敏感性仍 Unresolved。文献 2021 surrogate-measure 条目已更正为 Lu et al., Accident Analysis & Prevention 162, 106403, DOI 10.1016/j.aap.2021.106403。所有参数仍 Proposal / Pending Parameters / Not Frozen，科学 Gate、Protocol Lock 和 Stage I 均未启动。报告：`docs/STAGE_0_2_TASK_2_5_1_TARGETED_VALIDATION_2026-10-11.md`；产物：`code/outputs/formal/calibration/stage_0_2_task_2_5_1_20261011_r2/`。


## 2026-10-11 任务 2.5.2

基于 Task 2.5.1 成员级结果完成关键差异案例分析：中心事件按 source、车辆对和 original_row_number 成员精确匹配，附近 ±3 s 事件单独计数；选择 P2-only、P3-only 和三规则确认时刻差异案例共 11 个，生成新 PDF 和逐案例 CSV。P2 仍仅为条件性 Proposal，缺少独立安全真值、公平采样和独立几何真实性，未冻结科学规则。报告：`docs/STAGE_0_2_TASK_2_5_2_KEY_DIFFERENCE_CASES_2026-10-11.md`。


## 2026-10-11 科研决策归档与参数核定

研究者已确认 Stage 0.2 风险设计：P2=可靠 TTC<2.0 s、首末跨度≥0.2 s，P1/P3 为敏感性对照；TTC 触发、DRAC 作严重程度；连续风险使用 rho=exp(-TTC/tau)，固定车辆/区域/窗口、车辆等权、缺失上下界和四格 DID。四源时间加权 TTC 中位数为 11.378882、17.170886、16.312500、14.416058 s，tau=15.364279 s。该设计已记录但 rho burden、固定窗口和 P2 0.2 s 正式实现仍待完成；Scientific Gate、Protocol Lock 和 Stage I 未启动。报告：`docs/STAGE_0_2_DECISION_RATIFICATION_2026-10-11.md`。


## 2026-10-11 连续风险时间尺度验证

在四源任务 1.5 状态上，以可靠相邻 100 ms 闭合边计算 `rho=exp(-TTC/tau)`。tau=15.364279 s 下时间加权平均 rho 为 Lankershim 0.4390、US-101 三窗口 0.3375/0.3529/0.3833；`>=10 s` TTC 暴露占比很高但 rho 较低，风险贡献由暴露时间和条件强度共同决定。tau/2、2tau 敏感性与极端压力结果已封存；正式固定目标区域 burden 仍 Unresolved。报告：`code/outputs/formal/calibration/stage_0_2_rho_timescale_validation_20261011_r1/report.md`。

## 2026-10-11 正式风险测量接口实现

新增 `code/src/riskprop/formal_risk_measurement.py` 与版本化配置 `code/configs/stage_0_2_formal_risk_measurement_p2_v1.json`。P2 使用可靠 TTC<2.0 s、首末跨度≥0.2 s，确认时间取实际观测帧；`rho=exp(-TTC/tau)` 使用 tau=15.364279197080283，仅对可靠有效正闭合 TTC 计算。新增贡献上下界、固定窗口积分、车辆等权平均和 DID 区间算术接口；目标区域、固定车辆资格、评价窗口和消息去重仍为空配置，尚未宣称正式区域 burden 已实现。独立复算得到 P2=4545，与任务 2.5.1 参考一致；产物：`code/outputs/formal/calibration/stage_0_2_formal_risk_measurement_20261011_r1/`。旧提取器 0.1 s 默认和旧线性 TTC 指标保留不变。测试与 Stage 0.2 Gate、Protocol Lock、Stage I 状态分离。

## 2026-10-11 正式风险测量一致性修复

修正区域外贡献判定顺序、车辆对统计和 NGSIM 诊断时钟连续性字段；P2 仍为 4,545 个事件，唯一后车 2,512，唯一车辆对 3,072。新验证产物：`code/outputs/formal/calibration/stage_0_2_formal_risk_measurement_20261011_r2/`；报告：`docs/STAGE_0_2_FORMAL_RISK_MEASUREMENT_CONSISTENCY_REPAIR_2026-10-11.md`。


## 2026-10-12 Stage 0.2 综合收口（当前状态）

**最新状态覆盖（2026-10-12 最终验收审计）：Stage 0.2 Gate=`Blocked`，尚未正式关闭。** 独立边级复算确认可靠跟驰暴露512,043.2s与封存逐源值一致且不跨身份/缺帧/时钟；但分母包含 `invalid/non_positive_gap` 端点边，四源分别7,557.4s、187.4s、178.7s、197.5s。该状态下P2不可评价，研究者需裁决是否仍计入已批准的可靠跟驰事件率分母。包：`code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r3/`。该口径阻断覆盖下方历史 Gate Active 描述；此前综合包仍为不可改写的历史证据。

报告：`docs/STAGE_0_2_FINAL_CLOSURE_2026-10-12.md`；结果：`RES-STAGE-0.2-FINAL-CLOSURE`；最终包：`code/outputs/formal/calibration/stage_0_2_final_closure_20261012_final_r1/`。四源5,706,252行状态、P2=4,545、唯一后车2,512/车辆对3,072逐事件独立复算一致；tau=15.364279197080283。可靠跟驰边512,043.2s、闭合边208,026.3s；固定分母与连续性fail-closed原语已测试。200ms两相位P2=4,155/4,162，存在消失/连接，不能证明采样等价。极端联合屏蔽P2=4,370，447中心全部唯一、125运动学探索标记，48人工判断仍空；独立物理真实性Unverified。验收准备包可提交研究者，**非Gate Pass Candidate**，Gate仍Active，正式质量标准/有限适用域与独立物理证据待研究者；Stage0.5覆盖及四格配置非本阶段阻断。无Protocol Lock/Stage I/holdout访问。

本段为当前事实；前述Proposal、尚未实现与旧暴露/事件描述均为历史状态，不自动沿用为当前结论。依据：最终包audit/config/provenance、逐事件核验表和Gate矩阵。

## 2026-10-12 Stage 0.3 综合实施与验收准备（当前状态）

报告：`docs/STAGE_0_3_PNEUMA_KINEMATICS_2026-10-12.md`；结果：`RES-STAGE-0.3-PNEUMA-KINEMATICS-R1`；验收准备包：`code/outputs/formal/calibration/stage_0_3_pneuma_kinematics_20261012_r1/`（不可覆盖，SHA256SUMS 校验通过）。pNEUMA 全量文件 785 条唯一轨迹、1,239,475 条状态、0.04 s 等间隔、零缺口/畸形/重复；时间加权速度 mean=4.8382 m/s、车辆等权 mean=6.2077 m/s；纵向加速度 mean=-0.0044、sd=0.7454 m/s²，极端记录保留并做敏感性；轨迹簇 bootstrap 2000 次。新增 `pneuma_urban_kinematics.py`、`run_stage_0_3_pneuma_kinematics.py`、`verify_stage_0_3_independent.py` 与 19 个单元测试；独立复算 discrepancies=0；Stage 0.5 现有 `write_real_reference_package()` 真实全量接口测试通过（25,000 kinematics、20,000 following、4,545 events，pNEUMA TTC 未纳入）。状态 **Gate Pass Candidate**；连续性容差（工程锚定 0.043 s 未冻结）、描述性阈值、车型→SUMO vType 映射、适用范围与科学 Gate 待研究者决定。未恢复 pNEUMA 地图匹配/前车/TTC/人工 QA；无 Protocol Lock/Stage I/holdout 访问。

## 2026-10-16 Stage 0.3 R2 边界修复与验收准备（当前状态）

报告：`docs/STAGE_0_3_BOUNDARY_REPAIR_R2_2026-10-16.md`；结果：`RES-STAGE-0.3-BOUNDARY-REPAIR-R2`；验收准备包：`code/outputs/formal/calibration/stage_0_3_pneuma_boundary_repair_20261016_r2/`（不可覆盖）。任务 AAD-S0.3-T02 修复 R1 三项工程边界缺陷：时间连续性改为排序前按原始记录顺序评估（时间加权区间由原始顺序邻接定义，异常不可经排序重获权重）；轨迹审计以原始行为单位、重复 track_id fail-closed 不合并不改名；`quality_status` 逐状态推导、`time_weighting_eligible` 由解析质量+身份+原始顺序+可靠区间共同决定，`write_real_reference_package()` 读取并使用质量字段（抽样规则未变）。真实统计不变：785 行/785 唯一 ID/1,239,475 状态，速度 TW mean=4.8382、VW mean=6.2077，加速度 TW mean=-0.0044 m/s²，R1/R2 145 项比较仅 30 项浮点末位（≤1e-9，求和对齐效应）+1 项结构性记录差异；独立复算（含身份/原始顺序/暴露语义）discrepancies=0；全量测试 315 passed（287/232/315 数量差异由收集范围与新增 9 测试解释）。状态保持 **Gate Pass Candidate（R2）**；连续性容差、描述性阈值、车型映射、适用范围与科学 Gate 待研究者，未创建 Protocol Lock，未启动 Stage I/holdout 访问。

## 2026-10-12 Stage 0.2 最终科学验收与正式关闭

Gate=`pass`；阶段状态=`Completed / Closed`，仅对四个批准 NGSIM 来源在 100 ms 连续性语义下的纵向跟驰风险代理指标测量和描述性现实校准有效。正式 P2 分母为可靠且 P2 可评价跟驰时间：相邻可靠边两端状态均为 `valid` 或 `not_applicable`；不可评价边不作为零风险，仍保留质量统计。P2=4,545；原可靠跟驰512,043.2s；P2可评价503,922.2s；不可评价8,121.0s；可靠闭合208,026.3s。逐源率见最终验收包。Lankershim不可评价比例较高，缺失/无效导致的选择偏差仍未验证。

永久限制：独立物理真实性和人工/独立几何真值未验证；极端值敏感性必须披露；100/200 ms不等价；结果不外推到来源外道路、总体交通或SUMO。不得声称事故预测、危险识别准确率、P2全局最优或AAD因果效应通过。Stage 0.3/0.5/0.6及Protocol Lock、Stage I另行执行；本次未创建锁、未运行Stage I、未访问holdout。R3 Blocked 包保留为历史审计，不覆盖。依据：`code/outputs/formal/calibration/stage_0_2_scientific_acceptance_20261012_r4/`。

## 2026-10-16 Stage 0.3 最终科学验收与正式关闭（当前状态）

报告：`docs/STAGE_0_3_SCIENTIFIC_ACCEPTANCE_2026-10-16.md`；结果：`RES-STAGE-0.3-SCIENTIFIC-ACCEPTANCE-R3`；关闭包：`code/outputs/formal/calibration/stage_0_3_scientific_acceptance_20261016_r3/`（不可覆盖）。研究者经任务 AAD-0.3.3 批准五项决定（归档 `AI_CONTEXT/06_DECISIONS.md` 2026-10-16）：正式范围限本文件实际观测车辆的描述性城市运动学参考；`0<Δt≤0.043 s` 升格为已批准科学参数（仅本 25 Hz 文件）；极端观测原始保留+标记+敏感性，物理真实性 Unverified；低速/近静止/近零阈值仅统计描述；`Scientific Gate=pass`、`Completed / Closed`。关闭包对 R2 证据 fail-closed 复核 18 项全过（勘误：原记 17 项为计数笔误（勘误日期原标 2026-10-17，实际为 2026-10-16），以封存包内 scientific_gate_report.json 的 18 项机器记录为准；checksum、785/1,239,475/[38.40,888.00] s/暴露 49,547.6 s、速度 TW 4.838218/VW 6.207738/加速度 -0.004410 不变、独立复算 discrepancies=0），未重跑全量管线；验收矩阵 11 项 Verified。R1/R2 历史包保留不覆盖。禁止外推：30 分钟连续观测、城市总体、其他文件/采样率、事故概率、AAD 因果效应、SUMO 覆盖。Stage 0.5 的车型映射、时间权重抽样与覆盖阈值独立待决；无 Protocol Lock/Stage I/holdout 访问。

## 2026-10-16 文献库结构（当前）（标题日期勘误 2026-10-17：执行日为 2026-10-16；`doc/literature-notes/zotero_reorg_2026-10-17_execution.json` 文件名按 Git 原状保留）

Zotero `TJU → AAD`（唯一文献库）已按研究者批准完成六主题调整：01_风险事件与安全指标 7、02_混合自动驾驶传播与控制 11、03_闭环仿真与场景测试 7、04_人类行为交互与轨迹预测 4、05_非局部交通流模型 11、06_类超距与因果理论 16，共 56 条；`NC_统一汇总` 已退役，11 篇 NC 论文由 `NC` 标签追踪；7 对 AAD↔DRIFT 重复条目按决定保留不合并。执行记录：`doc/literature-notes/zotero_reorg_2026-10-17_execution.json`（item key 级 before/after，可恢复）；59 份退役 PDF 与 56 条论文的 3 份差额 `Unverified`。授权方式为 Zotero 10 官方本机 API 授权对话框，未触碰数据库文件。

## 2026-10-16 Stage 0.4 数据源调查（AAD-0.4.1，下载前）（标题日期勘误 2026-10-16）

只读调查完成，未下载任何数据、未提交任何申请、Gate 不变（`pending_official_packet_access`）。SPMD 官方条目 2026-01 重建（DOI 10.21949/1504482，视图无附件，本地手册继续为准）；下载端点由历史 403 变为 302→官方文件 API，最终可达性与 46 成员结构待下个授权下载任务用 Range 验证。官方字典确认：Packet= RSE 侧包捕获（捕获时间戳/PSID/信道/功率，无发送时刻，IP 轮换）；BsmP1=发送侧主表（TxRandom/MsgCount/Gentime，官方换算 /1e6−35 s）；RSE_BSM（3.23 GB，新识别）= RSE 接收 BSM 内容，4 个未文档化字段待验。时延共同前置=跨设备时钟同步（Unknown）。候选外源：AMCD BSM（2,593,113 行，唯一同行 time_sent/time_received，云接收）、NYC IE EVENT（164,131 行告警级，时空分箱，告警≠采用）、Tampa BSM 样本（34,464 行 RSU 接收）、ITS DataHub Sandbox（表单通道）。推荐：P0 渐进取 RSE_BSM+Packet（18.6 GB）→ 核验后再定 BsmP1（55.7 GB）；完整 117 GB 主包不必要。报告 `docs/STAGE_0_4_TASK_0_4_1_DATASET_SURVEY.md`；结构化清单 `docs/research/stage_0_4_dataset_candidates.json`。控制器采用在任何候选数据中均不可观察，属永久仿真/实验职责。

## 2026-10-16 Stage 0.4 RSE_BSM 获取与核验（AAD-0.4.2）（标题日期勘误 2026-10-16）

经研究者批准，仅获取 SPMD `RSE_BSM.csv.zip`（3,228,646,514 B，本地 `dataset/SPMD/selected/`）：成员级 Range（官方 blob Range/ZIP64 目录重新验证通过），CRC32 对中央目录一致、内层 ZIP 校验通过、SHA-256 `9C40C15F…D722`；磁盘 182.98→179.98 GiB。实测：25 字段（官方 24+RxDevice；手册 28 说法有误）、124,115,615 行零畸形、表头独立、BSMID 逐行唯一（行 ID 非消息身份）、TemporaryId 155,220、MsgCount 0–127、DSeconds 发送端分钟内毫秒；**无绝对时间**；RxDevice 2,008 全在 BsmP1Summary 设备命名空间、与 RSE LocID 零重叠（记录方身份 Ambiguous，"RSE" 命名与手册描述不符实际数据）；(TempID,MsgCount,DSeconds) 部分覆盖下重复 ≥26.9M。证据边界：接收时间/时延/丢包 Not Observable、配对 Ambiguous；行为统计按 holdout 规则暂缓（无 DeviceID-Trip 列，隔离策略待研究者）。Packet 建议下一批（RSE 侧绝对时间+信道/功率；修正预期：与 RSE_BSM 无文档化连接键）；BsmP1 价值上调（RxDevice+Gentime 时间锚候选）；新识别 BsmMd（17.29 GB）与 RSE_locations.kml（520 B）。Gate 保持 `pending_official_packet_access`；V3 与其他封存结果未动。结果 `RES-STAGE-0.4-RSE-BSM-V1`（`code/outputs/formal/calibration/stage_0_4_rse_bsm_v1/`）；报告 `docs/STAGE_0_4_TASK_0_4_2_RSE_BSM_AUDIT.md`。

## 2026-10-17 Stage 0.4 身份与时间语义核查（AAD-0.4.3，当前）

只读核查（零下载；Gate `pending_official_packet_access` 不变）。新获官方文档（本地 `dataset/SPMD/Safety_Pilot_Model_Deployment_WSU_BSM_Codebook_ROSA_P_dot66785.pdf` 与 `dataset/SPMD/mcity_documentation/`，SHA 已录）裁定：**RxDevice≡车辆设备 ID**（接收日志；VAD 自记 Rx=Tx）、**Gentime=BSM 生成时间**（µs 自 2004-01-01，1609.2；与样本手册 /1e6−35 s 换算存在官方文档间冲突，待经验校准）、**TxDevice/TxRandom=临时 ID 静态/随机 2 字节**（RSE_BSM.TemporaryId 结构可对应）、**DSecond=分钟内毫秒**（手册 §5.4 被样例算术否定）、BsmP1 ~96% 行程 Rx==Tx。硬边界：**车辆侧接收时间在 SPMD 全家族不存在→V2V 端到端时延不可算**；唯一时延类量=生成→RSE 捕获（需 Packet，身份匹配未证）。RSE_BSM 采样设计 Unverified（每 TemporaryId ≤2 记录方、双记录对 102,469/102,469 全含 10106；10106 为有 488 次 4 月行程的已登记车辆，30 BSM/s 驾驶接收率与 7 个月跨度一致）——**接收率/丢包统计前必须查明采样设计**。Holdout 4 候选已列（结构审计专用维持；其余待研究者）。下一批建议：**BsmMd（17.29 GB）优先**（未脱敏 Tx/Rx 天线 ID+GenTimeRelOffset），BsmP1（55.72 GB）次之（生成时间锚，仍无接收时间），Packet 不为凑 Gate 项提前；新渠道候选 **mCity Rx-BSM 过滤数据集（~9 GB，136 Rx 车辆，Globus）**。日期勘误：0.4.1/0.4.2 实际均执行于 2026-10-16（commit/封存时间戳证明；存活文档已非覆盖式更正，封存包零改动）。报告：`docs/STAGE_0_4_TASK_0_4_3_IDENTITY_TIME_REVIEW.md`。

## 2026-10-18 AAD-0.5.4-A+ 定向补充

`RES-STAGE-0.5-CALIBRATION-GAPS-V1`：两个原始校准TXT共2,583,693行与R2状态100%连接，冲突0；来源车辆2169/2017，汽车比例96.173%/97.323%、汽车中位长4.4196m，车型/长度物理真值仍Unverified。源时钟解释952.8/999s、两源重叠89.5s，没有发现标准化时间错误。候选主线1–5、150≤y<350m；首尾按最长观测轨迹时长100.9/123.5s作候选缓冲后，保留12/11个60s片，统一密度阈值42.8767/48.0828veh/km/lane，内部覆盖720/660s；300m主线1648/1449.82veh/h/lane。局部/分层P2完整成员归属未批准，率Unresolved。

四次300s工程负载完成（SUMO1.26.0，seed20261018，recorded.1s）；.05s低/中/高实际密度41.91/48.06/54.76，墙钟100.27/103.03/116.24s，峰值合计RSS271.9/297.8/327.7MB，末时未插入0/17/23，无碰撞/teleport/守恒残差。初始化积压仍在，60s不是批准暖机；.05s自动ballistic而.1s积分器未显式固定，不能声称数值收敛。完整P2提取成本未含入。Engineering Ready有条件、Measurement Ready待有限批准、Calibration Ready=false、Reality Coverage Accepted=false；所有科学容差Tolerance Not Yet Justified，推荐路径B受限探索仅Proposal，未启动。Gate继续pending_simulation_sample，无验证/holdout/下载/正式校准/锁/Stage I/II。

依据：`docs/STAGE_0_5_TASK_0_5_4A_SUPPLEMENT_CALIBRATION_GAPS.md`及同ID的diagnostics、unified_strata、benchmark、candidate_protocol、audit。完整包`code/outputs/formal/calibration/stage_0_5_calibration_gaps_v1_final/`。Context Consistency Check：不将Proposal写入06_DECISIONS的Approved Research Decision。


## 2026-10-18 B0当前决策节点（覆盖此前仅Proposal的探索状态）

2026-10-18 AAD-0.5.4-B0（RES-STAGE-0.5-EXPLORATORY-RESPONSE-V1）：受限探索完成19/23次，4次高输入seed20261019响应未运行。统一27.78m/s上限、空初态、ballistic显式、internal.05/recorded.1、action.1、sigmaStep1；三个基准输入1087.364/1449.818/1648veh/h/lane仅实现局部密度10.37–15.75、均速约27.1，局部低速/P2均0。tau2三次末期未服务21/22/71，入口main0约2.5–20.1m有低速插入/加速，局部段无拥堵。B0-EXEC-STOP-01：原调度器未因completed+blocker停止，发现后人工停止，源码停止后修复并测试；最后worker峰值内存Unverified。推荐先批准需求边界/最小结构对照，不继续参数搜索掩盖状态支持缺口。所有结果exploratory_diagnostic_only、scientific_claim_eligible=false；Gate=pending_simulation_sample、Calibration Ready=false、Reality Coverage Accepted=false、正式容差Tolerance Not Yet Justified、Energy Distance上界Not Identifiable；B0实验验证输入0；根全量回归无过滤打开历史Stage0.2全源事件/案例产物，任务级验证访问不能认证（B0-VALIDATION-SCOPE-02）；数据隔离验收不Accepted。无holdout/正式校准/锁/Stage I。依据：docs/STAGE_0_5_TASK_0_5_4B0_EXPLORATORY_RESPONSE_DIAGNOSTICS.md、同ID证据和execution_ledger。

## 2026-10-19 当前B1决策节点

B1（RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1）按阻断提前结束：V1失败A后7次未启动，V2 A有效/B警告/C阻断/D未启动，累计4次尝试；无补跑或新seed。A/B局部均速27.1088/26.5152m/s、密度16.3208/16.8197、低速0；C记录2.4007m/s、93.8653veh/km/lane、低速80.1719%、末期未服务252，但停车位移检查与冻结回溢资格阻断，不能作为有效校准样本。D只有静态/空加载检查，动态未知。

研究者保留B0有限描述证据，B0任务隔离false/验证物化Unknown不变。B1用两校准摘要白名单、SHA/角色守卫、-S最小胶囊、Python路径/子进程审计；冻结前45测试通过、假路径拒绝3/3，矩阵worker拒绝0；不声称OS/native全监控。根工作区不跑全量pytest，全量只在无本地历史数据的Git检出执行，数据skip不算通过。

Gate=pending_simulation_sample、scientific_claim_eligible=false、ready_to_start_stage_0_5_4b=false、reality_coverage_accepted=false；容差Tolerance Not Yet Justified，ED上界Not Identifiable，ProtocolLock/StageI禁止。仅推荐下一项B1.1停车数值/队列回溢观测契约整改，未启动。

依据：`docs/STAGE_0_5_TASK_0_5_4B1_BOUNDARY_BOTTLENECK_CONTRAST.md`、`evidence/results/RES-STAGE-0.5-BOUNDARY-BOTTLENECK-V1/`中的preflight、execution_stop_observation、numerical_stop_diagnostic、queue_diagnostics、run_manifest和SHA256SUMS。

## 2026-10-28 Stage 0.5 first-round offline decision package
Verified: R0/R1/B00 evidence and all directly linked admission/audit files were enumerated and hashed. R1 event arrays reconcile 7/1/19/0, window onsets 5/0/17/0, while formal source/target P2 remain 0. B10/B11 window events are chiefly auxiliary lane 6; B01 event is pre-window; one B11 mainline event is outside target. Candidate comparisons are exploratory only; SUMO/TraCI=0, holdout=0, formal P2 unchanged. Stage 0.5 blocked; Stage 0.6 and Stage I unchanged. Report: docs/STAGE_0_5_FIRST_ROUND_OFFLINE_DECISION_20261028.md; evidence: evidence/results/RES-STAGE-0.5-FIRST-ROUND-OFFLINE-DECISION-20261028/.
