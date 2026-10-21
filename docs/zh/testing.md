# 🧪 SYNAPSE: 自动化测试套件与质量保证指南

本规范阐述 **SYNAPSE CORE** 的全层级测试架构、Pytest 测试套件、合成遥测数据流生成器与代码覆盖率准则。

⬅️ [文档总中心](README.md) | 🛡️ [安全机制与守卫](safety_and_watchdog.md) | 🏛️ [系统架构蓝图](architecture.md)

---

## 1. 测试套件分层架构

测试用例统一归整于 `tests/` 目录，按职责分层：

- **单元测试 (`tests/unit/`)**：针对领域实体、运动学计算与状态机流转进行单模块隔离测试。
- **神经网络测试 (`tests/models/`)**：验证 11 个 MARKVART™ 架构的前向与反向传播、张量维度一致性及梯度稳定性。
- **系统集成测试 (`tests/integration/`)**：验证从传感器采集端口经过 AppState 门面直至 gRPC 推流器的全链路数据流通。
- **IPC 协议测试 (`tests/ipc/`)**：针对 Stdio JSON-RPC 管道进行高并发突发指令与畸形报文鲁棒性注入测试。
- **性能基准测试 (`tests/benchmarks/`)**：测定高频推理周期时延、内存开销及序列化带宽吞吐。

---

## 2. 运行自动化测试

在执行测试前激活 Python 虚拟环境：

```bash
source .venv/bin/activate
```

### 运行全量测试套件：
```bash
pytest tests/ -v
```

### 运行并生成代码覆盖率分析报告：
```bash
pytest --cov=src --cov-report=term-missing --cov-report=html tests/
```

### 仅测试深度神经网络模型：
```bash
pytest tests/test_neural_models.py -v
```

---

## 3. 合成交通流与确定性仿真桩 (Mocks)

为支持在无物理雷达线圈的隔离研发环境中持续交付：

- **`SyntheticTrafficGenerator`**：基于 Greenshields 与激波偏微分方程生成高度拟真的动态车辆流。
- **`MockHftReceiver`**：内存级 gRPC 模拟服务端，用于捕获输出快照并校验延迟与契约模式。
- **固定确定性随机数种子**：所有深度模型测试强制固定底层随机数种子 (`torch.manual_seed(42)`)，确保跨平台比特级可复现。

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
