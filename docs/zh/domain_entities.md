# 🗂️ SYNAPSE: 领域实体与空间拓扑模式

本规范详细定义 `src/domain/entities.py` 中声明的核心领域实体、城市路网图拓扑、贝叶斯可信权重分级以及零信任状态机模型。

⬅️ [文档总中心](README.md) | 🏛️ [系统架构蓝图](architecture.md) | 🧠 [MARKVART™ 神经网络群](neural_models.md)

---

## 1. 空间拓扑图实体

城市路网被抽象为有向多重图 $G = (V, E)$，对应强类型的 Python 数据类：

### `MapNode`
表示信号交叉口、道路决策点或虚拟感知信标：
- `node_id: str`：唯一 UUID 或市政 OSM 节点标识。
- `latitude: float`, `longitude: float`：WGS84 地理经纬度坐标。
- `elevation: float`：海拔高度（米）。
- `node_type: NodeType`：枚举 (`INTERSECTION`, `RAMP`, `MIDBLOCK`, `BRIDGE`, `TUNNEL`)。
- `connected_edges: List[str]`：相连的出入道路边列表。

### `MapEdge`
表示连接两个节点的单向路段：
- `edge_id: str`：路段唯一标识。
- `source_node_id: str`, `target_node_id: str`：路段起止端点。
- `length_meters: float`：物理长度（米）。
- `lanes: int`：有效车道数量 ($N_l \ge 1$)。
- `speed_limit_kmh: float`：路段法定最高限速。
- `capacity_veh_per_hour: float`：基于格林希尔茨 (Greenshields) 模型计算的最大设计通行能力：
  $$C = v_f \cdot \frac{\rho_{\text{jam}}}{4}$$

---

## 2. 数据采集源实体

### `DataSource`
封装物理或虚拟感知设备源：
- `source_id: str`：传感器或数据提供商唯一 ID。
- `name: str`：便于运维人员辨识的名称。
- `source_type: SourceType`：(`CAMERA`, `RADAR`, `INDUCTION_LOOP`, `BLUETOOTH`, `WAZE_API`, `TOMTOM_API`, `SUMO_SIM`)。
- `protocol: IngestionProtocol`：接入协议 (`HTTP_POST`, `MQTT_TOPIC`, `WEBSOCKET`, `GRPC`)。
- `trust_score: float`：动态贝叶斯可信度权重 ($0.0 \le \tau \le 1.0$)。
- `status: SourceStatus`：在零信任状态机中的当前流转状态。

---

## 3. 贝叶斯先验可信度分级

为杜绝虚假网络流量、高噪第三方接口对神经网络张量的干扰，SYNAPSE 根据感知物理距离设定先验权重：

$$\tau_{\text{initial}} = \begin{cases} 0.95 & \text{本地地面感知（地磁地感线圈、专用毫米波雷达、边缘相机）} \\ 0.60 & \text{外部云端 API（众包众包路况 Waze/TomTom、基站信令）} \end{cases}$$

### 可信度动态迭代
权重根据测量的物理守恒性持续动态更新：

$$\tau_{t+1} = \frac{\tau_t \cdot P(E \mid \text{有效})}{\tau_t \cdot P(E \mid \text{有效}) + (1 - \tau_t) \cdot P(E \mid \text{故障})}$$

若 $\tau_t$ 降至门限值 $\tau_{\text{threshold}} = 0.40$ 以下，系统将自动触发降级隔离。

---

## 4. `SourceStatus` 零信任状态机

```
              ┌───────────────┐
              │   隔离状态    │ ◄── 初始接入
              └───────┬───────┘
                      │ 满足格式与模式规范
              ┌───────▼───────┐
              │   校验状态    │ ◄── 物理极限测试 ($|\Delta v| \le a_{\max}$)
              └───────┬───────┘
                      │ 连续数据包有效 ($N \ge 10$)
              ┌───────▼───────┐
       ┌────► │   激活状态    │ ◄── 直接参与 MARKVART 神经网络计算
       │      └───────┬───────┘
恢复连通      │ 丢包或超时 (> 3 个采集周期)
       │      ┌───────▼───────┐
       └───── │   后备状态    │ ◄── 触发 KSE 运动学航位推算
              └───────┬───────┘
                      │ 持续异常或长时间失联
              ┌───────▼───────┐
              │   拒绝状态    │
              └───────────────┘
```

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
