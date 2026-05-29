import tiktoken


def _get_encoding(model: str):
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        # GPT-5.x models not yet in tiktoken registry; o200k_base is their family
        return tiktoken.get_encoding("o200k_base")


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    return len(_get_encoding(model).encode(text))


def tokenize(text: str, model: str = "gpt-4o") -> list[str]:
    encoding = _get_encoding(model)
    ids = encoding.encode(text)
    return [encoding.decode_single_token_bytes(t).decode("utf-8", errors="replace") for t in ids]


def tokenize_by_encoding(text: str, encoding_name: str) -> list[str]:
    encoding = tiktoken.get_encoding(encoding_name)
    ids = encoding.encode(text)
    return [encoding.decode_single_token_bytes(t).decode("utf-8", errors="replace") for t in ids]
