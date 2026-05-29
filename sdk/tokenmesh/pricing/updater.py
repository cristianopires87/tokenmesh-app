"""
Fetches model prices from LiteLLM's community-maintained pricing database.
Caches results to ~/.tokenmesh/prices_cache.json for 24 hours.
Falls back to hardcoded pricing_table.py on any error.

Source: github.com/BerriAI/litellm : model_prices_and_context_window.json
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

import httpx

from tokenmesh.pricing.pricing_table import MODEL_PRICING as _FALLBACK

log = logging.getLogger(__name__)

LITELLM_URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/main/"
    "model_prices_and_context_window.json"
)
CACHE_PATH    = Path.home() / ".tokenmesh" / "prices_cache.json"
CACHE_TTL     = 86_400  # 24 h
# Increment whenever models are added/removed from pricing_table.py so the
# disk cache is automatically invalidated without manual deletion.
CACHE_VERSION = len(_FALLBACK)

# Maps each TokenMesh model name to LiteLLM key candidates (tried in order).
# LiteLLM sometimes uses versioned suffixes or provider/ prefixes.
_KEY_MAP: dict[str, list[str]] = {
    # ── OpenAI ────────────────────────────────────────────────────────────────
    "gpt-5":          ["gpt-5"],
    "gpt-5-mini":     ["gpt-5-mini"],
    "gpt-5-nano":     ["gpt-5-nano"],
    "gpt-5.2":        ["gpt-5.2"],
    "gpt-5.4":        ["gpt-5.4"],
    "gpt-5.4-mini":   ["gpt-5.4-mini"],
    "gpt-5.4-nano":   ["gpt-5.4-nano"],
    "gpt-5.5":        ["gpt-5.5"],
    "gpt-4o":         ["gpt-4o"],
    "gpt-4o-mini":    ["gpt-4o-mini"],
    "gpt-4.1":        ["gpt-4.1"],
    "gpt-4.1-mini":   ["gpt-4.1-mini"],
    "gpt-4.1-nano":   ["gpt-4.1-nano"],
    "gpt-3.5-turbo":  ["gpt-3.5-turbo"],
    "o1":             ["o1"],
    "o1-mini":        ["o1-mini"],
    "o3":             ["o3"],
    "o3-mini":        ["o3-mini"],
    "o4-mini":        ["o4-mini"],
    # ── Anthropic ─────────────────────────────────────────────────────────────
    "claude-opus-4":     ["claude-opus-4-5", "claude-opus-4"],
    "claude-sonnet-4":   ["claude-sonnet-4-5", "claude-sonnet-4"],
    "claude-haiku-4":    ["claude-haiku-4-5", "claude-haiku-4"],
    "claude-3-opus":     ["claude-3-opus-20240229", "claude-3-opus"],
    "claude-3-5-sonnet": ["claude-3-5-sonnet-20241022", "claude-3-5-sonnet-20240620"],
    "claude-3-5-haiku":  ["claude-3-5-haiku-20241022", "claude-3-5-haiku"],
    "claude-3-haiku":    ["claude-3-haiku-20240307", "claude-3-haiku"],
    # ── DeepSeek ──────────────────────────────────────────────────────────────
    "deepseek-v3": ["deepseek/deepseek-chat-v3-0324", "deepseek/deepseek-chat"],
    "deepseek-r1": ["deepseek/deepseek-reasoner", "deepseek/deepseek-r1"],
    # ── Google ────────────────────────────────────────────────────────────────
    "gemini-2.0-flash": ["gemini/gemini-2.0-flash", "gemini/gemini-2.0-flash-001"],
    "gemini-1.5-pro":   ["gemini/gemini-1.5-pro", "gemini/gemini-1.5-pro-latest"],
    "gemini-1.5-flash": ["gemini/gemini-1.5-flash", "gemini/gemini-1.5-flash-latest"],
    # ── Mistral ───────────────────────────────────────────────────────────────
    "mistral-large": ["mistral/mistral-large-latest", "mistral-large-latest"],
    "mistral-small": ["mistral/mistral-small-latest", "mistral-small-latest"],
    # ── Devin : ACU-based, no LiteLLM entry expected; fallback price is used ─
    "devin-agent":   [],
}


def _resolve(raw: dict, tm_model: str) -> Optional[dict]:
    """Return {input, output} prices for tm_model using the first matching LiteLLM key."""
    for key in _KEY_MAP.get(tm_model, [tm_model]):
        entry = raw.get(key)
        if not entry:
            continue
        inp = entry.get("input_cost_per_token")
        out = entry.get("output_cost_per_token")
        if inp is not None and out is not None:
            return {"input": float(inp), "output": float(out)}
    return None


def _fetch_and_map() -> tuple[dict, list[str]]:
    """
    Download LiteLLM JSON and map to MODEL_PRICING format.
    Returns (pricing_dict, list_of_updated_model_names).
    """
    resp = httpx.get(LITELLM_URL, timeout=10, follow_redirects=True, verify=False)
    resp.raise_for_status()
    raw = resp.json()

    result: dict  = {}
    changed: list = []

    for tm_model, fallback_meta in _FALLBACK.items():
        resolved = _resolve(raw, tm_model)
        if resolved:
            new_entry = {"provider": fallback_meta["provider"], **resolved}
            if abs(new_entry["input"]  - fallback_meta["input"])  > 1e-12 or \
               abs(new_entry["output"] - fallback_meta["output"]) > 1e-12:
                changed.append(tm_model)
            result[tm_model] = new_entry
        else:
            result[tm_model] = fallback_meta

    return result, changed


def load_model_pricing() -> tuple[dict, dict]:
    """
    Returns (MODEL_PRICING, meta).

    meta keys:
      source      "live" | "cache" | "fallback"
      updated_at  unix timestamp (float) or None
      changed     list of model names whose prices differ from hardcoded values
    """
    # ── Try disk cache ─────────────────────────────────────────────────────────
    if CACHE_PATH.exists():
        try:
            cached = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            age_ok     = time.time() - cached.get("ts", 0) < CACHE_TTL
            version_ok = cached.get("version") == CACHE_VERSION
            if age_ok and version_ok:
                return cached["data"], {
                    "source":     "cache",
                    "updated_at": cached["ts"],
                    "changed":    cached.get("changed", []),
                }
        except Exception as exc:
            log.debug("Cache read failed: %s", exc)

    # ── Try live fetch ─────────────────────────────────────────────────────────
    try:
        data, changed = _fetch_and_map()
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(
            json.dumps({"ts": time.time(), "version": CACHE_VERSION,
                        "data": data, "changed": changed}),
            encoding="utf-8",
        )
        return data, {
            "source":     "live",
            "updated_at": time.time(),
            "changed":    changed,
        }
    except Exception as exc:
        log.warning("LiteLLM price fetch failed (%s) : using fallback.", exc)
        return _FALLBACK, {"source": "fallback", "updated_at": None, "changed": []}
