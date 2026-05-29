import pytest
from tokenmesh.tokenizers import count_tokens
from tokenmesh.tokenizers.generic_tokenizer import count_tokens as generic_count


def test_generic_nonempty_text():
    assert generic_count("Hello world") >= 1


def test_generic_proportional_to_length():
    short = generic_count("Hi")
    long = generic_count("This is a much longer piece of text that should produce more tokens than a short one")
    assert long > short


def test_generic_minimum_is_one():
    assert generic_count("") == 1
    assert generic_count("x") == 1


def test_count_tokens_unknown_provider_falls_back_to_generic():
    result = count_tokens("Hello world", model="some-model", provider="unknown_provider")
    assert result >= 1


def test_count_tokens_openai():
    result = count_tokens("Hello world", model="gpt-4o", provider="openai")
    assert result > 0


def test_count_tokens_anthropic_uses_generic():
    result = count_tokens("Hello world", model="claude-sonnet-4", provider="anthropic")
    assert result >= 1


def test_count_tokens_deepseek_uses_generic():
    result = count_tokens("Hello world", model="deepseek-v3", provider="deepseek")
    assert result >= 1
