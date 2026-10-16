# Stage 0.4 任务 0.4.2：RSE_BSM 获取与独立证据核验

仅获取 `SPMD/RSE_BSM.csv.zip`（研究者批准的唯一成员）。来源为官方 SPMD.zip blob（DOI 10.21949/1504482），ZIP64 成员级 Range 下载，49 个 64 MiB 分块全部通过 206/Content-Range/ETag 检查；成员 CRC32 与中央目录一致（41d7512f），内层 ZIP testzip 通过；本地 SHA-256 9C40C15F…D722。磁盘 182.98→179.98 GiB，全程远高于 5 GiB 安全余量。

核心核验结论（细节见本目录 audit.json 与 `docs/STAGE_0_4_TASK_0_4_2_RSE_BSM_AUDIT.md`）：
1. 实际 schema = 25 字段（官方 24 + RxDevice）；无任何绝对时间字段；数据文件无表头（表头为独立 head.csv）。
2. 124,115,615 行、0 畸形；BSMID 逐行唯一（非跨接收方消息身份）；MsgCount 0–127 循环；DSeconds 0–59999（发送端分钟内毫秒）。
3. 最佳成员内配对键 (TemporaryId,MsgCount,DSeconds) 在部分覆盖下已有 ≥26,919,767 次重复——月尺度消息身份 Ambiguous。
4. RxDevice 2,008 个值全部落在 BsmP1Summary 设备 ID 命名空间（2,008/2,008），与 PCAPFile 的 25 个 RSE LocID 零重叠——"RSE" 命名与官方手册 RSE-dataset 描述同实际记录方命名空间不符，物理身份 Ambiguous。
5. 无接收时间戳：RSE_BSM 单独不能提供任何时延或时序证据。
6. Gate 不变（pending_official_packet_access）；RV_RX/V3 封存结果不动；行为统计按 holdout 规则暂缓。

Packet 决策输入：Packet 为 RSE/PCAP 侧（绝对 GMT 捕获时间+信道/功率），与 RSE_BSM 无文档化连接键；BsmP1 的 RxDevice+Gentime 结构与本成员记录方命名空间一致，其价值上调；另识别 BsmMd（17.29 GB，身份链接候选）与 RSE_locations.kml（520 B）。
