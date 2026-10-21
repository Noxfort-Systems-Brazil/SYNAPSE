# ⚡ SYNAPSE: Сбор данных и высокочастотный транспорт gRPC HFT-Link

Данный документ описывает мультипротокольный концентратор сбора данных, спецификацию Protocol Buffers v3 и архитектуру высокоскоростной передачи gRPC с автоматическим восстановлением соединений.

⬅️ [Главный Хаб](README.md) | ⏱️ [Фазы выполнения](execution_phases.md) | 🖥️ [Десктопный интерфейс](ui_architecture.md)

---

## 1. Мультипротокольный концентратор сбора данных

Модуль Ingestion Hub (`src/infrastructure/ingestion/`) предоставляет адаптеры для интеграции разнородных источников:

- **HTTP Ingestion**: REST-эндпоинты для получения агрегированных данных от сторонних систем (Waze CCP, TomTom Move).
- **MQTT-клиент**: Подписка на каналы дорожных контроллеров (RSU) и индуктивных петель (`traffic/sensors/#`).
- **Шлюз WebSocket**: Постоянные двунаправленные соединения с низкой задержкой для радаров прямого обзора.
- **Высокопроизводительный шлюз на Go**: Скомпилированный бинарный модуль (`synapse-go`) для обработки сетевых сокетов на скорости физической линии.

---

## 2. Спецификация Protocol Buffers v3 (HFT-Link)

Для субмиллисекундной сериализации используется Protocol Buffers v3 (`proto/synapse_hft.proto`):

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

## 3. Высокочастотный стриминг в CARINA

Модуль `HftStreamer` поддерживает постоянный поток HTTP/2 gRPC для снабжения данными контроллеров **CARINA CORE**:

- **Гарантированная задержка**: Сквозная задержка (прием датчика $\rightarrow$ инференс $\rightarrow$ доставка gRPC) строго поддерживается на уровне **менее 250 мс**.
- **Zero-Copy сериализация**: Тензоры PyTorch упаковываются в байтовые буферы без лишних аллокаций памяти.
- **Регулировка противодавления**: Динамические скользящие окна предотвращают замедление инференса из-за медленных потребителей.

---

## 4. Автономная отказоустойчивость и Circuit Breaker

Модуль восстановления (`src/infrastructure/hft_recovery.py`) нейтрализует сетевые сбои:

1. **Экспоненциальная задержка со случайным разбросом (Jitter)**:
   $$T_{\text{wait}} = \min(T_{\max}, T_{\text{base}} \cdot 2^{\text{attempt}}) \cdot \mathcal{U}(0.5, 1.5)$$
2. **Паттерн Circuit Breaker**: После 5 неудачных попыток передачи цепь размыкается (`OPEN`), данные буферизуются в кольцевой очереди, а супервизор получает оповещение.
3. **Плавная повторная синхронизация**: При восстановлении канала статус переходит в `HALF-OPEN`, сбрасывая накопленный буфер перед возобновлением прямого вещания.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
