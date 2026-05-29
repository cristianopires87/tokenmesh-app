"""
TokenMesh: DeepSeek integration example.

DeepSeek exposes an OpenAI-compatible API, so the openai SDK works directly.

Install: pip install openai
"""
import time
from openai import OpenAI
from tokenmesh import tracker

client = OpenAI(
    api_key="YOUR_DEEPSEEK_API_KEY",
    base_url="https://api.deepseek.com",
)

start = time.time()

response = client.chat.completions.create(
    model="deepseek-v3",
    messages=[
        {"role": "user", "content": "Explain token counting in large language models."}
    ],
)

latency_ms = int((time.time() - start) * 1000)

tracker.track(
    provider="deepseek",
    model="deepseek-v3",
    tenant_id="my_company",
    project_id="my_project",
    agent_id="explainer_agent",
    input_tokens=response.usage.prompt_tokens,
    output_tokens=response.usage.completion_tokens,
    latency_ms=latency_ms,
)

print(response.choices[0].message.content)
