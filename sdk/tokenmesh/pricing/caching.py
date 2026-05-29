# Prompt caching configuration per provider
# cache_write_multiplier: cost factor applied to the FIRST call (writing to cache)
# cache_read_multiplier:  cost factor applied to SUBSEQUENT calls (cache hits)
# min_tokens: minimum prompt length required to activate caching

CACHING: dict[str, dict] = {
    "anthropic": {
        "supported": True,
        "cache_write_multiplier": 1.25,  # 25% surcharge to write cache
        "cache_read_multiplier":  0.10,  # 90% discount on cache reads
        "min_tokens": 1_024,
        "note": "Explicit cache_control. Writes cost 1.25×, reads cost 0.10×.",
    },
    "openai": {
        "supported": True,
        "cache_write_multiplier": 1.00,  # automatic, no write surcharge
        "cache_read_multiplier":  0.50,  # 50% discount on cache hits
        "min_tokens": 1_024,
        "note": "Automatic for prompts >1k tokens. Cache reads cost 0.50×.",
    },
    "deepseek": {
        "supported": True,
        "cache_write_multiplier": 1.00,
        "cache_read_multiplier":  0.10,  # 90% discount
        "min_tokens": 1_024,
        "note": "Cache reads at 10% of input price.",
    },
    "google": {
        "supported": True,
        "cache_write_multiplier": 1.00,
        "cache_read_multiplier":  0.25,  # 75% discount
        "min_tokens": 32_768,
        "note": "Context caching for prompts >32k tokens only.",
    },
    "aws_bedrock": {
        "supported": True,
        "cache_write_multiplier": 1.25,  # 25% surcharge to write cache
        "cache_read_multiplier":  0.10,  # 90% discount on cache reads
        "min_tokens": 1_024,
        "note": "Prompt caching via Bedrock cache_point blocks. Writes 1.25×, reads 0.10×.",
    },
    "mistral": {
        "supported": False,
        "note": "No prompt caching available.",
    },
    "devin": {
        "supported": False,
        "note": "ACU-based pricing; prompt caching concept does not apply.",
    },
}


def caching_breakeven(base_cost: float, cache_info: dict) -> int | None:
    """
    Returns the number of calls at which caching becomes cheaper than no caching.
    Returns None if the provider doesn't support caching or base_cost is 0.

    Math:
        No caching:   N × base
        With caching: write + (N-1) × read
        Savings start when: write + (N-1)×read < N×base
        N > (write - read) / (base - read)
    """
    if not cache_info.get("supported") or base_cost <= 0:
        return None

    write = base_cost * cache_info["cache_write_multiplier"]
    read  = base_cost * cache_info["cache_read_multiplier"]

    if base_cost <= read:
        return None

    n = (write - read) / (base_cost - read)
    return max(2, int(n) + 1)


def caching_cost(base_cost: float, cache_info: dict, n_calls: int) -> float:
    """Total cost for n_calls WITH caching enabled."""
    if not cache_info.get("supported") or n_calls <= 0:
        return base_cost * n_calls
    write = base_cost * cache_info["cache_write_multiplier"]
    read  = base_cost * cache_info["cache_read_multiplier"]
    return write + max(0, n_calls - 1) * read
