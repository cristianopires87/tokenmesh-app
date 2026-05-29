from tokenmesh.pricing.pricing_table import MODEL_PRICING


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        return 0.0
    return round(
        input_tokens * pricing["input"] + output_tokens * pricing["output"],
        8,
    )
