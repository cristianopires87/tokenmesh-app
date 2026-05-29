from tokenmesh.pricing.calculator import calculate_cost
from tokenmesh.pricing.pricing_table import MODEL_PRICING
from tokenmesh.pricing.context_windows import CONTEXT_WINDOWS
from tokenmesh.pricing.caching import CACHING, caching_breakeven

# ── Content-type detection ─────────────────────────────────────────────────────

_CODE_SIGNALS = [
    "def ", "class ", "import ", "function ", "const ", "let ", "var ",
    "return ", "#include", "public static", "fn main", "#!/",
    "elif ", "while (", "for (", " => ", " -> ", "===", "!==", "::",
]
_SQL_SIGNALS = [
    "select ", "from ", "where ", "join ", "group by",
    "order by", "insert into", "create table", "alter table",
]
_CHAT_SIGNALS = ["user:", "assistant:", "human:", "ai:", "system:", "[user]", "[assistant]"]


def detect_content_type(text: str) -> str:
    t = text.strip()
    tl = t.lower()

    if sum(1 for s in _CODE_SIGNALS if s in t) >= 3:
        return "code"
    if sum(1 for s in _SQL_SIGNALS if s in tl) >= 2:
        return "sql"
    if t.startswith(("{", "[")) and '":' in t:
        return "json"
    if sum(1 for s in _CHAT_SIGNALS if s in tl) >= 2:
        return "conversation"
    lines = [l for l in t.split("\n") if l.strip()]
    if lines and sum(len(l) for l in lines) / len(lines) < 70 and len(lines) >= 4:
        return "conversation"
    return "document"


# ── Size classification ────────────────────────────────────────────────────────

def size_label(tokens: int) -> str:
    if tokens < 100:    return "tiny"
    if tokens < 500:    return "small"
    if tokens < 2_000:  return "medium"
    if tokens < 8_000:  return "large"
    if tokens < 32_000: return "xlarge"
    return "huge"


# ── Output size estimation by content type ────────────────────────────────────

_OUTPUT_ESTIMATE: dict[str, float] = {
    "code":         0.50,   # code review/gen typically ~50% of input
    "sql":          0.20,   # SQL output is compact
    "json":         0.40,   # JSON transform output
    "conversation": 0.30,   # responses shorter than full history
    "document":     0.25,   # summaries/extractions smaller than source
}


# ── Model ranking ──────────────────────────────────────────────────────────────

def _rank_models(input_tokens: int, output_tokens: int) -> list:
    return sorted(
        [
            {
                "model": m,
                "provider": meta["provider"],
                "cost": calculate_cost(m, input_tokens, output_tokens),
            }
            for m, meta in MODEL_PRICING.items()
        ],
        key=lambda x: x["cost"],
    )


# ── Context window filtering ───────────────────────────────────────────────────

def _split_by_context(input_tokens: int, output_tokens: int) -> tuple[list, list]:
    """Return (eligible_sorted_by_cost, excluded) based on context window capacity."""
    total = input_tokens + output_tokens
    eligible: list = []
    excluded: list = []
    for model, meta in MODEL_PRICING.items():
        ctx  = CONTEXT_WINDOWS.get(model, 128_000)
        cost = calculate_cost(model, input_tokens, output_tokens)
        entry = {"model": model, "provider": meta["provider"], "cost": cost, "context": ctx}
        if total <= ctx:
            eligible.append(entry)
        else:
            excluded.append({**entry, "needed": total, "shortfall": total - ctx})
    return sorted(eligible, key=lambda x: x["cost"]), excluded


# ── Tier selection ─────────────────────────────────────────────────────────────

_BALANCED_SET = {
    "gpt-5-mini", "gpt-4o-mini", "gpt-5-nano",
    "claude-haiku-4", "claude-3-5-haiku",
    "gemini-2.0-flash", "gemini-1.5-flash",
    "deepseek-v3",
    "mistral-small",
}
_PREMIUM_SET = {
    "gpt-5.5", "gpt-5", "o3",
    "claude-opus-4",
    "gemini-1.5-pro",
    "deepseek-r1",
    "mistral-large",
}

