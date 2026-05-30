# Contributing to TokenMesh

Contributions are welcome. The most common ones are **adding new models** and **fixing prices** — providers update pricing often.

---

## Updating prices

Prices are kept in two files that must stay in sync:

- `sdk/tokenmesh/pricing/pricing_table.py` — used by the SDK
- `collector/app/pricing.py` — used by the Collector API

Add or update an entry in both:

```python
"model-id-as-returned-by-api": {
    "provider": "openai",   # openai | anthropic | google | mistral | ...
    "input":  0.000003,     # USD per token  (price per 1M / 1_000_000)
    "output": 0.000015,
},
```

Include a link to the official pricing page in the PR description.

PR title format: `pricing: add MODEL_NAME (PROVIDER)`

---

## Adding a new provider

1. Add all known models to both pricing files.
2. If there's an official tokenizer, add it under `sdk/tokenmesh/tokenizers/`. Otherwise, the generic estimate (`len(text) / 4`) is fine.
3. Add an example under `examples/` showing a real call with `tracker.track()`.

---

## Running locally

```bash
poetry install
cp .env.example .env
poetry run uvicorn collector.app.main:app --reload
```

---

## PR checklist

- [ ] Both pricing files updated
- [ ] Prices sourced from official docs
- [ ] Source URL in PR description
- [ ] Example added for new providers

---

## Reporting outdated prices

Open an issue with the model name, correct prices per 1M tokens, and a link to the provider's pricing page.

---

## Bug fixes and features

Open an issue first to align on the approach before writing code.

---

## Review and merging

All pull requests require review and approval by the maintainer ([@cristianopires](https://github.com/cristianopires)) before merging.
