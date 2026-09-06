# Security Policy

> **Vulnerability Disclosure & Security Architecture Guidelines for Critical Municipal Infrastructure**

---

> 🧭 **Navigation**:
> [🏠 Synapse Core](README.md) • [🏗️ Architecture](ARCHITECTURE.md) • [🤝 Contributing](CONTRIBUTING.md) • [📜 Code of Conduct](CODE_OF_CONDUCT.md) • [📄 License](LICENSE)

---

## 🛡️ Supported Versions

SYNAPSE CORE orchestrates real-time municipal traffic operations. Only actively supported versions receive critical security patches and hotfixes:

| Version | Supported | Security Patch Cadence |
| :--- | :--- | :--- |
| **v2.0.x** | :white_check_mark: Yes | Active (Critical hotfixes within 48h) |
| **v1.0.x** | :warning: Maintenance | High-severity security issues only |
| **< v1.0** | :x: No | End of Life (Upgrade strongly recommended) |

---

## 🔒 Threat Model & Zero-Trust Posture

SYNAPSE controls physical city infrastructure (interfaced with traffic signal controllers such as CARINA via the [`HFT-Link`](proto/README.md)). As an intelligent gateway deployed on edge servers and municipal data centers, the platform assumes an untrusted operating environment:

1. **Ingestion Zero-Trust**: All inbound sensor telemetry is initially held in `QUARANTINE` and analyzed by the [`Linguist Agent`](docs/01_domain_entities.md#the-zero-trust-security-pipeline) and symbolic rule verifiers before entering graph memory.
2. **Zero-Port IPC**: The desktop interface communicates strictly through standard streams (`stdin`/`stdout`) via [`StdioDaemon`](src/README.md#-core-subsystems-in-detail), opening zero local TCP or HTTP listening ports.
3. **Ghost-File Verification**: Historical Data Lake `.parquet` files and neural `.safetensors` checkpoints undergo zero-byte and checksum validation during [`Phase 1 Bootstrap`](docs/04_execution_phases.md#phase-1-offline-bootstrap-bootstrap_phasepy) to prevent filesystem tampering.

---

## 🚨 Reporting a Vulnerability

> [!WARNING]
> **DO NOT** report security vulnerabilities or exploits via public GitHub Issues, discussions, or pull requests.

If you identify a security vulnerability—particularly involving:
- **Sensor Data Injection / Spoofing Attacks**: Bypassing zero-trust validation to inject false queue lengths or velocities.
- **Protobuf / gRPC Exploits**: Memory corruption, buffer overflows, or amplification attacks on `proto/synapse_hft.proto`.
- **Model Poisoning / Adversarial Evasion**: Adversarial perturbations targeting PyTorch neural operators (PINO, DeepONet, iTransformer).
- **Process Escalation / IPC Hijacking**: Intercepting or executing unauthorized commands through the Tauri/Rust sidecar pipe.

Please report the issue confidentially via email to:
**`security@noxfort.com`**

### Vulnerability Report Checklist:
When submitting a report, please include:
1. Clear description of the vulnerability and attack vector.
2. Complete steps to reproduce (or a minimal Proof of Concept script).
3. Affected versions, OS, and environment details (CUDA version, Python runtime).
4. Potential impact on physical traffic control safety or system availability.

---

## ⏱️ Response Timeline & SLA

- **Acknowledgment**: Within **24 to 48 hours** of initial receipt.
- **Assessment & Triage**: Within **5 business days**, detailing severity scoring (CVSS) and patch roadmap.
- **Remediation & Patch Release**: Critical vulnerabilities impacting traffic light operations receive emergency hotfixes within **7 business days**.
- **Public Disclosure**: Coordinated public disclosure only occurs *after* a security patch has been merged and distributed to municipal operators.

---

<p align="center">
  <sub>SYNAPSE Security Operations — Noxfort Systems</sub><br/>
  <sub><a href="#security-policy">Back to top ↑</a></sub>
</p>
