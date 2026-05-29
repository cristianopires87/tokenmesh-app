# Context window sizes in tokens per model
# Sources: official provider documentation : May 2026
CONTEXT_WINDOWS: dict[str, int] = {
    # ── OpenAI : GPT-5 ────────────────────────────────────────────────────────
    "gpt-5":        128_000,
    "gpt-5-mini":   128_000,
    "gpt-5-nano":   128_000,
    "gpt-5.2":      128_000,
    "gpt-5.4":      128_000,
    "gpt-5.4-mini": 128_000,
    "gpt-5.4-nano": 128_000,
    "gpt-5.5":      128_000,
    # ── OpenAI : GPT-4 ────────────────────────────────────────────────────────
    "gpt-4o":         128_000,
    "gpt-4o-mini":    128_000,
    "gpt-4.1":      1_047_576,
    "gpt-4.1-mini": 1_047_576,
    "gpt-4.1-nano": 1_047_576,
    "gpt-3.5-turbo":   16_385,
    "o1":             200_000,
    "o1-mini":        128_000,
    "o3":             200_000,
    "o3-mini":        200_000,
    "o4-mini":        200_000,
    # ── Anthropic : Claude 4 Opus family ─────────────────────────────────────
    "claude-opus-4-8":   1_000_000,
    "claude-opus-4-7":   1_000_000,
    "claude-opus-4-6":   1_000_000,
    "claude-opus-4-5":     200_000,
    "claude-opus-4-1":     200_000,
    "claude-opus-4":       200_000,   # deprecated 2026-06-15
    # ── Anthropic : Claude 4 Sonnet family ───────────────────────────────────
    "claude-sonnet-4-6": 1_000_000,
    "claude-sonnet-4-5":   200_000,
    "claude-sonnet-4":     200_000,   # deprecated 2026-06-15
    # ── Anthropic : Claude 4 Haiku family ────────────────────────────────────
    "claude-haiku-4-5":    200_000,
    # ── Anthropic : Claude 3 family ───────────────────────────────────────────
    "claude-3-opus":     200_000,
    "claude-3-5-sonnet": 200_000,
    "claude-3-5-haiku":  200_000,
    "claude-3-haiku":    200_000,
    # ── DeepSeek ──────────────────────────────────────────────────────────────
    "deepseek-v3": 128_000,
    "deepseek-r1": 128_000,
    # ── Google ────────────────────────────────────────────────────────────────
    "gemini-2.0-flash": 1_000_000,
    "gemini-1.5-pro":   2_000_000,
    "gemini-1.5-flash": 1_000_000,
    # ── AWS Bedrock : Meta Llama ──────────────────────────────────────────────
    "llama-4-maverick":        1_000_000,
    "llama-4-scout":          10_000_000,
    "llama-3.3-70b-instruct":    128_000,
    "llama-3.1-8b-instruct":     128_000,
    "llama-2-chat-13b":            4_096,
    "llama-2-chat-70b":            4_096,
    # ── Mistral ───────────────────────────────────────────────────────────────
    "mistral-large":  128_000,
    "mistral-small":   32_000,
    # ── Devin (Cognition AI) ──────────────────────────────────────────────────
    "devin-agent":    128_000,
}
