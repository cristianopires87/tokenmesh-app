from tokenmesh import tracker


tracker.track(
    provider="openai",
    model="gpt-5",
    tenant_id="itau_bba",
    project_id="crm_ai",
    agent_id="cadastro_agent",
    input_tokens=1500,
    output_tokens=300,
    latency_ms=1200
)
