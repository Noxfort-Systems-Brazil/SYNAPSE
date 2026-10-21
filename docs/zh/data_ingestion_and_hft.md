# ⚡ SYNAPSE: 数据采集接入与 HFT-Link 高频 gRPC 传输

本规范详细说明多协议传感器接入适配层、Protocol Buffers v3 通信协议以及高频低时延 gRPC 流水线的自动重连与自愈机制。

⬅️ [文档总中心](README.md) | ⏱️ [执行阶段机制](execution_phases.md) | 🖥️ [桌面交互界面](ui_architecture.md)

---

## 1. 异构数据采集中心 (Ingestion Hub)

采集适配中心 (`src/infrastructure/ingestion/`) 提供了标准化接口：

- **HTTP 采集组件**：提供 REST 接收端口，接收第三方平台交通路况推流 (Waze CCP、TomTom Move)。
- **MQTT Broker 客户端**：订阅城市路侧边缘计算单元 (RSU) 与信号机发布的话题 (`traffic/sensors/#`)。
- **WebSocket 网关**：针对毫米波雷达设备建立低时延双向长连接。
- **Go 编写的高性能网关**：原生编译二进制 (`synapse-go`) 运行于网络边界，在线速下直接处理原始套接字报文。

---

## 2. HFT-Link Protocol Buffers v3 接口定义

遥测数据与神经网络输出均采用 Protocol Buffers v3 进行极速紧凑序列化 (`proto/synapse_hft.proto`)：

```protobuf
syntax = "proto3";

package synapse.hft;

service HftLinkService {
  rpc StreamSnapshots(SnapshotRequest) returns (stream TrafficSnapshot);
  rpc SendTelemetryBatch(TelemetryBatch) returns (IngestionResponse);
}

message TrafficSnapshot {
  int64 timestamp_ns = 1;
  string snapshot_id = 2;
  repeated EdgeMetrics edges = 3;
  repeated NodeMetrics nodes = 4;
  repeated float density_matrix = 5;
  int32 confidence_score = 6;
}

message EdgeMetrics {
  string edge_id = 1;
  float density_veh_km = 2;
  float mean_speed_kmh = 3;
  float occupancy_ratio = 4;
  int32 source_status = 5;
}
```

---

## 3. 向 CARINA 控制机推送高频状态流

`HftStreamer` 模块基于 HTTP/2 协议建立通向下游 **CARINA CORE** 的专用 gRPC 高速通道：

- **端到端时延保证**：全链路处理时延（现场传感器采集 $\rightarrow$ 深度神经网络推理 $\rightarrow$ gRPC 交付）严格控制在 **250 毫秒** 以内。
- **零内存拷贝 (Zero-Copy)**：PyTorch 张量直接平铺进入 Protobuf 二进制缓冲区。
- **背压流量控制**：动态滑动窗口机制确保慢速客户端不会拖慢核心推理循环。

---

## 4. 自主恢复机制与熔断器 (Circuit Breaker)

通信恢复策略 (`src/infrastructure/hft_recovery.py`) 有效抵御网络断连：

1. **指数退避与随机抖动 (Jitter)**：
   $$T_{\text{wait}} = \min(T_{\max}, T_{\text{base}} \cdot 2^{\text{attempt}}) \cdot \mathcal{U}(0.5, 1.5)$$
2. **熔断器模式**：若连续 5 次传输失败，熔断器立即切断 (`OPEN`)，将遥测数据缓存在环形内存队列中并上报 F.E.N.I.X.。
3. **半开平滑重连**：当通道连通性恢复后，状态切换至 `HALF-OPEN`，优先排空堆积的关键遥测包，继而无缝恢复实时推流。

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
