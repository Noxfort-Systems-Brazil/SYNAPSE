# SYNAPSE Model Vault — Pre-Trained Weights & Neural Assets

> **Foundational Neural Weights, Transformer Tokenizers, and Quantized LLMs**

---

> 🧭 **Navigation**:
> [🏠 Synapse Core](../README.md) • [🏗️ Architecture](../ARCHITECTURE.md) • [📚 Docs Index](../docs/README.md) • [🧠 Neural Models](../docs/03_neural_models.md) • [🛡️ Zero-Trust Gatekeeper](../docs/01_domain_entities.md#the-zero-trust-security-pipeline)

---

## 🏛️ Overview

The `Model_Vault/` directory hosts foundational pre-trained neural network weights, tokenizers, and Large Language Model (LLM) binaries required by **SYNAPSE CORE**. 

These assets power the zero-trust semantic ingestion gatekeeper ([`Linguist Agent`](../docs/03_neural_models.md#10-distilroberta--gmm-zero-trust-linguist--peak-scheduler)), the urban schedule segmenter ([`Peak Classifier`](../docs/03_neural_models.md#10-distilroberta--gmm-zero-trust-linguist--peak-scheduler)), and the legal/compliance explainable AI generator ([`Jurist Agent`](../docs/03_neural_models.md#11-qwen3-explainable-ai--legal-jurist)).

---

## 📂 Model Vault Directory Layout

```text
Model_Vault/
├── distilroberta/                 # Transformer Language Model for Zero-Trust Validation
│   ├── config.json                # Model architecture hyper-parameters
│   ├── merges.txt                 # BPE tokenizer merges
│   ├── model.safetensors          # PyTorch weights in zero-copy SafeTensors format
│   ├── special_tokens_map.json    # Special token mapping
│   ├── tokenizer.json             # Fast HuggingFace Tokenizer definition
│   ├── tokenizer_config.json      # Tokenizer parameters
│   └── vocab.json                 # Vocabulary dictionary
│
└── Qwen3.5-2B-UD-Q6_K_XL.gguf     # 6-bit Quantized LLM for XAI Jurist Reports (~1.86 GB)
```

---

## 🧠 Model Specifications

### 1. DistilRoBERTa (Zero-Trust Gatekeeper & Peak Classifier)
- **Role**: Encodes unstructured incoming sensor payload schemas, verifies semantic validity (e.g., speed vs. volume), and clusters temporal traffic periods.
- **Format**: `SafeTensors` + HuggingFace Tokenizer.
- **Source**: [Hugging Face Hub (DistilRoBERTa-base)](https://huggingface.co/distilbert/distilroberta-base)
- **Architecture**: 6 layers, 768 hidden dimensions, 12 attention heads (~82M parameters).

### 2. Qwen 3 (XAI Jurist Agent)
- **Role**: Evaluates anomaly alerts from [`WaveletAE-OCC`](../docs/03_neural_models.md#9-waveletae-occ-high-frequency-anomaly-detector), analyzes multi-model voting conflicts, and generates natural language legal compliance reports.
- **Format**: `GGUF` (Quantization: `Q6_K_XL` or `Q4_K_M`) executed locally via `llama-cpp-python` with Zero Cloud API reliance.
- **Source**: [Hugging Face Hub (Qwen/Qwen2.5-1.5B-Instruct / Qwen3)](https://huggingface.co/Qwen)

---

## 📥 Downloading & Updating Models

To set up or refresh foundational weights in the Model Vault:

### 1. Download DistilRoBERTa via Python
```python
from transformers import AutoTokenizer, AutoModel

model_name = "distilbert/distilroberta-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

tokenizer.save_pretrained("Model_Vault/distilroberta")
model.save_pretrained("Model_Vault/distilroberta")
```

### 2. Download Qwen GGUF Model
```bash
# Using huggingface-cli or curl
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct-GGUF \
    qwen2.5-1.5b-instruct-q6_k.gguf \
    --local-dir Model_Vault/ \
    --local-dir-use-symlinks False
```

---

## 🔒 Security & Git Tracking

Due to size considerations ($> 100\text{ MB}$), large weight files (`*.gguf`, `*.safetensors`, `*.bin`, `*.pt`) are excluded from standard Git tracking via [`.gitignore`](../.gitignore). Documentation files (`Model_Vault/README.md`) remain actively tracked.

Always verify SHA256 checksums when provisioning new edge nodes in production.

---

<p align="center">
  <sub>SYNAPSE Model Vault — Noxfort Systems AI Assets</sub><br/>
  <sub><a href="#synapse-model-vault--pre-trained-weights--neural-assets">Back to top ↑</a></sub>
</p>
