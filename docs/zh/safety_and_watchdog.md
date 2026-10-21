# 🛡️ SYNAPSE: 安全机制、看门狗守卫与平滑降级门控策略

本规范详细说明神经符号学安全规则集、**F.E.N.I.X.** 跨进程常驻监督器、高敏心跳监测机制、物理内存硬性防护以及分级降级门控策略 (**Gating Policy**)。

⬅️ [文档总中心](README.md) | 🖥️ [桌面交互界面](ui_architecture.md) | 🧪 [测试规范与 QA](testing.md)

---

## 1. F.E.N.I.X. 独立外部监督器

为确保城市级高频感知融合平台永不停机，核心推理进程受制于外部守护进程 (`src/fenix/process_supervisor.py`)：

```bash
python synapse.py --supervisor
```

### 核心管理职责：
1. **进程活性心跳 (Heartbeats)**：核心计算线程每隔 250 毫秒通过匿名管道发出心跳。若超过 **500 毫秒** 未收到心跳包，监督器立即判定进程出现死锁。
2. **物理内存上限约束**：监督器周期性采样常驻内存 (RSS)。一旦超过配置硬顶（如 4096 MB），强制触发显存回收或平滑交接重启。
3. **毫秒级极速自愈**：在发生段错误 (Segmentation Fault)、CUDA 显存溢出或未捕获致命异常时，F.E.N.I.X. 可在 **1.0 秒** 内快速拉起全新 Worker 进程，并加载最新持久化检查点完成数据平滑衔接。

---

## 2. 分级降级门控策略 (Gating Policy)

当遇到城市网络故障或雷达损坏时，**Gating Policy** (`src/domain/gating_policy.py`) 严防产生空值或导致网络震荡：

```
┌────────────────────────────────────────────────────────┐
│                   门控策略分级降级瀑布                 │
│                                                        │
│  [第一层级: 完整神经网络感知]                          │
│  对所有处于激活状态的可靠传感器执行 MARKVART™ 推理     │
│                           │                            │
│                           ▼ (发生瞬时传感器丢包)       │
│  [第二层级: 运动学航位推算 (KSE)]                      │
│  基于卡尔曼滤波进行车辆动力学坐标连续外推 (v, a)       │
│                           │                            │
│                           ▼ (传感器持续失联 > 30秒)    │
│  [第三层级: 历史微观基线 (MEH)]                        │
│  平滑注入历史分时段标定交通流量分布特征                │
└────────────────────────────────────────────────────────┘
```

- **第一级 (神经网络)**：标准工况，数据源置信度 $\tau \ge 0.70$。
- **第二级 (KSE)**：应对偶发网络拥塞 ($1 \le N_{\text{missed}} \le 30$)，基于流体连续性外推，消除突变毛刺。
- **第三级 (历史基线)**：应对现场传感器硬件严重损坏，在人工维修介入前维持系统稳态。

---

## 3. 神经符号学物理守恒法则

所有采集数据在进入张量前必须通过物理不变量断言检查：
- **`SR-01 (速度上限)`**：城市普通道路车速 $v \le 180\text{ km/h}$。
- **`SR-02 (加速度不变量)`**：物理加减速度极限 $|a| \le 8.5\text{ m/s}^2$。
- **`SR-03 (堵塞密度极限)`**：车道密度 $\rho \le \rho_{\text{jam}} = 140\text{ 辆/公里/车道}$。
- **`SR-04 (交叉口流量守恒)`**：节点进出流量必须符合物理守恒定律。

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
