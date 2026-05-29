def count_tokens(text: str) -> int:
    # ~4 characters per token is a well-known approximation across most LLMs
    return max(1, len(text) // 4)


def tokenize(text: str) -> list[str]:
    chunk = 4
    return [text[i:i + chunk] for i in range(0, len(text), chunk)] or [""]
