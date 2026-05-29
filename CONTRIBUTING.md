# Contributing to TokenMesh

Thank you for helping keep this repository useful for the community.

The most frequent and impactful contributions are **adding new models** and **updating prices** — providers change their pricing often, and the table needs to stay current.

---

## Adding or updating a model price

Pricing lives in two files that must be kept in sync:

| File | Purpose |
|------|---------|
| `sdk/tokenmesh/pricing/pricing_table.py` | Used by the SDK for local cost estimation |
| `collector/app/pricing.py` | Used by the Collector API when persisting events |

### Steps

1. Fork the repository and create a branch:
   ```bash
   git checkout -b pricing/add-MODEL_NAME
   ```

2. Open both pricing files and add (or update) the model entry:

   ```python
   "model-name-exactly-as-api-returns": {
       "provider": "provider_name",   # openai | anthropic | deepseek | google | mistral | ...
       "input":  0.000003,            # USD per token  =  (price per 1M tokens) / 1_000_000
       "output": 0.000015,
   },
   ```

   > **How to convert:** if the provider charges $3.00 per 1M input tokens, the per-token price is `3.00 / 1_000_000 = 0.000003`.

3. Add the same entry to **both files**.

4. Add a source comment or link to the official pricing page in the PR description so reviewers can verify.

5. Open a pull request with the title `pricing: add MODEL_NAME (PROVIDER)`.

---

## Adding a new provider

1. Add all known models to both pricing files (follow the format above).

2. If the provider has a dedicated tokenizer, add it under `sdk/tokenmesh/tokenizers/`:

   ```python
   # sdk/tokenmesh/tokenizers/my_provider_tokenizer.py
   def count_tokens(text: str, model: str) -> int:
       # provider-specific logic here
       ...
   ```

   If no official tokenizer is available, use the generic character-based estimate:
   `tokens ≈ len(text) / 4`

3. Add an example under `examples/my_provider_example.py` showing a real call followed by `tracker.track()`.

---

## Running locally

```bash
poetry install
cp .env.example .env
poetry run uvicorn collector.app.main:app --reload
```

---

## Pull request checklist

- [ ] Both pricing files updated (if adding/changing a model)
- [ ] Prices sourced from official provider documentation
- [ ] Source URL included in the PR description
- [ ] Example added or updated (for new providers)
- [ ] No unrelated changes included

---

## Reporting outdated prices

If you notice a price is wrong but don't want to submit a PR, open an issue with:

- Model name
- Correct input/output price per 1M tokens
- Link to the official pricing page

---

## Code contributions

For bug fixes or new features, open an issue first to discuss the approach. This keeps everyone aligned before writing code.
