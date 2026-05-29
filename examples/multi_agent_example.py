"""
TokenMesh: Multi-agent, multi-provider example.

Shows how a pipeline with three specialized agents, each using a different
LLM provider, reports token usage under the same tenant and project.

This is the core use case TokenMesh is built for.
"""
import time
from openai import OpenAI
import anthropic
from tokenmesh import tracker

openai_client = OpenAI()
anthropic_client = anthropic.Anthropic()

TENANT = "acme_corp"
PROJECT = "document_pipeline"


# ── Agent 1: Extractor (GPT-4o-mini, cheap and fast) ─────────────────────────

def run_extractor(document: str) -> str:
    start = time.time()
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Extract the key facts from the document."},
            {"role": "user", "content": document},
        ],
    )
    tracker.track(
        provider="openai",
        model="gpt-4o-mini",
        tenant_id=TENANT,
        project_id=PROJECT,
        agent_id="extractor_agent",
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        latency_ms=int((time.time() - start) * 1000),
    )
    return response.choices[0].message.content


# ── Agent 2: Analyst (Claude Sonnet, balanced cost/quality) ───────────────────

def run_analyst(facts: str) -> str:
    start = time.time()
    response = anthropic_client.messages.create(
        model="claude-sonnet-4",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": f"Analyse these facts and provide insights:\n\n{facts}"},
        ],
    )
    tracker.track(
        provider="anthropic",
        model="claude-sonnet-4",
        tenant_id=TENANT,
        project_id=PROJECT,
        agent_id="analyst_agent",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        latency_ms=int((time.time() - start) * 1000),
    )
    return response.content[0].text


# ── Agent 3: Summariser (GPT-4o, high quality for final output) ──────────────

def run_summariser(analysis: str) -> str:
    start = time.time()
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Write a concise executive summary."},
            {"role": "user", "content": analysis},
        ],
    )
    tracker.track(
        provider="openai",
        model="gpt-4o",
        tenant_id=TENANT,
        project_id=PROJECT,
        agent_id="summariser_agent",
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        latency_ms=int((time.time() - start) * 1000),
    )
    return response.choices[0].message.content


# ── Pipeline ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    document = """
    Q1 2025 results: revenue grew 18% YoY to $4.2B. Operating margin improved
    to 24% from 19% in Q1 2024. Headcount increased by 340 to 12,800 globally.
    Key driver: enterprise segment up 31%, offsetting a 5% decline in SMB.
    """

    facts = run_extractor(document)
    analysis = run_analyst(facts)
    summary = run_summariser(analysis)

    print("=== Executive Summary ===")
    print(summary)
    print("\nAll agent events tracked. Check the TokenMesh dashboard at http://localhost:8501")
