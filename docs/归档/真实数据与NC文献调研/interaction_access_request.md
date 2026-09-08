# INTERACTION 数据集申请材料

状态：材料已准备，尚未提交。官方要求使用高校或单位邮箱申请；以下个人信息不得猜填。

## 待填写信息

- 申请人姓名：`[待填写]`
- 同济大学院系：`[待填写]`
- 单位邮箱：`[待填写]`
- 导师/课题负责人：`[待填写]`
- 预计研究期限：`[待填写]`

## 英文项目说明（表单短版）

**Project title:** Information-mediated non-nearest-neighbour traffic risk effects in connected traffic

We study whether a traceable remote risk message can change a target vehicle's action and risk outcome before the physical influence of the source disturbance reaches that vehicle. INTERACTION trajectories will be used only for non-commercial academic research at Tongji University. They will provide real-traffic baselines for leader-follower interaction, positive-gap and closing-speed conditions, time-to-collision risk, and physical risk propagation across merging, lane-changing, intersection and roundabout scenarios. The dataset will not be treated as evidence of message delivery or controller adoption because it contains trajectories rather than a complete V2X message lifecycle. We will not redistribute the raw data and will cite the dataset and its associated publication as required.

## 英文项目说明（邮件长版）

**Subject:** Request for non-commercial research access to the INTERACTION dataset

Dear INTERACTION Dataset Team,

I am `[name]`, a `[student/researcher]` at `[department]`, Tongji University, working under the supervision of `[supervisor]`. I would like to request access to the INTERACTION dataset for a non-commercial academic research project on traffic-risk propagation and connected-vehicle information effects.

The project distinguishes physical traffic propagation from explicit information propagation. Its central question is whether a traceable remote risk message, after generation, transmission, delivery and controller use, can alter a target vehicle's action and risk outcome before the physical effect of the source disturbance arrives. We plan to use INTERACTION only for the trajectory-observable part of this question: reconstructing leader-follower relations, enforcing valid positive-gap and closing-speed conditions, calculating trajectory-based time-to-collision risk, and testing physical propagation patterns across merging, lane-changing, intersection and roundabout scenarios.

We understand that INTERACTION trajectories do not observe V2X message generation, delivery or controller adoption. We will therefore not use the dataset to claim causal identification of the information channel. Instead, it will serve as an external real-traffic benchmark for the physical-interaction and risk-measurement components of the study.

The data will be used only by authorized members of our research group, stored on access-controlled institutional devices, and not redistributed. Any publication will cite the dataset and comply with its non-commercial terms of use.

Sincerely,

`[name]`  
`[department, Tongji University]`  
`[institutional email]`  
`[supervisor, if required]`

## 中文用途边界

- 可以验证：真实轨迹中的 leader-follower 关系、正间距、接近速度、TTC 风险负担，以及合流/换道等物理交互场景中的风险时序。
- 不能验证：消息生成、发送、交付、丢包、控制器采用和由采用导致的动作变化。
- 因此它是“物理传播与风险指标的外部锚定”，不是“显式信息作用的现场因果验证”。

## 提交前检查

- [ ] 用单位邮箱填写申请人、院系和导师信息。
- [ ] 确认课题负责人同意数据用途和存储方式。
- [ ] 阅读并接受非商业使用、署名和禁止再分发条款。
- [ ] 保存申请日期、表单文本和官方回复。
- [ ] 获批后记录下载文件、版本、校验和与许可文本。
- [ ] 原始数据只放入受控目录，不提交到公开仓库。
