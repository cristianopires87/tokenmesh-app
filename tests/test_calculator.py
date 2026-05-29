import pytest
from tokenmesh.pricing.calculator import calculate_cost


def test_known_model_returns_nonzero():
    assert calculate_cost("gpt-4o", 1000, 500) > 0


def test_unknown_model_returns_zero():
    assert calculate_cost("non-existent-model-xyz", 1000, 500) == 0.0


def test_zero_tokens_returns_zero():
    assert calculate_cost("gpt-4o", 0, 0) == 0.0


def test_cost_formula_gpt4o():
    # gpt-4o: input=$2.50/1M → $2.50 for 1M input tokens, $0 output
    cost = calculate_cost("gpt-4o", 1_000_000, 0)
    assert cost == pytest.approx(2.50, rel=1e-3)


def test_output_more_expensive_than_input():
    # For every provider, output price > input price
    for model in ("gpt-4o", "claude-sonnet-4", "deepseek-v3", "gemini-2.0-flash"):
        input_cost = calculate_cost(model, 1000, 0)
        output_cost = calculate_cost(model, 0, 1000)
        assert output_cost > input_cost, f"{model}: output should cost more than input"


def test_deepseek_cheaper_than_gpt4o():
    deepseek = calculate_cost("deepseek-v3", 10_000, 5_000)
    gpt4o = calculate_cost("gpt-4o", 10_000, 5_000)
    assert deepseek < gpt4o


def test_all_providers_have_entries():
    expected_providers = {"openai", "anthropic", "deepseek", "google", "mistral"}
    from tokenmesh.pricing.pricing_table import MODEL_PRICING
    found_providers = {v["provider"] for v in MODEL_PRICING.values()}
    assert expected_providers.issubset(found_providers)


def test_result_precision():
    cost = calculate_cost("gpt-4o", 123, 456)
    # Should not raise and should be a float
    assert isinstance(cost, float)
