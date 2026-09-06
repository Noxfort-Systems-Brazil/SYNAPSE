# 07. Production Deployment Guide

> **Production Server Configuration, Headless Daemon Mode, Systemd Services, Watchdog Supervisor (F.E.N.I.X.), and Log Rotation**

---

> 🧭 **Navigation**:
> [🏠 Synapse Core](../README.md) • [📚 Docs Index](README.md) • [« Previous: 06. Developer Guide](06_developer_guide.md)

---

## 🏭 Overview

Running `npm run tauri dev` or `python synapse.py` without arguments launches the native desktop graphical interface. 

In enterprise municipal traffic centers or edge server cabinets, SYNAPSE must run as an autonomous, auto-restarting headless background daemon to ensure traffic lights connected to the [HFT-Link](05_data_ingestion_and_hft.md) never lose their neural perception feed.

---

## ⚙️ 1. Environment Preparation (Ubuntu 22.04 / 24.04 LTS)

1. **GPU & CUDA**: Ensure NVIDIA proprietary drivers (v535+) and the CUDA 12.x Toolkit are installed at the host OS level.
2. **Directory Placement**: Deploy the repository to `/opt/noxfort/synapse`.
3. **Dedicated System User**:
   ```bash
   sudo useradd -r -s /bin/false -d /opt/noxfort/synapse trafficadmin
   sudo chown -R trafficadmin:trafficadmin /opt/noxfort/synapse
   ```
4. **Virtual Environment & Dependencies**:
   ```bash
   cd /opt/noxfort/synapse
   sudo -u trafficadmin python3 -m venv .venv
   sudo -u trafficadmin /opt/noxfort/synapse/.venv/bin/pip install --upgrade pip
   sudo -u trafficadmin /opt/noxfort/synapse/.venv/bin/pip install -r requirements.txt
   ```
5. **Model Weights**: Ensure [`Model_Vault/`](../Model_Vault/README.md) contains `distilroberta/` and `Qwen3.5-2B-UD-Q6_K_XL.gguf`.

---

## 🛡️ 2. Running as a `systemd` Service

### Option A: Standard Headless Daemon Unit
Create `/etc/systemd/system/synapse-core.service`:

```ini
[Unit]
Description=SYNAPSE Core Intelligent Perception Gateway
After=network.target postgresql.service
Wants=network-online.target

[Service]
Type=simple
User=trafficadmin
Group=trafficadmin
WorkingDirectory=/opt/noxfort/synapse
Environment="PATH=/opt/noxfort/synapse/.venv/bin:/usr/local/cuda/bin"
Environment="SYNAPSE_ROOT=/opt/noxfort/synapse"
Environment="SYNAPSE_HEADLESS=1"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/noxfort/synapse/.venv/bin/python synapse.py --daemon

# Resource Limits & Sandboxing
LimitNOFILE=65536
Restart=always
RestartSec=3s
ProtectSystem=full
ProtectHome=read-only
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

### Option B: Mission-Critical Watchdog Supervisor (F.E.N.I.X.)
For high-availability mission-critical signalized corridors, launch the out-of-process supervisor:

```ini
ExecStart=/opt/noxfort/synapse/.venv/bin/python synapse.py --supervisor
```
F.E.N.I.X. continuously monitors the child Python neural core process, intercepts out-of-memory (OOM) alerts, and hot-resurrects the inference pipeline without manual human intervention.

---

## 🚀 3. Managing the Service

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service on boot
sudo systemctl enable synapse-core

# Start the service
sudo systemctl start synapse-core

# Inspect real-time status and journal logs
sudo systemctl status synapse-core
sudo journalctl -u synapse-core -f
```

---

## 📦 4. Native Debian Package Installation (`.deb`)

For municipal edge nodes with standard package managers:

```bash
# Build standalone .deb package
bash packaging/build_deb.sh

# Install on target server
sudo dpkg -i synapse_2.0_amd64.deb
sudo apt-get install -f

# Start the global systemd service
sudo systemctl enable --now synapse.service
```

For complete packaging build scripts, refer to [`packaging/README.md`](../packaging/README.md).

---

## 📊 5. Observability Stack (Prometheus & Grafana)

To monitor system throughput, neural cycle jitter, and GPU VRAM in production:

```bash
# Launch Prometheus and Grafana containers
docker compose -f observability/docker-compose.yml up -d
```
- **Grafana**: `http://<server-ip>:3000` (User: `admin` | Password: `synapse123`)
- **Prometheus**: `http://<server-ip>:9090`
- Complete metric definitions in [`observability/README.md`](../observability/README.md).

---

## 🧹 6. Automated Log Rotation

To prevent telemetry logs from filling the storage drive, configure `/etc/logrotate.d/synapse`:

```text
/opt/noxfort/synapse/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 trafficadmin trafficadmin
    sharedscripts
    postrotate
        kill -USR1 $(pgrep -f "synapse.py") 2>/dev/null || true
    endscript
}
```
This preserves 14 days of historical logs for [Jurist Agent](03_neural_models.md#11-qwen3-explainable-ai--legal-jurist) audits and compresses older files.

---

<p align="center">
  <sub>SYNAPSE Production Operations — Noxfort Systems</sub><br/>
  <sub><a href="#07-production-deployment-guide">Back to top ↑</a></sub>
</p>
