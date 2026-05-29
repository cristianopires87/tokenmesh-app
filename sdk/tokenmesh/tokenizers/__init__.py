from tokenmesh.tokenizers.openai_tokenizer import (
    count_tokens as _openai_count,
    tokenize as _openai_tokenize,
    tokenize_by_encoding as _tokenize_by_enc,
)
from tokenmesh.tokenizers.generic_tokenizer import (
    count_tokens as _generic_count,
    tokenize as _generic_tokenize,
)

# Providers with a precise tiktoken model mapping
_EXACT_PROVIDERS = {"openai"}

# Providers where cl100k_base (GPT-4 encoding) is a close approximation
_APPROX_ENCODINGS: dict[str, str] = {
    "anthropic": "cl100k_base",
    "deepseek":  "cl100k_base",
    "devin":     "cl100k_base",  # Devin uses Claude/GPT internals; cl100k_base is a reasonable proxy
}


def count_tokens(text: str, model: str, provider: str = "openai") -> int:
    if provider in _EXACT_PROVIDERS:
        try:
            return _openai_count(text, model)
        except Exception:
            pass
    if provider in _APPROX_ENCODINGS:
        try:
            return len(_tokenize_by_enc(text, _APPROX_ENCODINGS[provider]))
        except Exception:
            pass
    return _generic_count(text)


def tokenize(text: str, model: str, provider: str = "openai") -> tuple[list[str], bool]:
    """Return (token_strings, is_exact).

    is_exact=True means the tokenizer matches the provider's real tokenizer.
    is_exact=False means it's an approximation (same BPE family but not identical).
    """
    if provider in _EXACT_PROVIDERS:
        try:
            return _openai_tokenize(text, model), True
        except Exception:
            pass
    if provider in _APPROX_ENCODINGS:
        try:
            return _tokenize_by_enc(text, _APPROX_ENCODINGS[provider]), False
        except Exception:
            pass
    return _generic_tokenize(text), False
