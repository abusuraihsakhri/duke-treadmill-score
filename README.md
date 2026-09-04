# Duke Treadmill Score

> **Domain:** Cardiovascular Medicine & Hemodynamic Analytics  
> **Reference Guidelines & Standards:** AHA/ACC Practice Guidelines & ESC Clinical Standards

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

Duke Treadmill Score Calculator — computes cardiovascular risk scores from clinical factors including smoking, hypertension, diabetes, prior stroke, and vascular disease. Produces a points-based score with tiered risk thresholds (low, moderate, high).

---

## Key Modules

### Core Scoring (`duke.py`)
- **`calculate_score(present)`** — Computes score from a dictionary of clinical factors.
- **`assess_row(row)`** — Maps CSV row data to scoring factors.
- **`process_csv(inp, out)`** — Batch processes CSV files with scoring results.
- **`main()`** — CLI entry point for single and batch operations.

### Enterprise Agent Suite (`agents/`)
- **`supervisor.py`** — Multi-worker orchestration with consensus dossier generation.
- **`workers.py`** — Specialized workers: InvariantQC, SafetyEscalation, ProtocolConformance.
- **`base.py`** — PHI outbound guard and HMAC-SHA256 tamper-evident audit trail.
- **`api.py`** — FastAPI REST server with `/health`, `/metrics`, `/api/audit`, `/api/chat` endpoints.
- **`models.py`** — Pydantic schemas for task payloads, alerts, and dossiers.

### CLI (`cli.py`)
- **`audit`** — Run single task evaluation with multi-worker analysis.
- **`chat`** — Query the supervisory LLM adapter.
- **`batch`** — Batch process CSV records through the agent pipeline.
- **`verify-audit`** — Verify HMAC audit trail integrity.
- **`serve`** — Launch FastAPI REST server.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/duke-treadmill-score.git
cd duke-treadmill-score

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Core Scoring CLI (`duke.py`)

**Single evaluation:**
```bash
python duke.py single --age 68 --sex M --smoking 1 --hypertension 1
```

**With JSON input:**
```bash
python duke.py single --json '{"Smoking": true, "Diabetes": true}'
```

**Batch CSV processing:**
```bash
python duke.py batch --input sample.csv --output results.csv
```

### Enterprise CLI (`cli.py`)

**Run audit evaluation:**
```bash
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2
```

**Batch processing:**
```bash
python cli.py batch -i sample.csv -o results.csv
```

**Verify audit integrity:**
```bash
python cli.py verify-audit
```

**Start API server:**
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

---

## API Endpoints

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/health` | GET | Service health check |
| `/metrics` | GET | Operational metrics |
| `/api/audit` | POST | Submit task for evaluation |
| `/api/chat` | POST | Query supervisory chat |
| `/api/audit/logs` | GET | Retrieve audit trail |

---

## Testing

```bash
# Run full test suite
pytest -v

# Run with coverage
pytest -v --cov=.
```

---

## Security

- **Zero-PHI Outbound Guard:** AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
- **HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation.
- **Secure Defaults:** Audit keys are generated using `secrets.token_hex()` when not provided via environment variable.

### Environment Variables

| Variable | Description | Default |
|:---------|:------------|:--------|
| `AUDIT_SECRET_KEY` | Secret key for HMAC audit trail | Auto-generated (random) |
| `MODEL_PROVIDER` | LLM provider for chat | `mock` |

---

## Docker Deployment

```bash
# Build and run with Docker Compose
AUDIT_SECRET_KEY=$(openssl rand -hex 32) docker-compose up --build

# Or build and run manually
docker build -t duke-treadmill-score .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=$(openssl rand -hex 32) duke-treadmill-score
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
