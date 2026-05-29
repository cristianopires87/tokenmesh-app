# Prices in USD per token (divide official per-1M price by 1_000_000)
# Sources: official provider pricing pages : update when providers change rates
MODEL_PRICING = {

    # ── OpenAI : GPT-5 family ─────────────────────────────────────────────────
    # Sources: developers.openai.com/api/docs/models : May 2026
    "gpt-5": {
        "provider": "openai",
        "input":  0.00000125,   # $1.25 / 1M
        "output": 0.00001,      # $10.00 / 1M
    },
    "gpt-5-mini": {
        "provider": "openai",
        "input":  0.00000025,   # $0.25 / 1M
        "output": 0.000002,     # $2.00 / 1M
    },
    "gpt-5-nano": {
        "provider": "openai",
        "input":  0.00000005,   # $0.05 / 1M
        "output": 0.0000004,    # $0.40 / 1M
    },
    "gpt-5.2": {
        "provider": "openai",
        "input":  0.00000175,   # $1.75 / 1M
        "output": 0.000014,     # $14.00 / 1M
    },
    "gpt-5.4": {
        "provider": "openai",
        "input":  0.0000025,    # $2.50 / 1M
        "output": 0.00001,      # $10.00 / 1M (estimated : same tier as gpt-5.4 family)
    },
    "gpt-5.4-mini": {
        "provider": "openai",
        "input":  0.00000075,   # $0.75 / 1M
        "output": 0.0000045,    # $4.50 / 1M
    },
    "gpt-5.4-nano": {
        "provider": "openai",
        "input":  0.0000002,    # $0.20 / 1M
        "output": 0.0000008,    # $0.80 / 1M (estimated)
    },
    "gpt-5.5": {
        "provider": "openai",
        "input":  0.000005,     # $5.00 / 1M
        "output": 0.00003,      # $30.00 / 1M
    },

    # ── OpenAI : GPT-4 family ─────────────────────────────────────────────────
    "gpt-4o": {
        "provider": "openai",
        "input":  0.0000025,
        "output": 0.00001,
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "input":  0.00000015,
        "output": 0.0000006,
    },
    "gpt-4.1": {
        "provider": "openai",
        "input":  0.000002,
        "output": 0.000008,
    },
    "gpt-4.1-mini": {
        "provider": "openai",
        "input":  0.0000004,
        "output": 0.0000016,
    },
    "gpt-4.1-nano": {
        "provider": "openai",
        "input":  0.0000001,
        "output": 0.0000004,
    },
    "gpt-3.5-turbo": {
        "provider": "openai",
        "input":  0.0000005,
        "output": 0.0000015,
    },
    "o1": {
        "provider": "openai",
        "input":  0.000015,
        "output": 0.00006,
    },
    "o1-mini": {
        "provider": "openai",
        "input":  0.0000011,
        "output": 0.0000044,
    },
    "o3": {
        "provider": "openai",
        "input":  0.00001,
        "output": 0.00004,
    },
    "o3-mini": {
        "provider": "openai",
        "input":  0.0000011,
        "output": 0.0000044,
    },
    "o4-mini": {
        "provider": "openai",
        "input":  0.0000011,
        "output": 0.0000044,
    },

    # ── Anthropic : Claude 4 Opus family ─────────────────────────────────────
    # Sources: docs.anthropic.com/en/docs/about-claude/models/overview : May 2026
    "claude-opus-4-8": {          # latest Opus : context: 1M tokens
        "provider": "anthropic",
        "input":  0.000005,        # $5.00 / 1M
        "output": 0.000025,        # $25.00 / 1M
    },
    "claude-opus-4-7": {          # context: 1M tokens
        "provider": "anthropic",
        "input":  0.000005,        # $5.00 / 1M
        "output": 0.000025,        # $25.00 / 1M
    },
    "claude-opus-4-6": {          # context: 1M tokens
        "provider": "anthropic",
        "input":  0.000005,        # $5.00 / 1M
        "output": 0.000025,        # $25.00 / 1M
    },
    "claude-opus-4-5": {          # context: 200k tokens
        "provider": "anthropic",
        "input":  0.000005,        # $5.00 / 1M
        "output": 0.000025,        # $25.00 / 1M
    },
    "claude-opus-4-1": {          # context: 200k tokens
        "provider": "anthropic",
        "input":  0.000015,        # $15.00 / 1M
        "output": 0.000075,        # $75.00 / 1M
    },
    # DEPRECATED : retires 2026-06-15; migrate to claude-opus-4-8
    "claude-opus-4": {
        "provider": "anthropic",
        "input":  0.000015,        # $15.00 / 1M
        "output": 0.000075,        # $75.00 / 1M
    },

    # ── Anthropic : Claude 4 Sonnet family ───────────────────────────────────
    "claude-sonnet-4-6": {        # latest Sonnet : context: 1M tokens
        "provider": "anthropic",
        "input":  0.000003,        # $3.00 / 1M
        "output": 0.000015,        # $15.00 / 1M
    },
    "claude-sonnet-4-5": {        # context: 200k tokens
        "provider": "anthropic",
        "input":  0.000003,        # $3.00 / 1M
        "output": 0.000015,        # $15.00 / 1M
    },
    # DEPRECATED : retires 2026-06-15; migrate to claude-sonnet-4-6
    "claude-sonnet-4": {
        "provider": "anthropic",
        "input":  0.000003,        # $3.00 / 1M
        "output": 0.000015,        # $15.00 / 1M
    },

    # ── Anthropic : Claude 4 Haiku family ────────────────────────────────────
    "claude-haiku-4-5": {         # latest Haiku : context: 200k tokens
        "provider": "anthropic",
        "input":  0.000001,        # $1.00 / 1M
        "output": 0.000005,        # $5.00 / 1M
    },

    # ── Anthropic : Claude 3 family ───────────────────────────────────────────
    "claude-3-opus": {
        "provider": "anthropic",
        "input":  0.000015,
        "output": 0.000075,
    },
    "claude-3-5-sonnet": {
        "provider": "anthropic",
        "input":  0.000003,
        "output": 0.000015,
    },
    "claude-3-5-haiku": {
        "provider": "anthropic",
        "input":  0.0000008,
        "output": 0.000004,
    },
    "claude-3-haiku": {
        "provider": "anthropic",
        "input":  0.00000025,
        "output": 0.00000125,
    },

    # ── DeepSeek ──────────────────────────────────────────────────────────────
    "deepseek-v3": {
        "provider": "deepseek",
        "input":  0.00000027,
        "output": 0.0000011,
    },
    "deepseek-r1": {
        "provider": "deepseek",
        "input":  0.00000055,
        "output": 0.00000219,
    },

    # ── Google ────────────────────────────────────────────────────────────────
    "gemini-2.0-flash": {
        "provider": "google",
        "input":  0.0000001,
        "output": 0.0000004,
    },
    "gemini-1.5-pro": {
        "provider": "google",
        "input":  0.00000125,
        "output": 0.000005,
    },
    "gemini-1.5-flash": {
        "provider": "google",
        "input":  0.000000075,
        "output": 0.0000003,
    },

    # ── AWS Bedrock : Meta Llama ──────────────────────────────────────────────
    # Sources: aws.amazon.com/bedrock/pricing : May 2026 (US East / US West)
    # Provider: "aws_bedrock" : models accessed via Amazon Bedrock on-demand
    "llama-4-maverick": {         # 400B MoE, 1M context
        "provider": "aws_bedrock",
        "input":  0.00000024,      # $0.24 / 1M
        "output": 0.00000097,      # $0.97 / 1M
    },
    "llama-4-scout": {            # 109B MoE (17B active), 10M context
        "provider": "aws_bedrock",
        "input":  0.00000017,      # $0.17 / 1M
        "output": 0.00000017,      # $0.17 / 1M
    },
    "llama-3.3-70b-instruct": {   # 128k context
        "provider": "aws_bedrock",
        "input":  0.00000072,      # $0.72 / 1M
        "output": 0.00000072,      # $0.72 / 1M
    },
    "llama-3.1-8b-instruct": {    # 128k context
        "provider": "aws_bedrock",
        "input":  0.00000022,      # $0.22 / 1M
        "output": 0.00000022,      # $0.22 / 1M
    },
    "llama-2-chat-13b": {
        "provider": "aws_bedrock",
        "input":  0.00000075,      # $0.75 / 1M
        "output": 0.000001,        # $1.00 / 1M
    },
    "llama-2-chat-70b": {
        "provider": "aws_bedrock",
        "input":  0.00000195,      # $1.95 / 1M
        "output": 0.00000256,      # $2.56 / 1M
    },

    # ── Mistral ───────────────────────────────────────────────────────────────
    "mistral-large": {
        "provider": "mistral",
        "input":  0.000002,
        "output": 0.000006,
    },
    "mistral-small": {
        "provider": "mistral",
        "input":  0.0000001,
        "output": 0.0000003,
    },

    # ── Devin (Cognition AI) ──────────────────────────────────────────────────
    # Pricing is ACU-based: 1 ACU = $2.25. Per-token rate is a derived estimate.
    # Assumption: 1 ACU ≈ 100,000 tokens of agent context (code reads + LLM calls).
    # Effective rate: $2.25 / 100,000 = $22.50 / 1M tokens.
    # Input and output are priced equally (ACU does not differentiate).
    "devin-agent": {
        "provider": "devin",
        "input":  0.0000225,    # $22.50 / 1M  (≈ 1 ACU per 100k tokens)
        "output": 0.0000225,    # $22.50 / 1M  (same : ACU-based, no split)
    },
}
