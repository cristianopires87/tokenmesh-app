"""
TokenMesh: Anthropic (Claude) integration example.

Install: pip install anthropic
"""
import time
import anthropic
from tokenmesh import tracker

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

start = time.time()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    messages=[
        {"role": "user", "content": "Explain token counting in large language models."}
    ],
)

latency_ms = int((time.time() - start) * 1000)

tracker.track(
    provider="anthropic",
    model="claude-sonnet-4-6",
    tenant_id="my_company",
    project_id="my_project",
    agent_id="explainer_agent",
    input_tokens=response.usage.input_tokens,
    output_tokens=response.usage.output_tokens,
    latency_ms=latency_ms,
)

print(response.content[0].text)
