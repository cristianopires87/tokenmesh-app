# TokenMesh

Token observability and cost governance for multi-agent LLM systems.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-1.57-FF4B4B)

---

## Overview

TokenMesh provides two things:

- **Pre-flight calculator:** count tokens and compare costs across providers before making a call
- **Usage collector:** a lightweight HTTP API that records every LLM event from your agents

It supports OpenAI, Anthropic, DeepSeek, Google Gemini, Mistral, and AWS Bedrock out of the box.

---

## Requirements

- Python 3.11+
- Docker (optional, for the PostgreSQL stack)

---

## Installation

### Local (SQLite)

```bash
git clone https://github.com/YOUR_USERNAME/tokenmesh.git
cd tokenmesh
pip install -r requirements.txt   # or: poetry install
cp .env.example .env

# Terminal 1 — Collector API
uvicorn collector.app.main:app --reload

# Terminal 2 — Dashboard
streamlit run dashboard/app.py
```

- Collector: http://localhost:8000
- Dashboard:  http://localhost:8501

### Docker (PostgreSQL)

```bash
git clone https://github.com/YOUR_USERNAME/tokenmesh.git
cd tokenmesh
docker compose up
```

> PostgreSQL requires `psycopg2-binary`: `pip install psycopg2-binary`

---

## SDK Usage

```python
from tokenmesh import tracker

tracker.track(
    provider="openai",
    model="gpt-4o",
    tenant_id="acme_corp",
    project_id="customer_support",
    agent_id="triage_agent",
    input_tokens=850,
    output_tokens=210,
    latency_ms=1100,
)
```

If the Collector is unreachable, the event is printed locally — nothing is silently dropped.

### Custom Collector URL

```python
from tokenmesh.tracker.tracker import TokenTracker

tracker = TokenTracker(collector_url="https://tokenmesh.my-company.com")
```

Or via environment variable:

```bash
export TOKENMESH_COLLECTOR_URL=https://tokenmesh.my-company.com
```

---

## Dashboard

### Token Calculator

Enter any prompt text and get:

- Token count per provider (each uses its own tokenizer)
- Cost comparison across 47+ models
- Context window usage with overflow detection
- Prompt caching ROI and break-even analysis
- Multi-turn cost projection
- Architecture recommendations (pipeline, routing, single-call)
- Budget calculator (calls per month for a given spend)
- Prompt Compressor: flags redundant tokens (comments, stopwords, repeated phrases)
- Token Hotspot: highlights the densest segments
- Template Analyzer: separates fixed from variable sections and marks cache eligibility

### Token Visualizer

Highlights each token with a distinct color, like the OpenAI tokenizer playground, for every supported provider.

| Provider      | Tokenizer            | Accuracy  |
|---------------|----------------------|-----------|
| OpenAI        | tiktoken (exact)     | Exact     |
| Anthropic     | cl100k_base BPE      | ~Approx   |
| DeepSeek      | cl100k_base BPE      | ~Approx   |
| Google Gemini | char-based estimate  | Estimate  |
| Mistral       | char-based estimate  | Estimate  |
| AWS Bedrock   | char-based estimate  | Estimate  |

---

## Supported Models

### OpenAI — GPT-5

| Model          | Input ($/1M) | Output ($/1M) |
|----------------|-------------:|---------------:|
| gpt-5          | $1.25        | $10.00         |
| gpt-5-mini     | $0.25        | $2.00          |
| gpt-5-nano     | $0.05        | $0.40          |
| gpt-5.2        | $1.75        | $14.00         |
| gpt-5.4        | $2.50        | $10.00         |
| gpt-5.4-mini   | $0.75        | $4.50          |
| gpt-5.4-nano   | $0.20        | $0.80          |
| gpt-5.5        | $5.00        | $30.00         |

### OpenAI — GPT-4

| Model          | Input ($/1M) | Output ($/1M) |
|----------------|-------------:|---------------:|
| gpt-4o         | $2.50        | $10.00         |
| gpt-4o-mini    | $0.15        | $0.60          |
| gpt-4.1        | $2.00        | $8.00          |
| gpt-4.1-mini   | $0.40        | $1.60          |
| gpt-4.1-nano   | $0.10        | $0.40          |
| gpt-3.5-turbo  | $0.50        | $1.50          |
| o1             | $15.00       | $60.00         |
| o1-mini        | $1.10        | $4.40          |
| o3             | $10.00       | $40.00         |
| o3-mini        | $1.10        | $4.40          |
| o4-mini        | $1.10        | $4.40          |

### Anthropic — Claude 4