_TIER_NOTES = {
    "cheapest": "Lowest inference cost, ideal for high-volume or batch workloads.",
    "balanced": "Good reasoning at moderate cost, best for interactive products.",
    "premium": "Highest capability, suited for complex reasoning or flagship features.",
}


def _pick_tiers(ranked: list) -> list:
    cheapest = ranked[0]

    balanced_cands = [r for r in ranked if r["model"] in _BALANCED_SET]
    balanced = balanced_cands[0] if balanced_cands else ranked[max(1, len(ranked) // 3)]

    premium_cands = [r for r in ranked if r["model"] in _PREMIUM_SET]
    premium = premium_cands[0] if premium_cands else ranked[-1]

    # Ensure distinct tiers
    if balanced["model"] == cheapest["model"] and len(ranked) > 1:
        balanced = ranked[1]
    if premium["model"] in {cheapest["model"], balanced["model"]}:
        premium = ranked[-1]

    return [
        {"tier": "cheapest", "label": "Cost-optimized",
         "model": cheapest["model"], "provider": cheapest["provider"],
         "cost": cheapest["cost"], "note": _TIER_NOTES["cheapest"]},
        {"tier": "balanced", "label": "Balanced",
         "model": balanced["model"], "provider": balanced["provider"],
         "cost": balanced["cost"], "note": _TIER_NOTES["balanced"]},
        {"tier": "premium", "label": "Premium",
         "model": premium["model"], "provider": premium["provider"],
         "cost": premium["cost"], "note": _TIER_NOTES["premium"]},
    ]


# ── Content-type tips ──────────────────────────────────────────────────────────

_CONTENT_TIPS: dict[str, list[str]] = {
    "code": [
        "Run a static analyser before the LLM call. Catching syntax errors early halves round-trips.",
        "Use structured output (JSON schema with diff hunks) for reliable patch generation.",
        "Cache the system prompt with language and framework context; it rarely changes per session.",
        "For review tasks, send only the changed file rather than the full repo context.",
    ],
    "sql": [
        "Always run EXPLAIN on generated queries before execution. Never trust raw LLM DDL.",
        "Route simple SELECTs to a nano/haiku model; reserve reasoning models for complex joins.",
        "Enforce table and column names via JSON schema to eliminate hallucinated identifiers.",
        "Add a validation step that parses the generated SQL AST before sending it to the database.",
    ],
    "json": [
        "Enable structured output / response_format to eliminate JSON parse failures entirely.",
        "Strip whitespace and minify before sending. It reduces tokens with zero information loss.",
        "Use schema-first prompting: include only the fields you need in your system prompt.",
        "Validate against a JSON schema in the post-processing step before returning to the user.",
    ],
    "conversation": [
        "Chat history grows quadratically. Compress or summarize after every 5-10 turns.",
        "Apply a sliding window: system prompt + last 3 turns + a running summary of older turns.",
        "Cache the system prompt; it stays constant while the conversation grows.",
        "Use a cheap model to generate the compression summary, premium only for new responses.",
    ],
    "document": [
        "Chunk into segments of up to 2k tokens with 10% overlap for retrieval-augmented generation (RAG).",
        "Store embeddings to avoid resending the full document on every call; retrieve top-k chunks.",
        "Summarise sections independently then synthesise; prevents filling the entire context window.",
        "Use hierarchical summarisation for very long documents: chunks, section summaries, then final.",
    ],
}


# ── Warnings ───────────────────────────────────────────────────────────────────

def _warnings(token_count: int, content_type: str, best_model: str) -> list[str]:
    out = []
    ctx = CONTEXT_WINDOWS.get(best_model, 128_000)
    pct = token_count / ctx * 100
    ctx_k = ctx // 1_000 if ctx < 1_000_000 else f"{ctx/1_000_000:.1f}M"
    if pct > 90:
        out.append(
            f"Input uses {pct:.0f}% of {best_model}'s {ctx_k}k context window; "
            "output may not fit. Consider compression or chunking."
        )
    elif pct > 70:
        out.append(
            f"Input uses {pct:.0f}% of {best_model}'s {ctx_k}k context window; "
            "leave headroom for the response."
        )
    if token_count > 50_000:
        out.append("Very large input. Expect latency of 15-40 s across most providers.")
    if content_type == "conversation" and token_count > 4_000:
        out.append(
            "Chat history exceeds 4k tokens. Apply compression now to prevent "
            "quadratic cost growth."
        )
    return out


# ── Caching tip ────────────────────────────────────────────────────────────────

def _caching_tip(model: str, provider: str, token_count: int) -> str | None:
    info = CACHING.get(provider, {"supported": False})
    if not info.get("supported"):
        return None
    min_tok = info.get("min_tokens", 1_024)
    if token_count < min_tok:
        return (
            f"Prompt caching for {provider} activates at {min_tok:,} tokens. "
            f"Your input ({token_count:,} tokens) is below that threshold. "
            "Consider padding the system prompt with reusable context to unlock it."
        )
    base_cost = calculate_cost(model, token_count, 0)
    be = caching_breakeven(base_cost, info)
    read_pct = int((1 - info["cache_read_multiplier"]) * 100)
    if be:
        return (
            f"Caching eligible: {provider} saves {read_pct}% on repeated reads. "
            f"Break-even at {be} calls; highly profitable for repeated system prompts "
            "such as RAG context, instructions, or few-shot examples."
        )
    return None


# ── Main suggestion function ───────────────────────────────────────────────────

def suggest_architecture(token_count: int, text: str) -> dict:
    content_type = detect_content_type(text)
    size = size_label(token_count)
    gpt4o_cost = calculate_cost("gpt-4o", token_count, token_count)

    est_output = max(50, int(token_count * _OUTPUT_ESTIMATE.get(content_type, 1.0)))
    ranked, excluded_models = _split_by_context(token_count, est_output)
    if not ranked:
        ranked = _rank_models(token_count, est_output)
        excluded_models = []

    best = ranked[0]
    runner_up = ranked[1] if len(ranked) > 1 else None

    out_ext = max(1, token_count // 4)
    use_pipeline = False
    cost_ext = cost_rea = 0.0

    if token_count >= 4_000:
        cost_ext = calculate_cost(best["model"], token_count, out_ext)
        cost_rea = calculate_cost(best["model"], out_ext, max(1, out_ext // 2))
        if cost_ext + cost_rea < best["cost"]:
            use_pipeline = True

    # Routing: lightweight classifier before the main model
    use_routing = False
    router_model = router_provider = None
    router_in = router_out = router_cost = 0.0

    if not use_pipeline and token_count >= 1_000:
        router_ranked = _rank_models(min(token_count, 500), 50)
        r = router_ranked[0]
        if r["model"] != best["model"]:
            use_routing = True
            router_model    = r["model"]
            router_provider = r["provider"]
            router_in       = min(token_count, 500)
            router_out      = 50
            router_cost     = r["cost"]

    # ── Build steps and narrative ──────────────────────────────────────────────

    if use_pipeline:
        total_cost = cost_ext + cost_rea
        saving_pct = round((1 - total_cost / best["cost"]) * 100)
        steps = [
            {
                "role": "Extractor",
                "model": best["model"],
                "desc": f"Reads full {content_type} ({token_count:,} tokens), outputs a compressed summary (~{out_ext:,} tokens)",
                "why": f"Cheapest model handles the expensive read; compression is mechanical, not semantic.",
                "input_tokens": token_count,
                "output_tokens": out_ext,
                "cost": cost_ext,
            },
            {
                "role": "Reasoner",
                "model": best["model"],
                "desc": f"Reasons over the {out_ext:,}-token summary, generates the final response",
                "why": "Compressed context cuts this step's cost significantly. Model sees ~25% of original.",
                "input_tokens": out_ext,
                "output_tokens": max(1, out_ext // 2),
                "cost": cost_rea,
            },
        ]
        headline = f"2-step pipeline: {saving_pct}% cheaper than a single {best['model']} call"
        rationale = (
            f"At {token_count:,} tokens, splitting into extract + reason costs "
            f"${total_cost:.6f} vs ${best['cost']:.6f} for a single pass. "
            f"The extractor compresses the {content_type} to ~25% ({out_ext:,} tokens), "
            f"so the reasoner works on a fraction of the original input."
        )
        approach = "pipeline"

    elif use_routing:
        main_cost  = best["cost"]
        total_cost = router_cost + main_cost
        steps = [
            {
                "role": "Router",
                "model": router_model,
                "desc": f"Classifies intent and selects downstream model (reads up to 500 tokens, outputs ~50)",
                "why": "Classification needs no reasoning power; cheapest possible model keeps overhead near zero.",
                "input_tokens": int(router_in),
                "output_tokens": int(router_out),
                "cost": router_cost,
            },
            {
                "role": "Main",
                "model": best["model"],
                "desc": f"Handles the routed {content_type} task ({token_count:,} tokens)",
                "why": f"Lowest-cost model for this token count across all {len(MODEL_PRICING)} options.",
                "input_tokens": token_count,
                "output_tokens": token_count,
                "cost": main_cost,
            },
        ]
        headline = f"Router to {best['model']}: intent classification for multi-task systems"
        rationale = (
            f"A lightweight router classifies the request before passing it to "
            f"{best['model']} ({best['provider']}). Useful in systems that serve multiple "
            f"intent types: the router can redirect simple requests to nano-tier models "
            f"and complex ones to premium models, reducing blended cost significantly."
        )
        approach = "routing"

    else:
        total_cost = best["cost"]
        runner_note = (
            f" Next cheapest: {runner_up['model']} at ${runner_up['cost']:.6f}."
            if runner_up else ""
        )
        steps = [
            {
                "role": "Main",
                "model": best["model"],
                "desc": f"Handles the full {content_type} request ({token_count:,} tokens)",
                "why": f"Lowest cost across all {len(MODEL_PRICING)} models at this exact token count.",
                "input_tokens": token_count,
                "output_tokens": token_count,
                "cost": best["cost"],
            }
        ]
        headline = f"Direct call to {best['model']}, {token_count:,} tokens"
        rationale = (
            f"Evaluated across all {len(MODEL_PRICING)} models in real time: "
            f"{best['model']} ({best['provider']}) is cheapest at ${best['cost']:.6f} "
            f"for this input size.{runner_note}"
        )
        approach = "single"

    savings_vs_gpt4o = round((1 - total_cost / gpt4o_cost) * 100) if gpt4o_cost > 0 else 0

    return {
        # Core fields (unchanged shape)
        "content_type": content_type,
        "size": size,
        "token_count": token_count,
        "approach": approach,
        "steps": steps,
        "headline": headline,
        "rationale": rationale,
        "savings_vs_gpt4o_pct": max(0, savings_vs_gpt4o),
        "total_cost": total_cost,
        # Extended fields
        "tiers": _pick_tiers(ranked),
        "warnings": _warnings(token_count, content_type, best["model"]),
        "caching_tip": _caching_tip(best["model"], best["provider"], token_count),
        "content_tips": _CONTENT_TIPS.get(content_type, []),
        # Context window filtering results
        "excluded_models":         excluded_models,
        "estimated_output_tokens": est_output,
    }