| Model              | Input ($/1M) | Output ($/1M) |
|--------------------|-------------:|---------------:|
| claude-opus-4-8    | $5.00        | $25.00         |
| claude-opus-4-7    | $5.00        | $25.00         |
| claude-opus-4-6    | $5.00        | $25.00         |
| claude-opus-4-5    | $5.00        | $25.00         |
| claude-opus-4-1    | $15.00       | $75.00         |
| claude-sonnet-4-6  | $3.00        | $15.00         |
| claude-sonnet-4-5  | $3.00        | $15.00         |
| claude-haiku-4-5   | $1.00        | $5.00          |

### Anthropic — Claude 3

| Model              | Input ($/1M) | Output ($/1M) |
|--------------------|-------------:|---------------:|
| claude-3-opus      | $15.00       | $75.00         |
| claude-3-5-sonnet  | $3.00        | $15.00         |
| claude-3-5-haiku   | $0.80        | $4.00          |
| claude-3-haiku     | $0.25        | $1.25          |

### DeepSeek

| Model          | Input ($/1M) | Output ($/1M) |
|----------------|-------------:|---------------:|
| deepseek-v3    | $0.27        | $1.10          |
| deepseek-r1    | $0.55        | $2.19          |

### Google Gemini

| Model               | Input ($/1M) | Output ($/1M) |
|---------------------|-------------:|---------------:|
| gemini-2.0-flash    | $0.10        | $0.40          |
| gemini-1.5-pro      | $1.25        | $5.00          |
| gemini-1.5-flash    | $0.075       | $0.30          |

### AWS Bedrock — Meta Llama

| Model                    | Input ($/1M) | Output ($/1M) |
|--------------------------|-------------:|---------------:|
| llama-4-maverick         | $0.24        | $0.97          |
| llama-4-scout            | $0.17        | $0.17          |
| llama-3.3-70b-instruct   | $0.72        | $0.72          |
| llama-3.1-8b-instruct    | $0.22        | $0.22          |
| llama-2-chat-13b         | $0.75        | $1.00          |
| llama-2-chat-70b         | $1.95        | $2.56          |

### Mistral

| Model          | Input ($/1M) | Output ($/1M) |
|----------------|-------------:|---------------:|
| mistral-large  | $2.00        | $6.00          |
| mistral-small  | $0.10        | $0.30          |

### Devin (Cognition AI)

Uses ACU-based pricing (1 ACU = $2.25). The effective rate is derived from a typical session estimate of 100k tokens/ACU and is provided for comparison only.

| Model          | Effective ($/1M) |
|----------------|------------------:|
| devin-agent    | $22.50            |

Missing a model? See [CONTRIBUTING.md](CONTRIBUTING.md) — adding one takes under 5 minutes.

---

## Collector API

| Method | Endpoint                   | Description                                  |
|--------|----------------------------|----------------------------------------------|
| POST   | `/track`                   | Ingest an LLM event                          |
| GET    | `/health`                  | Health check                                 |
| GET    | `/analytics/summary`       | Total tokens, requests, average latency      |
| GET    | `/analytics/costs`         | Total estimated cost in USD                  |
| GET    | `/analytics/providers`     | Tokens and cost grouped by provider          |
| GET    | `/analytics/agents`        | Tokens and cost grouped by agent             |
| GET    | `/analytics/projects`      | Tokens and cost grouped by project           |
| GET    | `/analytics/models`        | Tokens and cost grouped by model             |
| GET    | `/analytics/timeline`      | Daily breakdown (configurable window)        |
| GET    | `/analytics/filters`       | Available tenant/project/agent filter values |

All analytics endpoints accept `?tenant_id=`, `?project_id=`, and `?agent_id=` query parameters.

### POST `/track`

```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "tenant_id": "acme_corp",
  "project_id": "customer_support",
  "agent_id": "triage_agent",
  "input_tokens": 850,
  "output_tokens": 210,
  "latency_ms": 1100
}
```

### GET `/analytics/providers`

```json
[
  {
    "provider": "openai",
    "requests": 15,
    "input_tokens": 34670,
    "output_tokens": 8200,
    "total_tokens": 42870,
    "estimated_cost": 0.124453
  }
]
```

---

## Examples

Ready-to-run scripts in [`examples/`](examples/):

- [`openai_example.py`](examples/openai_example.py) — GPT-4o / GPT-5
- [`claude_example.py`](examples/claude_example.py) — Claude via Anthropic SDK
- [`deepseek_example.py`](examples/deepseek_example.py) — DeepSeek via OpenAI-compatible API
- [`gemini_example.py`](examples/gemini_example.py) — Gemini via Google SDK
- [`llama_bedrock_example.py`](examples/llama_bedrock_example.py) — Meta Llama via AWS Bedrock
- [`multi_agent_example.py`](examples/multi_agent_example.py) — multiple agents and providers

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The most needed contributions are:

- New models or updated pricing
- New provider tokenizers (improved accuracy beyond BPE approximation)
- Dashboard improvements

---

## License

MIT — see [LICENSE](LICENSE).
